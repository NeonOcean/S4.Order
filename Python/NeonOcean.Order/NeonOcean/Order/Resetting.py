import inspect
import sys
import types
import typing

from NeonOcean.Order import Debug, Language, Mods, This
from NeonOcean.Order.UI import Dialogs
from ui import ui_dialog

DialogTitle = Language.String(This.Mod.Namespace + ".System.Reset.Dialog.Title")  # type: Language.String
DialogText = Language.String(This.Mod.Namespace + ".System.Reset.Dialog.Text")  # type: Language.String
DialogEverythingButton = Language.String(This.Mod.Namespace + ".System.Reset.Dialog.Everything_Button")  # type: Language.String
DialogSettingsButton = Language.String(This.Mod.Namespace + ".System.Reset.Dialog.Settings_Button")  # type: Language.String
DialogCancelButton = Language.String(This.Mod.Namespace + ".System.Reset.Dialog.Cancel_Button")  # type: Language.String

ConfirmDialogTitle = Language.String(This.Mod.Namespace + ".System.Reset.Confirm_Dialog.Title")  # type: Language.String
ConfirmDialogEverythingText = Language.String(This.Mod.Namespace + ".System.Reset.Confirm_Dialog.Everything_Text")  # type: Language.String
ConfirmDialogSettingsText = Language.String(This.Mod.Namespace + ".System.Reset.Confirm_Dialog.Settings_Text")  # type: Language.String
ConfirmDialogYesButton = Language.String(This.Mod.Namespace + ".System.Reset.Confirm_Dialog.Yes_Button")  # type: Language.String
ConfirmDialogNoButton = Language.String(This.Mod.Namespace + ".System.Reset.Confirm_Dialog.No_Button")  # type: Language.String

def ResetEverything (mod: Mods.Mod) -> bool:
	"""
	Resets everything that can be reset in the target mod.

	:return: Returns true if successful or false if not.
	:rtype: bool
	"""

	try:
		for module in mod.Modules:  # type: str
			OnReset = None  # type: types.FunctionType

			try:
				OnReset = getattr(sys.modules[module], "_OnReset")
			except:
				pass

			if isinstance(OnReset, types.FunctionType):
				if len(inspect.signature(OnReset).parameters) == 0:
					OnReset()
	except Exception as e:
		Debug.Log("Failed to reset mod.", mod.Namespace, Debug.LogLevels.Exception, group = mod.Namespace, owner = __name__, exception = e)
		return False

	return True

def ResetSettings (mod: Mods.Mod) -> bool:
	"""
	Resets all settings in this mod.

	:return: Returns true if successful or false if not.
	:rtype: bool
	"""

	try:
		for module in mod.Modules:  # type: str
			OnReset = None  # type: types.FunctionType

			try:
				OnReset = getattr(sys.modules[module], "_OnResetSettings")
			except:
				pass

			if isinstance(OnReset, types.FunctionType):
				if len(inspect.signature(OnReset).parameters) == 0:
					OnReset()
	except Exception as e:
		Debug.Log("Failed to reset all settings.", mod.Namespace, Debug.LogLevels.Exception, group = mod.Namespace, owner = __name__, exception = e)
		return False

	return True

def ShowResetDialog (mod: Mods.Mod) -> None:
	everythingResponseID = 20000  # type: int
	everythingResponse = ui_dialog.UiDialogResponse(
		sort_order = -2,
		dialog_response_id = everythingResponseID,
		text = DialogEverythingButton.GetCallableLocalizationString()
	)  # type: ui_dialog.UiDialogResponse

	settingsResponseID = 20001  # type: int
	settingsResponse = ui_dialog.UiDialogResponse(
		sort_order = -1,
		dialog_response_id = settingsResponseID,
		text = DialogSettingsButton.GetCallableLocalizationString()
	)  # type: ui_dialog.UiDialogResponse

	dialogArguments = {
		"title": DialogTitle.GetCallableLocalizationString(mod.Name),
		"text": DialogText.GetCallableLocalizationString(),
		"text_ok": DialogCancelButton.GetCallableLocalizationString(),
		"ui_responses": [everythingResponse, settingsResponse]
	}

	def ConfirmDialogEverythingCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				ResetEverything(mod)
				return
		except Exception as e:
			Debug.Log("Failed to run the confirm dialog everything callback for the reset dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	def ConfirmDialogSettingsCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				ResetSettings(mod)
				return
		except Exception as e:
			Debug.Log("Failed to run the confirm dialog settings callback for the reset dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				return

			confirmDialogCallback = None  # type: typing.Callable
			confirmDialogText = None  # type: typing.Callable

			if dialogReference.response == everythingResponseID:
				confirmDialogCallback = ConfirmDialogEverythingCallback
				confirmDialogText = ConfirmDialogEverythingText.GetCallableLocalizationString()
			elif dialogReference.response == settingsResponseID:
				confirmDialogCallback = ConfirmDialogSettingsCallback
				confirmDialogText = ConfirmDialogSettingsText.GetCallableLocalizationString()

			confirmDialogArguments = {
				"title": ConfirmDialogTitle.GetCallableLocalizationString(mod.Name),
				"text": confirmDialogText,
				"text_ok": ConfirmDialogYesButton.GetCallableLocalizationString(),
				"text_cancel": ConfirmDialogNoButton.GetCallableLocalizationString()
			}  # type: typing.Dict[str, ...]

			Dialogs.ShowOkCancelDialog(callback = confirmDialogCallback, queue = False, **confirmDialogArguments)
		except Exception as e:
			Debug.Log("Failed to run the callback for the reset dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	Dialogs.ShowOkDialog(callback = DialogCallback, queue = False, **dialogArguments)
