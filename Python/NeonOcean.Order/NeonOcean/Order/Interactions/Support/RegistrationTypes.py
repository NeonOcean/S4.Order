import typing

from NeonOcean.Order.Interactions.Support import RegistrationHandler
from objects import script_object
from sims import sim
from sims.baby import baby

def _SimDeterminer (objectReference: typing.Type[script_object.ScriptObject]) -> bool:
	return issubclass(objectReference, sim.Sim) or issubclass(objectReference, baby.Baby)

RegistrationHandler.RegistrationHandler.RegisterTypeDeterminer(_SimDeterminer, "Sim")
