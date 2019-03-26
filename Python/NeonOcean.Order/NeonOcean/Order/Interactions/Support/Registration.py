import typing

import enum
import services
from NeonOcean.Order import Debug, Director, This
from NeonOcean.Order.Tools import Types
from interactions import aop, context, priority
from objects import script_object
from sims4 import resources
from sims4.tuning import instance_manager, tunable

_registeredInteractions = list()  # type: typing.List[typing.Type[RegistrationExtension]]

class RegistrationTargets(enum.Int):
	Terrain = 14982  # type: RegistrationTargets
	Humans = 14965  # type: RegistrationTargets
	Dogs = 120620  # type: RegistrationTargets
	SmallDogs = 174619  # type: RegistrationTargets
	Cats = 120621  # type: RegistrationTargets

class RegistrationExtension:
	"""
	Allows you to setup automatic registration of interactions to objects.
	"""

	# noinspection SpellCheckingInspection
	INSTANCE_TUNABLES = {
		"ObjectRegistrationTargeting": tunable.TunableTuple(
			RegisterAllObjects = tunable.Tunable(description = "When this is set to true this interaction will be registered to all objects in the game. All other targeting settings will be ignored if this is enabled.", tunable_type = bool, default = False),
			AutoRegisterTerrain = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to the terrain object.", tunable_type = bool, default = False),
			AutoRegisterHumans = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to humans.", tunable_type = bool, default = False),
			AutoRegisterDogs = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to dogs.", tunable_type = bool, default = False),
			AutoRegisterSmallDogs = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to small dogs.", tunable_type = bool, default = False),
			AutoRegisterCats = tunable.Tunable(description = "Whether or not the interaction will be automatically registered to cats.", tunable_type = bool, default = False),
			UseCustomRegistration = tunable.Tunable(description = "Whether or not all objects will be sent to 'RegisterCustomObjectTargets' to be registered. This will not override other automatic registration", tunable_type = bool, default = False),
		),
	}

	ObjectRegistrationTargeting: ...

	@classmethod
	def RegisterCustomObjectTargets (cls, objectReferences: typing.List[script_object.ScriptObject]) -> None:
		pass

	@classmethod
	def _tuning_loaded_callback (cls):
		superObject = super()
		if hasattr(superObject, "_tuning_loaded_callback"):
			# noinspection PyProtectedMember
			superObject._tuning_loaded_callback()

		_registeredInteractions.append(cls)

class BasicRegistrationExtension(RegistrationExtension):
	"""
	Allows you to specify specific objects for the interaction to be registered to.
	"""

	# noinspection SpellCheckingInspection
	INSTANCE_TUNABLES = {
		"BasicObjectRegistrationIDs": tunable.TunableList(
			description = "A list of instance id of objects for this interaction to be registered to. The tunable 'ObjectRegistrationTargeting.RegisterCustom' needs to be set to true before this will be used.",
			tunable = tunable.Tunable(description = "An instance id.", tunable_type = int, default = None)
		)
	}

	BasicObjectRegistrationIDs: typing.List[int]

	@classmethod
	def RegisterCustomObjectTargets (cls, objectReferences: typing.List[script_object.ScriptObject]) -> None:
		for objectReference in objectReferences:  # type: script_object.ScriptObject
			if objectReference.guid64 in cls.BasicObjectRegistrationIDs:
				RegisterObjectInteraction(cls, objectReference)

class _AnnouncerReliable(Director.Controller):
	Host = This.Mod
	Reliable = True  # type: bool

	@classmethod
	def OnInstanceManagerLoaded (cls, instanceManager: instance_manager.InstanceManager):
		RegistrationTargetPrefix = "AutoRegister"  # type: str

		if instanceManager.TYPE != resources.Types.OBJECT:
			return

		for interactionReference in _registeredInteractions:  # type: typing.Type[RegistrationExtension]
			# noinspection PyProtectedMember
			objectReferences = instanceManager._tuned_classes.values()  # type: typing.List[script_object.ScriptObject]

			if interactionReference.ObjectRegistrationTargeting.RegisterAllObjects:
				for objectReference in objectReferences:
					RegisterObjectInteraction(interactionReference, objectReference)

				continue

			autoRegisterInteraction = False  # type: bool

			for RegistrationTargetName in RegistrationTargets.names():
				if getattr(interactionReference.ObjectRegistrationTargeting, RegistrationTargetPrefix + RegistrationTargetName) is True:
					autoRegisterInteraction = True

			if autoRegisterInteraction:
				for objectReference in objectReferences:
					for RegistrationTargetName in RegistrationTargets.names():

						if RegistrationTargets[RegistrationTargetName] == objectReference.guid64:
							if getattr(interactionReference.ObjectRegistrationTargeting, RegistrationTargetPrefix + RegistrationTargetName) is True:
								RegisterObjectInteraction(interactionReference, objectReference)

			if interactionReference.ObjectRegistrationTargeting.RegisterCustom:
				try:
					interactionReference.RegisterCustomObjectTargets(objectReferences)
				except Exception as e:
					Debug.Log("Failed to call 'RegisterCustomObjectTargets' for an interaction with the class '" + Types.GetFullName(interactionReference) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

def RegisterAllObjectsInteraction (interactionReference: typing.Type) -> None:
	# noinspection PyProtectedMember
	objectReferences = services.get_instance_manager(resources.Types.OBJECT)._tuned_classes.values()  # type: typing.List[script_object.ScriptObject]

	for objectReference in objectReferences:
		RegisterObjectInteraction(interactionReference, objectReference)

# noinspection PyProtectedMember
def RegisterObjectInteraction (interactionReference: typing.Type, objectReference: script_object.ScriptObject) -> None:
	if interactionReference in objectReference._super_affordances:
		return

	objectReference._super_affordances += (interactionReference,)

def GenerateInteractionInstance (interactionReference: typing.Type) -> object:
	interactionAOP = aop.AffordanceObjectPair(interactionReference, None, interactionReference, None)
	interactionContext = context.InteractionContext(None, context.InteractionContext.SOURCE_SCRIPT, priority.Priority.High)

	return interactionReference(aop = interactionAOP, context = interactionContext)
