from __future__ import annotations

import abc
import typing

from sims4 import localization

class SettingAbstract(abc.ABC):
	IsSetting: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Dialog: typing.Any

	ListPath: str
	ListPriority: typing.Union[float, int]

	def __init_subclass__ (cls, **kwargs):
		cls.OnInitializeSubclass()

	@classmethod
	def OnInitializeSubclass (cls) -> None:
		pass

	@classmethod
	@abc.abstractmethod
	def Setup (cls) -> None: ...

	@classmethod
	@abc.abstractmethod
	def IsSetup (cls) -> bool: ...

	@classmethod
	@abc.abstractmethod
	def IsHidden (cls) -> bool: ...

	@classmethod
	@abc.abstractmethod
	def Get (cls, ignoreOverride: bool = False) -> typing.Any: ...

	@classmethod
	@abc.abstractmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None: ...

	@classmethod
	def SetDefault (cls) -> None: ...

	@classmethod
	@abc.abstractmethod
	def Reset (cls, autoSave: bool = True, autoUpdate: bool = True) -> None: ...

	@classmethod
	@abc.abstractmethod
	def Verify (cls, value: typing.Any, lastChangeVersion = None) -> typing.Any: ...

	@classmethod
	@abc.abstractmethod
	def Override (cls, value: typing.Any, overrideIdentifier: str, overridePriority: typing.Union[float, int],
				  overrideReasonText: typing.Optional[typing.Callable[[], localization.LocalizedString]] = None) -> None: ...

	@classmethod
	@abc.abstractmethod
	def RemoveOverride (cls, overrideIdentifier: str) -> None: ...

	@classmethod
	@abc.abstractmethod
	def ClearAllOverrides (cls) -> None: ...

	@classmethod
	@abc.abstractmethod
	def IsOverridden (cls) -> bool: ...

	@classmethod
	@abc.abstractmethod
	def IsOverriddenBy (cls, overrideIdentifier: str) -> bool: ...

	@classmethod
	@abc.abstractmethod
	def GetActiveOverrideIdentifier (cls) -> str: ...

	@classmethod
	@abc.abstractmethod
	def GetAllOverrideIdentifiers (cls) -> typing.Set[str]: ...

	@classmethod
	@abc.abstractmethod
	def GetOverrideValue (cls, overrideIdentifier: str) -> typing.Any: ...

	@classmethod
	@abc.abstractmethod
	def GetOverridePriority (cls, overrideIdentifier: str) -> typing.Union[float, int]: ...

	@classmethod
	@abc.abstractmethod
	def GetOverrideReasonText (cls, overrideIdentifier: str) -> typing.Callable[[], localization.LocalizedString]: ...

	@classmethod
	@abc.abstractmethod
	def GetNameText (cls) -> typing.Any: ...

	@classmethod
	@abc.abstractmethod
	def GetValueText (cls, value: typing.Any) -> localization.LocalizedString: ...

	@classmethod
	@abc.abstractmethod
	def CanShowDialog (cls) -> bool: ...

	@classmethod
	@abc.abstractmethod
	def ShowDialog (cls, returnCallback: typing.Optional[typing.Callable[[], None]] = None) -> None: ...

	@classmethod
	@abc.abstractmethod
	def GetSettingIconKey (cls) -> typing.Optional[str]: ...
