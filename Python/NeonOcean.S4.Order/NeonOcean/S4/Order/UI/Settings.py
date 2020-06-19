from __future__ import annotations

import abc
import traceback
import typing

import services
from NeonOcean.S4.Order import Debug, Language, This
from NeonOcean.S4.Order.Tools import Exceptions, TextBuilder
from NeonOcean.S4.Order.UI import SettingsShared as UISettingsShared
from sims4 import localization
from ui import ui_dialog, ui_dialog_picker

InvalidInputNotificationTitle = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Invalid_Input_Notification.Title")  # type: Language.String
InvalidInputNotificationText = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Invalid_Input_Notification.Text")  # type: Language.String

PresetConfirmDialogTitle = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.Title")  # type: Language.String
PresetConfirmDialogText = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.Text")  # type: Language.String
PresetConfirmDialogYesButton = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.Yes_Button", fallbackText = "Preset_Confirm_Dialog.Yes_Button")  # type: Language.String
PresetConfirmDialogNoButton = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Preset_Confirm_Dialog.No_Button", fallbackText = "Preset_Confirm_Dialog.No_Button")  # type: Language.String

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
	ChoiceButton = Language.String(This.Mod.Namespace + ".Setting_Dialogs.Choice_Button", fallbackText = "Choice_Button")  # type: Language.String

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

		if self.ChoiceButton.IdentifierIsRegistered():
			buttonTextString = self.ChoiceButton.GetCallableLocalizationString(*valueButtonStringTokens)
		else:
			buttonTextString = self.Text

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
				  description: localization.LocalizedString = None,
				  icon = None):
		"""
		:param optionID: The identifier used to determine which response the dialog was given.
		:type optionID: int

		:param callback: A function that will be called after this row was clicked, it should take the associated dialog as an argument.
		:type callback: typing.Callable[[], None]

		:param text: The localization string of the text shown on the row, you shouldn't make this callable.
		:type text: localization.LocalizedString

		:param description: The localization string of the sub text shown on the row, you shouldn't make this callable.
		:type description: localization.LocalizedString | None

		:param icon: A key pointing to this row's icon resource.
		:type icon: resources.Key | None
		"""

		self.OptionID = optionID  # type: int

		self.Callback = callback  # type: typing.Callable[[ui_dialog.UiDialog], None]

		self.Text = text  # type: localization.LocalizedString
		self.Description = description  # type: localization.LocalizedString

		self.Icon = icon

	def GenerateRow (self) -> ui_dialog_picker.ObjectPickerRow:
		row = ui_dialog_picker.ObjectPickerRow(option_id = self.OptionID, name = self.Text, row_description = self.Description, icon = self.Icon)
		return row

class SettingDialogBase(abc.ABC):
	HostNamespace = This.Mod.Namespace
	HostName = This.Mod.Name

	def __init_subclass__ (cls, **kwargs):
		cls._OnInitializeSubclass()

	def ShowDialog (self,
					setting: UISettingsShared.SettingWrapper,
					returnCallback: typing.Callable[[], None] = None,
					**kwargs) -> None:

		if not isinstance(setting, UISettingsShared.SettingWrapper):
			raise Exceptions.IncorrectTypeException(setting, "setting", (UISettingsShared.SettingWrapper,))

		if not isinstance(returnCallback, typing.Callable) and returnCallback is not None:
			raise Exceptions.IncorrectTypeException(returnCallback, "returnCallback", ("Callable", None))

		if services.current_zone() is None:
			Debug.Log("Tried to show setting dialog before a zone was loaded\n" + str.join("", traceback.format_stack()), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
			return

		self._ShowDialogInternal(setting, setting.Get(ignoreOverride = True), kwargs, returnCallback = returnCallback)

	@classmethod
	def _OnInitializeSubclass (cls) -> None:
		pass

	@abc.abstractmethod
	def _ShowDialogInternal (self,
							 setting: UISettingsShared.SettingWrapper,
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		pass

	@abc.abstractmethod
	def _CreateArguments (self,
						  setting: UISettingsShared.SettingWrapper,
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		pass

	@abc.abstractmethod
	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog.UiDialog:

		pass

	@abc.abstractmethod
	def _OnDialogResponse (self,
						   dialog: ui_dialog.UiDialogBase,
						   *args, **kwargs) -> None:
		pass

class StandardDialog(SettingDialogBase):
	def __init__ (self):
		super().__init__()

	def _GetTitleText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetNameText()

	def _GetDescriptionText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		descriptionParts = self._GetDescriptionParts(setting)  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]
		return TextBuilder.BuildText(descriptionParts)

	def _GetDescriptionParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		descriptionParts = list()  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]
		descriptionParts.extend(self._GetDescriptionInformationParts(setting))
		descriptionParts.append("\n\n")
		descriptionParts.extend(self._GetDescriptionValuesParts(setting))

		documentationURL = self._GetDescriptionDocumentationURL(setting)  # type: typing.Optional[str]
		if documentationURL is not None:
			descriptionParts.append("\n\n")
			descriptionParts.extend(self._GetDescriptionDocumentationParts(setting))

		return descriptionParts

	def _GetDescriptionInformationParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		informationParts = [self._GetDescriptionSettingText(setting)]  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]

		if setting.IsOverridden():
			informationParts.append("\n")
			informationParts.append(self._GetDescriptionPartsOverriddenText())

		return informationParts

	def _GetDescriptionValuesParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		valuesParts = list()  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]

		defaultPart = self._GetDescriptionPartsDefaultText()  # type: localization.LocalizedString
		Language.AddTokens(defaultPart, self._GetDescriptionDefaultText(setting))
		valuesParts.append(defaultPart)

		if setting.IsOverridden():
			overriddenPart = self._GetDescriptionPartsOverriddenValueText()  # type: localization.LocalizedString
			overriddenPartTokens = (
				self._GetDescriptionOverrideValueText(setting),
				self._GetDescriptionOverrideReasonText(setting)
			)  # type: tuple

			Language.AddTokens(overriddenPart, *overriddenPartTokens)

			valuesParts.append("\n")
			valuesParts.append(overriddenPart)

		return valuesParts

	def _GetDescriptionDocumentationParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		documentationURL = self._GetDescriptionDocumentationURL(setting)  # type: typing.Optional[str]

		if documentationURL is None:
			documentationURL = "**"

		documentationPart = self._GetDescriptionPartsDocumentationText()  # type: localization.LocalizedString
		Language.AddTokens(documentationPart, documentationURL)
		return [documentationPart]

	def _GetDescriptionSettingText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return Language.CreateLocalizationString("**")

	def _GetDescriptionDefaultText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetDefaultText()

	def _GetDescriptionOverrideValueText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetOverrideValueText()

	def _GetDescriptionOverrideReasonText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetOverrideReasonText()

	def _GetDescriptionDocumentationURL (self, setting: UISettingsShared.SettingWrapper) -> typing.Optional[str]:
		return None

	def _GetDescriptionPartsOverriddenText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Overridden")

	def _GetDescriptionPartsOverriddenValueText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Overridden_Value")

	def _GetDescriptionPartsDefaultText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Default")

	def _GetDescriptionPartsDocumentationText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Description_Parts.Documentation")

	def _GetAcceptButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Apply_Button", fallbackText = "Apply_Button")

	def _GetCancelButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Dialogs.Cancel_Button", fallbackText = "Cancel_Button")

	def _ShowDialogInternal (self,
							 setting: UISettingsShared.SettingWrapper,
							 currentValue: typing.Any,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		acceptButtonCallback = self._CreateAcceptButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]
		cancelButtonCallback = self._CreateCancelButtonCallback(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]

		dialogButtons = self._CreateButtons(setting, currentValue, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogButton]
		dialogArguments = self._CreateArguments(setting, currentValue, showDialogArguments, dialogButtons = dialogButtons)  # type: typing.Dict[str, typing.Any]
		dialog = self._CreateDialog(dialogArguments)  # type: ui_dialog.UiDialogOkCancel

		def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel):
			try:
				self._OnDialogResponse(dialogReference, dialogButtons = dialogButtons, acceptButtonCallback = acceptButtonCallback, cancelButtonCallback = cancelButtonCallback)
			except Exception as e:
				Debug.Log("Failed to run the callback for the setting dialog of '" + setting.Key + "'.", self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
				raise e

		dialog.add_listener(DialogCallback)
		dialog.show_dialog()

	# noinspection PyUnusedLocal
	def _CreateAcceptButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialogOkCancel], None]:

		# noinspection PyUnusedLocal
		def AcceptButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			setting.Set(currentValue)

			if returnCallback is not None:
				returnCallback()

		return AcceptButtonCallback

	# noinspection PyUnusedLocal
	def _CreateCancelButtonCallback (self,
									 setting: UISettingsShared.SettingWrapper,
									 currentValue: typing.Any,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialogOkCancel], None]:

		# noinspection PyUnusedLocal
		def CancelButtonCallback (dialog: ui_dialog.UiDialogOkCancel) -> None:
			if returnCallback is not None:
				returnCallback()

		return CancelButtonCallback

	def _CreateButtons (self,
						setting: UISettingsShared.SettingWrapper,
						currentValue: typing.Any,
						showDialogArguments: typing.Dict[str, typing.Any],
						returnCallback: typing.Callable[[], None] = None,
						*args, **kwargs) -> typing.List[DialogButton]:

		buttons = list()
		return buttons

	def _CreateArguments (self,
						  setting: UISettingsShared.SettingWrapper,
						  currentValue: typing.Any,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		dialogArguments = dict()

		dialogOwner = showDialogArguments.get("owner")

		dialogButtons = kwargs["dialogButtons"]  # type: typing.List[DialogButton]
		dialogResponses = list()  # type: typing.List[ui_dialog.UiDialogResponse]

		for dialogButton in dialogButtons:  # type: DialogButton
			dialogResponses.append(dialogButton.GenerateDialogResponse())

		textString = self._GetDescriptionText(setting)  # type: localization.LocalizedString

		dialogArguments["owner"] = dialogOwner
		dialogArguments["title"] = Language.MakeLocalizationStringCallable(self._GetTitleText(setting))
		dialogArguments["text"] = Language.MakeLocalizationStringCallable(textString)
		dialogArguments["text_ok"] = Language.MakeLocalizationStringCallable(self._GetAcceptButtonText())
		dialogArguments["text_cancel"] = Language.MakeLocalizationStringCallable(self._GetCancelButtonText())
		dialogArguments["ui_responses"] = dialogResponses

		return dialogArguments

	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog.UiDialogOkCancel:

		if not "owner" in dialogArguments:
			dialogArguments["owner"] = None

		dialog = ui_dialog.UiDialogOkCancel.TunableFactory().default(**dialogArguments)  # type: ui_dialog.UiDialogOkCancel

		return dialog

	def _OnDialogResponse (self, dialog: ui_dialog.UiDialog, *args, **kwargs) -> None:
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
