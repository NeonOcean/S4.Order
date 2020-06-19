from __future__ import annotations

from NeonOcean.S4.Order import Language, This
from NeonOcean.S4.Order.Settings import Base as SettingsBase, Dialogs as SettingsDialogs
from NeonOcean.S4.Order.Tools import Exceptions, Version
from sims4 import localization

class BooleanYesNoSetting(SettingsBase.Setting):
	Type = bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def GetValueText (cls, value: bool) -> localization.LocalizedString:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		valueString = str(value)  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Settings.Types.Boolean.Yes_No." + valueString, fallbackText = valueString)

class BooleanYesNoDialogSetting(BooleanYesNoSetting):
	Dialog = SettingsDialogs.BooleanYesNoDialog
