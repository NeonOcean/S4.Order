import traceback
import typing

import services
from NeonOcean.Order import Debug, Language, Mods, SettingsShared, This, Websites
from NeonOcean.Order.UI import Dialogs, Notifications
from sims4 import collections, localization
from ui import ui_dialog, ui_dialog_generic, ui_dialog_notification, ui_text_input

DialogTextTemplate = Language.String(This.Mod.Namespace + ".System.Settings.Dialog.Text_Template")  # type: Language.String
DialogChoiceButton = Language.String(This.Mod.Namespace + ".System.Settings.Dialog.Choice_Button")  # type: Language.String
DialogAcceptButton = Language.String(This.Mod.Namespace + ".System.Settings.Dialog.Apply_Button")  # type: Language.String
DialogCancelButton = Language.String(This.Mod.Namespace + ".System.Settings.Dialog.Cancel_Button")  # type:  Language.String

InvalidNotificationTitle = Language.String(This.Mod.Namespace + ".System.Settings.Invalid_Notification.Title")  # type: Language.String
InvalidNotificationText = Language.String(This.Mod.Namespace + ".System.Settings.Invalid_Notification.Text")  # type: Language.String

def ShowSettingDialog (setting: typing.Type[SettingsShared.SettingBase], mod: Mods.Mod) -> None:
	if services.current_zone() is None:
		Debug.Log("Tried to show setting dialog before a zone was loaded\n" + str.join("", traceback.format_stack()), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	currentValue = setting.Get()  # type: bool

	if setting.DialogType == SettingsShared.DialogTypes.Input:
		_ShowInputSettingInternal(currentValue, setting, mod)
	elif setting.DialogType == SettingsShared.DialogTypes.Choice:
		_ShowMultipleChoiceSettingInternal(currentValue, setting, mod)

def _ShowMultipleChoiceSettingInternal (currentValue, setting: typing.Type[SettingsShared.SettingBase], mod: Mods.Mod) -> None:
	valueResponseIDs = dict()  # type: typing.Dict[int, typing.Any]
	responses = list()  # type: typing.List[ui_dialog.UiDialogResponse]

	defaultString = None  # type: typing.Union[str, localization.LocalizedString]

	currentPosition = 0  # type: int
	for settingValue, settingValueString in setting.Values.items():  # type: object, Language.String
		if settingValue == setting.Default and defaultString is None:
			defaultString = settingValueString.GetLocalizationString()

		if settingValue == currentValue:
			valueButtonStringTokens = ("&gt; ", settingValueString.GetLocalizationString(), " &lt;")
		else:
			valueButtonStringTokens = ("", settingValueString.GetLocalizationString(), "")

		valueButtonString = DialogChoiceButton.GetCallableLocalizationString(*valueButtonStringTokens)

		valueSortOrder = -(currentPosition + 1)  # type: int
		valueResponseID = 20000 + currentPosition  # type: int

		valueResponse = ui_dialog.UiDialogResponse(
			sort_order = valueSortOrder,
			dialog_response_id = valueResponseID,
			text = valueButtonString
		)

		responses.append(valueResponse)
		valueResponseIDs[valueResponseID] = settingValue

		currentPosition += 1

	if defaultString is None:
		defaultString = setting.GetInputString(setting.Default)

	textTokens = (
		setting.Description.GetLocalizationString(),
		"",
		defaultString,
		Websites.GetNODocumentationSettingURL(setting, mod)
	)

	textString = DialogTextTemplate.GetCallableLocalizationString(*textTokens)

	dialogArguments = {
		"title": setting.Name.GetCallableLocalizationString(),
		"text": textString,
		"text_ok": DialogAcceptButton.GetCallableLocalizationString(),
		"text_cancel": DialogCancelButton.GetCallableLocalizationString(),
		"ui_responses": responses
	}

	def DialogCallback (dialogReference: ui_dialog.UiDialogOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				setting.Set(currentValue)
				return

			for responseID, value in valueResponseIDs.items():  # type: int, object
				if dialogReference.response == responseID:
					_ShowMultipleChoiceSettingInternal(value, setting, mod)
		except Exception as e:
			Debug.Log("Failed to run the callback for a setting dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	Dialogs.ShowOkCancelDialog(DialogCallback, queue = False, **dialogArguments)

def _ShowInputSettingInternal (currentValue, setting: typing.Type[SettingsShared.SettingBase], mod: Mods.Mod) -> None:
	inputToken = ""  # type: typing.Union[str, localization.LocalizedString]

	if setting.DescriptionInput is not None:
		inputToken = setting.DescriptionInput.GetLocalizationString(*setting.GetInputTokens())

	textTokens = (
		setting.Description.GetLocalizationString(),
		inputToken,
		setting.GetInputString(setting.Default),
		Websites.GetNODocumentationSettingURL(setting, mod)
	)

	textString = DialogTextTemplate.GetCallableLocalizationString(*textTokens)

	textInputKey = "Input"  # type: str

	textInputLockedArguments = {
		"sort_order": 0,
	}

	textInput = ui_text_input.UiTextInput.TunableFactory(locked_args = textInputLockedArguments).default  # type: ui_text_input.UiTextInput
	textInput.initial_value = lambda *args, **kwargs: Language.CreateLocalizationString(setting.GetInputString(currentValue))
	textInput.restricted_characters = setting.InputRestriction

	textInputs = collections.make_immutable_slots_class([textInputKey])
	textInputs = textInputs({
		textInputKey: textInput
	})

	dialogArguments = {
		"title": setting.Name.GetCallableLocalizationString(),
		"text": textString,
		"text_ok": DialogAcceptButton.GetCallableLocalizationString(),
		"text_cancel": DialogCancelButton.GetCallableLocalizationString(),
		"text_inputs": textInputs
	}

	def DialogCallback (dialogReference: ui_dialog_generic.UiDialogTextInputOkCancel) -> None:
		try:
			if dialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
				inputText = dialogReference.text_input_responses.get(textInputKey)  # type: str

				if inputText is None:
					return

				try:
					inputValue = setting.ParseInputString(inputText)
				except:
					_ShowInvalidInputNotification(inputText, mod)
					_ShowInputSettingInternal(currentValue, setting, mod)
					return

				try:
					setting.Set(inputValue)
				except:
					_ShowInvalidInputNotification(inputText, mod)
					_ShowInputSettingInternal(currentValue, setting, mod)
					return

		except Exception as e:
			Debug.Log("Failed to run the callback for a setting dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	Dialogs.ShowOkCancelInputDialog(DialogCallback, queue = False, **dialogArguments)

def _ShowInvalidInputNotification (inputString, mod: Mods.Mod) -> None:
	if services.current_zone() is None:
		Debug.Log("Tried to show setting dialog before a zone was loaded\n" + str.join("", traceback.format_stack()), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	notificationArguments = {
		"title": InvalidNotificationTitle.GetCallableLocalizationString(*mod.Name),
		"text": InvalidNotificationText.GetCallableLocalizationString(*inputString),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}

	Notifications.ShowNotification(queue = False, **notificationArguments)
