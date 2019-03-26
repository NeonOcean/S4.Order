import typing

import enum

class DialogTypes(enum.Int):
	NoDialog = 0
	Input = 2  # type: DialogTypes
	Choice = 3  # type: DialogTypes

class SettingBase:
	IsSetting: bool

	Key: str
	Type: typing.Type
	Default: typing.Any

	Name: typing.Any
	Description: typing.Any
	DescriptionInput: typing.Optional[typing.Any]

	DialogType: DialogTypes
	Values: dict
	InputRestriction: typing.Optional[str]

	DocumentationPage: str

	@classmethod
	def Setup (cls) -> None:
		raise NotImplementedError()

	@classmethod
	def isSetup (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	def Get (cls) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	def Set (cls, value: typing.Any, autoSave: bool = True, autoUpdate: bool = True) -> None:
		raise NotImplementedError()

	@classmethod
	def Reset (cls) -> None:
		raise NotImplementedError()

	@classmethod
	def Verify (cls, value: typing.Any, lastChangeVersion = None) -> typing.Any:
		raise NotImplementedError()

	@classmethod
	def IsActive (cls) -> bool:
		raise NotImplementedError()

	@classmethod
	def GetInputTokens (cls) -> typing.Tuple[typing.Any, ...]:
		return tuple()

	@classmethod
	def ShowDialog (cls) -> None:
		raise NotImplementedError()

	@classmethod
	def GetInputString (cls, inputValue: typing.Any) -> str:
		raise NotImplementedError()

	@classmethod
	def ParseInputString (cls, inputString: str) -> typing.Any:
		raise NotImplementedError()
