import typing

import services
import snippets
import zone
from NeonOcean.Order import Director, Information, Mods, This
from NeonOcean.Order.Tools import Exceptions
from sims4 import localization
from sims4.tuning import tunable

IdentifiersTemplate = tunable.TunableMapping(
	description = "A dictionary of identifiers and their corresponding localization string keys.",
	key_type = tunable.Tunable(description = "The identifier of the localization string.",
							   tunable_type = str,
							   default = None),

	value_type = tunable.Tunable(description = "The key used to find the localization string.",
								 tunable_type = int,
								 default = 0))  # type: tunable.TunableMapping

IdentifiersSnippetName = Information.GlobalNamespace.replace(".", "_") + "_Language_Identifiers"  # type: str

IdentifiersSnippetReference = None  # type: snippets.TunableSnippetReference
IdentifiersSnippet = None  # type: snippets.TunableSnippet

_identifiers = list()  # type: typing.List[_Identifier]

class String:
	def __init__ (self, identifier: str):
		self.Identifier = identifier  # type: str

	def GetLocalizationString (self, *tokens) -> localization.LocalizedString:
		return GetLocalizationStringByIdentifier(self.Identifier, *tokens)

	def GetCallableLocalizationString (self, *tokens) -> typing.Callable[[], localization.LocalizedString]:
		return lambda *args, **kwargs: self.GetLocalizationString(*tokens)

class _Identifier:
	def __init__ (self, identifier: str, stringKey: int = None):
		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		if stringKey is not None:
			if not isinstance(stringKey, int):
				raise Exceptions.IncorrectTypeException(stringKey, "stringKey", (int,))

		self.Identifier = identifier  # type: str
		self.StringKey = stringKey  # type: typing.Optional[int]

		self.Children = list()  # type: typing.List[_Identifier]

	def Get (self, identifierSegments: typing.List[str]):
		"""
		Gets the identifier object corresponding to the first string of 'identifierSegments'.
		The remaining identifier segments will be passed to the found identifier object.
		If the identifier object doesn't exist one will be created.
		:rtype identifierSegments: typing.List[str]
		:rtype: _Identifier
		"""

		identifierSegmentLower = identifierSegments[0].lower()  # type: str

		for identifierObject in self.Children:  # type: _Identifier
			if identifierObject.Identifier.lower() == identifierSegmentLower:
				if len(identifierSegments) > 1:
					return identifierObject.Get(identifierSegments[1:])
				else:
					return identifierObject

		targetIdentifierObject = _Identifier(identifierSegments[0])  # type: _Identifier
		self.Children.append(targetIdentifierObject)

		if len(identifierSegments) > 1:
			return targetIdentifierObject.Get(identifierSegments[1:])
		else:
			return targetIdentifierObject

class _AnnouncerReliable(Director.Controller):
	Host = This.Mod
	Reliable = True  # type: bool

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		_LoadEntries()

def GetLocalizationStringByIdentifier (identifier: str, *tokens) -> localization.LocalizedString:
	"""
	Find localized string by identifier. No identifiers will be loaded until a zone is loaded.
	:param identifier: This function will look through the list or registered entries to find one with this identifier.
					   Case will be ignored while searching for the identifier.
					   If the corresponding identifier object cannot be found a localization string will be created containing the identifier.
	:type identifier: str
	:param tokens: Valid tokens include any object with a function called "populate_localization_token", numbers, strings, LocalizedString objects, and arrays.
	 			   Array tokens seem to be considered lists of sims and all objects inside them require the "populate_localization_token" function.
	:rtype: localization.LocalizedString
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	identifierObject = _GetIdentifierObject(_SplitIdentifier(identifier))

	if identifierObject.StringKey is not None:
		return GetLocalizationStringByKey(identifierObject.StringKey, *tokens)
	else:
		return CreateLocalizationString(identifier)

def GetLocalizationStringByKey (stringKey: int, *tokens) -> localization.LocalizedString:
	"""
	Find localized string by key.
	:param stringKey: The key for the desired localization string.
	:type stringKey: int
	:param tokens: Valid tokens include any object with a function called "populate_localization_token", numbers, strings, LocalizedString objects, and arrays.
	 			   Array tokens seem to be considered lists of sims and all objects inside them require the "populate_localization_token" function.
	:rtype: localization.LocalizedString
	"""

	if not isinstance(stringKey, int):
		raise Exceptions.IncorrectTypeException(stringKey, "stringKey", (int,))

	localized = localization.LocalizedString()
	localized.hash = stringKey
	# noinspection PyUnresolvedReferences
	localization.create_tokens(localized.tokens, *tokens)

	return localized

def CreateLocalizationString (text: str) -> localization.LocalizedString:
	"""
	Creates a localized string from a normal string.
	:param text: The string that will be used as the localization string.
	:rtype: localization.LocalizedString
	"""

	if not isinstance(text, str):
		raise Exceptions.IncorrectTypeException(text, "text", (str,))

	return localization.LocalizationHelperTuning.get_raw_text(text)

def _SplitIdentifier (identifier: str) -> typing.List[str]:
	return identifier.split(".")  # type: typing.List[str]

def _GetIdentifierObject (identifierSegments: typing.List[str]) -> _Identifier:
	identifierSegmentLower = identifierSegments[0].lower()  # type: str

	for identifierObject in _identifiers:  # type: _Identifier
		if identifierObject.Identifier.lower() == identifierSegmentLower:
			if len(identifierSegments) > 1:
				return identifierObject.Get(identifierSegments[1:])
			else:
				return identifierObject

	targetIdentifierObject = _Identifier(identifierSegments[0])  # type: _Identifier
	_identifiers.append(targetIdentifierObject)

	if len(identifierSegments) > 1:
		return targetIdentifierObject.Get(identifierSegments[1:])
	else:
		return targetIdentifierObject

def _LoadEntries () -> None:
	for snippetID, snippet in services.snippet_manager().types.items():  # type: snippets.SnippetInstanceMetaclass
		if isinstance(snippet, snippets.SnippetInstanceMetaclass):
			if snippet.snippet_type == IdentifiersSnippetName:
				for identifier, stringKey in snippet.value.items():  # type: str, int
					identifierSegments = _SplitIdentifier(identifier)  # type: typing.List[str]
					targetIdentifierObject = _GetIdentifierObject(identifierSegments)  # type: _Identifier

					if targetIdentifierObject.StringKey is None:
						targetIdentifierObject.StringKey = stringKey

def _Setup ():
	global IdentifiersSnippetReference, IdentifiersSnippet

	if not Mods.IsInstalled("NeonOcean.Main"):
		IdentifiersSnippetReference, IdentifiersSnippet = snippets.define_snippet(IdentifiersSnippetName, IdentifiersTemplate)

_Setup()
