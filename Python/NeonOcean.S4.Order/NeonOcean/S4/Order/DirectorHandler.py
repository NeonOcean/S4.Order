from __future__ import annotations

import typing

import services
import zone
from NeonOcean.S4.Order import Director
from NeonOcean.S4.Order.Tools import Patcher, Types

class _Announcement:
	def __init__ (self, targetObject: object, targetCallableName: str, announcementName: str, announcementCallWrapper: typing.Callable = None):
		self.AnnouncementName = announcementName  # type: str
		self.AnnouncementCallWrapper = announcementCallWrapper  # type: typing.Optional[typing.Callable]

		def AnnouncementBeforePatch (*args, **kwargs) -> typing.Any:
			self._TriggerAnnouncement(self.AnnouncementName, True, *args, **kwargs)

		def AnnouncementAfterPatch (*args, **kwargs) -> typing.Any:
			self._TriggerAnnouncement(self.AnnouncementName, False, *args, **kwargs)

		Patcher.Patch(targetObject, targetCallableName, AnnouncementBeforePatch, patchType = Patcher.PatchTypes.Before, permanent = True)
		Patcher.Patch(targetObject, targetCallableName, AnnouncementAfterPatch, patchType = Patcher.PatchTypes.After, permanent = True)

	def _TriggerAnnouncement (self, announcementMethodName: str, preemptive: bool, *announcementArgs, **announcementKwargs) -> None:
		for announcer in Director.GetAllAnnouncers():  # type: typing.Type[Director.Announcer]
			try:
				if not announcer.Enabled:
					continue

				if not announcer.Host.IsLoaded() and not announcer.Reliable:
					continue

				if preemptive != announcer.Preemptive:
					continue

				announcementMethod = getattr(announcer, announcementMethodName, None)  # type: typing.Callable

				if announcementMethod is not None:
					if self.AnnouncementCallWrapper is None:
						announcementMethod(*announcementArgs, **announcementKwargs)
					else:
						self.AnnouncementCallWrapper(announcementMethod, *announcementArgs, **announcementKwargs)

			except Exception:
				from NeonOcean.S4.Order import Debug
				Debug.Log("Failed to run '" + announcementMethodName + "' for '" + Types.GetFullName(announcer) + "'", announcer.Host.Namespace, Debug.LogLevels.Exception, group = announcer.Host.Namespace, owner = __name__)

# noinspection PyUnusedLocal
def _OnLoadingScreenAnimationFinishedWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

# noinspection PyUnusedLocal
def _OnClientDisconnectWrapper (announcementMethod: typing.Callable, client, *args, **kwargs) -> None:
	announcementMethod(client)

# noinspection PyUnusedLocal
def _ZoneLoadWrapper (announcementMethod: typing.Callable, self, *args, **kwargs) -> None:
	announcementMethod(self)

_onLoadingScreenAnimationFinished = _Announcement(zone.Zone, "on_loading_screen_animation_finished", Director.Announcer.OnLoadingScreenAnimationFinished.__name__, announcementCallWrapper = _OnLoadingScreenAnimationFinishedWrapper)
_onClientDisconnect = _Announcement(services, "on_client_disconnect", Director.Announcer.OnClientDisconnect.__name__, announcementCallWrapper = _OnClientDisconnectWrapper)
_zoneLoad = _Announcement(zone.Zone, "load_zone", Director.Announcer.ZoneLoad.__name__, announcementCallWrapper = _ZoneLoadWrapper)
