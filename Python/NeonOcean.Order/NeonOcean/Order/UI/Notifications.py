import typing

import services
import zone
from NeonOcean.Order import Director, This
from NeonOcean.Order.Tools import Exceptions
from ui import ui_dialog, ui_dialog_notification

_queue = list()  # type: typing.List[ui_dialog.UiDialogBase]

class _Announcer(Director.Announcer):
	Host = This.Mod

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		global _queue

		from NeonOcean.Order import Debug

		for dialog in _queue:  # type: ui_dialog.UiDialogBase
			try:
				dialog.show_dialog()
			except:
				Debug.Log("Failed to show a queued notification.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		_queue = list()

def ShowNotification (queue: bool = False, **dialogArguments) -> None:
	"""
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	global _canShowDialog

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in dialogArguments:
		dialogArguments["owner"] = None

	dialog = ui_dialog_notification.UiDialogNotification.TunableFactory().default(**dialogArguments)  # type: ui_dialog_notification.UiDialogNotification

	if services.current_zone() is not None:
		dialog.show_dialog()
	else:
		_canShowDialog = False

		if queue:
			_queue.append(dialog)
