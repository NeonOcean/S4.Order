from NeonOcean.Order.Tools import Exceptions

def FNV32HashString (string: str) -> int:
	"""
	Hash string using the 32 bit Fowler-Noll-Vo hash function.
	:type string: str
	:return: Returns hashed string in integer form. Use the ConvertIntegerToHexadecimal function to get it in a base 16 format.
	:rtype: int
	"""

	if not isinstance(string, str):
		raise Exceptions.IncorrectTypeException(string, "string", (str,))

	size = 2 ** 32
	prime = 16777619
	offset = 2166136261

	returnHash = offset  # type: int

	for character in string:
		returnHash = returnHash * prime % size
		returnHash = returnHash ^ ord(character)

	return returnHash

def FNV64HashString (string: str) -> int:
	"""
	Hash string using the 64 bit Fowler-Noll-Vo hash function.
	:type string: str
	:return: Returns hashed string in integer form. Use the ConvertIntegerToHexadecimal function to get it in a base 16 format.
	:rtype: int
	"""

	if not isinstance(string, str):
		raise Exceptions.IncorrectTypeException(string, "string", (str,))

	size = 2 ** 64
	prime = 1099511628211
	offset = 14695981039346656037

	returnHash = offset  # type: int

	for character in string:
		returnHash = returnHash * prime % size
		returnHash = returnHash ^ ord(character)

	return returnHash

def ConvertHexadecimalToDecimal (hexadecimal: str) -> int:
	"""
	Convert hexadecimal string to integer
	:type hexadecimal: str
	:rtype: int
	"""

	if not isinstance(hexadecimal, str):
		raise Exceptions.IncorrectTypeException(hexadecimal, "hexadecimal", (str,))

	return int(hexadecimal, 16)

def ConvertDecimalToHexadecimal (integer: int, minimumLength: int = -1) -> str:
	"""
	Convert integer to hexadecimal string
	:type integer: int
	:param minimumLength: If the hexadecimal is shorter than this number it will be padded with extra zeros.
	:type minimumLength: int
	:type: str
	"""

	hexString = hex(integer)[2:]

	if len(hexString) < minimumLength:
		hexString = "0" * (minimumLength - len(hexString)) + hexString

	hexString = hexString.upper()

	return hexString
