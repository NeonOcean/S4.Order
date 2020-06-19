from __future__ import annotations

import time
import typing

import services
import zone
from NeonOcean.S4.Order import Debug, Director, This
from NeonOcean.S4.Order.Tools import Types
from objects import definition_manager, script_object
from sims4.tuning import tunable
from sims4 import resources

_registrationExtensionInteractions = list()  # type: typing.List[typing.Type[RegistrationExtension]]

class RegistrationInformation(tunable.HasTunableSingletonFactory, tunable.AutoFactoryInit):
	FACTORY_TUNABLES = {
		"InteractionListAttribute": tunable.Tunable(description = "The attribute name of the object's interaction list that the interaction needs to be added to.", tunable_type = str, default = "_super_affordances"),
		"IgnoreMissingAttribute": tunable.Tunable(description = "Whether or not we should ignore an object that is missing the target interaction list or log an error instead.", tunable_type = bool, default = False)
	}

	InteractionListAttribute: str
	IgnoreMissingAttribute: bool

	def GetRelevantObjectInstanceIDs (self) -> typing.Set[int]:
		"""
		Get a list of instances ids that point to the game objects that the interaction should be attached to.
		"""

		return set()

	def GetRelevantObjectTypes (self) -> typing.Set[str]:
		"""
		Get a list of the types of game object that the interaction should be attached to.
		"""

		return set()

	def RegisterObject (self, objectType: typing.Type[script_object.ScriptObject], interactionReference: typing.Type) -> bool:
		"""
		Add the specified interaction to the specified object. This will return false if the interaction could not be registered and true if it could.
		"""

		objectInteractionList = getattr(objectType, self.InteractionListAttribute, None)

		if isinstance(objectInteractionList, (tuple, list)):
			objectInteractionList += (interactionReference,)
			setattr(objectType, self.InteractionListAttribute, objectInteractionList)

			return True
		else:
			if not self.IgnoreMissingAttribute:
				Debug.Log("Failed to find valid interaction list with the attribute name '%s' in an object with a type of '%s'" % (self.InteractionListAttribute, Types.GetFullName(interactionReference)),
						  This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__, lockIdentifier = __name__ + ":ObjectRegistration", lockReference = interactionReference)

			return False

class ByObjectInstanceIDRegistrationInformation(RegistrationInformation):
	FACTORY_TUNABLES = {
		"InstanceIDs": tunable.TunableList(
			description = "The instance id of any game objects that this interaction should be attached to.",
			tunable = tunable.Tunable(tunable_type = int, default = 0)
		)
	}

	InstanceIDs: typing.Tuple[int, ...]

	def GetRelevantObjectInstanceIDs (self) -> typing.Set[int]:
		"""
		Get a list of instances ids that point to the game objects that the interaction should be attached to.
		"""

		return set(self.InstanceIDs)

class RegistrationInformationVariant(tunable.TunableVariant):
	def __init__ (self, *args, **kwargs):
		super().__init__(
			*args,
			byObjectInstanceID = ByObjectInstanceIDRegistrationInformation.TunableFactory(),
			**kwargs
		)

class RegistrationExtension:
	"""
	Allows you to setup automatic registration of interactions to objects.
	"""

	RegisterAllObjects: bool

	# noinspection SpellCheckingInspection
	INSTANCE_TUNABLES = {
		"ObjectRegistrationInformation": tunable.TunableList(
			tunable = RegistrationInformationVariant()
		),
	}

	ObjectRegistrationInformation: typing.List[RegistrationInformation]

	_registeredObjects = dict()  # type: typing.Dict[typing.Type[script_object.ScriptObject], typing.Set[str]]

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		cls._registeredObjects = dict()  # type: typing.Dict[typing.Type[script_object.ScriptObject], typing.Set[str]]

	@classmethod
	def RegisterToObjects (cls) -> None:
		"""
		Add this interaction to the appropriate objects.
		"""

		definitionManager = services.definition_manager()  # type: definition_manager.DefinitionManager

		for registrationInformation in cls.ObjectRegistrationInformation:  # type: RegistrationInformation
			relevantObjects = set()  # type: typing.Set[typing.Type[script_object.ScriptObject]]

			for relevantObjectInstanceID in registrationInformation.GetRelevantObjectInstanceIDs():  # type: int
				relevantObjectKey = resources.get_resource_key(relevantObjectInstanceID, resources.Types.OBJECT)
				matchingObject = definitionManager.types.get(relevantObjectKey, None)  # type: typing.Optional[typing.Type[script_object.ScriptObject]]

				if matchingObject is None:
					continue

				relevantObjects.add(matchingObject)

			for relevantObject in relevantObjects:  # type: typing.Type[script_object.ScriptObject]
				registeredInteractionLists = cls._registeredObjects.get(relevantObject, None)  # type: typing.Optional[typing.List[str]]

				if registeredInteractionLists is not None:
					if registrationInformation.InteractionListAttribute in registeredInteractionLists:
						continue

				registrationInformation.RegisterObject(relevantObject, cls)

				if registeredInteractionLists is not None:
					registeredInteractionLists.append(registrationInformation.InteractionListAttribute)
				else:
					cls._registeredObjects[relevantObject] = { registrationInformation.InteractionListAttribute }

	@classmethod
	def _tuning_loaded_callback (cls):
		superObject = super()
		if hasattr(superObject, "_tuning_loaded_callback"):
			# noinspection PyProtectedMember
			superObject._tuning_loaded_callback()

		cls._RegisterRegistrationExtendedInteraction()

	@classmethod
	def _RegisterRegistrationExtendedInteraction (cls) -> None:
		_registrationExtensionInteractions.append(cls)

class _Announcer(Director.Announcer):
	Host = This.Mod

	_priority = 3000  # type: int

	_zoneLoadTriggered = False  # type: bool

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		if not cls._zoneLoadTriggered:
			RegisterInteractionsToObjects()
			cls._zoneLoadTriggered = True

def RegisterInteractionsToObjects () -> None:
	operationStartTime = time.time()  # type: float

	for extensionInteraction in _registrationExtensionInteractions:  # type: RegistrationExtension
		extensionInteraction.RegisterToObjects()

	operationTime = time.time() - operationStartTime
	Debug.Log("Finished registering %s interactions in %s seconds." % (len(_registrationExtensionInteractions), operationTime), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
