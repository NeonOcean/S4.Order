from __future__ import annotations

import typing

import services
import snippets
import zone
from NeonOcean.S4.Order import Director, Information, This
from NeonOcean.S4.Order.Tools import Exceptions
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

IdentifiersSnippetReference: snippets.TunableSnippetReference
IdentifiersSnippet: snippets.TunableSnippet

_identifiers = list()  # type: typing.List[_Identifier]

class String:
	def __init__ (self, identifierOrKey: typing.Union[str, int], fallbackText: str = None):
		"""
		:param identifierOrKey: The identifier or key of the desired string, it this value is a string the function 'GetLocalizationStringByIdentifier' will be
		used, otherwise the function 'GetLocalizationStringByKey' is used instead.
		:type identifierOrKey: str | int
		:param fallbackText: The fallback text, this is only used if an identifier is specified and it has not been registered. I
		:type fallbackText: str | None
		"""

		if not isinstance(identifierOrKey, str) and not isinstance(identifierOrKey, int):
			raise Exceptions.IncorrectTypeException(identifierOrKey, "identifierOrKey", (str, int))

		if not isinstance(fallbackText, str) and fallbackText is not None:
			raise Exceptions.IncorrectTypeException(fallbackText, "fallbackText", (str, None))

		self._identifierOrKey = identifierOrKey  # type: typing.Union[str, int]
		self._fallbackText = fallbackText

	@property
	def IdentifierOrKey (self) -> typing.Union[str, int]:
		return self._identifierOrKey

	@property
	def FallbackText (self) -> str:
		if self._fallbackText is not None:
			return self._fallbackText
		elif isinstance(self.IdentifierOrKey, str):
			return self.IdentifierOrKey
		else:
			return ""

	def IdentifierIsRegistered (self) -> bool:
		"""
		Whether or not the specified identifier has been registered with a key. No identifiers will be loaded until a zone is loaded.
		"""

		if isinstance(self.IdentifierOrKey, str):
			return IdentifierIsRegistered(self.IdentifierOrKey)

		return True

	def GetLocalizationString (self, *tokens, fallbackText: str = None) -> localization.LocalizedString:
		"""
		:param fallbackText: The fallback text, this is only used if an identifier is specified and it has not been registered. If fallback text has been
		specified during initialization of this object, this will override it.
		:type fallbackText: str | None
		"""

		if fallbackText is None:
			fallbackText = self._fallbackText

		if isinstance(self.IdentifierOrKey, str):
			return GetLocalizationStringByIdentifier(self.IdentifierOrKey, *tokens, fallbackText = fallbackText)
		else:
			return GetLocalizationStringByKey(self.IdentifierOrKey, *tokens)

	def GetCallableLocalizationString (self, *tokens, fallbackText: str = None) -> typing.Callable[[], localization.LocalizedString]:
		"""
		:param fallbackText: The fallback text, this is only used if an identifier is specified and it has not been registered. If fallback text has been
		specified during initialization of this object, this will override it.
		:type fallbackText: str | None
		"""

		return lambda *args, **kwargs: self.GetLocalizationString(*tokens, fallbackText = fallbackText)

	def __call__ (self, *tokens, **kwargs) -> localization.LocalizedString:
		return self.GetLocalizationString(*tokens)

class _Identifier:
	def __init__ (self, identifier: str, key: int = None):
		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		if key is not None:
			if not isinstance(key, int):
				raise Exceptions.IncorrectTypeException(key, "key", (int,))

		self.Identifier = identifier  # type: str
		self.Key = key  # type: typing.Optional[int]

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

class _AnnouncerReliable(Director.Announcer):
	Host = This.Mod
	Reliable = True  # type: bool

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		_LoadEntries()

def GetLocalizationStringByIdentifier (identifier: str, *tokens, fallbackText: str = None) -> localization.LocalizedString:
	"""
	Find localized string by identifier. No identifiers will be loaded until a zone is loaded.
	:param identifier: This function will look through the list or registered entries to find one with this identifier.
					   Case will be ignored while searching for the identifier.
					   If the corresponding identifier object cannot be found a localization string will be created containing the identifier.
	:type identifier: str
	:param tokens: Valid tokens include any object with a function called "populate_localization_token", numbers, strings, LocalizedString objects, and arrays.
	 			   Array tokens seem to be considered lists of sims and all objects inside them require the "populate_localization_token" function.

	:param fallbackText: The text that will be fallen back to if the specified identifier isn't registered. If this is None the identifier will be used instead.
	:type fallbackText: str

	:rtype: localization.LocalizedString
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	identifierObject = _GetIdentifierObject(_SplitIdentifier(identifier))

	if identifierObject.Key is not None:
		return GetLocalizationStringByKey(identifierObject.Key, *tokens)
	else:
		if fallbackText is None:
			return CreateLocalizationString(identifier)
		else:
			return CreateLocalizationString(fallbackText)

def IdentifierIsRegistered (identifier: str) -> bool:
	"""
	Whether or not this identifier has been registered with a key. No identifiers will be loaded until a zone is loaded.
	"""

	if not isinstance(identifier, str):
		raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

	identifierObject = _GetIdentifierObject(_SplitIdentifier(identifier))

	return identifierObject.Key is not None

def GetLocalizationStringByKey (key: int, *tokens) -> localization.LocalizedString:
	"""
	Find localized string by key.
	:param key: The key for the desired localization string.
	:type key: int
	:param tokens: Valid tokens include any object with a function called "populate_localization_token", numbers, strings, LocalizedString objects, and arrays.
	 			   Array tokens seem to be considered lists of sims and all objects inside them require the "populate_localization_token" function.
	:rtype: localization.LocalizedString
	"""

	if not isinstance(key, int):
		raise Exceptions.IncorrectTypeException(key, "key", (int,))

	localizedString = localization.LocalizedString()
	localizedString.hash = key
	# noinspection PyUnresolvedReferences
	localization.create_tokens(localizedString.tokens, *tokens)

	return localizedString

def CreateLocalizationString (text: str) -> localization.LocalizedString:
	"""
	Creates a localized string from a normal string.
	:param text: The string that will be used as the localization string.
	:rtype: localization.LocalizedString
	"""

	if not isinstance(text, str):
		raise Exceptions.IncorrectTypeException(text, "text", (str,))

	return localization.LocalizationHelperTuning.get_raw_text(text)

def MakeLocalizationStringCallable (string: localization.LocalizedString) -> typing.Callable[[], localization.LocalizedString]:
	return lambda *args, **kwargs: string

def AddTokens (localizedString: localization.LocalizedString, *tokens) -> None:
	"""
	Add these tokens to a localization string.
	:param localizedString: The localized string the tokens are to be added to.
	:type localizedString: localization.LocalizedString
	:param tokens: Valid tokens include any object with a function called "populate_localization_token", numbers, strings, LocalizedString objects, and arrays.
	 			   Array tokens seem to be considered lists of sims and all objects inside them require the "populate_localization_token" function.
	:return:
	"""

	if not isinstance(localizedString, localization.LocalizedString):
		raise Exceptions.IncorrectTypeException(localizedString, "localizedString", (localization.LocalizedString,))

	# noinspection PyUnresolvedReferences
	localization.create_tokens(localizedString.tokens, *tokens)

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
	for snippetID, snippet in services.snippet_manager().types.items():  # type: typing.Any, snippets.SnippetInstanceMetaclass
		if isinstance(snippet, snippets.SnippetInstanceMetaclass):
			if snippet.snippet_type == IdentifiersSnippetName:
				for identifier, key in snippet.value.items():  # type: str, int
					identifierSegments = _SplitIdentifier(identifier)  # type: typing.List[str]
					targetIdentifierObject = _GetIdentifierObject(identifierSegments)  # type: _Identifier

					if targetIdentifierObject.Key is None:
						targetIdentifierObject.Key = key

	_loadedEntries = True

def _Setup ():
	global IdentifiersSnippetReference, IdentifiersSnippet
	IdentifiersSnippetReference, IdentifiersSnippet = snippets.define_snippet(IdentifiersSnippetName, IdentifiersTemplate)

_Setup()
