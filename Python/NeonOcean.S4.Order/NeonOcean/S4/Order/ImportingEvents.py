from __future__ import annotations

from NeonOcean.S4.Order import Debug, This
from NeonOcean.S4.Order.Tools import Events, Types

OnAllImportedEvent = Events.EventHandler()
OnAllImportedLateEvent = Events.EventHandler()

# Called when every mod's modules have been imported

def InvokeOnAllImportedEvent () -> Events.EventArguments:
	"""
	Invokes the on all imported events.
	On all imported events should be called after every mod's modules have been imported.
	"""

	eventArguments = Events.EventArguments()

	for onAllImportedCallback in OnAllImportedEvent:
		try:
			onAllImportedCallback(None, eventArguments)
		except:
			Debug.Log("Failed to invoke an on all imported callback at '" + Types.GetFullName(onAllImportedCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	for onAllImportedLateCallback in OnAllImportedLateEvent:
		try:
			onAllImportedLateCallback(None, eventArguments)
		except:
			Debug.Log("Failed to invoke an on all imported late callback at '" + Types.GetFullName(onAllImportedLateCallback) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	return eventArguments
