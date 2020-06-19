from __future__ import annotations

import sys

from NeonOcean.S4.Order import Debug, Mods, This
from NeonOcean.S4.Order.Tools import Events, Exceptions, Types

ModLoadedEvent = Events.EventHandler()
ModUnloadedEvent = Events.EventHandler()  # type: Events.EventHandler

class ModLoadedEventArguments(Events.EventArguments):
	def __init__ (self, mod: Mods.Mod):
		if not isinstance(mod, Mods.Mod):
			raise Exceptions.IncorrectTypeException(mod, "mod", (Mods.Mod,))

		self.Mod = mod  # type: Mods.Mod

class ModUnloadedEventArguments(Events.EventArguments):
	def __init__ (self, mod: Mods.Mod, exiting: bool):
		if not isinstance(mod, Mods.Mod):
			raise Exceptions.IncorrectTypeException(mod, "mod", (Mods.Mod,))

		if not isinstance(exiting, bool):
			raise Exceptions.IncorrectTypeException(exiting, "exiting", (bool,))

		self.Mod = mod  # type: Mods.Mod
		self.Exiting = exiting  # type: bool

def InvokeModLoadedEvent (mod: Mods.Mod) -> ModLoadedEventArguments:
	"""
	Invokes the mod loaded event. Should be triggered every time a mod is loaded.

	:param mod: A reference the mod in question.
	:type mod: Mods.Mod
	:rtype: None
	"""

	eventArguments = ModLoadedEventArguments(mod)  # type: ModLoadedEventArguments

	for modLoadedCallback in ModLoadedEvent:
		try:
			modLoadedCallback(sys.modules[__name__], eventArguments)
		except:
			Debug.Log("Failed to invoke a mod loaded callback at '" + Types.GetFullName(modLoadedCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	return eventArguments

def InvokeModUnloadedEvent (mod: Mods.Mod, exiting: bool) -> ModUnloadedEventArguments:
	"""
	Invokes the mod unloaded event. Should be triggered every time a mod is unloaded.

	:param mod: A reference the mod in question.
	:type mod: Mods.Mod
	:param exiting: Whether or not the mod is unloading because the application is closing.
	:type exiting: bool
	:rtype: None
	"""

	eventArguments = ModUnloadedEventArguments(mod, exiting)  # type: ModUnloadedEventArguments

	for modUnloadedCallback in ModUnloadedEvent:
		try:
			modUnloadedCallback(sys.modules[__name__], eventArguments)
		except:
			Debug.Log("Failed to invoke a mod unloaded callback at '" + Types.GetFullName(modUnloadedCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	return eventArguments
