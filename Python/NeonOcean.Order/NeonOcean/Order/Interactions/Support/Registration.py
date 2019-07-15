import typing

from NeonOcean.Order.Interactions.Support import RegistrationHandler, RegistrationShared
from objects import script_object
from sims4.tuning import tunable

class AutomaticObjectRegistrationHandler:
	@classmethod
	def GetRelevantGUIDs (cls, interactionReference) -> typing.List[int]:
		"""
		Get the GUIDs of the objects that this interaction should be registered to.
		:return:
		"""

		relevantGUIDs = list()  # type: list
		getGUIDMethods = [cls._GetGUIDsTerrain, cls._GetGUIDsHumans, cls._GetGUIDsHumanBabies, cls._GetGUIDsDogs, cls._GetGUIDsSmallDogs, cls._GetGUIDsCats]

		for getGUIDMethod in getGUIDMethods:  # type: typing.Callable
			receivedGUIDs = getGUIDMethod(interactionReference)  # type: typing.Union[None, int, typing.List[int]]

			if receivedGUIDs is None:
				continue
			elif isinstance(receivedGUIDs, int):
				relevantGUIDs.append(receivedGUIDs)
			else:
				relevantGUIDs.extend(receivedGUIDs)

		return relevantGUIDs

	@classmethod
	def GetRelevantTypes (cls, interactionReference) -> typing.List[str]:
		"""
		Get the types of the objects that this interaction should be registered to.
		:return:
		"""

		relevantTypes = list()  # type: list
		getTypesMethods = [cls._GetTypesSims]

		for getTypeMethod in getTypesMethods:  # type: typing.Callable
			receivedTypes = getTypeMethod(interactionReference)  # type: typing.Union[None, int, typing.List[int]]

			if receivedTypes is None:
				continue
			elif isinstance(receivedTypes, str):
				relevantTypes.append(receivedTypes)
			else:
				relevantTypes.extend(receivedTypes)

		return relevantTypes

	@classmethod
	def ShouldRegisterAll (cls, interactionReference) -> bool:
		try:
			if not getattr(interactionReference.ObjectRegistrationTargeting, "RegisterAllObjects"):
				return False
		except:
			return False

		return True

	@classmethod
	def _GetGUIDsTerrain (cls, interactionReference) -> typing.Union[None, int, typing.List[int]]:
		return cls._GetGUIDsSimpleInternal(interactionReference, "Terrain", RegistrationShared.RegistrationTargets.Terrain)

	@classmethod
	def _GetGUIDsHumans (cls, interactionReference) -> typing.Union[None, int, typing.List[int]]:
		return cls._GetGUIDsSimpleInternal(interactionReference, "Humans", RegistrationShared.RegistrationTargets.Humans)

	@classmethod
	def _GetGUIDsHumanBabies (cls, interactionReference) -> typing.Union[None, int, typing.List[int]]:
		return cls._GetGUIDsSimpleInternal(interactionReference, "HumanBabies", RegistrationShared.RegistrationTargets.HumanBabies)

	@classmethod
	def _GetGUIDsDogs (cls, interactionReference) -> typing.Union[None, int, typing.List[int]]:
		return cls._GetGUIDsSimpleInternal(interactionReference, "Dogs", RegistrationShared.RegistrationTargets.Dogs)

	@classmethod
	def _GetGUIDsSmallDogs (cls, interactionReference) -> typing.Union[None, int, typing.List[int]]:
		return cls._GetGUIDsSimpleInternal(interactionReference, "SmallDogs", RegistrationShared.RegistrationTargets.SmallDogs)

	@classmethod
	def _GetGUIDsCats (cls, interactionReference) -> typing.Union[None, int, typing.List[int]]:
		return cls._GetGUIDsSimpleInternal(interactionReference, "Cats", RegistrationShared.RegistrationTargets.Cats)

	@classmethod
	def _GetGUIDsSimpleInternal (cls, interactionReference, targetingAttributeName: str, targets: typing.Union[int, typing.List[int]]) -> typing.Union[None, int, typing.List[int]]:
		try:
			if not getattr(interactionReference.AutomaticObjectRegistration, targetingAttributeName):
				return None
		except:
			return None

		return targets

	@classmethod
	def _GetTypesSims (cls, interactionReference) -> typing.Union[None, int, typing.List[int]]:
		return cls._GetTypesSimpleInternal(interactionReference, "Sims", "Sim")

	@classmethod
	def _GetTypesSimpleInternal (cls, interactionReference, targetingAttributeName: str, targets: typing.Union[str, typing.List[str]]) -> typing.Union[None, str, typing.List[str]]:
		try:
			if not getattr(interactionReference.AutomaticObjectRegistration, targetingAttributeName):
				return None
		except:
			return None

		return targets

class RegistrationExtension(RegistrationShared.RegistrationExtensionAbstract):
	"""
	Allows you to setup automatic registration of interactions to objects.
	"""

	class AutomaticObjectRegistrationHandler(AutomaticObjectRegistrationHandler):
		pass

	RegisterAllObjects: bool
	BasicObjectRegistrationGUIDs: typing.Tuple[int]
	BasicObjectRegistrationTypes: typing.Tuple[str]
	AutomaticObjectRegistration: typing.Any

	# noinspection SpellCheckingInspection
	INSTANCE_TUNABLES = {
		"RegisterAllObjects": tunable.Tunable(description = "When this is set to true this interaction will be registered to all objects in the game. All other targeting settings will be ignored if this is enabled.", tunable_type = bool, default = False),

		"BasicObjectRegistrationGUIDs": tunable.TunableList(
			description = "A list of instance id of objects for this interaction to be registered to.",
			tunable = tunable.Tunable(description = "An instance id.", tunable_type = int, default = None)
		),

		"BasicObjectRegistrationTypes": tunable.TunableList(
			description = "A list of the types of object this interaction should be registered to. A type determiner python function needs to also exist and be registered with the type identifier for object registration to occur.",
			tunable = tunable.Tunable(description = "An instance id.", tunable_type = int, default = None)
		),

		"AutomaticObjectRegistration": tunable.TunableTuple(
			Terrain = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to the terrain object.", tunable_type = bool, default = False),
			Sims = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to all sims, this includes all humans, human babies, cats, dogs and any future creatures that use the 'Sim' or 'Baby' python class.", tunable_type = bool, default = False),
			Humans = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to humans.", tunable_type = bool, default = False),
			HumanBabies = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to human babies.", tunable_type = bool, default = False),
			Dogs = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to dogs.", tunable_type = bool, default = False),
			SmallDogs = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to small dogs.", tunable_type = bool, default = False),
			Cats = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to cats.", tunable_type = bool, default = False),
		)
	}

	_registeredObjects = list()  # type: typing.List[typing.Type[script_object.ScriptObject]]

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		cls._registeredObjects = list()  # type: typing.List[typing.Type[script_object.ScriptObject]]

	@classmethod
	def GetRegisteredObjects (cls) -> typing.List[typing.Type[script_object.ScriptObject]]:
		"""
		Get a list of game objects this interaction is registered to.
		"""

		return list(cls._registeredObjects)

	@classmethod
	def RegisterObject (cls, objectReference: typing.Type[script_object.ScriptObject]) -> None:
		"""
		Add this interaction to the specified object.
		:return:
		"""

		if objectReference in cls._registeredObjects:
			return

		# noinspection PyProtectedMember
		objectReference._super_affordances += (cls,)
		cls._registeredObjects.append(objectReference)

	@classmethod
	def UnregisterObject (cls, objectReference: typing.Type[script_object.ScriptObject]) -> None:
		"""
		Remove this interaction from a specific object
		:return:
		"""

		# noinspection PyProtectedMember, SpellCheckingInspection
		objectReference._super_affordances = tuple(filter(lambda interactionReference: interactionReference != cls, objectReference._super_affordances))
		cls._registeredObjects.remove(objectReference)

	@classmethod
	def UnregisterAllObjects (cls) -> None:
		"""
		Remove this interaction from all objects its registered to.
		:return:
		"""

		objectReferenceIndex = 0  # type: int

		while objectReferenceIndex < len(cls._registeredObjects):
			cls.UnregisterObject(cls._registeredObjects[objectReferenceIndex])

	@classmethod
	def ShouldRegisterAllObjects (cls) -> bool:
		"""
		Whether or not this interaction should be attached to all game objects.
		"""

		try:
			return cls.RegisterAllObjects
		except:
			return False

	@classmethod
	def GetRelevantObjectGUIDs (cls) -> typing.List[int]:
		"""
		Get a list of the GUIDs of every game object that this interaction should be attached to.
		"""

		relevantGUIDS = list()  # type: typing.List[int]
		relevantGUIDS.extend(cls.AutomaticObjectRegistrationHandler.GetRelevantGUIDs(cls))

		try:
			relevantGUIDS.extend(cls.BasicObjectRegistrationGUIDs)
		except:
			pass

		return relevantGUIDS

	@classmethod
	def GetRelevantObjectTypes (cls) -> typing.List[str]:
		"""
		Get a list of the types of game object that this interaction should be attached to. You will probably also need to create a type determiner function and
		register it with the interaction's registration handler.
		"""

		relevantTypes = list()  # type: typing.List[str]
		relevantTypes.extend(cls.AutomaticObjectRegistrationHandler.GetRelevantTypes(cls))

		try:
			relevantTypes.extend(cls.BasicObjectRegistrationTypes)
		except:
			pass

		return relevantTypes

	@classmethod
	def _tuning_loaded_callback (cls):
		superObject = super()
		if hasattr(superObject, "_tuning_loaded_callback"):
			# noinspection PyProtectedMember
			superObject._tuning_loaded_callback()

		RegistrationHandler.RegistrationHandler.HandleInteraction(cls)
