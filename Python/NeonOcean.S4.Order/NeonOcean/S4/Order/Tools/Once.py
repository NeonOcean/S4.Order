from __future__ import annotations

import typing

from NeonOcean.S4.Order.Tools import Exceptions

class Once:
	def __init__ (self):
		"""
		An object for tracking whether or not sections of code that are only suppose to run once have done so already.
		"""

		self.Triggered = dict()  # type: typing.Dict[str, typing.Set[typing.Any]]

	def Block (self, identifier: str, reference: typing.Any = None) -> None:
		"""
		Signal that a section of code is blocked off.
		:param identifier: This identifier should be unique to the section of code meant to be blocked. The line number and module name together should be sufficient.
		:type identifier: str
		:param reference: If you want the section of code to be run then blocked for every object, set the object as the reference. Other let this be None.
		"""

		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		if identifier not in self.Triggered:
			identifierReferences = set()  # type: typing.Set[typing.Any]
			identifierReferences.add(reference)
			self.Triggered[identifier] = set()

		self.Triggered[identifier].add(reference)

	def Unblock (self, identifier: str, reference: typing.Any = None) -> None:
		"""
		Unblock a previously blocked identifier and reference combination. If it is not blocked nothing will happen.
		:param identifier: This identifier should be unique to the section of code meant to be blocked. The line number and module name together should be sufficient.
		:type identifier: str
		:param reference: If you want the section of code to be run then blocked for every object, set the object as the reference. Other let this be None.
		"""

		if identifier not in self.Triggered:
			return

		blockedReferences = self.Triggered[identifier]

		if reference in blockedReferences:
			blockedReferences.remove(reference)

	def UnblockIdentifier (self, identifier: str) -> None:
		"""
		Remove all blocked references for this identifier.
		:param identifier: This identifier should be unique to the section of code meant to be blocked. The line number and module name together should be sufficient.
		:type identifier: str
		"""

		if identifier not in self.Triggered:
			return

		self.Triggered[identifier] = set()

	def UnblockAll (self) -> None:
		"""
		Remove all blocked identifier and reference combinations.
		"""

		self.Triggered = dict()

	def IsBlocked (self, identifier: str, reference: typing.Any = None) -> bool:
		"""
		Get whether or not this combination of identifier and reference has been blocked.
		:param identifier: This identifier should be unique to the section of code meant to be blocked. The line number and module name together should be sufficient.
		:type identifier: str
		:param reference: If you want the section of code to be run then blocked for every object, set the object as the reference. Other let this be None.
		"""

		if not isinstance(identifier, str):
			raise Exceptions.IncorrectTypeException(identifier, "identifier", (str,))

		if identifier in self.Triggered:
			if reference in self.Triggered[identifier]:
				return True

		return False
