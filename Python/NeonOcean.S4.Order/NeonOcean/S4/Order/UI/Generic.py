from __future__ import annotations

import typing
import webbrowser

from NeonOcean.S4.Order import Debug, Language, Mods, This
from NeonOcean.S4.Order.Tools import Exceptions
from NeonOcean.S4.Order.UI import Dialogs
from sims4 import localization
from ui import ui_dialog

OpenBrowserDialogText = Language.String(This.Mod.Namespace + ".Generic_Dialogs.Open_Browser_Dialog.Text")  # type: Language.String
OpenBrowserDialogYesButton = Language.String(This.Mod.Namespace + ".Generic_Dialogs.Open_Browser_Dialog.Yes_Button", fallbackText = "Yes_Button")  # type: Language.String
OpenBrowserDialogNoButton = Language.String(This.Mod.Namespace + ".Generic_Dialogs.Open_Browser_Dialog.No_Button", fallbackText = "No_Button")  # type: Language.String

AboutModDialogTitle = Language.String(This.Mod.Namespace + ".Generic_Dialogs.About_Mod_Dialog.Title")  # type: Language.String
AboutModDialogText = Language.String(This.Mod.Namespace + ".Generic_Dialogs.About_Mod_Dialog.Text")  # type: Language.String
AboutModDialogOkButton = Language.String(This.Mod.Namespace + ".Generic_Dialogs.About_Mod_Dialog.Ok_Button", fallbackText = "Ok_Button")  # type: Language.String
AboutModDialogUnknown = Language.String(This.Mod.Namespace + ".Generic_Dialogs.About_Mod_Dialog.Unknown", fallbackText = "About_Mod_Dialog.Unknown")  # type: Language.String

def ShowOpenBrowserDialog (url: str, returnCallback: typing.Optional[typing.Callable[[], None]] = None) -> None:
	"""
	Show a dialog asking the user to confirm their intention to open a website in their browser.
	:param url: The url to be opened when the user clicks the ok button.
	:type url: str
	:param returnCallback: Called after the dialog has closed.
	:type returnCallback: typing.Optional[typing.Callable[[], None]]
	"""

	if not isinstance(url, str):
		raise Exceptions.IncorrectTypeException(url, "url", (str,))

	if not isinstance(returnCallback, typing.Callable) and returnCallback is not None:
		raise Exceptions.IncorrectTypeException(returnCallback, "returnCallback", ("Callable", None))

	dialogArguments = {
		"text": OpenBrowserDialogText.GetCallableLocalizationString(url),
		"text_ok": OpenBrowserDialogYesButton.GetCallableLocalizationString(),
		"text_cancel": OpenBrowserDialogNoButton.GetCallableLocalizationString()
	}

	def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				webbrowser.open(url, new = 2)

			if returnCallback is not None:
				returnCallback()
		except Exception:
			Debug.Log("Failed to run the callback for the open browser dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	Dialogs.ShowOkCancelDialog(callback = DialogCallback, queue = False, **dialogArguments)

def ShowAboutModDialog (mod: Mods.Mod, returnCallback: typing.Optional[typing.Callable[[], None]] = None) -> None:
	"""
	:param mod: The mod for the about dialog to show information on.
	:type mod: Mods.Mod
	:param returnCallback: Called after the dialog has closed.
	:type returnCallback: typing.Optional[typing.Callable[[], None]]
	"""

	if not isinstance(mod, Mods.Mod):
		raise Exceptions.IncorrectTypeException(mod, "mod", (Mods.Mod,))

	if mod.BuildDate is not None:
		buildDate = str(mod.BuildDate.date())  # type: typing.Union[str, localization.LocalizedString]
	else:
		buildDate = AboutModDialogUnknown.GetLocalizationString()  # type: typing.Union[str, localization.LocalizedString]

	if mod.BuildGameVersion is None:
		buildGameVersion = str(mod.BuildGameVersion)  # type: typing.Union[str, localization.LocalizedString]
	else:
		buildGameVersion = AboutModDialogUnknown.GetLocalizationString()  # type: typing.Union[str, localization.LocalizedString]

	dialogArguments = {
		"title": AboutModDialogTitle.GetCallableLocalizationString(mod.Name),
		"text": AboutModDialogText.GetCallableLocalizationString(mod.Name, mod.Author, str(mod.Version), buildDate, buildGameVersion),
		"text_ok": AboutModDialogOkButton.GetCallableLocalizationString(),
	}

	# noinspection PyUnusedLocal
	def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if returnCallback is not None:
				returnCallback()
		except Exception:
			Debug.Log("Failed to run the callback for the about mod dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	Dialogs.ShowOkDialog(callback = DialogCallback, queue = False, **dialogArguments)
