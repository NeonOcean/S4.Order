import re

from NeonOcean.Order.Tools import Exceptions, Types

class Version:
	def __init__ (self, versionString: str = None):
		if not isinstance(versionString, str):
			raise Exceptions.IncorrectTypeException(versionString, "versionString", (str,))

		self.ParseRegex = re.compile(r'^(\d+) \. (\d+) (?:\. (\d+))? (?:\. (\d+))?$', re.VERBOSE | re.ASCII)

		self.Major = 1
		self.Minor = 0
		self.Patch = -1
		self.Build = -1

		if versionString is not None:
			self._Parse(versionString)

	def __repr__ (self):
		return "%s ('%s')" % (self.__class__.__name__, str(self))

	def __eq__ (self, other):
		compareResult = self._Compare(other)  # type: int
		return compareResult == 0

	def __ne__ (self, other):
		compareResult = self._Compare(other)  # type: int
		return compareResult != 0

	def __lt__ (self, other):
		compareResult = self._Compare(other)  # type: int
		return compareResult < 0

	def __le__ (self, other):
		compareResult = self._Compare(other)  # type: int
		return compareResult <= 0

	def __gt__ (self, other):
		compareResult = self._Compare(other)  # type: int
		return compareResult > 0

	def __ge__ (self, other):
		compareResult = self._Compare(other)  # type: int
		return compareResult >= 0

	def __str__ (self):
		return self._ToString()

	def _Parse (self, string: str) -> None:
		match = self.ParseRegex.match(string)

		if not match:
			raise ValueError("Invalid version number '%s'" % string)

		(major, minor, patch, build) = match.groups()

		self.Major = int(major)
		self.Minor = int(minor)

		if patch:
			self.Patch = int(patch)

		if build:
			self.Build = int(build)

	def _ToString (self):
		versionString = str(self.Major) + "." + str(self.Minor)

		if self.Patch >= 0:
			versionString += "." + str(self.Patch)

		if self.Build >= 0:
			versionString += "." + str(self.Build)

		return versionString

	def _Compare (self, other):
		if other is None:
			return 1

		if not isinstance(other, Version):
			raise TypeError("Compare operations are not supported between instances of '%s' and '%s'" % (Types.GetFullName(self), Types.GetFullName(other)))

		if isinstance(other, str):
			other = Version(other)

		if self.Major != other.Major:
			if self.Major < other.Major:
				return -1
			else:
				return 1

		if self.Minor != other.Minor:
			if self.Minor < other.Minor:
				return -1
			else:
				return 1

		if self.Patch != other.Patch:
			if self.Patch < other.Patch:
				return -1
			else:
				return 1

		if self.Build != other.Build:
			if self.Build < other.Build:
				return -1
			else:
				return 1

		return 0
