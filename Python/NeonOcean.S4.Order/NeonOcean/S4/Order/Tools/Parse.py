from __future__ import annotations

import enum_lib
import typing

import enum
from NeonOcean.S4.Order.Tools import Exceptions, Types

def ParseNumber (string: str) -> typing.Union[float, int]:
	if not isinstance(string, str):
		raise Exceptions.IncorrectTypeException(string, "string", (str,))

	try:
		return int(string)
	except Exception:
		return float(string)

def ParseBool (string: str) -> bool:
	if not isinstance(string, str):
		raise Exceptions.IncorrectTypeException(string, "string", (str,))

	stringLower = string.lower()

	if stringLower == "true":
		return True
	elif stringLower == "false":
		return False

	raise ValueError("'" + string + "' is not a valid boolean.")

def ParsePythonEnum (string: str, enumType: typing.Type[enum_lib.Enum]) -> typing.Any:
	if not isinstance(string, str):
		raise Exceptions.IncorrectTypeException(string, "string", (str,))

	if not isinstance(enumType, type):
		raise Exceptions.IncorrectTypeException(enumType, "enumType", (type,))

	if not issubclass(enumType, enum_lib.Enum):
		raise Exceptions.DoesNotInheritException("enumType", (enum_lib.Enum,))

	if "." in string:
		stringSplit = string.split(".")  # type: typing.List[str]

		if len(stringSplit) == 2:
			if stringSplit[0] == enumType.__name__:
				string = stringSplit[1]
			else:
				raise ValueError("Cannot parse '" + string + "' to '" + Types.GetFullName(enumType) + "'.")
		else:
			raise ValueError("Cannot parse '" + string + "' to '" + Types.GetFullName(enumType) + "'.")

	try:
		return enumType[string]
	except KeyError:
		pass

	raise ValueError("'" + string + "' is not an attribute of '" + Types.GetFullName(enumType) + "'.")

def ParseS4Enum (string: str, enumType: enum.Metaclass) -> typing.Any:
	if not isinstance(string, str):
		raise Exceptions.IncorrectTypeException(string, "string", (str,))

	if not isinstance(enumType, enum.Metaclass):
		raise Exceptions.IncorrectTypeException(enumType, "enumType", (enum.Metaclass,))

	if "." in string:
		stringSplit = string.split(".")  # type: typing.List[str]

		if len(stringSplit) == 2:
			if stringSplit[0] == enumType.__name__:
				string = stringSplit[1]
			else:
				raise ValueError("Cannot parse '" + string + "' to '" + Types.GetFullName(enumType) + "'.")
		else:
			raise ValueError("Cannot parse '" + string + "' to '" + Types.GetFullName(enumType) + "'.")

	try:
		return enumType[string]
	except KeyError:
		pass

	raise ValueError("'" + string + "' is not an attribute of '" + Types.GetFullName(enumType) + "'.")