from __future__ import annotations

import abc
import typing

from NeonOcean.S4.Order.Abstract import Settings as AbstractSettings
from NeonOcean.S4.Order.Tools import Exceptions
from sims4 import localization

class SettingWrapper(abc.ABC):
	def __init__ (self, setting):
		self._setting = setting

	@property
	def Setting (self) -> typing.Any:
		return self._setting

	@property
	@abc.abstractmethod
	def Key (self) -> str: ...

	@abc.abstractmethod
	def IsHidden (self) -> bool: ...

	@abc.abstractmethod
	def Get (self, ignoreOverride: bool = False) -> typing.Any: ...

	@abc.abstractmethod
	def GetDefault (self) -> typing.Any: ...

	@abc.abstractmethod
	def Set (self, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		The autoSave and autoUpdate parameters should allow a setting dialog to change multiple setting's values without saving or notifying the rest
		of the mod each time. They can be ignored if your settings system doesn't support such things, though it may slow things down.
		"""
		...

	@abc.abstractmethod
	def Reset (self, autoSave: bool = True, autoUpdate: bool = True) -> None:
		"""
		The autoSave and autoUpdate parameters should allow a setting dialog to change multiple setting's values without saving or notifying the rest
		of the mod each time. They can be ignored if your settings system doesn't support such things, though it may slow things down.
		"""

		...

	@abc.abstractmethod
	def IsOverridden (self) -> bool: ...

	@abc.abstractmethod
	def GetOverrideValue (self) -> typing.Any: ...

	@abc.abstractmethod
	def GetOverrideValueText (self) -> localization.LocalizedString: ...

	@classmethod
	@abc.abstractmethod
	def GetOverrideReasonText (cls) -> localization.LocalizedString: ...

	@abc.abstractmethod
	def GetNameText (self) -> localization.LocalizedString: ...

	@abc.abstractmethod
	def GetDefaultText (self) -> localization.LocalizedString: ...

	@abc.abstractmethod
	def GetValueText (self, value: typing.Any) -> localization.LocalizedString: ...

	@abc.abstractmethod
	def CanShowDialog (self) -> bool: ...

	@abc.abstractmethod
	def ShowDialog (self, returnCallback: typing.Callable[[], None] = None) -> None: ...

	@abc.abstractmethod
	def GetListPath (self) -> str: ...

	@abc.abstractmethod
	def GetListPriority (self) -> typing.Union[float, int]: ...

	@abc.abstractmethod
	def GetListIconKey (self) -> typing.Optional[str]: ...

class SettingSystemWrapper(abc.ABC):
	def __init__ (self, settingSystem):
		self._settingSystem = settingSystem
		pass

	@property
	def SettingSystem (self) -> typing.Any:
		return self._settingSystem

	@property
	@abc.abstractmethod
	def Settings (self) -> typing.List[SettingWrapper]: ...

	@abc.abstractmethod
	def Save (self): ...

	@abc.abstractmethod
	def Update (self):
		"""
		This method should prompt your mod to handle changes made to a setting's value.
		"""

		...

	@abc.abstractmethod
	def ResetAll (self): ...

class SettingStandardWrapper(SettingWrapper):
	def __init__ (self, setting: typing.Type[AbstractSettings.SettingAbstract]):
		"""
		A wrapper for the standard settings system used by NeonOcean
		"""

		if not isinstance(setting, type):
			raise Exceptions.IncorrectTypeException(setting, "setting", (type,))

		if not issubclass(setting, AbstractSettings.SettingAbstract):
			raise Exceptions.DoesNotInheritException("setting", (AbstractSettings.SettingAbstract,))

		super().__init__(setting)

	@property
	def Setting (self) -> typing.Type[AbstractSettings.SettingAbstract]:
		return self._setting

	@property
	def Key (self) -> str:
		return self.Setting.Key

	def IsHidden (self) -> bool:
		return self.Setting.IsHidden()

	def Get (self, ignoreOverride: bool = False) -> typing.Any:
		return self.Setting.Get(ignoreOverride = ignoreOverride)

	def GetDefault (self) -> typing.Any:
		return self.Setting.Default

	def Set (self, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		return self.Setting.Set(value, autoSave = autoSave, autoUpdate = autoUpdate)

	def Reset (self, autoSave: bool = True, autoUpdate: bool = True) -> None:
		self.Setting.Reset(autoSave = autoSave, autoUpdate = autoUpdate)

	def IsOverridden (self) -> bool:
		return self.Setting.IsOverridden()

	def GetOverrideValue (self) -> typing.Any:
		activeOverrideIdentifier = self.Setting.GetActiveOverrideIdentifier()  # type: str
		return self.Setting.GetOverrideValue(activeOverrideIdentifier)

	def GetOverrideValueText (self) -> localization.LocalizedString:
		return self.Setting.GetValueText(self.GetOverrideValue())

	def GetOverrideReasonText (self) -> localization.LocalizedString:
		activeOverrideIdentifier = self.Setting.GetActiveOverrideIdentifier()  # type: str
		return self.Setting.GetOverrideReasonText(activeOverrideIdentifier)()

	def GetNameText (self) -> localization.LocalizedString:
		return self.Setting.GetNameText()

	def GetDefaultText (self) -> localization.LocalizedString:
		return self.Setting.GetValueText(self.Setting.Default)

	def GetValueText (self, value: typing.Any) -> localization.LocalizedString:
		return self.Setting.GetValueText(value)

	def CanShowDialog (self) -> bool:
		return self.Setting.CanShowDialog()

	def ShowDialog (self, returnCallback: typing.Callable[[], None] = None) -> None:
		if not isinstance(returnCallback, typing.Callable) and returnCallback is not None:
			raise Exceptions.IncorrectTypeException(returnCallback, "returnCallback", ("Callable", None))

		return self.Setting.ShowDialog(returnCallback = returnCallback)

	def GetListPath (self) -> str:
		return self.Setting.ListPath

	def GetListPriority (self) -> typing.Union[float, int]:
		return self.Setting.ListPriority

	def GetListIconKey (self) -> typing.Optional[str]:
		return self.Setting.GetSettingIconKey()

class SettingsSystemStandardWrapper(SettingSystemWrapper):
	def __init__ (self, settingSystem: typing.Any,
				  settings: typing.List[SettingStandardWrapper],
				  save: typing.Callable[[], None], update: typing.Callable[[], None]):

		"""
		A wrapper for the standard settings system used by NeonOcean
		"""

		super().__init__(settingSystem)

		if not isinstance(save, typing.Callable):
			raise Exceptions.IncorrectTypeException(save, "save", ("Callable",))

		if not isinstance(update, typing.Callable):
			raise Exceptions.IncorrectTypeException(update, "update", ("Callable",))

		if not isinstance(settings, list):
			raise Exceptions.IncorrectTypeException(settings, "settings", (list,))

		for settingIndex in range(len(settings)):  # type: int
			setting = settings[settingIndex]  # type: SettingStandardWrapper

			if not isinstance(setting, SettingStandardWrapper):
				raise Exceptions.IncorrectTypeException(setting, "settings[%s]" % settingIndex, (SettingStandardWrapper,))

		self._settings = settings  # type: typing.List[SettingStandardWrapper]
		self._save = save  # type: typing.Callable[[], None]
		self._update = update  # type: typing.Callable[[], None]

	@property
	def Settings (self) -> typing.List[SettingStandardWrapper]:
		return self._settings

	def Save (self) -> None:
		self._save()

	def Update (self) -> None:
		self._update()

	def ResetAll (self) -> None:
		for setting in self.Settings:
			setting.Reset(autoSave = False, autoUpdate = False)

		self.Save()
		self.Update()
