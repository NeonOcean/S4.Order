import typing

import services
from NeonOcean.Order import Director, This
from NeonOcean.Order.Tools import Exceptions
from ui import ui_dialog, ui_dialog_notification

_dialogDisplayable = False  # type: bool
_queue = list()  # type: typing.List[ui_dialog.UiDialogBase]

class _EnableAnnouncer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, *args, **kwargs) -> None:
		global _dialogDisplayable, _queue

		_dialogDisplayable = True

		from NeonOcean.Order import Debug

		for dialog in _queue:  # type: ui_dialog.UiDialogBase
			try:
				dialog.show_dialog()
			except Exception:
				Debug.Log("Failed to show a queued notification.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		_queue = list()

class _DisableAnnouncer(Director.Announcer):
	Host = This.Mod

	Preemptive = True

	@classmethod
	def OnClientDisconnect (cls, *args, **kwargs) -> None:
		global _dialogDisplayable
		_dialogDisplayable = False

def ShowNotification (queue: bool = False, **notificationArguments) -> None:
	"""
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	global _dialogDisplayable

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in notificationArguments:
		notificationArguments["owner"] = None

	dialog = ui_dialog_notification.UiDialogNotification.TunableFactory().default(**notificationArguments)  # type: ui_dialog_notification.UiDialogNotification

	if services.current_zone() is not None and _dialogDisplayable:
		dialog.show_dialog()
	else:
		_dialogDisplayable = False

		if queue:
			_queue.append(dialog)
