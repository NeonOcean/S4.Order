from __future__ import annotations

import typing

import clock
import zone
from NeonOcean.S4.Order import Mods, This
from NeonOcean.S4.Order.Tools import Exceptions
from protocolbuffers import FileSerialization_pb2
from server import client as clientModule
from sims4 import service_manager
from sims4.tuning import instance_manager

_announcers = list()  # type: typing.List[typing.Type[Announcer]]

class Announcer:
	Host = This.Mod  # type: Mods.Mod
	Enabled = True  # type: bool

	Reliable = False  # type: bool  # Whether the announcer will be called if the host is disabled.
	Preemptive = False  # type: bool  # Whether the annoucnment methods are called before or after the function they are announcing.

	_priority = 0  # type: float # Higher priority announcers will run before lower priority ones.

	def __init_subclass__ (cls, **kwargs):
		SetupAnnouncer(cls)

	@classmethod
	def GetPriority (cls) -> float:
		return cls._priority

	@classmethod
	def SetPriority (cls, value) -> None:
		cls._priority = value
		_SortAnnouncer()

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		pass

	@classmethod
	def OnClientDisconnect (cls, clientReference: clientModule.Client) -> None:
		pass

	@classmethod
	def ZoneLoad (cls, zoneReference: zone.Zone) -> None:
		pass

def GetAllAnnouncers () -> typing.List[typing.Type[Announcer]]:
	return list(_announcers)

def SetupAnnouncer (announcer: typing.Type[Announcer]) -> None:
	if not isinstance(announcer, type):
		raise Exceptions.IncorrectTypeException(announcer, "announcer", (type,))

	if not issubclass(announcer, Announcer):
		raise Exceptions.DoesNotInheritException("announcer", (Announcer,))

	if announcer in _announcers:
		return

	_Register(announcer)

	_SortAnnouncer()

def _Register (announcer: typing.Type[Announcer]) -> None:
	if not announcer in _announcers:
		_announcers.append(announcer)

def _SortAnnouncer () -> None:
	global _announcers

	announcersCopy = _announcers.copy()  # type: typing.List[typing.Type[Announcer]]

	sortedAnnouncers = list()

	for loopCount in range(len(announcersCopy)):  # type: int
		targetIndex = None  # type: typing.Optional[int]

		for currentIndex in range(len(announcersCopy)):
			if targetIndex is None:
				targetIndex = currentIndex
				continue

			if -announcersCopy[currentIndex].GetPriority() != -announcersCopy[targetIndex].GetPriority():
				if -announcersCopy[currentIndex].GetPriority() < -announcersCopy[targetIndex].GetPriority():
					targetIndex = currentIndex
					continue
			else:
				if announcersCopy[currentIndex].__module__ < announcersCopy[targetIndex].__module__:
					targetIndex = currentIndex
					continue

		sortedAnnouncers.append(announcersCopy[targetIndex])
		announcersCopy.pop(targetIndex)

	_announcers = sortedAnnouncers



