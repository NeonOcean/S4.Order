from __future__ import annotations

import typing

from NeonOcean.S4.Order import Language, This
from NeonOcean.S4.Order.Tools import Exceptions
from sims4 import localization

def _GetFormattingText () -> localization.LocalizedString:
	return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Text_Builder.Formatting", fallbackText = "Missing Formatting String!")

def BuildText (parts: typing.List[typing.Union[localization.LocalizedString, str, int, float]]) -> localization.LocalizedString:
	"""
	Create new The Sims 4 localized strings by combining any localized string, string, int, or float together.
	:param parts: Parts to combined together to create the new localized string.
	:type parts: typing.List[typing.Union[localization.LocalizedString, str, int, float]]
	"""

	if not isinstance(parts, list):
		raise Exceptions.IncorrectTypeException(parts, "parts", (list,))

	for partIndex in range(len(parts)):  # type: int
		part = parts[partIndex]  # type: typing.Union[localization.LocalizedString, str, int, float]
		if not isinstance(part, (localization.LocalizedString, str, int, float)):
			raise Exceptions.IncorrectTypeException(part, "parts[%s]" % partIndex, (localization.LocalizedString, str, int, float))

		if isinstance(part, (int, float)):
			parts[partIndex] = str(part)

	if len(parts) == 0:
		return Language.CreateLocalizationString("")

	lastString = None  # type: typing.Optional[localization.LocalizedString]

	for part in reversed(parts):  # type: typing.Union[localization.LocalizedString, str, int, float]
		partString = _GetFormattingText()  # type: localization.LocalizedString
		partStringTokens = (part, )

		if lastString is not None:
			partStringTokens += (lastString, )

		Language.AddTokens(partString, *partStringTokens)
		lastString = partString

	return lastString
