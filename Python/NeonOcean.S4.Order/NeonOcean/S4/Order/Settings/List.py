from __future__ import annotations

import typing

from NeonOcean.S4.Order import Language, Settings, This
from NeonOcean.S4.Order.Settings import Base as SettingsBase
from NeonOcean.S4.Order.UI import SettingsList as UISettingsList, SettingsShared as UISettingsShared
from sims4 import localization

SettingsListRoot = "Root"  # type: str

class SettingsList(UISettingsList.SettingsList):
	def _GetTitleText (self, listPath: str) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Mod_Settings.List.Title")

	def _GetTitleListPathText (self, listPath: str) -> localization.LocalizedString:
		listPathIdentifier = listPath.replace(self.ListPathSeparator, "_")  # type: str
		fallbackText = "List.Paths" + listPathIdentifier + ".Title"  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Mod_Settings.List.Paths." + listPathIdentifier + ".Title", fallbackText = fallbackText)

	def _GetDescriptionText (self, listPath: str) -> localization.LocalizedString:
		listPathIdentifier = listPath.replace(self.ListPathSeparator, "_")  # type: str
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Mod_Settings.List.Paths." + listPathIdentifier + ".Description")

def GetListDialogSettingsSystem () -> UISettingsShared.SettingsSystemStandardWrapper:
	return UISettingsShared.SettingsSystemStandardWrapper(SettingsBase, GetListDialogSettings(), SettingsBase.Save, SettingsBase.Update)

def GetListDialogSettings () -> typing.List[UISettingsShared.SettingStandardWrapper]:
	return [UISettingsShared.SettingStandardWrapper(setting) for setting in Settings.GetAllSettings()]

def ShowListDialog (returnCallback: typing.Callable[[], None] = None) -> None:
	"""
	Open the settings list dialog. A lot must be loaded or nothing will happen.
	:param returnCallback: The return callback will be triggered after the settings list dialog has completely closed.
	:type returnCallback: typing.Callable[[], None] | None
	"""

	settingsSystem = GetListDialogSettingsSystem()  # type: UISettingsShared.SettingsSystemStandardWrapper
	settingsList = SettingsList(This.Mod.Namespace, settingsSystem)  # type: SettingsList
	settingsList.ShowDialog(SettingsListRoot, returnCallback = returnCallback)
