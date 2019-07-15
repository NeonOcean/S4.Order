import typing

from NeonOcean.Order.Tools import Types

class IncorrectTypeException(Exception):
	def __init__ (self, value, valueName: str, correctTypes: typing.Tuple[typing.Union[type, str, None], ...], *additional):
		"""
		This exception will display error messages such as: 'Expected type 'builtins.str' not 'builtins.int' for 'parameter 1'."

		:param value: The incorrectly typed value. When converting the exception to a string it will display the full name of the value's type.
		:param valueName: Use this to provide information on what is incorrect.
		:type valueName: str
		:param correctTypes: A iterable object containing any possibly correct types. The entries can be either a type or a string object.
							 If an entry is a type, when converting the exception to a string it will display the full name of the type.
		:type correctTypes: typing.Tuple[typing.Union[type, str], typing.Any]
		"""

		if not isinstance(valueName, str):
			raise IncorrectTypeException(valueName, "valueName", (str,))

		if not isinstance(correctTypes, tuple):
			raise IncorrectTypeException(correctTypes, "correctTypes", (tuple,))

		if len(correctTypes) == 0:
			raise Exception("This exception must receive at least one correct type")

		for correctTypeIndex in range(len(correctTypes)):  # type: int
			if not isinstance(correctTypes[correctTypeIndex], type) and not (not isinstance(correctTypes[correctTypeIndex], type) and isinstance(correctTypes[correctTypeIndex], str)):
				raise IncorrectTypeException(correctTypes[correctTypeIndex], "correctTypes[%d]" % correctTypeIndex, (type, str))

		self._value = value  # type: type
		self._valueName = valueName  # type: str
		self._correctTypes = correctTypes  # type: typing.Tuple[typing.Union[type, str], typing.Any]
		self._additional = additional  # type: typing.Tuple[typing.Any, ...]

		super().__init__((value, valueName, correctTypes, *additional))

	def __str__ (self):
		valueType = type(self._value)

		correctString = "'{}'" + (", '{}'" * (len(self._correctTypes) - 2) if len(self._correctTypes) > 2 else "") + (" or '{}'" if len(self._correctTypes) > 1 else "")

		formatList = list()

		for correctTypeIndex in range(0, len(self._correctTypes)):
			if isinstance(self._correctTypes[correctTypeIndex], type):
				formatList.append(Types.GetFullName(self._correctTypes[correctTypeIndex]))
			elif isinstance(self._correctTypes[correctTypeIndex], str):
				formatList.append(self._correctTypes[correctTypeIndex])

		formatList.append(Types.GetFullName(valueType))
		formatList.append(self._valueName)

		exceptionString = ("Expected type " + correctString + " not '{}' for '{}'").format(*formatList)

		for additionalObject in self._additional:  # type: typing.Any
			exceptionString += "\n" + str(additionalObject)

		return exceptionString

def GetIncorrectTypeExceptionText (value, valueName: str, correctTypes: typing.Tuple[typing.Union[type, str, None], ...], *additional):
	if not isinstance(valueName, str):
		raise IncorrectTypeException(valueName, "valueName", (str,))

	if not isinstance(correctTypes, tuple):
		raise IncorrectTypeException(correctTypes, "correctTypes", (tuple,))

	if len(correctTypes) == 0:
		raise Exception("This exception must receive at least one correct type")

	for correctTypeIndex in range(len(correctTypes)):  # type: int
		if not isinstance(correctTypes[correctTypeIndex], type) and not (not isinstance(correctTypes[correctTypeIndex], type) and isinstance(correctTypes[correctTypeIndex], str)):
			raise IncorrectTypeException(correctTypes[correctTypeIndex], "correctTypes[%d]" % correctTypeIndex, (type, str))

	valueType = type(value)

	correctString = "'{}'" + (", '{}'" * (len(correctTypes) - 2) if len(correctTypes) > 2 else "") + (" or '{}'" if len(correctTypes) > 1 else "")

	formatList = list()

	for correctTypeIndex in range(0, len(correctTypes)):
		if isinstance(correctTypes[correctTypeIndex], type):
			formatList.append(Types.GetFullName(correctTypes[correctTypeIndex]))
		elif isinstance(correctTypes[correctTypeIndex], str):
			formatList.append(correctTypes[correctTypeIndex])

	formatList.append(Types.GetFullName(valueType))
	formatList.append(valueName)

	exceptionString = ("Expected type " + correctString + " not '{}' for '{}'").format(*formatList)

	for additionalObject in additional:  # type: typing.Any
		exceptionString += "\n" + str(additionalObject)

	return exceptionString
