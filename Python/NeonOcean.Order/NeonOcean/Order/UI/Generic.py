import webbrowser

from NeonOcean.Order import Debug, Language, This
from NeonOcean.Order.UI import Dialogs
from ui import ui_dialog

OpenBrowserDialogText = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.Open_Browser_Dialog.Text")  # type: Language.String
OpenBrowserDialogYesButton = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.Open_Browser_Dialog.Yes_Button")  # type: Language.String
OpenBrowserDialogNoButton = Language.String(This.Mod.Namespace + ".System.Generic_Dialogs.Open_Browser_Dialog.No_Button")  # type: Language.String

def ShowOpenBrowserDialog (url: str) -> None:
	dialogArguments = {
		"text": OpenBrowserDialogText.GetCallableLocalizationString(),
		"text_ok": OpenBrowserDialogYesButton.GetCallableLocalizationString(),
		"text_cancel": OpenBrowserDialogNoButton.GetCallableLocalizationString()
	}

	def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				webbrowser.open(url, new = 2)
		except Exception as e:
			Debug.Log("Failed to run the callback for the open browser dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	Dialogs.ShowOkCancelDialog(callback = DialogCallback, queue = False, **dialogArguments)
