import typing

import zone
from NeonOcean.Order import Debug, This, Mods
from NeonOcean.Order.Tools import Exceptions, Patcher, Types
from sims4.tuning import instance_manager

_announcers = list()  # type: typing.List[typing.Type[Announcer]]

class Announcer:
	Host = This.Mod  # type: Mods.Mod
	Enabled = True  # type: bool
	Reliable = False  # type: bool

	_level = 0  # type: float

	def __init_subclass__ (cls, **kwargs):
		SetupAnnouncer(cls)

	@classmethod
	def GetLevel (cls) -> float:
		return cls._level

	@classmethod
	def SetLevel (cls, value) -> None:
		cls._level = value
		_SortAnnouncers()

	@classmethod
	def OnInitializeSubclass (cls) -> None:
		pass

	@classmethod
	def OnInstanceManagerLoaded (cls, instanceManager: instance_manager.InstanceManager) -> None:
		pass

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		pass

def SetupAnnouncer (announcer: typing.Type[Announcer]) -> None:
	if not issubclass(announcer, Announcer):
		raise Exceptions.IncorrectTypeException(announcer, "announcer", (Announcer,))

	if announcer in _announcers:
		return

	_announcers.append(announcer)

	_SortAnnouncers()
	OnInitializeSubclass(announcer)

def OnInitializeSubclass (announcer: typing.Type[Announcer]) -> None:
	try:
		if not announcer.Enabled:
			return

		if not announcer.Host.IsLoaded() and not announcer.Reliable:
			return

		announcer.OnInitializeSubclass()
	except Exception as e:
		Debug.Log("Failed to run 'OnInitializeSubclass' for '" + Types.GetFullName(announcer) + "'", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__, exception = e)

@Patcher.Decorator(instance_manager.InstanceManager, "on_start", permanent = True)
def OnInstanceManagerLoaded (self: instance_manager.InstanceManager) -> None:
	for announcer in _announcers:  # type: typing.Type[Announcer]
		try:
			if not announcer.Enabled:
				continue

			if not announcer.Host.IsLoaded() and not announcer.Reliable:
				continue

			announcer.OnInstanceManagerLoaded(self)
		except Exception as e:
			Debug.Log("Failed to run 'OnInstanceManagerLoaded' for '" + Types.GetFullName(announcer) + "'", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__, exception = e)

@Patcher.Decorator(zone.Zone, "on_loading_screen_animation_finished", permanent = True)
def OnLoadingScreenAnimationFinished (self: zone.Zone) -> None:
	for announcer in _announcers:  # type: typing.Type[Announcer]
		try:
			if not announcer.Enabled:
				continue

			if not announcer.Host.IsLoaded() and not announcer.Reliable:
				continue

			announcer.OnLoadingScreenAnimationFinished(self)
		except Exception as e:
			Debug.Log("Failed to run 'OnLoadingScreenAnimationFinished' for '" + Types.GetFullName(announcer) + "'", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__, exception = e)

def _SortAnnouncers () -> None:
	global _announcers

	announcers = _announcers.copy()  # type: typing.List[typing.Type[Announcer]]

	sortedAnnouncers = list()

	for loopCount in range(len(announcers)):  # type: int
		targetIndex = None  # type: int

		for currentIndex in range(len(announcers)):
			if targetIndex is None:
				targetIndex = currentIndex
				continue

			if announcers[currentIndex].GetLevel() != announcers[targetIndex].GetLevel():
				if announcers[currentIndex].GetLevel() < announcers[targetIndex].GetLevel():
					targetIndex = currentIndex
					continue
			else:
				if announcers[currentIndex].__module__ < announcers[targetIndex].__module__:
					targetIndex = currentIndex
					continue

		sortedAnnouncers.append(announcers[targetIndex])
		announcers.pop(targetIndex)

		_announcers = sortedAnnouncers