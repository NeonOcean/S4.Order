import time
import typing

import services
from NeonOcean.Order import Debug, Director, Mods, This
from NeonOcean.Order.Interactions.Support import RegistrationShared
from NeonOcean.Order.Tools import Exceptions
from objects import script_object
from sims4 import resources
from sims4.tuning import instance_manager

class RegistrationHandler:
	Host = This.Mod  # type: Mods.Mod

	_registeredInteractions = list()  # type: typing.List[typing.Type[RegistrationShared.RegistrationExtensionAbstract]]
	_typeDeterminers = dict()  # type: typing.Dict[typing.Callable, str]

	def __init_subclass__ (cls, **kwargs):
		cls._registeredInteractions = list()
		cls._typeDeterminers = dict()

	@classmethod
	def HandleInteraction (cls, interactionReference: typing.Type[RegistrationShared.RegistrationExtensionAbstract]) -> None:
		"""
		Register an interaction to be handled by this handler.
		:param interactionReference:
		:return:
		"""

		if not isinstance(interactionReference, type):
			raise Exceptions.IncorrectTypeException(interactionReference, "interactionReference", (type,))

		if not issubclass(interactionReference, RegistrationShared.RegistrationExtensionAbstract):
			raise Exception("Interaction does not inherit the registration extension")

		if interactionReference in cls._registeredInteractions:
			return

		cls._registeredInteractions.append(interactionReference)

	@classmethod
	def StopHandlingInteraction (cls, interactionReference: typing.Type[RegistrationShared.RegistrationExtensionAbstract]) -> None:
		if not interactionReference in cls._registeredInteractions:
			return

		cls._registeredInteractions.remove(interactionReference)

	@classmethod
	def RegisterTypeDeterminer (cls, typeDeterminer: typing.Callable[[typing.Type[script_object.ScriptObject]], bool], typeIdentifier: str) -> None:
		"""
		Register a method to determine the type of an object.
		:param typeDeterminer: A type determiner, this should take the object reference and give a boolean indicating whether or not it is of that type. This should be
		unique as type determiners are stored in a dictionary by this value.
		:param typeIdentifier: The type identifier, used to signal to interactions what type of object it is. Non built-in type determiners should have unique
		identifiers to avoid conflicts. Case does not matter for type identifier strings.
		"""

		if typeDeterminer in cls._typeDeterminers:
			return

		cls._typeDeterminers[typeDeterminer] = typeIdentifier.lower()

	@classmethod
	def UnregisterTypeDeterminer (cls, typeDeterminer: typing.Callable[[typing.Type[script_object.ScriptObject]], bool]) -> None:
		"""
		Unregister a object type determiner.
		:param typeDeterminer: The type determiner to be removed from the list.
		"""

		cls._typeDeterminers.pop(typeDeterminer, None)

	@classmethod
	def RegisterAllInteractions (cls) -> None:
		"""
		Register all interactions handled by this handler.
		"""

		cls.RegisterInteractions(cls._registeredInteractions)

	@classmethod
	def RegisterInteractions (cls, interactions: typing.List[typing.Type[RegistrationShared.RegistrationExtensionAbstract]]) -> None:
		"""
		Register a list of interactions.
		"""

		operationStartTime = time.time()  # type: float

		# noinspection PyProtectedMember
		objectReferences = services.get_instance_manager(resources.Types.OBJECT)._tuned_classes.values()  # type: typing.List[typing.Type[script_object.ScriptObject]]

		guidTargets = dict()  # type: typing.Dict[int, list]
		typeTargets = dict()  # type: typing.Dict[str, list]

		for interactionReference in interactions:  # type: typing.Type[RegistrationShared.RegistrationExtensionAbstract]
			for relevantGUID in interactionReference.GetRelevantObjectGUIDs():  # type: int
				if relevantGUID not in guidTargets:
					guidTargets[relevantGUID] = [interactionReference]
				else:
					guidTargets[relevantGUID].append(interactionReference)

			for relevantType in interactionReference.GetRelevantObjectTypes():  # type: str
				relevantType = relevantType.lower()

				if relevantType not in typeTargets:
					typeTargets[relevantType] = [interactionReference]
				else:
					typeTargets[relevantType].append(interactionReference)

		relevantTypeDeterminers = dict()  # type: typing.Dict[typing.Callable, str]

		for typeDeterminer, typeIdentifier in cls._typeDeterminers.items():  # type: typing.Callable, str
			typeIdentifier = typeIdentifier.lower()

			if typeIdentifier in typeTargets:
				relevantTypeDeterminers[typeDeterminer] = typeIdentifier

		shouldTypeCheck = bool(relevantTypeDeterminers)  # type: bool

		for objectReference in objectReferences:  # type: typing.Type[script_object.ScriptObject]
			objectDeterminedTypes = list()  # type: typing.List[str]

			if shouldTypeCheck:
				for typeDeterminer, typeIdentifier in relevantTypeDeterminers.items():  # type: typing.Callable, str
					try:
						if typeDeterminer(objectReference):
							objectDeterminedTypes.append(typeIdentifier)
					except:
						Debug.Log("Type determiner failed to determine if an object matches the type identifier '" + typeIdentifier + "'.\n" + str(objectReference), cls.Host.Namespace, Debug.LogLevels.Exception, group = cls.Host.Namespace, owner = __name__)

			if objectReference.guid in guidTargets:
				for interactionReference in guidTargets[objectReference.guid]:
					interactionReference.RegisterObject(objectReference)

			for objectDeterminedType in objectDeterminedTypes:  # type: str
				if objectDeterminedType in typeTargets:
					for interactionReference in typeTargets[objectDeterminedType]:
						interactionReference.RegisterObject(objectReference)

		operationTime = time.time() - operationStartTime
		Debug.Log("Finished Registering %s interactions in %s seconds with %s game objects existing." % (len(interactions), operationTime, len(objectReferences)), cls.Host.Namespace, Debug.LogLevels.Info, group = cls.Host.Namespace, owner = __name__)

class _Announcer(Director.Announcer):
	_level = 500  # type: int

	@classmethod
	def InstanceManagerOnStart (cls, instanceManager: instance_manager.InstanceManager):
		if instanceManager.TYPE != resources.Types.OBJECT:
			return

		RegistrationHandler.RegisterAllInteractions()

def RegisterInteractionToAll (interactionReference: typing.Type) -> None:
	"""
	Attach an interaction to every object in the game.
	:param interactionReference: The interaction, this doesn't need to inherit the RegistrationExtension class to work.
	"""

	# noinspection PyProtectedMember
	objectReferences = services.get_instance_manager(resources.Types.OBJECT)._tuned_classes.values()  # type: typing.List[typing.Type[script_object.ScriptObject]]

	for objectReference in objectReferences:  # type: typing.Type[script_object.ScriptObject]
		RegisterInteraction(interactionReference, objectReference)

# noinspection PyProtectedMember
def RegisterInteraction (interactionReference: typing.Type, objectReference: typing.Type[script_object.ScriptObject]) -> None:
	"""
	Attach an interaction to a specific object. If the interaction is already attached nothing will happen.
	:param interactionReference: The interaction, this doesn't need to inherit the RegistrationExtension class to work.
	:param objectReference: The script object that the interaction is meant to be attached to.
	"""

	if interactionReference in objectReference._super_affordances:
		return

	objectReference._super_affordances += (interactionReference,)
