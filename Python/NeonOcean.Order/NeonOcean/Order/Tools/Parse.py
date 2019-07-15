import typing

import enum
from NeonOcean.Order.Tools import Exceptions, Types

def ParseNumber (string: str) -> typing.Union[int, float]:
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

def ParseEnum (string: str, enumType: enum.Metaclass, ignoreCase: bool = False) -> enum.Int:
	if not isinstance(string, str):
		raise Exceptions.IncorrectTypeException(string, "string", (str,))

	if not isinstance(enumType, enum.Metaclass):
		raise Exceptions.IncorrectTypeException(enumType, "enumType", (enum.Metaclass,))

	if not isinstance(ignoreCase, bool):
		raise Exceptions.IncorrectTypeException(ignoreCase, "ignoreCase", (bool,))

	if "." in string:
		stringSplit = string.split(".")  # type: list

		if len(stringSplit) == 2:
			if stringSplit[0] == enumType.__name__:
				string = stringSplit[1]
			else:
				raise ValueError("Cannot parse '" + string + "' to '" + Types.GetFullName(enumType) + "'.")
		else:
			raise ValueError("Cannot parse '" + string + "' to '" + Types.GetFullName(enumType) + "'.")

	if ignoreCase:
		itemName = string.lower()  # type: str
	else:
		itemName = string  # type: str

	for itemTuple in enumType.items():  # type: typing.Tuple[str, enum.Int]
		if ignoreCase:
			if itemTuple[0].lower() == itemName:
				return itemTuple[1]
		else:
			if itemTuple[0] == itemName:
				return itemTuple[1]

	raise ValueError("'" + string + "' is not a attribute of '" + Types.GetFullName(enumType) + "'.")
