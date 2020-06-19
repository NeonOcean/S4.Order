from __future__ import annotations

import typing

from NeonOcean.S4.Order.Tools import Types

class IncorrectTypeException(Exception):
	def __init__ (self, value, valueName: str, correctTypes: typing.Tuple[typing.Union[type, str, None], ...], *additional):
		"""
		This exception will display error messages such as: 'Expected type 'builtins.str' not 'builtins.int' for 'parameter 1'."

		:param value: The incorrectly typed value. When converting the exception to a string it will display the full name of the value's type.
		:param valueName: Use this to provide information on what is incorrect.
		:type valueName: str
		:param correctTypes: A iterable object containing any possibly correct types. The entries can be either a type, a string object, or None.
		If an entry is a type, when converting the exception to a string it will display the full name of the type.
		:type correctTypes: typing.Tuple[typing.Union[type, str, None], ...]
		"""

		if not isinstance(valueName, str):
			raise IncorrectTypeException(valueName, "valueName", (str,))

		if not isinstance(correctTypes, tuple):
			raise IncorrectTypeException(correctTypes, "correctTypes", (tuple,))

		if len(correctTypes) == 0:
			raise Exception("This exception must receive at least one correct type.")

		for correctTypeIndex in range(len(correctTypes)):  # type: int
			if isinstance(correctTypes[correctTypeIndex], type):
				continue

			if isinstance(correctTypes[correctTypeIndex], str):
				continue

			if correctTypes[correctTypeIndex] is None:
				continue

			raise IncorrectTypeException(correctTypes[correctTypeIndex], "correctTypes[%d]" % correctTypeIndex, (type, str, None))

		self._value = value  # type: typing.Any
		self._valueName = valueName  # type: str
		self._correctTypes = correctTypes  # type: tuple
		self._additional = additional  # type: typing.Tuple[typing.Any, ...]

		super().__init__(*(value, valueName, correctTypes, *additional))

	def __str__ (self):
		return GetIncorrectTypeExceptionText(self._value, self._valueName, self._correctTypes, *self._additional)

class IncorrectReturnTypeException(Exception):
	def __init__ (self, value, callableName: str, correctTypes: typing.Tuple[typing.Union[type, str, None], ...], *additional):
		"""
		This exception will display error messages such as: 'Expected 'function' to return a 'builtins.str' not 'builtins.int'."

		:param value: The incorrectly typed value. When converting the exception to a string it will display the full name of the value's type.
		:param callableName: Use this to provide information on what returned incorrect values.
		:type callableName: str
		:param correctTypes: A iterable object containing any possibly correct types. The entries can be either a type, a string object or None.
		If an entry is a type, when converting the exception to a string it will display the full name of the type.
		:type correctTypes: typing.Tuple[typing.Union[type, str, None], ...]
		"""

		if not isinstance(callableName, str):
			raise IncorrectTypeException(callableName, "callableName", (str,))

		if not isinstance(correctTypes, tuple):
			raise IncorrectTypeException(correctTypes, "correctTypes", (tuple,))

		if len(correctTypes) == 0:
			raise Exception("This exception must receive at least one correct type.")

		for correctTypeIndex in range(len(correctTypes)):  # type: int
			if isinstance(correctTypes[correctTypeIndex], type):
				continue

			if isinstance(correctTypes[correctTypeIndex], str):
				continue

			if correctTypes[correctTypeIndex] is None:
				continue

			raise IncorrectTypeException(correctTypes[correctTypeIndex], "correctTypes[%d]" % correctTypeIndex, (type, str, None))

		self._value = value  # type: typing.Any
		self._callableName = callableName  # type: str
		self._correctTypes = correctTypes  # type: tuple
		self._additional = additional  # type: typing.Tuple[typing.Any, ...]

		super().__init__(*(value, callableName, correctTypes, *additional))

	def __str__ (self):
		return GetIncorrectReturnTypeExceptionText(self._value, self._callableName, self._correctTypes, *self._additional)

class DoesNotInheritException(Exception):
	def __init__ (self, valueName: str, correctParents: typing.Tuple[typing.Union[type, str], ...], *additional):
		"""
		This exception will display error messages such as: 'Expected 'type' to inherit 'extender'."

		:param valueName: Use this to provide information on what is incorrect.
		:type valueName: str
		:param correctParents: A iterable object containing any possibly correct parents. The entries can be either a type or a string object.
		If an entry is a type, when converting the exception to a string it will display the full name of the type.
		:type correctParents: typing.Tuple[typing.Union[type, str], ...]
		"""

		if not isinstance(valueName, str):
			raise IncorrectTypeException(valueName, "valueName", (str,))

		if not isinstance(correctParents, tuple):
			raise IncorrectTypeException(correctParents, "correctParents", (tuple,))

		if len(correctParents) == 0:
			raise Exception("This exception must receive at least one correct parent.")

		for correctParentIndex in range(len(correctParents)):  # type: int
			if isinstance(correctParents[correctParentIndex], type):
				continue

			if isinstance(correctParents[correctParentIndex], str):
				continue

			raise IncorrectTypeException(correctParents[correctParentIndex], "correctParents[%d]" % correctParentIndex, (type, str))

		self._valueName = valueName  # type: str
		self._correctParents = correctParents  # type: tuple
		self._additional = additional  # type: typing.Tuple[typing.Any, ...]

		super().__init__(*(valueName, correctParents, *additional))

	def __str__ (self):
		return GetDoesNotInheritExceptionText(self._valueName, self._correctParents, *self._additional)

class DummyException(Exception):
	pass

def GetIncorrectTypeExceptionText (value, valueName: str, correctTypes: typing.Tuple[typing.Union[type, str, None], ...], *additional) -> str:
	if not isinstance(valueName, str):
		raise IncorrectTypeException(valueName, "valueName", (str,))

	if not isinstance(correctTypes, tuple):
		raise IncorrectTypeException(correctTypes, "correctTypes", (tuple,))

	if len(correctTypes) == 0:
		raise Exception("This exception must receive at least one correct type")

	for correctTypeIndex in range(len(correctTypes)):  # type: int
		if isinstance(correctTypes[correctTypeIndex], type):
			continue

		if isinstance(correctTypes[correctTypeIndex], str):
			continue

		if correctTypes[correctTypeIndex] is None:
			continue

		raise IncorrectTypeException(correctTypes[correctTypeIndex], "correctTypes[%d]" % correctTypeIndex, (type, str, None))

	valueType = type(value)

	correctString = "'{}'" + (", '{}'" * (len(correctTypes) - 2) if len(correctTypes) > 2 else "") + (" or '{}'" if len(correctTypes) > 1 else "")

	formatList = list()

	for correctTypeIndex in range(0, len(correctTypes)):
		if isinstance(correctTypes[correctTypeIndex], type) or correctTypes[correctTypeIndex] is None:
			formatList.append(Types.GetFullName(correctTypes[correctTypeIndex]))
		elif isinstance(correctTypes[correctTypeIndex], str):
			formatList.append(correctTypes[correctTypeIndex])
		else:
			formatList.append("")

	formatList.append(Types.GetFullName(valueType))
	formatList.append(valueName)

	exceptionString = ("Expected type " + correctString + " not '{}' for '{}'").format(*formatList)

	for additionalObject in additional:  # type: typing.Any
		exceptionString += "\n" + str(additionalObject)

	return exceptionString

def GetIncorrectReturnTypeExceptionText (value, callableName: str, correctTypes: typing.Tuple[typing.Union[type, str, None], ...], *additional) -> str:
	if not isinstance(callableName, str):
		raise IncorrectTypeException(callableName, "callableName", (str,))

	if not isinstance(correctTypes, tuple):
		raise IncorrectTypeException(correctTypes, "correctTypes", (tuple,))

	if len(correctTypes) == 0:
		raise Exception("This exception must receive at least one correct type")

	for correctTypeIndex in range(len(correctTypes)):  # type: int
		if isinstance(correctTypes[correctTypeIndex], type):
			continue

		if isinstance(correctTypes[correctTypeIndex], str):
			continue

		if correctTypes[correctTypeIndex] is None:
			continue

		raise IncorrectTypeException(correctTypes[correctTypeIndex], "correctTypes[%d]" % correctTypeIndex, (type, str, None))

	valueType = type(value)

	correctString = "'{}'" + (", '{}'" * (len(correctTypes) - 2) if len(correctTypes) > 2 else "") + (" or '{}'" if len(correctTypes) > 1 else "")

	formatList = list()

	formatList.append(callableName)

	for correctTypeIndex in range(0, len(correctTypes)):
		if isinstance(correctTypes[correctTypeIndex], type) or correctTypes[correctTypeIndex] is None:
			formatList.append(Types.GetFullName(correctTypes[correctTypeIndex]))
		elif isinstance(correctTypes[correctTypeIndex], str):
			formatList.append(correctTypes[correctTypeIndex])
		else:
			formatList.append("")

	formatList.append(Types.GetFullName(valueType))

	exceptionString = ("Expected '{}' to return a '" + correctString + "' not '{}'.").format(*formatList)

	for additionalObject in additional:  # type: typing.Any
		exceptionString += "\n" + str(additionalObject)

	return exceptionString

def GetDoesNotInheritExceptionText (valueName: str, correctParents: typing.Tuple[typing.Union[type, str], ...], *additional) -> str:
	if not isinstance(valueName, str):
		raise IncorrectTypeException(valueName, "valueName", (str,))

	if not isinstance(correctParents, tuple):
		raise IncorrectTypeException(correctParents, "correctParents", (tuple,))

	if len(correctParents) == 0:
		raise Exception("This exception must receive at least one correct type")

	for correctParentIndex in range(len(correctParents)):  # type: int
		if isinstance(correctParents[correctParentIndex], type):
			continue

		if isinstance(correctParents[correctParentIndex], str):
			continue

		if correctParents[correctParentIndex] is None:
			continue

		raise IncorrectTypeException(correctParents[correctParentIndex], "correctParents[%d]" % correctParentIndex, (type, str, None))

	correctString = "'{}'" + (", '{}'" * (len(correctParents) - 2) if len(correctParents) > 2 else "") + (" or '{}'" if len(correctParents) > 1 else "")

	formatList = list()

	formatList.append(valueName)

	for correctParentIndex in range(0, len(correctParents)):
		if isinstance(correctParents[correctParentIndex], type) or correctParents[correctParentIndex] is None:
			formatList.append(Types.GetFullName(correctParents[correctParentIndex]))
		elif isinstance(correctParents[correctParentIndex], str):
			formatList.append(correctParents[correctParentIndex])
		else:
			formatList.append("")

	exceptionString = ("Expected '{}' to inherit " + correctString + "").format(*formatList)

	for additionalObject in additional:  # type: typing.Any
		exceptionString += "\n" + str(additionalObject)

	return exceptionString
