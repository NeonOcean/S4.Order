from __future__ import annotations

import typing

import services
from NeonOcean.S4.Order import Director, This
from NeonOcean.S4.Order.Tools import Exceptions
from ui import ui_dialog

_dialogDisplayable = False  # type: bool
_queue = list()  # type: typing.List[ui_dialog.UiDialogBase]

class _EnableAnnouncer(Director.Announcer):
	Host = This.Mod

	Reliable = True

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, *args, **kwargs) -> None:
		global _dialogDisplayable, _queue

		_dialogDisplayable = True

		from NeonOcean.S4.Order import Debug

		for dialog in _queue:  # type: ui_dialog.UiDialogBase
			try:
				dialog.show_dialog()
			except Exception:
				Debug.Log("Failed to show a queued notification.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

		_queue = list()

class _DisableAnnouncer(Director.Announcer):
	Host = This.Mod

	Reliable = True
	Preemptive = True

	@classmethod
	def OnClientDisconnect (cls, *args, **kwargs) -> None:
		global _dialogDisplayable
		_dialogDisplayable = False

def ShowOkDialog (callback: typing.Callable = None, queue: bool = True, **dialogArguments) -> None:
	"""
	:param callback: Called after the dialog gets a response from the user. This will never be called it the dialog has no responses.
	 				 The callback function will receive one argument; a reference to the dialog.
	:type callback: typing.Callable
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	global _dialogDisplayable

	if not isinstance(callback, typing.Callable) and callback is not None:
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in dialogArguments:
		dialogArguments["owner"] = None

	dialog = ui_dialog.UiDialogOk.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOk

	if callback is not None:
		dialog.add_listener(callback)

	if services.current_zone() is not None and _dialogDisplayable:
		dialog.show_dialog()
	else:
		_dialogDisplayable = False

		if queue:
			_queue.append(dialog)

def ShowOkCancelDialog (callback: typing.Callable = None, queue: bool = True, **dialogArguments) -> None:
	"""
	:param callback: Called after the dialog gets a response from the user. This will never be called it the dialog has no responses.
	 				 The callback function will receive one argument; a reference to the dialog.
	:type callback: typing.Callable
	:param queue: When true and the UI dialog service is not running the dialog will be put in queue until it is. Otherwise the dialog will be ignored.
				  The ui dialog service will only run while a zone is loaded.
	:type queue: bool
	"""

	global _dialogDisplayable

	if not isinstance(callback, typing.Callable) and callback is not None:
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	if not isinstance(queue, bool):
		raise Exceptions.IncorrectTypeException(queue, "queue", (bool,))

	if not "owner" in dialogArguments:
		dialogArguments["owner"] = None

	dialog = ui_dialog.UiDialogOkCancel.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOkCancel

	if callback is not None:
		dialog.add_listener(callback)

	if services.current_zone() is not None and _dialogDisplayable:
		dialog.show_dialog()
	else:
		_dialogDisplayable = False

		if queue:
			_queue.append(dialog)
