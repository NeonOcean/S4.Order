import traceback
import typing

import services
from NeonOcean.Order import Debug, Language, SettingsShared, This
from sims4 import localization
from ui import ui_dialog, ui_dialog_picker

InvalidInputNotificationTitle = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Invalid_Input_Notification.Title")  # type: Language.String
InvalidInputNotificationText = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Invalid_Input_Notification.Text")  # type: Language.String

PresetConfirmDialogTitle = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Preset_Confirm_Dialog.Title")  # type: Language.String
PresetConfirmDialogText = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Preset_Confirm_Dialog.Text")  # type: Language.String
PresetConfirmDialogYesButton = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Preset_Confirm_Dialog.Yes_Button")  # type: Language.String
PresetConfirmDialogNoButton = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Preset_Confirm_Dialog.No_Button")  # type: Language.String

class SettingDialog:
	HostNamespace = This.Mod.Namespace
	HostName = This.Mod.Name

	_returnCallbacks = dict()  # type: typing.Dict[ui_dialog.UiDialogBase, typing.Callable[[], None]]

	def __init_subclass__ (cls, **kwargs):
		cls.OnInitializeSubclass()

	@classmethod
	def OnInitializeSubclass (cls) -> None:
		pass

	@classmethod
	def ShowDialog (cls, setting: typing.Type[SettingsShared.SettingBase], returnCallback: typing.Callable[[], None] = None, **kwargs) -> None:
		if services.current_zone() is None:
			Debug.Log("Tried to show setting dialog before a zone was loaded\n" + str.join("", traceback.format_stack()), cls.HostNamespace, Debug.LogLevels.Warning, group = cls.HostNamespace, owner = __name__)
			return

		cls._ShowDialogInternal(setting, setting.Get(), kwargs, returnCallback = returnCallback)

	@classmethod
	def _ShowDialogInternal (cls,
							 setting: typing.Type[SettingsShared.SettingBase],
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		pass

	@classmethod
	def _CreateArguments (cls,
						  setting: typing.Type[SettingsShared.SettingBase],
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		pass

	@classmethod
	def _CreateDialog (cls, dialogArguments: dict,
					   *args, **kwargs) -> None:

		pass

	@classmethod
	def _OnDialogResponse (cls, dialog: ui_dialog.UiDialogBase, *args, **kwargs) -> None:
		pass

class DialogButton:
	def __init__ (self,
				  responseID: int,
				  sortOrder: int,
				  callback: typing.Callable[[ui_dialog.UiDialog], None],
				  text: localization.LocalizedString,
				  subText: localization.LocalizedString = None):
		"""
		:param responseID: The identifier used to determine which response the dialog was given.
		:type responseID: int

		:param sortOrder: A number used to sort button on the dialog.
		:type sortOrder: int

		:param callback: A function that will be called after this button was clicked, it should take the associated dialog as an argument.
		:type callback: typing.Callable[[], None]

		:param text: The localization string of the text shown on the button, you shouldn't make this callable.
		:type text: localization.LocalizedString

		:param subText: The localization string of the sub text shown on the button, you shouldn't make this callable.
		:type subText: localization.LocalizedString | None
		"""

		self.ResponseID = responseID  # type: int
		self.SortOrder = sortOrder  # type: int

		self.Callback = callback  # type: typing.Callable[[ui_dialog.UiDialog], None]

		self.Text = text  # type: localization.LocalizedString
		self.SubText = subText  # type: localization.LocalizedString

	Callback: typing.Callable

	def GenerateDialogResponse (self) -> ui_dialog.UiDialogResponse:
		buttonTextString = lambda *args, **kwargs: self.Text

		responseArguments = {
			"dialog_response_id": self.ResponseID,
			"sort_order": self.SortOrder,
			"text": buttonTextString
		}

		if self.SubText is not None:
			buttonSubTextString = lambda *args, **kwargs: self.SubText

			responseArguments["subtext"] = buttonSubTextString

		response = ui_dialog.UiDialogResponse(**responseArguments)

		return response

class ChoiceDialogButton(DialogButton):
	ChoiceButton = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Choice_Button")  # type: Language.String

	def __init__ (self, selected: bool = False, *args, **kwargs):
		"""
		:param selected: Whether or not the button's text will have a selected look.
		:type selected: bool
		"""

		super().__init__(*args, **kwargs)

		self.Selected = selected  # type: bool

	def GenerateDialogResponse (self) -> ui_dialog.UiDialogResponse:
		if self.Selected:
			valueButtonStringTokens = ("&gt; ", self.Text, " &lt;")
		else:
			valueButtonStringTokens = ("", self.Text, "")

		buttonTextString = self.ChoiceButton.GetCallableLocalizationString(*valueButtonStringTokens)

		responseArguments = {
			"dialog_response_id": self.ResponseID,
			"sort_order": self.SortOrder,
			"text": buttonTextString
		}

		if self.SubText is not None:
			buttonSubTextString = lambda *args, **kwargs: self.SubText

			responseArguments["subtext"] = buttonSubTextString

		response = ui_dialog.UiDialogResponse(**responseArguments)

		return response

class DialogRow:
	def __init__ (self,
				  optionID: int,
				  callback: typing.Callable[[ui_dialog.UiDialog], None],
				  text: localization.LocalizedString,
				  icon = None):
		"""
		:param optionID: The identifier used to determine which response the dialog was given.
		:type optionID: int

		:param callback: A function that will be called after this row was clicked, it should take the associated dialog as an argument.
		:type callback: typing.Callable[[], None]

		:param text: The localization string of the text shown on the row, you shouldn't make this callable.
		:type text: localization.LocalizedString

		:param icon: The icon of this row.
		:type icon: localization.LocalizedString | None
		"""

		self.OptionID = optionID  # type: int

		self.Callback = callback  # type: typing.Callable[[ui_dialog.UiDialog], None]

		self.Text = text  # type: localization.LocalizedString
		self.Icon = icon  # type: localization.LocalizedString

	def GenerateRow (self) -> ui_dialog_picker.ObjectPickerRow:
		row = ui_dialog_picker.ObjectPickerRow(option_id = self.OptionID, name = self.Text, icon = self.Icon)
		return row

class StandardDialog(SettingDialog):
	TextTemplate = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Standard.Text_Template")  # type: Language.String
	TextDocumentationTemplate = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Standard.Text_Documentation_Template")  # type: Language.String

	AcceptButton = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Apply_Button")  # type: Language.String
	CancelButton = Language.String(This.Mod.Namespace + ".System.Setting_Dialogs.Cancel_Button")  # type:  Language.String

	@classmethod
	def GetTitleText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
		return Language.CreateLocalizationString("")

	@classmethod
	def GetDescriptionText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
		return Language.CreateLocalizationString("")

	@classmethod
	def GetDefaultText (cls, setting: typing.Type[SettingsShared.SettingBase]) -> localization.LocalizedString:
		return Language.CreateLocalizationString("")

	@classmethod
	def GetDocumentationURL (cls, setting: typing.Type[SettingsShared.SettingBase]) -> typing.Optional[str]:
		return None

	@classmethod
	def _ShowDialogInternal (cls,
							 setting: typing.Type[SettingsShared.SettingBase],
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		acceptButtonCallback = cls._CreateAcceptButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialog], None]
		cancelButtonCallback = cls._CreateCancelButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialog], None]

		dialogButtons = cls._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogButton]
		dialogArguments = cls._CreateArguments(setting, currentValue, showDialogArguments, dialogButtons = dialogButtons)  # type: typing.Dict[str, typing.Any]
		dialog = cls._CreateDialog(dialogArguments)  # type: ui_dialog.UiDialogOkCancel

		def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel):
			try:
				cls._OnDialogResponse(dialogReference, dialogButtons = dialogButtons, acceptButtonCallback = acceptButtonCallback, cancelButtonCallback = cancelButtonCallback)
			except Exception as e:
				Debug.Log("Failed to run the callback for the setting dialog of '" + setting.Key + "'.", cls.HostNamespace, Debug.LogLevels.Exception, group = cls.HostNamespace, owner = __name__)
				raise e

		dialog.add_listener(DialogCallback)
		dialog.show_dialog()

	# noinspection PyUnusedLocal
	@classmethod
	def _CreateAcceptButtonCallback (cls,
									 setting: typing.Type[SettingsShared.SettingBase],
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def AcceptButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			setting.Set(currentValue)

			if returnCallback is not None:
				returnCallback()

		return AcceptButtonCallback

	# noinspection PyUnusedLocal
	@classmethod
	def _CreateCancelButtonCallback (cls,
									 setting: typing.Type[SettingsShared.SettingBase],
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def CancelButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			if returnCallback is not None:
				returnCallback()

		return CancelButtonCallback

	@classmethod
	def _CreateButtons (cls,
						setting: typing.Type[SettingsShared.SettingBase],
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs) -> typing.List[DialogButton]:

		buttons = list()
		return buttons

	@classmethod
	def _CreateArguments (cls,
						  setting: typing.Type[SettingsShared.SettingBase],
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		dialogArguments = dict()

		dialogOwner = showDialogArguments.get("owner")

		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]

		dialogResponses = list()  # type: typing.List[ui_dialog.UiDialogResponse]

		for dialogButton in dialogButtons:  # type: DialogButton
			dialogResponses.append(dialogButton.GenerateDialogResponse())

		documentationURL = cls.GetDocumentationURL(setting)  # type: typing.Optional[str]

		if documentationURL is not None:
			textTokens = (
				cls.GetDescriptionText(setting),
				cls.GetDefaultText(setting),
				documentationURL
			)

			textString = cls.TextDocumentationTemplate.GetCallableLocalizationString(*textTokens)
		else:
			textTokens = (
				cls.GetDescriptionText(setting),
				cls.GetDefaultText(setting)
			)

			textString = cls.TextTemplate.GetCallableLocalizationString(*textTokens)

		dialogArguments["owner"] = dialogOwner
		dialogArguments["title"] = Language.MakeLocalizationStringCallable(cls.GetTitleText(setting))
		dialogArguments["text"] = textString
		dialogArguments["text_ok"] = cls.AcceptButton.GetCallableLocalizationString()
		dialogArguments["text_cancel"] = cls.CancelButton.GetCallableLocalizationString()
		dialogArguments["ui_responses"] = dialogResponses

		return dialogArguments

	@classmethod
	def _CreateDialog (cls, dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog.UiDialogOkCancel:

		if not "owner" in dialogArguments:
			dialogArguments["owner"] = None

		dialog = ui_dialog.UiDialogOkCancel.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOkCancel

		return dialog

	@classmethod
	def _OnDialogResponse (cls, dialog: ui_dialog.UiDialog, *args, **kwargs) -> None:
		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
			acceptButtonCallback = kwargs["acceptButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			acceptButtonCallback(dialog)

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
			cancelButtonCallback = kwargs["cancelButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			cancelButtonCallback(dialog)

		for dialogButton in dialogButtons:  # type: DialogButton
			if dialog.response == dialogButton.ResponseID:
				dialogButton.Callback(dialog)
