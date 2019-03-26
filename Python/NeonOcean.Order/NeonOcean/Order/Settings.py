import collections
import os
import typing

from NeonOcean.Order import Debug, Language, LoadingShared, SettingsShared, This
from NeonOcean.Order.Data import Persistence
from NeonOcean.Order.Tools import Exceptions, Parse, Version
from NeonOcean.Order.UI import Settings as SettingsUI

SettingsPath = os.path.join(This.Mod.PersistentPath, "Settings.json")  # type: str

_settings = None  # type: Persistence.Persistent
_allSettings = list()  # type: typing.List[typing.Type[Setting]]

class Setting(SettingsShared.SettingBase):
	IsSetting = False  # type: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Name: Language.String
	Description: Language.String
	DescriptionInput = None  # type: typing.Optional[Language.String]

	DialogType = SettingsShared.DialogTypes.Input  # type: SettingsShared.DialogTypes
	Values = dict()  # type: typing.Dict[typing.Any, Language.String]
	InputRestriction = None  # type: typing.Optional[str]

	DocumentationPage: str

	def __init_subclass__ (cls, **kwargs):
		if cls.IsSetting:
			cls.SetDefaults()
			_allSettings.append(cls)

	@classmethod
	def SetDefaults (cls) -> None:
		cls.Name = Language.String(This.Mod.Namespace + ".System.Settings.Values." + cls.Key + ".Name")  # type: Language.String
		cls.Description = Language.String(This.Mod.Namespace + ".System.Settings.Values." + cls.Key + ".Description")  # type: Language.String
		cls.DocumentationPage = cls.Key.replace("_", "-").lower()  # type: str

	@classmethod
	def Setup (cls) -> None:
		Setup(cls.Key,
			  cls.Type,
			  cls.Default,
			  cls.Verify)

	@classmethod
	def isSetup (cls) -> bool:
		return isSetup(cls.Key)

	@classmethod
	def Get (cls):
		return Get(cls.Key)

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		return Set(cls.Key, value, autoSave = autoSave, autoUpdate = autoUpdate)

	@classmethod
	def Reset (cls) -> None:
		Reset(cls.Key)

	@classmethod
	def Verify (cls, value: typing.Any, lastChangeVersion: Version.Version = None) -> typing.Any:
		return value

	@classmethod
	def GetInputTokens (cls) -> typing.Tuple[typing.Any, ...]:
		return tuple()

	@classmethod
	def IsActive (cls) -> bool:
		return True

	@classmethod
	def ShowDialog (cls):
		SettingsUI.ShowSettingDialog(cls, This.Mod)

	@classmethod
	def GetInputString (cls, inputValue: typing.Any) -> str:
		raise NotImplementedError()

	@classmethod
	def ParseInputString (cls, inputString: str) -> typing.Any:
		raise NotImplementedError()

class BooleanSetting(Setting):
	Type = bool

	DialogType = SettingsShared.DialogTypes.Choice  # type: SettingsShared.DialogTypes

	Values = {
		True: Language.String(This.Mod.Namespace + ".System.Settings.Boolean.True"),
		False: Language.String(This.Mod.Namespace + ".System.Settings.Boolean.False")
	}

	@classmethod
	def GetInputString (cls, inputValue: bool) -> str:
		if not isinstance(inputValue, bool):
			raise Exceptions.IncorrectTypeException(inputValue, "inputValue", (bool,))

		return str(inputValue)

	@classmethod
	def ParseInputString (cls, inputString: str) -> bool:
		if not isinstance(inputString, str):
			raise Exceptions.IncorrectTypeException(inputString, "inputString", (str,))

		return Parse.ParseBool(inputString)

class Check_For_Updates(BooleanSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Updates"  # type: str
	Default = True  # type: bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

class Check_For_Preview_Updates(BooleanSetting):
	IsSetting = True  # type: bool

	Key = "Check_For_Preview_Updates"  # type: str
	Default = False  # type: bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def IsActive (cls) -> bool:
		return Check_For_Updates.IsActive()

class Show_Promotions(BooleanSetting):
	IsSetting = True  # type: bool

	Key = "Show_Promotions"  # type: str
	Default = True  # type: bool

	@classmethod
	def Verify (cls, value: bool, lastChangeVersion: Version.Version = None) -> bool:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "value", (bool,))

		if not isinstance(lastChangeVersion, Version.Version) and lastChangeVersion is not None:
			raise Exceptions.IncorrectTypeException(lastChangeVersion, "lastChangeVersion", (Version.Version, "None"))

		return value

	@classmethod
	def IsActive (cls) -> bool:
		return True

def GetAllSettings () -> typing.List[typing.Type[Setting]]:
	return _allSettings

def Load () -> None:
	_settings.Load()

def Save () -> None:
	_settings.Save()

def Setup (key: str, valueType: type, default, verify: collections.Callable) -> None:
	_settings.Setup(key, valueType, default, verify)

def isSetup (key: str) -> bool:
	return _settings.isSetup(key)

def Get (key: str) -> typing.Any:
	return _settings.Get(key)

def Set (key: str, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
	_settings.Set(key, value, autoSave = autoSave, autoUpdate = autoUpdate)

def Reset (key: str = None) -> None:
	_settings.Reset(key = key)

def Update () -> None:
	_settings.Update()

def RegisterUpdate (update: collections.Callable) -> None:
	_settings.RegisterUpdate(update)

def UnregisterUpdate (update: collections.Callable) -> None:
	_settings.UnregisterUpdate(update)

def _OnInitiate (cause: LoadingShared.LoadingCauses) -> None:
	global _settings

	if cause:
		pass

	if _settings is None:
		_settings = Persistence.Persistent(SettingsPath, This.Mod.Version, hostNamespace = This.Mod.Namespace)

		for setting in _allSettings:
			setting.Setup()

	Load()

def _OnUnload (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	try:
		Save()
	except Exception as e:
		Debug.Log("Failed to save settings.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _OnReset () -> None:
	Reset()

def _OnResetSettings () -> None:
	Reset()
