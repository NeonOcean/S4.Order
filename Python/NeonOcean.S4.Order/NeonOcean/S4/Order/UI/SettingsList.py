from __future__ import annotations

import abc
import traceback
import typing

import services
from NeonOcean.S4.Order import Debug, Language, This
from NeonOcean.S4.Order.Tools import Exceptions, TextBuilder
from NeonOcean.S4.Order.UI import Resources as UIResources, SettingsShared as UISettingsShared, Dialogs
from sims4 import localization, resources
from ui import ui_dialog, ui_dialog_picker

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

class SettingsListBase(abc.ABC):
	def __init__ (self, hostNamespace: str, settingsSystem: UISettingsShared.SettingSystemWrapper):
		if not isinstance(hostNamespace, str):
			raise Exceptions.IncorrectTypeException(hostNamespace, "hostNamespace", (str,))

		if not isinstance(settingsSystem, UISettingsShared.SettingSystemWrapper):
			raise Exceptions.IncorrectTypeException(settingsSystem, "settingsSystem", (UISettingsShared.SettingSystemWrapper, ))

		self.HostNamespace = hostNamespace  # type: str
		self._settingsSystem = settingsSystem  # type: UISettingsShared.SettingSystemWrapper

	def __init_subclass__ (cls, **kwargs):
		cls._OnInitializeSubclass()

	@property
	def SettingsSystem (self) -> UISettingsShared.SettingSystemWrapper:
		return self._settingsSystem

	@property
	def Settings (self) -> typing.List[UISettingsShared.SettingWrapper]:
		return self._settingsSystem.Settings

	def ShowDialog (self,
					listPath: str,
					returnCallback: typing.Callable[[], None] = None,
					**kwargs) -> None:

		if not isinstance(listPath, str):
			raise Exceptions.IncorrectTypeException(listPath, "listPath", (str,))

		if not isinstance(returnCallback, typing.Callable) and returnCallback is not None:
			raise Exceptions.IncorrectTypeException(returnCallback, "returnCallback", ("Callable", None))

		if services.current_zone() is None:
			Debug.Log("Tried to show setting dialog before a zone was loaded\n" + str.join("", traceback.format_stack()), self.HostNamespace, Debug.LogLevels.Warning, group = self.HostNamespace, owner = __name__)
			return

		self._ShowDialogInternal(listPath, kwargs, returnCallback = returnCallback)

	@classmethod
	def _OnInitializeSubclass (cls) -> None:
		pass

	@abc.abstractmethod
	def _ShowDialogInternal (self,
							 listPath: str,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		pass

	@abc.abstractmethod
	def _CreateArguments (self,
						  listPath: str,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		pass

	@abc.abstractmethod
	def _CreateRows (self,
					 listPath: str,
					 showDialogArguments: typing.Dict[str, typing.Any],
					 returnCallback: typing.Callable[[], None] = None,
					 *args, **kwargs) -> typing.List[DialogRow]:

		pass

	@abc.abstractmethod
	def _CreateDialog (self,
					   dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog.UiDialog:

		pass

	@abc.abstractmethod
	def _OnDialogResponse (self, dialog: ui_dialog.UiDialogBase, *args, **kwargs) -> None:
		pass

class SettingsList(SettingsListBase):
	def __init__ (self, hostNamespace: str, settingsSystem: UISettingsShared.SettingSystemWrapper):
		super().__init__(hostNamespace, settingsSystem)

		self.ShowResetAllButton = True

	@property
	def ShowResetAllButton (self) -> bool:
		return self._showResetAllButton

	@ShowResetAllButton.setter
	def ShowResetAllButton (self, value: bool) -> None:
		if not isinstance(value, bool):
			raise Exceptions.IncorrectTypeException(value, "ShowResetAllButton", (bool,))

		self._showResetAllButton = value

	@property
	def ListPathSeparator (self) -> str:
		return "/"

	def _GetTitleText (self, listPath: str) -> localization.LocalizedString:
		titleText = self._GetTitleTemplateText()  # type: localization.LocalizedString
		titleTextStandard = self._GetTitleStandardText()  # type: localization.LocalizedString
		titleTextListPath = self._GetTitleListPathText(listPath)  # type: localization.LocalizedString
		Language.AddTokens(titleText, titleTextStandard, titleTextListPath)
		return titleText

	def _GetTitleTemplateText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Title_Template")

	def _GetTitleStandardText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Title")

	def _GetTitleListPathText (self, listPath: str) -> localization.LocalizedString:
		return Language.CreateLocalizationString(listPath.rsplit(self.ListPathSeparator, 1)[-1])

	def _GetDescriptionText (self, listPath: str) -> localization.LocalizedString:
		return Language.CreateLocalizationString("")

	def _GetRowSettingText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		return setting.GetNameText()

	def _GetRowSettingDescriptionText (self, setting: UISettingsShared.SettingWrapper) -> localization.LocalizedString:
		descriptionParts = self._GetRowSettingDescriptionParts(setting)  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]
		return TextBuilder.BuildText(descriptionParts)

	def _GetRowSettingDescriptionParts (self, setting: UISettingsShared.SettingWrapper) -> typing.List[typing.Union[localization.LocalizedString, str, int, float]]:
		descriptionParts = list()  # type: typing.List[typing.Union[localization.LocalizedString, str, int, float]]

		settingValue = setting.Get()  # type: typing.Any
		settingValueText = setting.GetValueText(settingValue)  # type: localization.LocalizedString

		valueText = self._GetRowPartsSettingValueText()  # type: localization.LocalizedString
		Language.AddTokens(valueText, settingValueText)
		descriptionParts.append(valueText)

		if setting.IsOverridden():
			descriptionParts.append("\n")

			actualValue = setting.Get(ignoreOverride = True)  # type: typing.Any
			actualValueText = setting.GetValueText(actualValue)  # type: localization.LocalizedString

			overriddenText = self._GetRowPartsSettingOverriddenText()
			Language.AddTokens(overriddenText, actualValueText)
			descriptionParts.append(overriddenText)

		return descriptionParts

	def _GetRowPartsSettingValueText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Row_Parts.Setting.Value")

	def _GetRowPartsSettingOverriddenText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Row_Parts.Setting.Overridden")

	def _GetRowSettingIconKey (self, setting: UISettingsShared.SettingWrapper) -> str:
		settingListIconKey = setting.GetListIconKey()  # type: typing.Optional[str]

		if settingListIconKey is None:
			if setting.IsOverridden():
				return UIResources.PickerLockIconKey
			else:
				return UIResources.PickerGearIconKey

		return settingListIconKey

	def _GetRowListPathText (self, listPath: str) -> localization.LocalizedString:
		return self._GetTitleListPathText(listPath)

	# noinspection PyUnusedLocal
	def _GetRowListPathDescriptionText (self, listPath: str) -> localization.LocalizedString:
		return Language.CreateLocalizationString("")

	# noinspection PyUnusedLocal
	def _GetRowListPathIconKey (self, listPath: str) -> str:
		return UIResources.PickerRightArrowIconKey

	def _GetResetAllButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Reset_All.Button.Text")

	def _GetResetAllButtonDescriptionText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Reset_All.Button.Description")

	def _GetResetAllButtonIconKey (self) -> str:
		return UIResources.PickerResetIconKey

	def _GetResetAllConfirmDialogTitleText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Reset_All.Confirm_Dialog.Title")

	def _GetResetAllConfirmDialogDescriptionText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Reset_All.Confirm_Dialog.Description")

	def _GetResetAllConfirmDialogYesButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Reset_All.Confirm_Dialog.Yes_Button", fallbackText = "Yes_Button")

	def _GetResetAllConfirmDialogNoButtonText (self) -> localization.LocalizedString:
		return Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".Setting_Lists.Reset_All.Confirm_Dialog.No_Button", fallbackText = "No_Button")

	def _GetSettingSortingKeys (self, setting: UISettingsShared.SettingWrapper) -> typing.Tuple[int, str]:
		return -setting.GetListPriority(), setting.Key

	def _GetVisibleListPaths (self, listPath: str) -> typing.List[str]:
		listPathParts = listPath.split(self.ListPathSeparator)  # type: typing.List[str]

		potentialListPaths = list()  # type: typing.List[str]

		for setting in self.Settings:  # type: UISettingsShared.SettingWrapper
			potentialListPaths.append(setting.GetListPath())

		visibleListPaths = list()  # type: typing.List[str]

		for potentialListPath in potentialListPaths:  # type: str
			potentialListPathParts = potentialListPath.split(self.ListPathSeparator)  # type: typing.List[str]

			if len(potentialListPathParts) <= len(listPathParts):
				continue

			mismatched = False  # type: bool

			for listPathPartIndex in range(len(listPathParts)):  # type: int
				if listPathParts[listPathPartIndex] != potentialListPathParts[listPathPartIndex]:
					mismatched = True
					break

			if not mismatched:
				visibleListPath = self.ListPathSeparator.join(potentialListPathParts[:len(listPathParts) + 1])  # type: str

				if visibleListPath not in visibleListPaths:
					visibleListPaths.append(visibleListPath)

		visibleListPaths.sort()

		return visibleListPaths

	def _GetVisibleSettings (self, listPath: str) -> typing.List[UISettingsShared.SettingWrapper]:
		visibleSettings = list()  # type: typing.List[UISettingsShared.SettingWrapper]

		for potentialSetting in self.Settings:  # type: UISettingsShared.SettingWrapper
			if potentialSetting.IsHidden():
				continue

			if not potentialSetting.CanShowDialog():
				continue

			if listPath == potentialSetting.GetListPath():
				visibleSettings.append(potentialSetting)

		visibleSettings.sort(key = self._GetSettingSortingKeys)

		return visibleSettings

	# noinspection PyUnusedLocal
	def _CreateReturnCallback (self,
							   listPath: str,
							   showDialogArguments: typing.Dict[str, typing.Any],
							   returnCallback: typing.Callable[[], None] = None,
							   *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def ReturnCallback () -> None:
			self.ShowDialog(listPath, returnCallback = returnCallback, **showDialogArguments)

		return ReturnCallback

	# noinspection PyUnusedLocal
	def _CreateAcceptButtonCallback (self,
									 listPath: str,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def AcceptButtonCallback (dialog: ui_dialog.UiDialog) -> None:
			pass

		return AcceptButtonCallback

	# noinspection PyUnusedLocal
	def _CreateCancelButtonCallback (self,
									 listPath: str,
									 showDialogArguments: typing.Dict[str, typing.Any],
									 returnCallback: typing.Callable[[], None] = None,
									 *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def CancelButtonCallback (dialog: ui_dialog.UiDialog) -> None:
			if returnCallback is not None:
				returnCallback()

		return CancelButtonCallback

	# noinspection PyUnusedLocal
	def _CreateResetAllButtonCallback (self,
									   listPath: str,
									   showDialogArguments: typing.Dict[str, typing.Any],
									   returnCallback: typing.Callable[[], None] = None,
									   *args, **kwargs) -> typing.Callable[[ui_dialog.UiDialog], None]:

		# noinspection PyUnusedLocal
		def ResetAllButtonCallback (listDialogReference: ui_dialog.UiDialog) -> None:
			def ResetAllConfirmDialogCallback (confirmDialogReference: ui_dialog.UiDialog) -> None:
				if confirmDialogReference.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
					self.SettingsSystem.ResetAll()

				self.ShowDialog(listPath, returnCallback = returnCallback, **showDialogArguments)

			confirmDialogArguments = {
				"title": Language.MakeLocalizationStringCallable(self._GetResetAllConfirmDialogTitleText()),
				"text": Language.MakeLocalizationStringCallable(self._GetResetAllConfirmDialogDescriptionText()),
				"text_ok": Language.MakeLocalizationStringCallable(self._GetResetAllConfirmDialogYesButtonText()),
				"text_cancel": Language.MakeLocalizationStringCallable(self._GetResetAllConfirmDialogNoButtonText())
			}

			Dialogs.ShowOkCancelDialog(callback = ResetAllConfirmDialogCallback, queue = False, **confirmDialogArguments)

		return ResetAllButtonCallback

	def _ShowDialogInternal (self,
							 listPath: str,
							 showDialogArguments: typing.Dict[str, typing.Any],
							 returnCallback: typing.Callable[[], None] = None,
							 *args, **kwargs) -> None:

		acceptButtonCallback = self._CreateAcceptButtonCallback(listPath, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]
		cancelButtonCallback = self._CreateCancelButtonCallback(listPath, showDialogArguments, returnCallback = returnCallback)  # type: typing.Callable[[ui_dialog.UiDialogOkCancel], None]

		dialogRows = self._CreateRows(listPath, showDialogArguments, returnCallback = returnCallback)  # type: typing.List[DialogRow]
		dialogArguments = self._CreateArguments(listPath, showDialogArguments)  # type: typing.Dict[str, typing.Any]
		dialog = self._CreateDialog(dialogArguments, dialogRows = dialogRows)  # type: ui_dialog_picker.UiObjectPicker

		def DialogCallback (dialogReference: ui_dialog_picker.UiObjectPicker):
			try:
				self._OnDialogResponse(dialogReference, dialogRows = dialogRows, acceptButtonCallback = acceptButtonCallback, cancelButtonCallback = cancelButtonCallback)
			except Exception as e:
				Debug.Log("Failed to run the callback for a setting list dialog.", self.HostNamespace, Debug.LogLevels.Exception, group = self.HostNamespace, owner = __name__)
				raise e

		dialog.add_listener(DialogCallback)
		dialog.show_dialog()

	def _CreateArguments (self,
						  listPath: str,
						  showDialogArguments: typing.Dict[str, typing.Any],
						  *args, **kwargs) -> typing.Dict[str, typing.Any]:

		dialogArguments = dict()

		dialogOwner = showDialogArguments.get("owner")

		dialogArguments["owner"] = dialogOwner
		dialogArguments["title"] = Language.MakeLocalizationStringCallable(self._GetTitleText(listPath))
		dialogArguments["text"] = Language.MakeLocalizationStringCallable(self._GetDescriptionText(listPath))

		return dialogArguments

	def _CreateRows (self,
					 listPath: str,
					 showDialogArguments: typing.Dict[str, typing.Any],
					 returnCallback: typing.Callable[[], None] = None,
					 *args, **kwargs) -> typing.List[DialogRow]:

		dialogRows = list()  # type: typing.List[DialogRow]

		if self.ShowResetAllButton:
			resetAllButtonCallback = self._CreateResetAllButtonCallback(listPath, showDialogArguments, returnCallback = returnCallback, *args, **kwargs)  # type: typing.Callable

			dialogRows.append(
				DialogRow(40000,
						  callback = resetAllButtonCallback,
						  text = self._GetResetAllButtonText(),
						  description = self._GetResetAllButtonDescriptionText(),
						  icon = resources.ResourceKeyWrapper(self._GetResetAllButtonIconKey()))
			)

		currentOptionID = 50000  # type: int
		currentReturnCallback = self._CreateReturnCallback(listPath, showDialogArguments, returnCallback)  # type: typing.Callable[[], None]

		visibleListPaths = self._GetVisibleListPaths(listPath)  # type: typing.List[str]

		for visibleListPath in visibleListPaths:  # type: str
			def CreateVisibleListPathCallback (targetListPath: str) -> typing.Callable[[ui_dialog.UiDialog], None]:

				# noinspection PyUnusedLocal
				def VisibleListPathCallback (dialog: ui_dialog.UiDialog) -> None:
					self.ShowDialog(targetListPath, returnCallback = currentReturnCallback, **showDialogArguments)

				return VisibleListPathCallback

			dialogRows.append(
				DialogRow(currentOptionID,
						  callback = CreateVisibleListPathCallback(visibleListPath),
						  text = self._GetRowListPathText(visibleListPath),
						  description = self._GetRowListPathDescriptionText(visibleListPath),
						  icon = resources.ResourceKeyWrapper(self._GetRowListPathIconKey(visibleListPath)))
			)

			currentOptionID += 1

		visibleSettings = self._GetVisibleSettings(listPath)  # type: typing.List[UISettingsShared.SettingWrapper]

		for visibleSetting in visibleSettings:  # type: UISettingsShared.SettingWrapper
			def CreateVisibleSettingCallback (targetSetting: UISettingsShared.SettingWrapper) -> typing.Callable[[ui_dialog.UiDialog], None]:

				# noinspection PyUnusedLocal
				def VisibleSettingCallback (dialog: ui_dialog.UiDialog) -> None:
					targetSetting.ShowDialog(returnCallback = currentReturnCallback)

				return VisibleSettingCallback

			dialogRows.append(
				DialogRow(currentOptionID,
						  callback = CreateVisibleSettingCallback(visibleSetting),
						  text = self._GetRowSettingText(visibleSetting),
						  description = self._GetRowSettingDescriptionText(visibleSetting),
						  icon = resources.ResourceKeyWrapper(self._GetRowSettingIconKey(visibleSetting)))
			)

			currentOptionID += 1

		return dialogRows

	def _CreateDialog (self, dialogArguments: dict,
					   *args, **kwargs) -> ui_dialog_picker.UiObjectPicker:

		dialogOwner = dialogArguments.get("owner")

		if dialogOwner is None:
			dialogArguments["owner"] = services.get_active_sim().sim_info

		dialog = ui_dialog_picker.UiObjectPicker.TunableFactory().default(**dialogArguments)  # type: ui_dialog_picker.UiObjectPicker

		dialogRows = kwargs["dialogRows"]  # type: typing.List[DialogRow]

		for dialogRow in dialogRows:  # type: DialogRow
			dialog.add_row(dialogRow.GenerateRow())

		return dialog

	def _OnDialogResponse (self, dialog: ui_dialog_picker.UiObjectPicker, *args, **kwargs) -> None:
		dialogRows = kwargs["dialogRows"]  # type: typing.List[DialogRow]

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_OK:
			resultRows = dialog.get_result_rows()  # type: typing.List[ui_dialog_picker.BasePickerRow]

			for resultRow in resultRows:  # type: ui_dialog_picker.BasePickerRow
				for dialogRow in dialogRows:  # type: DialogRow
					if dialogRow.OptionID == resultRow.option_id:
						dialogRow.Callback(dialog)

			acceptButtonCallback = kwargs["acceptButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			acceptButtonCallback(dialog)

		if dialog.response == ui_dialog.ButtonType.DIALOG_RESPONSE_CANCEL:
			cancelButtonCallback = kwargs["cancelButtonCallback"]  # type: typing.Callable[[ui_dialog.UiDialog], None]

			cancelButtonCallback(dialog)
