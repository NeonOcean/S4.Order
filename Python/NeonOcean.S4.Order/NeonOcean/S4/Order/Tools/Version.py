from __future__ import annotations

import re
import typing

from NeonOcean.S4.Order.Tools import Exceptions, Types

class Version:
	# noinspection SpellCheckingInspection
	ParsePattern = re.compile(r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$", re.VERBOSE | re.ASCII)
	# Parse pattern lifted from https://semver.org/.
	StringIdentifierPattern = re.compile("^[0-9a-zA-Z-]*$", re.VERBOSE | re.ASCII)

	def __init__ (self, versionString: typing.Optional[str] = None, translate: bool = False):
		"""
		A version system based on semantic versioning specification. https://semver.org/
		:param versionString: A string containing a valid version. Invalid inputs will produce exceptions. Letting this be none will cause the version object to
		default to '0.0.0'.
		:type versionString: typing.Optional[str]
		:param translate: Whether or not we should try to translate a version number if we cannot parse it initially.
		:type translate: bool
		"""

		if not isinstance(versionString, str) and versionString is not None:
			raise Exceptions.IncorrectTypeException(versionString, "versionString", (str, None))

		self.Major = 0
		self.Minor = 0
		self.Patch = 0
		self.PreRelease = ()
		self.Build = ()

		if versionString is not None:
			self.Apply(*self.Parse(versionString, translate = translate))

	@property
	def Major (self) -> int:
		return self._major

	@Major.setter
	def Major (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "Major", (int,))

		self._major = value

	@property
	def Minor (self) -> int:
		return self._minor

	@Minor.setter
	def Minor (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "Minor", (int,))

		self._minor = value

	@property
	def Patch (self) -> int:
		return self._patch

	@Patch.setter
	def Patch (self, value: int) -> None:
		if not isinstance(value, int):
			raise Exceptions.IncorrectTypeException(value, "Patch", (int,))

		self._patch = value

	@property
	def PreRelease (self) -> typing.Tuple[typing.Union[int, str], ...]:
		return self._preRelease

	@PreRelease.setter
	def PreRelease (self, value: typing.Tuple[typing.Union[int, str], ...]) -> None:
		if not isinstance(value, tuple):
			raise Exceptions.IncorrectTypeException(value, "PreRelease", (tuple,))

		for preReleaseIdentifierIndex in range(len(value)):  # type: int
			preReleaseIdentifier = value[preReleaseIdentifierIndex]  # type: typing.Union[str, int]

			if not isinstance(preReleaseIdentifier, (str, int)):
				raise Exceptions.IncorrectTypeException(value, "PreRelease[%s]" % preReleaseIdentifierIndex, (str, int))

			if isinstance(preReleaseIdentifier, str):
				if not self.ValidStringIdentifier(preReleaseIdentifier):
					raise ValueError("'PreRelease[%s]' contains a character outside what is allowed (0-9, A-Z, a-z, or -).\nValue: %s" % (preReleaseIdentifierIndex, preReleaseIdentifier))

		self._preRelease = value

	@property
	def Build (self) -> typing.Tuple[typing.Union[int, str], ...]:
		return self._build

	@Build.setter
	def Build (self, value: typing.Tuple[typing.Union[int, str], ...]) -> None:
		if not isinstance(value, tuple):
			raise Exceptions.IncorrectTypeException(value, "Build", (tuple,))

		for buildIdentifierIndex in range(len(value)):  # type: int
			buildIdentifier = value[buildIdentifierIndex]  # type: typing.Union[str, int]

			if not isinstance(buildIdentifier, (str, int)):
				raise Exceptions.IncorrectTypeException(value, "PreRelease[%s]" % buildIdentifierIndex, (str, int))

			if isinstance(buildIdentifier, str):
				if not self.ValidStringIdentifier(buildIdentifier):
					raise ValueError("'PreRelease[%s]' contains a character outside what is allowed (0-9, A-Z, a-z, or -).\nValue: %s" % (buildIdentifierIndex, buildIdentifier))

		self._build = value

	def __repr__ (self):
		return "%s ('%s')" % (self.__class__.__name__, str(self))

	def __eq__ (self, other):
		compareResult = self.Compare(self, other)  # type: int
		return compareResult == 0

	def __ne__ (self, other):
		compareResult = self.Compare(self, other)  # type: int
		return compareResult != 0

	def __lt__ (self, other):
		compareResult = self.Compare(self, other)  # type: int
		return compareResult < 0

	def __le__ (self, other):
		compareResult = self.Compare(self, other)  # type: int
		return compareResult <= 0

	def __gt__ (self, other):
		compareResult = self.Compare(self, other)  # type: int
		return compareResult > 0

	def __ge__ (self, other):
		compareResult = self.Compare(self, other)  # type: int
		return compareResult >= 0

	def __str__ (self):
		return self.ToString()

	def Apply (self, major: int, minor: int, patch: int, preRelease: tuple, build: tuple) -> None:
		self.Major = major
		self.Minor = minor
		self.Patch = patch
		self.PreRelease = preRelease
		self.Build = build

	def ToString (self):
		versionString = str(self.Major) + "." + str(self.Minor) + "." + str(self.Patch)

		preReleaseString = ""

		for preReleaseIdentifier in self.PreRelease:  # type: typing.Union[str, int]
			if preReleaseString:
				preReleaseString += "." + str(preReleaseIdentifier)
			else:
				preReleaseString += str(preReleaseIdentifier)

		if preReleaseString:
			versionString += "-" + preReleaseString

		buildString = ""

		for buildIdentifier in self.Build:  # type: typing.Union[str, int]
			if buildString:
				buildString += "." + str(buildIdentifier)
			else:
				buildString += str(buildIdentifier)

		if self.Build:
			versionString += "+" + buildString

		return versionString

	@classmethod
	def Parse (cls, versionString: str, translate: bool = False) -> typing.Tuple[int, int, int, typing.Tuple[typing.Union[int, str], ...], typing.Tuple[typing.Union[int, str], ...]]:
		"""
		Parse a version string to get its major, minor, patch, pre-release and build metadata values placed in a tuple in that order.
		:param versionString: A string containing a valid version. Invalid inputs will produce exceptions.
		:type: str
		:param translate: Whether or not we should try to translate a version number if we cannot parse it initially.
		:type translate: bool
		"""

		if not isinstance(versionString, str):
			raise Exceptions.IncorrectTypeException(versionString, "versionString", (str,))

		match = cls.ParsePattern.match(versionString)  # type: typing.Optional[typing.Match]

		if translate:
			try:
				translatedVersionString = cls.Translate(versionString)
			except Exception as e:
				raise ValueError("Could not parse or translate the version string '%s'." % versionString) from e

			match = cls.ParsePattern.match(translatedVersionString)  # type: typing.Optional[typing.Match]

			if not match:
				raise ValueError("Could not parse or translate the version string '%s'." % versionString)
		else:
			if not match:
				raise ValueError("Could not parse the version string '%s'." % versionString)

		(majorString, minorString, patchString, preReleaseString, buildString) = match.groups()  # type: str

		major = int(majorString)  # type: int
		minor = int(minorString)  # type: int
		patch = int(patchString)  # type: int

		if preReleaseString:
			preReleaseIdentifiers = preReleaseString.split(".")  # type: typing.List[str]
			preRelease = ()  # type: typing.Tuple[typing.Union[int, str], ...]

			for preReleaseIdentifier in preReleaseIdentifiers:  # type: str
				try:
					preRelease += (int(preReleaseIdentifier),)
					continue
				except:
					pass

				preRelease += (preReleaseIdentifier,)
		else:
			preRelease = ()  # type: typing.Tuple[typing.Union[int, str], ...]

		if buildString:
			buildIdentifiers = buildString.split(".")  # type: typing.List[str]
			build = ()  # type: typing.Tuple[typing.Union[int, str], ...]

			for buildIdentifier in buildIdentifiers:  # type: str
				try:
					build += (int(buildIdentifier),)
					continue
				except:
					pass

				build += (buildIdentifier,)
		else:
			build = ()  # type: typing.Tuple[typing.Union[int, str], ...]

		return major, minor, patch, preRelease, build

	@classmethod
	def IsValid (cls, versionString: str) -> bool:
		"""
		Get whether or not the input version string is valid.
		:param versionString: A string containing a valid or invalid version number.
		:type versionString: str
		"""

		if not isinstance(versionString, str):
			raise Exceptions.IncorrectTypeException(versionString, "versionString", (str,))

		match = cls.ParsePattern.match(versionString)

		return bool(match)

	@classmethod
	def Translate (cls, versionString: str) -> str:
		"""
		Try to translate a version string of another type to one that is inline with the semantic versioning specification.
		An exception will be raised if we could not translate if to a valid format.
		"""

		if not isinstance(versionString, str):
			raise Exceptions.IncorrectTypeException(versionString, "versionString", (str,))

		preReleaseStartIndex = versionString.find("-")  # type: typing.Optional[int]
		preReleaseStartIndex = None if preReleaseStartIndex == -1 else preReleaseStartIndex

		buildStartIndex = versionString.find("+")  # type: typing.Optional[int]
		buildStartIndex = None if buildStartIndex == -1 else buildStartIndex

		if buildStartIndex is not None and preReleaseStartIndex is not None:
			if buildStartIndex <= preReleaseStartIndex:  # Pre-release identifiers cannot come after the build meta data. The hyphen we found is just part of the build meta data.
				preReleaseStartIndex = None

		if preReleaseStartIndex is not None:
			mainPart = versionString[0:preReleaseStartIndex]  # type: str
		elif buildStartIndex is not None:
			mainPart = versionString[0:buildStartIndex]  # type: str
		else:
			mainPart = versionString

		if not mainPart:
			raise ValueError("Could not find at least a major version number in '%s'." % versionString)

		preReleasePart = versionString[preReleaseStartIndex + 1:buildStartIndex] if preReleaseStartIndex is not None else ""  # type: str
		buildPart = versionString[buildStartIndex + 1:None] if buildStartIndex is not None else ""  # type: str

		mainPartIdentifiers = mainPart.split(".")  # type: typing.List[str]

		if len(mainPartIdentifiers) > 3:
			# Too many identifiers in the main part, these will be booted to the front of the build meta data. All semantic version numbers can only have major, minor, and patch numbers in their main sections.

			mainPartExtraIdentifiers = mainPartIdentifiers[3:]

			if buildPart:
				buildPart = ".".join(mainPartExtraIdentifiers) + "." + buildPart
			else:
				buildPart = ".".join(mainPartExtraIdentifiers)

			mainPartIdentifiers = mainPartIdentifiers[:3]
			assert len(mainPartIdentifiers) == 3

		elif len(mainPartIdentifiers) < 3:
			# Too few identifiers in the main part, we need to add at least one. All semantic version numbers must have major, minor, and patch numbers.

			mainPartMissingIdentifiers = 3 - len(mainPartIdentifiers)  # type: int

			for _ in range(mainPartMissingIdentifiers):
				mainPartIdentifiers.append("0")

			assert len(mainPartIdentifiers) == 3

		mainPart = ".".join(mainPartIdentifiers)

		buildPart = buildPart.replace("+", ".")  # Replace extra plus signs in the build meta data part. More than one plus sign in a version string will cause errors.

		translatedVersionString = ""

		if mainPart:
			translatedVersionString += mainPart

		if preReleasePart:
			translatedVersionString += "-" + preReleasePart

		if buildPart:
			translatedVersionString += "+" + buildPart

		if not cls.IsValid(translatedVersionString):
			raise ValueError("Could not translate '%s' to a valid version number." % versionString)

		return translatedVersionString

	@classmethod
	def Compare (cls, leftVersion, rightVersion) -> int:
		"""
		Compare two version objects together.
		:return: Less than zero, if the left version is less than the right version. Zero, If the left and right version are equal. Greater than zero, If the
		left version is greater than the right version.
		:rtype: int
		"""

		if not isinstance(leftVersion, Version) or not isinstance(rightVersion, Version):
			raise TypeError("Version compare operations are not supported between instances of '%s' and '%s'" % (Types.GetFullName(leftVersion), Types.GetFullName(rightVersion)))

		if leftVersion.Major != rightVersion.Major:
			if leftVersion.Major < rightVersion.Major:
				return -1
			else:
				return 1

		if leftVersion.Minor != rightVersion.Minor:
			if leftVersion.Minor < rightVersion.Minor:
				return -1
			else:
				return 1

		leftPatch = leftVersion.Patch if leftVersion.Patch >= 0 else 0  # type: int
		rightPatch = rightVersion.Patch if rightVersion.Patch >= 0 else 0  # type: int
		if leftPatch != rightPatch:
			if leftPatch < rightPatch:
				return -1
			else:
				return 1

		if len(leftVersion.PreRelease) != 0 and len(rightVersion.PreRelease) == 0:
			return -1
		elif len(leftVersion.PreRelease) == 0 and len(rightVersion.PreRelease) != 0:
			return 1

		for preReleaseIndex in range(len(leftVersion.PreRelease)):  # type: int
			if len(rightVersion.PreRelease) - 1 < preReleaseIndex:
				break

			leftPreReleaseIdentifier = leftVersion.PreRelease[preReleaseIndex]  # type: typing.Union[str, int]
			rightPreReleaseIdentifier = rightVersion.PreRelease[preReleaseIndex]  # type: typing.Union[str, int]

			if leftPreReleaseIdentifier == rightPreReleaseIdentifier:
				continue

			if isinstance(leftPreReleaseIdentifier, int) and isinstance(rightPreReleaseIdentifier, str):
				return -1
			elif isinstance(leftPreReleaseIdentifier, str) and isinstance(rightPreReleaseIdentifier, int):
				return 1

			assert isinstance(leftPreReleaseIdentifier, int) and isinstance(rightPreReleaseIdentifier, int) or \
				   isinstance(leftPreReleaseIdentifier, str) and isinstance(rightPreReleaseIdentifier, str)

			if leftPreReleaseIdentifier < rightPreReleaseIdentifier:
				return -1
			else:
				return 1

		if len(leftVersion.PreRelease) < len(rightVersion.PreRelease):
			return -1
		elif len(leftVersion.PreRelease) > len(rightVersion.PreRelease):
			return 1

		return 0

	@classmethod
	def ValidStringIdentifier (cls, identifier: str) -> bool:
		"""
		Get whether or not a pre-release or build string identifier is valid. An identifier is invalid if it contains a character outside what is permitted
		(0-9, A-Z, a-z, or -).
		"""

		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		if re.match(cls.StringIdentifierPattern, identifier) is None:
			return False

		return True