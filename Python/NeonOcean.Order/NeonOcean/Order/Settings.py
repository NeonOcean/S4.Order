import os
import typing

from NeonOcean.Order import Debug, Language, LoadingShared, SettingsShared, This, Websites
from NeonOcean.Order.Data import Persistence
from NeonOcean.Order.Tools import Exceptions, Version
from NeonOcean.Order.UI import Settings as SettingsUI
from sims4 import localization
from ui import ui_dialog

SettingsPath = os.path.join(This.Mod.PersistentPath, "Settings.json")  # type: str

_settings = None  # type: Persistence.PersistentFile
_allSettings = list()  # type: typing.List[typing.Type[Setting]]

class Setting(SettingsShared.SettingBase):
	IsSetting = False  # type: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Dialog: typing.Type[SettingsUI.SettingDialog]

	def __init_subclass__ (cls, **kwargs):
		super().OnInitializeSubclass()

		if cls.IsSetting:
			cls.SetDefault()
			_allSettings.append(cls)

	@classmethod
	def Setup (cls) -> None:
		_Setup(cls.Key,
			   cls.Type,
			   cls.Default,
			   cls.Verify)

	@classmethod
	def IsSetup (cls) -> bool:
		return _isSetup(cls.Key)

	@classmethod
	def Get (cls):
		return _Get(cls.Key)

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		return _Set(cls.Key, value, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Reset (cls) -> None:
		_Reset(cls.Key)

	@classmethod
	def Verify (cls, value: typing.Any, lastChangeVersion: Version.Version = None) -> typing.Any:
		return value

	@classmethod
	def IsActive (cls) -> bool:
		return True

	@classmethod
	def ShowDialog (cls):
		if not hasattr(cls, "Dialog"):
			return

		if cls.Dialog is None:
			return

		settingWrapper = SettingsUI.SettingStandardWrapper(cls)  # type: SettingsUI.SettingStandardWrapper
		cls.Dialog.ShowDialog(settingWrapper)

	@classmethod
	def GetName (cls) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Values." + cls.Key + ".Name")

	@classmethod
	def _OnLoaded (cls) -> None:
		pass

class BooleanSetting(Setting):
	Type = bool

	class Dialog(SettingsUI.StandardDialog):
		HostNamespace = This.Mod.Namespace  # type: str
		HostName = This.Mod.Name  # type: str

		Values = [False, True]  # type: typing.List[bool]

		@classmethod
		def GetTitleText (cls, setting: SettingsUI.SettingStandardWrapper) -> localization.LocalizedString:
			return setting.Setting.GetName()

		@classmethod
		def GetDescriptionText (cls, setting: SettingsUI.SettingStandardWrapper) -> localization.LocalizedString:
			return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Values." + setting.Key + ".Description")

		@classmethod
		def GetDefaultText (cls, setting: SettingsUI.SettingStandardWrapper) -> localization.LocalizedString:
			return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Boolean." + str(setting.Setting.Default))

		@classmethod
		def GetDocumentationURL (cls, setting: SettingsUI.SettingStandardWrapper) -> typing.Optional[str]:
			return Websites.GetNODocumentationModSettingURL(setting.Setting, This.Mod)

		@classmethod
		def _CreateButtons (cls,
							setting: SettingsUI.SettingStandardWrapper,
							currentValue: typing.Any,
							showDialogArguments: typing.Dict[str, typing.Any],
							returnCallback: typing.Callable[[], None] = None,
							*args, **kwargs):

			buttons = super()._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.List[SettingsUI.DialogButton]

			for valueIndex in range(len(cls.Values)):  # type: int
				def CreateValueButtonCallback (value: typing.Any) -> typing.Callable:

					# noinspection PyUnusedLocal
					def ValueButtonCallback (dialog: ui_dialog.UiDialog) -> None:
						cls._ShowDialogInternal(setting, value, showDialogArguments, returnCallback = returnCallback)

					return ValueButtonCallback

				valueButtonArguments = {
					"responseID": 50000 + valueIndex + -1,
					"sortOrder": -(500 + valueIndex + -1),
					"callback": CreateValueButtonCallback(cls.Values[valueIndex]),
					"text": Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Settings.Boolean." + str(cls.Values[valueIndex])),
				}

				if currentValue == cls.Values[valueIndex]:
					valueButtonArguments["selected"] = True

				valueButton = SettingsUI.ChoiceDialogButton(**valueButtonArguments)
				buttons.append(valueButton)

			return buttons

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

class CheckForUpdates(BooleanSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Updates"  # type: str
	Default = True  # type: bool

class CheckForPreviewUpdates(BooleanSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Preview_Updates"  # type: str
	Default = False  # type: bool

class ShowPromotions(BooleanSetting):
	IsSetting = True  # type: bool

	Key = "Show_Promotions"  # type: str
	Default = True  # type: bool

def GetAllSettings () -> typing.List[typing.Type[Setting]]:
	return list(_allSettings)

def Load () -> None:
	_settings.Load()

def Save () -> None:
	_settings.Save()

def Update () -> None:
	_settings.Update()

def RegisterUpdate (update: typing.Callable) -> None:
	_settings.RegisterUpdate(update)

def UnregisterUpdate (update: typing.Callable) -> None:
	_settings.UnregisterUpdate(update)

def RegisterLoadCallback (callback: typing.Callable) -> None:
	_settings.RegisterLoadCallback(callback)

def UnregisterLoadCallback (callback: typing.Callable) -> None:
	_settings.UnregisterLoadCallback(callback)

def _OnInitiate (cause: LoadingShared.LoadingCauses) -> None:
	global _settings

	if cause:
		pass

	if _settings is None:
		_settings = Persistence.PersistentFile(SettingsPath, This.Mod.Version, hostNamespace = This.Mod.Namespace, alwaysSaveValues = True)

		for setting in _allSettings:
			setting.Setup()

		RegisterLoadCallback(_LoadCallback)

	Load()

def _OnUnload (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	try:
		Save()
	except Exception:
		Debug.Log("Failed to save settings.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _OnReset () -> None:
	for setting in GetAllSettings():  # type: Setting
		setting.Reset()

def _OnResetSettings () -> None:
	for setting in GetAllSettings():  # type: Setting
		setting.Reset()

def _Setup (key: str, valueType: type, default, verify: typing.Callable) -> None:
	_settings.Setup(key, valueType, default, verify)

def _isSetup (key: str) -> bool:
	return _settings.IsSetup(key)

def _Get (key: str) -> typing.Any:
	return _settings.Get(key)

def _Set (key: str, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
	_settings.Set(key, value, autoSave = autoSave, autoUpdate = autoUpdate)

def _Reset (key: str = None) -> None:
	_settings.Reset(key = key)

def _LoadCallback () -> None:
	for setting in _allSettings:  # type: Setting
		try:
			setting._OnLoaded()
		except Exception:
			Debug.Log("Failed to call the on loaded event for the setting '" + setting.Key + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
