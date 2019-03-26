import codecs
import json
import os
import random
import threading
import typing
from http import client
from urllib import request

import enum
import zone
from NeonOcean.Order import Debug, Director, Information, Language, Mods, Paths, Settings, This, Websites
from NeonOcean.Order.Tools import Exceptions, Parse, Timer, Version
from NeonOcean.Order.UI import Notifications
from sims4 import collections
from ui import ui_dialog

UpdateNotificationTitle = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Title")
UpdateNotificationReleaseText = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Release_Text")
UpdateNotificationPreviewText = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Preview_Text")
UpdateNotificationButton = Language.String(This.Mod.Namespace + ".System.Distribution.Update_Notification.Button")

PromotionDefaultTitle = Language.String(This.Mod.Namespace + ".System.Distribution.Promotions.Default.Title")
PromotionDefaultButton = Language.String(This.Mod.Namespace + ".System.Distribution.Promotions.Default.Button")

_distributionURL = "http://dist.mods.neonoceancreations.com"  # type: str

_ticker = None  # type: Timer.Timer
_tickerInterval = 1800  # type: int

_shownReleaseVersions = dict()  # type: typing.Dict[Mods.Mod, typing.List[Version.Version]]
_shownPreviewVersions = dict()  # type: typing.Dict[Mods.Mod, typing.List[Version.Version]]

_showedPromotion = False  # type: bool

_shownPromotionsFilePath = os.path.join(Paths.PersistentPath, Information.GlobalNamespace, "ShownPromotions.json")  # type: str
_shownPromotions = list()  # type: typing.List[str]

class _Announcer(Director.Controller):
	Host = This.Mod

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		global _ticker

		if _ticker is None:
			if not Mods.IsInstalled("NeonOcean.Main"):
				startDistributionTimer = Timer.Timer(15, _StartDistributionThread)  # type: Timer.Timer
				startDistributionTimer.start()

class _FilterTypes(enum.Int):
	Whitelist = 0  # type: _FilterTypes
	Blacklist = 1  # type: _FilterTypes

class _Promotion:
	def __init__ (self, promotionDictionary: dict):
		self.Identifier = promotionDictionary["Identifier"]  # type: str

		self.Targets = promotionDictionary.get("Targets", list())  # type: list

		if not isinstance(self.Targets, list):
			Debug.Log("Expected type of 'list' for promotion target lists. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.Targets = list()

		targetIndex = 0  # type: int
		poppedTargets = 0  # type: int
		while targetIndex < len(self.Targets):
			if not isinstance(self.Targets[targetIndex], str):
				Debug.Log("Expected type of 'str' for a promotion target at the index of '" + str(targetIndex + poppedTargets) + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				self.Targets.pop(targetIndex)
				poppedTargets += 1

			targetIndex += 1

		targetsTypeString = promotionDictionary.get("Targets Type", _FilterTypes.Whitelist.name)  # type: str

		try:
			self.TargetsType = Parse.ParseEnum(targetsTypeString, _FilterTypes)  # type: _FilterTypes
		except Exception as e:
			Debug.Log("Failed to parse target filter type from '" + targetsTypeString + "'. Promotion: " + self.Identifier + "\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.TargetsType = _FilterTypes.Whitelist

		self.Mods = promotionDictionary.get("Mods", list())  # type: list

		if not isinstance(self.Mods, list):
			Debug.Log("Expected type of 'list' for promotion mod lists. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.Mods = list()

		modIndex = 0  # type: int
		poppedMods = 0  # type: int
		while modIndex < len(self.Mods):
			if not isinstance(self.Mods[modIndex], str):
				Debug.Log("Expected type of 'str' for a promotion mod at the index of '" + str(modIndex + poppedMods) + "'. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				self.Mods.pop(modIndex)
				poppedMods += 1

			modIndex += 1

		modsTypeString = promotionDictionary.get("Mods Type", _FilterTypes.Whitelist.name)  # type: str

		try:
			self.ModsType = Parse.ParseEnum(modsTypeString, _FilterTypes)  # type: _FilterTypes
		except Exception as e:
			Debug.Log("Failed to parse mod filter type from '" + modsTypeString + "'. Promotion: " + self.Identifier + "\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.ModsType = _FilterTypes.Whitelist

		ratingString = promotionDictionary.get("Rating", Mods.Rating.Normal.name)  # type: str

		try:
			self.Rating = Parse.ParseEnum(ratingString, Mods.Rating)  # type: Mods.Rating
		except Exception as e:
			Debug.Log("Failed to parse rating type from '" + ratingString + "'. Promotion: " + self.Identifier + "\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			self.Rating = Mods.Rating.Normal

		self.Link = promotionDictionary.get("Link")  # type: typing.Optional[str]

		if not isinstance(self.Link, str) and self.Link is not None:
			Debug.Log("Expected type of 'str' for a promotion link. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self.Title = promotionDictionary.get("S4 Title")  # type: typing.Optional[str]

		if not isinstance(self.Title, str) and self.Title is not None:
			Debug.Log("Expected type of 'str' for a promotion title. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self.Text = promotionDictionary.get("S4 Text")  # type: typing.Optional[str]

		if not isinstance(self.Text, str) and self.Text is not None:
			Debug.Log("Expected type of 'str' for a promotion text. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self.LinkButton = promotionDictionary.get("S4 Link Button")  # type: typing.Optional[str]

		if not isinstance(self.LinkButton, str) and self.LinkButton is not None:
			Debug.Log("Expected type of 'str' for a promotion link button. Promotion: " + self.Identifier, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	def CanShow (self, shownPromotions: typing.List[str]) -> bool:
		if self.Text is None:
			return False

		if self.TargetsType == _FilterTypes.Whitelist:
			validGame = False  # type: bool

			for promotionTarget in self.Targets:  # type: str
				if promotionTarget.lower() == "s4":
					validGame = True

			if not validGame:
				return False
		else:
			for promotionTarget in self.Targets:  # type: str
				if promotionTarget.lower() == "s4":
					return False

		if self.ModsType == _FilterTypes.Whitelist:
			validMods = True  # type: bool

			for promotionMod in self.Mods:  # type: str
				if not Mods.IsInstalled(promotionMod):
					validMods = False

			if not validMods:
				return False
		else:
			for promotionMod in self.Mods:  # type: str
				if Mods.IsInstalled(promotionMod):
					return False

		if self.Rating == Mods.Rating.NSFW:
			validRating = False

			for mod in Mods.GetAllMods():  # type: Mods.Mod
				if mod.Rating == Mods.Rating.NSFW:
					validRating = True

			if not validRating:
				return False

		identifierLower = self.Identifier.lower()  # type: str

		for shownPromotion in shownPromotions:  # type: str
			if identifierLower == shownPromotion.lower():
				return False

		return True

def _Setup () -> None:
	global _shownPromotions

	if os.path.exists(_shownPromotionsFilePath):
		try:
			with open(_shownPromotionsFilePath) as shownPromotionsFile:
				shownPromotions = json.JSONDecoder().decode(shownPromotionsFile.read())

				if not isinstance(shownPromotions, list):
					raise Exceptions.IncorrectTypeException(shownPromotions, "Root", (list,))

				for shownPromotionIndex in range(len(shownPromotions)):  # type: int
					if not isinstance(shownPromotions[shownPromotionIndex], str):
						raise Exceptions.IncorrectTypeException(shownPromotions[shownPromotionIndex], "Root[%d]" % shownPromotionIndex, (str,))

				_shownPromotions = shownPromotions
		except Exception as e:
			Debug.Log("Failed to read shown promotions file.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

def _StartDistributionThread () -> None:
	global _ticker

	if _ticker is None:
		checkThread = threading.Thread(target = _CheckDistribution)  # type: threading.Thread
		checkThread.setDaemon(True)
		checkThread.start()

		_ticker = Timer.Timer(_tickerInterval, _CheckDistribution)
		_ticker.start()

def _CheckDistribution () -> None:
	try:
		_CheckUpdates()
	except Exception as e:
		Debug.Log("Failed to check for updates.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	try:
		if not _showedPromotion:
			_CheckPromos()
	except Exception as e:
		Debug.Log("Failed to check for promotions.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _CheckUpdates () -> None:
	previewAvailableMods = list()  # type: typing.List[typing.Tuple[Mods.Mod, Version.Version]]
	releaseAvailableMods = list()  # type: typing.List[typing.Tuple[Mods.Mod, Version.Version]]

	distributeUpdates = Settings.Check_For_Updates.Get()  # type: bool
	distributePreviewUpdates = Settings.Check_For_Preview_Updates.Get()  # type: bool

	if not distributeUpdates:
		return

	latestURL = _distributionURL + "/mods/latest.json"  # type: str

	try:
		latestDictionary = _ReadVersionFile(latestURL)  # type: typing.Dict[str, typing.Dict[str, Version.Version]]
	except Exception as e:
		Debug.Log("Failed to get mod versions.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	for mod in Mods.GetAllMods():  # type: Mods.Mod
		if not mod.ReadInformation:
			continue

		if mod.Distribution != Information.Author:
			continue

		modShownReleaseVersions = _shownReleaseVersions.get(mod)  # type: list

		if modShownReleaseVersions is None:
			modShownReleaseVersions = list()
			_shownReleaseVersions[mod] = modShownReleaseVersions

		modShownPreviewVersions = _shownPreviewVersions.get(mod)  # type: list

		if modShownPreviewVersions is None:
			modShownPreviewVersions = list()
			_shownPreviewVersions[mod] = modShownPreviewVersions

		try:
			modVersions = latestDictionary.get(mod.Namespace)  # type: Version

			if modVersions is None:
				Debug.Log("Missing version data for '" + mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				continue

			releaseVersion = modVersions.get("Release")  # type: Version.Version

			if releaseVersion is None:
				Debug.Log("Missing release version for '" + mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				releaseVersion = Version.Version("0.0.0.0")

			if distributePreviewUpdates:
				previewVersion = modVersions.get("Preview")  # type: Version.Version

				if previewVersion is None:
					Debug.Log("Missing preview version for '" + mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					previewVersion = Version.Version("0.0.0.0")

				if previewVersion <= releaseVersion:
					if not releaseVersion in modShownReleaseVersions:
						if mod.Version < releaseVersion:
							releaseAvailableMods.append((mod, releaseVersion))
							continue
				else:
					if not previewVersion in modShownPreviewVersions:
						if mod.Version < previewVersion:
							previewAvailableMods.append((mod, previewVersion))
							continue
			else:
				if not releaseVersion in modShownReleaseVersions:
					if mod.Version < releaseVersion:
						releaseAvailableMods.append((mod, releaseVersion))
						continue

		except Exception as e:
			Debug.Log("Failed to get update information for '" + mod.Namespace + "'.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	for releaseTuple in releaseAvailableMods:  # type: typing.Tuple[Mods.Mod, Version.Version]
		try:
			_ShowReleaseUpdateNotification(releaseTuple[0], releaseTuple[1])
		except Exception as e:
			Debug.Log("Failed to show release update notification for '" + releaseTuple[0].Namespace + "'.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

	for previewTuple in previewAvailableMods:  # type: typing.Tuple[Mods.Mod, Version.Version]
		try:
			_ShowPreviewUpdateNotification(previewTuple[0], previewTuple[1])
		except Exception as e:
			Debug.Log("Failed to show release update notification for '" + previewTuple[0].Namespace + "'.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

def _CheckPromos () -> None:
	global _showedPromotion

	showPromotions = Settings.Show_Promotions.Get()  # type: bool

	if not showPromotions:
		return

	promotionsURL = _distributionURL + "/promotions/promotions.json"  # type: str

	try:
		promotionsList = _ReadPromotionFile(promotionsURL)  # type: typing.List[dict]
	except Exception as e:
		Debug.Log("Failed to get promotions.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	validPromotions = list()  # type: typing.List[_Promotion]

	for promotionDictionary in promotionsList:  # type: typing.Dict
		promotion = _Promotion(promotionDictionary)  # type: _Promotion

		if promotion.CanShow(_shownPromotions):
			validPromotions.append(promotion)

	if len(validPromotions) == 0:
		return

	chosenPromotion = random.choice(validPromotions)  # type: _Promotion

	try:
		_ShowPromotionNotification(chosenPromotion)
	except Exception as e:
		Debug.Log("Failed to show promotion notification for promotion '" + chosenPromotion.Identifier + "'.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	_showedPromotion = True
	_shownPromotions.append(chosenPromotion.Identifier)

	try:
		shownPromotionsDirectory = os.path.dirname(_shownPromotionsFilePath)  # type: str

		if not os.path.exists(shownPromotionsDirectory):
			os.makedirs(shownPromotionsDirectory)

		with open(_shownPromotionsFilePath, "w+") as shownPromotionsFile:
			shownPromotionsFile.write(json.JSONEncoder(indent = "\t").encode(_shownPromotions))
	except Exception as e:
		Debug.Log("Failed to write shown promotions to a file.\n" + Debug.FormatException(e), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

def _ReadVersionFile (versionsFileURL: str) -> typing.Dict[str, typing.Dict[str, Version.Version]]:
	with request.urlopen(versionsFileURL) as versionsFile:  # type: client.HTTPResponse
		versionsDictionaryString = versionsFile.read().decode("utf-8")  # type: str

	if not versionsDictionaryString or versionsDictionaryString.isspace():
		raise Exception("Latest versions file at '" + versionsFileURL + "' is empty or whitespace.")

	try:
		versionDictionary = json.JSONDecoder().decode(versionsDictionaryString)  # type: typing.Dict[str, typing.Dict[str, typing.Any]]

		if not isinstance(versionDictionary, dict):
			raise Exceptions.IncorrectTypeException(versionDictionary, "Root", (dict,))

		for mod, modLatest in versionDictionary.items():  # type: str, typing.Dict[str, typing.Any]
			if not isinstance(mod, str):
				raise Exceptions.IncorrectTypeException(mod, "Root[Key]", (str,))

			if not isinstance(modLatest, dict):
				raise Exceptions.IncorrectTypeException(mod, "Root[%s]" % mod, (dict,))

			if "Release" in modLatest:
				modLatest["Release"] = Version.Version(modLatest["Release"])

			if "Preview" in modLatest:
				modLatest["Preview"] = Version.Version(modLatest["Preview"])
	except Exception as e:
		raise Exception("Failed to decode latest version file at '" + versionsFileURL + "'.") from e

	return versionDictionary

def _ReadPromotionFile (promotionsFileURL: str) -> typing.List[dict]:
	with request.urlopen(promotionsFileURL) as promotionsFile:  # type: client.HTTPResponse
		promotionsListString = promotionsFile.read().decode("utf-8")  # type: str

	if not promotionsListString or promotionsListString.isspace():
		raise Exception("Promotions file at '" + promotionsFileURL + "' is empty or whitespace.")

	try:
		promotionsList = json.JSONDecoder().decode(promotionsListString)  # type: typing.List[dict]

		if not isinstance(promotionsList, list):
			raise Exceptions.IncorrectTypeException(promotionsList, "Root", (list,))

		for promotionIndex in range(len(promotionsList)):
			if not isinstance(promotionsList[promotionIndex], dict):
				raise Exceptions.IncorrectTypeException(promotionsList[promotionIndex], "Root[%d]" % promotionIndex, (dict,))

			if not "Identifier" in promotionsList[promotionIndex]:
				raise Exception("Missing dictionary entry 'Identifier' in 'Root[%d]'." % promotionIndex)

			if not isinstance(promotionsList[promotionIndex]["Identifier"], str):
				raise Exceptions.IncorrectTypeException(promotionsList[promotionIndex]["Identifier"], "Root[%d][Identifier]" % promotionIndex, (str,))

			promotionIndex += 1
	except Exception as e:
		raise Exception("Failed to decode promotions file at '" + promotionsFileURL + "'.") from e

	return promotionsList

def _ShowReleaseUpdateNotification (mod: Mods.Mod, version: Version.Version) -> None:
	updateURL = Websites.GetNODocumentationModURL(mod)  # type: str

	showUpdateResponseCommand = collections.make_immutable_slots_class(("command", "arguments"))

	showUpdateResponseArguments = [
		collections.make_immutable_slots_class(("arg_value", "arg_type"))
	]

	showUpdateResponseArguments[0] = showUpdateResponseArguments[0]({
		"arg_value": codecs.encode(bytearray(updateURL, "utf-8"), "hex").decode("utf-8"),
		"arg_type": ui_dialog.CommandArgType.ARG_TYPE_STRING
	})

	showUpdateResponseCommand = showUpdateResponseCommand({
		"command": This.Mod.Namespace.lower() + ".distribution.show_url",
		"arguments": showUpdateResponseArguments
	})

	showUpdateResponse = ui_dialog.UiDialogResponse(
		text = UpdateNotificationButton.GetCallableLocalizationString(),
		ui_request = ui_dialog.UiDialogResponse.UiDialogUiRequest.SEND_COMMAND,
		response_command = showUpdateResponseCommand
	)

	notificationArguments = {
		"title": UpdateNotificationTitle.GetCallableLocalizationString(mod.Name),
		"text": UpdateNotificationReleaseText.GetCallableLocalizationString(str(version)),

		"ui_responses": (showUpdateResponse,)
	}

	Notifications.ShowNotification(queue = True, **notificationArguments)

	modShownReleaseVersions = _shownReleaseVersions.get(mod)  # type: list

	if modShownReleaseVersions is None:
		modShownReleaseVersions = list()
		_shownReleaseVersions[mod] = modShownReleaseVersions

	if not version in modShownReleaseVersions:
		modShownReleaseVersions.append(version)

def _ShowPreviewUpdateNotification (mod: Mods.Mod, version: Version.Version) -> None:
	updateURL = Websites.GetNOSupportModPreviewPostsURL(mod)  # type: str

	showUpdateResponseCommand = collections.make_immutable_slots_class(("command", "arguments"))

	showUpdateResponseArguments = [
		collections.make_immutable_slots_class(("arg_value", "arg_type"))
	]

	showUpdateResponseArguments[0] = showUpdateResponseArguments[0]({
		"arg_value": codecs.encode(bytearray(updateURL, "utf-8"), "hex").decode("utf-8"),
		"arg_type": ui_dialog.CommandArgType.ARG_TYPE_STRING
	})

	showUpdateResponseCommand = showUpdateResponseCommand({
		"command": This.Mod.Namespace.lower() + ".distribution.show_url",
		"arguments": showUpdateResponseArguments
	})

	showUpdateResponse = ui_dialog.UiDialogResponse(
		text = UpdateNotificationButton.GetCallableLocalizationString(),
		ui_request = ui_dialog.UiDialogResponse.UiDialogUiRequest.SEND_COMMAND,
		response_command = showUpdateResponseCommand
	)

	notificationArguments = {
		"title": UpdateNotificationTitle.GetCallableLocalizationString(mod.Name),
		"text": UpdateNotificationReleaseText.GetCallableLocalizationString(str(version)),

		"ui_responses": (showUpdateResponse,)
	}

	Notifications.ShowNotification(queue = True, **notificationArguments)

	modShownPreviewVersions = _shownPreviewVersions.get(mod)  # type: list

	if modShownPreviewVersions is None:
		modShownPreviewVersions = list()
		_shownPreviewVersions[mod] = modShownPreviewVersions

	if not version in modShownPreviewVersions:
		modShownPreviewVersions.append(version)

def _ShowPromotionNotification (promotion: _Promotion) -> None:
	notificationArguments = {
		"text": lambda *args, **kwargs: Language.CreateLocalizationString(promotion.Text)
	}

	if promotion.Link is not None:
		if promotion.LinkButton is not None:
			linkResponseText = lambda *args, **kwargs: Language.CreateLocalizationString(promotion.LinkButton)
		else:
			linkResponseText = PromotionDefaultButton.GetCallableLocalizationString()

		linkResponseCommand = collections.make_immutable_slots_class(("command", "arguments"))

		linkResponseArguments = [
			collections.make_immutable_slots_class(("arg_value", "arg_type"))
		]

		linkResponseArguments[0] = linkResponseArguments[0]({
			"arg_value": codecs.encode(bytearray(promotion.Link, "utf-8"), "hex").decode("utf-8"),
			"arg_type": ui_dialog.CommandArgType.ARG_TYPE_STRING
		})

		linkResponseCommand = linkResponseCommand({
			"command": This.Mod.Namespace.lower() + ".distribution.show_url",
			"arguments": linkResponseArguments
		})

		linkResponse = ui_dialog.UiDialogResponse(
			text = linkResponseText,
			ui_request = ui_dialog.UiDialogResponse.UiDialogUiRequest.SEND_COMMAND,
			response_command = linkResponseCommand
		)

		notificationArguments["ui_responses"] = (linkResponse,)

	if promotion.Title is not None:
		notificationArguments["title"] = lambda *args, **kwargs: Language.CreateLocalizationString(promotion.Title)
	else:
		notificationArguments["title"] = PromotionDefaultTitle.GetCallableLocalizationString()

	Notifications.ShowNotification(queue = True, **notificationArguments)

_Setup()
