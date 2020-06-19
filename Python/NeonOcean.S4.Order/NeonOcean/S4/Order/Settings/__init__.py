from __future__ import annotations

import types
import typing

from NeonOcean.S4.Order.Settings import Base as SettingsBase, Dialogs as SettingsDialogs, Types as SettingsTypes
from NeonOcean.S4.Order.Tools import Events

class CheckForUpdates(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Updates"  # type: str
	Default = True  # type: bool

class CheckForPreviewUpdates(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Preview_Updates"  # type: str
	Default = False  # type: bool

class ShowPromotions(SettingsTypes.BooleanYesNoDialogSetting):
	IsSetting = True  # type: bool

	Key = "Show_Promotions"  # type: str
	Default = True  # type: bool

def GetSettingsFilePath () -> str:
	return SettingsBase.SettingsFilePath

def GetAllSettings () -> typing.List[typing.Type[SettingsBase.Setting]]:
	return list(SettingsBase.AllSettings)

def Load () -> None:
	SettingsBase.Load()

def Save () -> None:
	SettingsBase.Save()

def Update () -> None:
	SettingsBase.Update()

def RegisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SettingsBase.UpdateEventArguments], None]) -> None:
	SettingsBase.RegisterOnUpdateCallback(updateCallback)

def UnregisterOnUpdateCallback (updateCallback: typing.Callable[[types.ModuleType, SettingsBase.UpdateEventArguments], None]) -> None:
	SettingsBase.UnregisterOnUpdateCallback(updateCallback)

def RegisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SettingsBase.RegisterOnLoadCallback(loadCallback)

def UnregisterOnLoadCallback (loadCallback: typing.Callable[[types.ModuleType, Events.EventArguments], None]) -> None:
	SettingsBase.UnregisterOnLoadCallback(loadCallback)
