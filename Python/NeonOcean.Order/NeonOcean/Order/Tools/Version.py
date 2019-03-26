import re

from NeonOcean.Order.Tools import Exceptions

ParseRegex = re.compile(r'^(\d+) \. (\d+) (?:\. (\d+))? (?:\. (\d+))?$', re.VERBOSE | re.ASCII)

class Version:
	def __init__ (self, string: str = None):
		if not isinstance(string, str):
			raise Exceptions.IncorrectTypeException(string, "string", (str,))

		self.Major = 1
		self.Minor = 0
		self.Patch = -1
		self.Build = -1

		if string:
			self.Parse(string)

	def __repr__ (self):
		return "%s ('%s')" % (self.__class__.__name__, str(self))

	def __eq__ (self, other):
		c = self.Compare(other)
		if c is NotImplemented:
			return c
		return c == 0

	def __ne__ (self, other):
		c = self.Compare(other)
		if c is NotImplemented:
			return c
		return c != 0

	def __lt__ (self, other):
		c = self.Compare(other)
		if c is NotImplemented:
			return c
		return c < 0

	def __le__ (self, other):
		c = self.Compare(other)
		if c is NotImplemented:
			return c
		return c <= 0

	def __gt__ (self, other):
		c = self.Compare(other)
		if c is NotImplemented:
			return c
		return c > 0

	def __ge__ (self, other):
		c = self.Compare(other)
		if c is NotImplemented:
			return c
		return c >= 0

	def __str__ (self):
		returnString = str(self.Major) + "." + str(self.Minor)

		if self.Patch >= 0:
			returnString += "." + str(self.Patch)

		if self.Build >= 0:
			returnString += "." + str(self.Build)

		return returnString

	def Parse (self, string):
		match = ParseRegex.match(string)
		if not match:
			raise ValueError("Invalid version number '%s'" % string)

		(major, minor, patch, build) = match.groups()

		self.Major = int(major)
		self.Minor = int(minor)

		if patch:
			self.Patch = int(patch)

		if build:
			self.Build = int(build)

	def Compare (self, other):
		if other is None:
			return 1

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
