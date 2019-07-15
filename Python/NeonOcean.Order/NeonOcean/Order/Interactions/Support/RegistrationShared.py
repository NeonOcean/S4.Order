import typing

import enum
from objects import script_object

class RegistrationTargets(enum.Int):
	Terrain = 14982  # type: RegistrationTargets
	Humans = 14965  # type: RegistrationTargets
	HumanBabies = 14826  # type: RegistrationTargets
	Dogs = 120620  # type: RegistrationTargets
	SmallDogs = 174619  # type: RegistrationTargets
	Cats = 120621  # type: RegistrationTargets

class RegistrationExtensionAbstract:
	@classmethod
	def GetRegisteredObjects (cls) -> typing.List[typing.Type[script_object.ScriptObject]]:
		"""
		Get a list of game objects this interaction is registered to.
		"""

		raise NotImplementedError()

	@classmethod
	def RegisterObject (cls, objectReference: typing.Type[script_object.ScriptObject]) -> None:
		"""
		Add this interaction to the specified object.
		:return:
		"""

		raise NotImplementedError()

	@classmethod
	def UnregisterObject (cls, objectReference: typing.Type[script_object.ScriptObject]) -> None:
		"""
		Remove this interaction from a specific object
		:return:
		"""

		raise NotImplementedError()

	@classmethod
	def UnregisterAllObjects (cls) -> None:
		"""
		Remove this interaction from all objects its registered to.
		:return:
		"""

		raise NotImplementedError()

	@classmethod
	def ShouldRegisterAllObjects (cls) -> bool:
		"""
		Whether or not this interaction should be attached to all game objects.
		"""

		raise NotImplementedError()

	@classmethod
	def GetRelevantObjectGUIDs (cls) -> typing.List[int]:
		"""
		Get a list of the GUIDs of every game object that this interaction should be attached to.
		"""

		raise NotImplementedError()

	@classmethod
	def GetRelevantObjectTypes (cls) -> typing.List[str]:
		"""
		Get a list of the types of game object that this interaction should be attached to. You will probably also need to create a type determiner function and
		register it with the interaction's registration handler.
		"""

		raise NotImplementedError()
