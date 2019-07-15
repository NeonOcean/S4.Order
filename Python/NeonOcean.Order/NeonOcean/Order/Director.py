import typing

import zone
from NeonOcean.Order import Mods, This
from NeonOcean.Order.Tools import Exceptions
from server import client as clientModule
from sims4.tuning import instance_manager

_announcers = list()  # type: typing.List[typing.Type[Announcer]]

class Announcer:
	Host = This.Mod  # type: Mods.Mod
	Enabled = True  # type: bool

	Reliable = False  # type: bool  # Whether the announcer will be called if the host is disabled.
	Preemptive = False  # type: bool  # Whether the annoucnment methods are called before or after the function they are announcing.

	_level = 0  # type: float

	def __init_subclass__ (cls, **kwargs):
		SetupAnnouncer(cls)

	@classmethod
	def GetLevel (cls) -> float:
		return cls._level

	@classmethod
	def SetLevel (cls, value) -> None:
		cls._level = value
		_SortAnnouncer()

	@classmethod
	def InstanceManagerOnStart (cls, instanceManager: instance_manager.InstanceManager) -> None:
		pass

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		pass

	@classmethod
	def OnClientConnect (cls, clientReference: clientModule.Client) -> None:
		pass

	@classmethod
	def OnClientDisconnect (cls, clientReference: clientModule.Client) -> None:
		pass

def GetAllAnnouncers () -> typing.List[typing.Type[Announcer]]:
	return list(_announcers)

def SetupAnnouncer (announcer: typing.Type[Announcer]) -> None:
	if not issubclass(announcer, Announcer):
		raise Exceptions.IncorrectTypeException(announcer, "announcer", (Announcer,))

	if announcer in _announcers:
		return

	_Register(announcer)

	_SortAnnouncer()

def _Register (announcer: typing.Type[Announcer]) -> None:
	if not announcer in _announcers:
		_announcers.append(announcer)

def _SortAnnouncer () -> None:
	global _announcers

	announcer = _announcers.copy()  # type: typing.List[typing.Type[Announcer]]

	sortedAnnouncer = list()

	for loopCount in range(len(announcer)):  # type: int
		targetIndex = None  # type: int

		for currentIndex in range(len(announcer)):
			if targetIndex is None:
				targetIndex = currentIndex
				continue

			if announcer[currentIndex].GetLevel() != announcer[targetIndex].GetLevel():
				if announcer[currentIndex].GetLevel() < announcer[targetIndex].GetLevel():
					targetIndex = currentIndex
					continue
			else:
				if announcer[currentIndex].__module__ < announcer[targetIndex].__module__:
					targetIndex = currentIndex
					continue

		sortedAnnouncer.append(announcer[targetIndex])
		announcer.pop(targetIndex)

		_announcers = sortedAnnouncer
