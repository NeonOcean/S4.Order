from __future__ import annotations

import atexit
import datetime
import functools
import importlib
import inspect
import json
import os
import sys
import types
import typing
import time
import zipfile

import zone
from NeonOcean.S4.Order import Debug, Language, LoadingEvents, LoadingShared, Mods, Paths, This
from NeonOcean.S4.Order.Tools import Exceptions, Parse, Version
from NeonOcean.S4.Order.UI import Notifications
from sims4.importer import custom_import
from ui import ui_dialog_notification

LoadingFailureNotificationTitle = Language.String(This.Mod.Namespace + ".Mod_Loading.Failure_Notification.Title")  # type: Language.String
LoadingFailureNotificationText = Language.String(This.Mod.Namespace + ".Mod_Loading.Failure_Notification.Text")  # type: Language.String

InvalidSetupNotificationTitle = Language.String(This.Mod.Namespace + ".Mod_Loading.Invalid_Setup_Notification.Title")  # type: Language.String
InvalidSetupNotificationText = Language.String(This.Mod.Namespace + ".Mod_Loading.Invalid_Setup_Notification.Text")  # type: Language.String

CascadeFailureNotificationTitle = Language.String(This.Mod.Namespace + ".Mod_Loading.Cascade_Failure_Notification.Title")  # type: Language.String
CascadeFailureNotificationText = Language.String(This.Mod.Namespace + ".Mod_Loading.Cascade_Failure_Notification.Text")  # type: Language.String

NotLoadedFailureNotificationTitle = Language.String(This.Mod.Namespace + ".Mod_Loading.Not_Loaded_Notification.Title")  # type: Language.String
NotLoadedFailureNotificationText = Language.String(This.Mod.Namespace + ".Mod_Loading.Not_Loaded_Notification.Text")  # type: Language.String

_allLoaders = list()  # type: typing.List[_Loader]

_autoLoad = True  # type: bool

_inLoadLoop = False  # type: bool
_loadedModules = list()  # type: typing.List[str]

_failedLoadingMods = set()  # type: typing.Set[str]
_invalidSetupMods = set()  # type: typing.Set[str]
_cascadeFailureMods = set()  # type: typing.Set[str]

_showedNotLoadedFailureNotification = False  # type: bool

class _Loader:
	"""
	Loads each mod's modules.

	Startup:
	Startup will begin as soon as the game is launched and can occur in as many as four phases, Initiate, InitiateLate, Start and StartLate
	Initiate phase functions will be called first, then the Start phase functions. New phases will not be started until every module's phase function is called for the
	previous phase. For a phase to run on a module, a function of the same name, prefixed with '_On', must exist within said module.
	These phase functions must take no parameters, the loader will pass over a module for any phase where the function does not meet expectations.
	Any unhandled exception in a phase will cause the mod to be unloaded.

	Initiate phases should be used for loading the module. You should not change things in other modules during initiate phases as it may not be fully functional.
	Start phases should be used for manipulating other modules. All modules should be functional before this phase starts.

	Shutdown:
	Shutdown could occur at any time, but will typically begin when the game is also shutting down. It has the phases, Stop, StopLate, Unload, UnloadLate.
	Stop phase functions will be called first, then the Unload phase functions.
	Shutdown's function is very similar to startup except for that any exceptions will not cause the unloading to stop.
	Shutdown phase function should be prepared to stop a module in at least most states, it should be safe to call at any time, even when only partially loaded.

	Stop phases are like Start phases and Unload phases are like Initiate phases.
	"""

	def __init__ (self, mod: Mods.Mod):
		self.Mod = mod  # type: Mods.Mod

		self.AutoLoad = True  # type: bool

		_allLoaders.append(self)

	def Disable (self, cascade: bool = True, warningList: typing.Set[str] = None) -> None:
		if self.Mod.Blocked or not self.Mod.ControlsLoading(This.Mod.Namespace):
			return

		Debug.Log("Disabling mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		if warningList is not None:
			if not self.Mod.Namespace in warningList:
				warningList.add(self.Mod.Namespace)

		self.Mod.Blocked = True

		if cascade:
			self._UnloadAndDisableRelatedMods()

		if self.Mod.IsReadyToUnload(This.Mod.Namespace):
			self.Unload()

	def GetInformation (self) -> None:
		try:
			with open(self.Mod.InformationFilePath) as informationFile:
				informationDictionary = json.JSONDecoder().decode(informationFile.read())  # type: dict

			if not isinstance(informationDictionary, dict):
				raise TypeError("Cannot convert mod file to a dictionary.")
		except Exception:
			Debug.Log("Failed to read the mod information for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			self.Disable(warningList = _failedLoadingMods)
			return

		if not self._UpdateInformation(informationDictionary):
			self._ResetInformation()
			self.Disable(warningList = _failedLoadingMods)
			return

		self.Mod.ReadInformation = True

	def Load (self, cause: LoadingShared.LoadingCauses = LoadingShared.LoadingCauses.Normal, loadIfUnsafe: bool = True) -> bool:
		"""
		:param cause: The cause of this load.
		:type cause: LoadingShared.LoadingCauses
		:param loadIfUnsafe: Whether or not we should abort this load if a mod meant to be already loaded is not.
		:type loadIfUnsafe: bool
		:return: Returns true if successful or false if not.
		:rtype: bool
		"""

		if not self.Mod.IsLoadable(This.Mod.Namespace):
			Debug.Log("Tried to load '" + self.Mod.Namespace + "' but this mod cannot be loaded.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return False

		if not self.Mod.IsReadyToLoad(This.Mod.Namespace):
			Debug.Log("Tried to load '" + self.Mod.Namespace + "' but it is not ready to load.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return False

		Debug.Log("Loading mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

		if not self.Mod.RequiredModsInstalled():
			Debug.Log("Aborted load of '" + self.Mod.Namespace + "' because a required mod is not installed.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
			return False

		if self.Mod.IncompatibleModsInstalled():
			Debug.Log("Aborted load of '" + self.Mod.Namespace + "' because an incompatible mod is installed.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
			return False

		if not self.Mod.PrerequisiteModsLoaded():
			if not loadIfUnsafe:
				Debug.Log("Aborted load of '" + self.Mod.Namespace + "' because one or more mods that are suppose to be already loaded are not.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
				return False
			else:
				Debug.Log("The mod '" + self.Mod.Namespace + "' is being loaded despite that one or more mods that are suppose to be already loaded are not.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

		operationStartTime = time.time()  # type: float

		self.Mod.Loading = True

		if self.Mod.ControlsLoading:
			try:
				self._ImportModules()
			except Exception:
				Debug.Log("Failed to completely import '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

				self.Disable(warningList = _failedLoadingMods)
				self.Mod.Loading = False
				return False

			try:
				self._InitiateModules(cause)
			except Exception:
				Debug.Log("Failed to completely initiate '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

				self.Disable(warningList = _failedLoadingMods)
				self.Mod.Loading = False
				return False

			self.Mod.Initiated = True

			try:
				self._StartModules(cause)
			except Exception:
				Debug.Log("Failed to completely start '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

				self.Disable(warningList = _failedLoadingMods)
				self.Mod.Loading = False

				return False

			self.Mod.Started = True

		operationTime = time.time() - operationStartTime  # type: float
		self.Mod.Loading = False
		self.Mod.LoadTime = operationTime

		Debug.Log("Successfully loaded the mod " + self.Mod.Namespace + "' in " + str(operationTime) + " seconds.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

		LoadingEvents.InvokeModLoadedEvent(self.Mod)

		return True

	def Unload (self, cause: LoadingShared.UnloadingCauses = LoadingShared.UnloadingCauses.Normal) -> bool:
		"""
		:return: Returns true if there where no issues unloading or false if not.
		:rtype: bool
		"""

		if not self.Mod.IsReadyToUnload(This.Mod.Namespace):
			Debug.Log("Tried to unload '" + self.Mod.Namespace + "' but we cannot currently unload it.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			return False

		Debug.Log("Unloading mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

		operationStartTime = time.time()  # type: float

		successful = True  # type: bool

		if self.Mod.ControlsLoading:
			if self.Mod.Started:
				if not self._StopModules(cause):
					Debug.Log("Failed to completely stop '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
					successful = False

			self.Mod.Started = False

			if self.Mod.Initiated:
				if not self._UnloadModules(cause):
					Debug.Log("Failed to completely unload '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
					successful = False

			self.Mod.Initiated = False
		else:
			Debug.Log("Unloading '" + self.Mod.Namespace + "' from it's mod object is not allowed.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
			return False

		operationTime = time.time() - operationStartTime  # type: float

		Debug.Log("Successfully unloaded the mod " + self.Mod.Namespace + "' in " + str(operationTime) + " seconds.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

		LoadingEvents.InvokeModUnloadedEvent(self.Mod, True if cause == LoadingShared.UnloadingCauses.Exiting else False)

		return successful

	def Reload (self) -> bool:
		"""
		:return: Returns true if successful or false if not.
		:rtype: bool
		"""

		return False

	def _UpdateInformation (self, informationDictionary: dict) -> bool:
		if not self._UpdateAuthor(informationDictionary) or \
				not self._UpdateVersion(informationDictionary) or \
				not self._UpdateVersionDisplay(informationDictionary) or \
				not self._UpdateDistribution(informationDictionary) or \
				not self._UpdateRating(informationDictionary) or \
				not self._UpdateScriptPaths(informationDictionary) or \
				not self._UpdateRequiredMods(informationDictionary) or \
				not self._UpdateIncompatibleMods(informationDictionary) or \
				not self._UpdateLoadAfter(informationDictionary) or \
				not self._UpdateLoadBefore(informationDictionary) or \
				not self._UpdateCompatibility(informationDictionary) or \
				not self._UpdateBuildDate(informationDictionary) or \
				not self._UpdateBuildGameVersion(informationDictionary) or \
				not self._UpdateAdditional(informationDictionary):

			return False

		return True

	def _UpdateAuthor (self, informationDictionary: dict) -> bool:
		informationKey = "Author"  # type: str

		try:
			if not informationKey in informationDictionary:
				raise Exception("Missing dictionary entry '%s' in 'Root'." % informationKey)

			author = informationDictionary[informationKey]  # type: str

			if not isinstance(author, str):
				raise Exceptions.IncorrectTypeException(author, "Root[%s]" % informationKey, (str,))

			self.Mod.Author = author
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateVersion (self, informationDictionary: dict) -> bool:
		informationKey = "Version"  # type: str

		try:
			if not "Version" in informationDictionary:
				raise Exception("Missing dictionary entry '%s' in 'Root'." % informationKey)

			version = informationDictionary["Version"]  # type: str

			if not isinstance(version, str):
				raise Exceptions.IncorrectTypeException(version, "Root[%s]" % informationKey, (str,))

			self.Mod.Version = Version.Version(version)
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateVersionDisplay (self, informationDictionary: dict) -> bool:
		informationKey = "VersionDisplay"  # type: str

		try:
			versionDisplay = informationDictionary.get(informationKey, None)  # type: str

			if versionDisplay is None:
				versionDisplay = str(self.Mod.Version)  # type: str
			elif not isinstance(versionDisplay, str):
				raise Exceptions.IncorrectTypeException(versionDisplay, "Root[%s]" % informationKey, (str,))

			self.Mod.VersionDisplay = versionDisplay

			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateDistribution (self, informationDictionary: dict) -> bool:
		informationKey = "Distribution"  # type: str

		try:
			distributionData = informationDictionary.get(informationKey, None)  # type: typing.Optional[typing.Dict[str, dict]]

			if distributionData is None:
				return True

			if not isinstance(distributionData, dict) and distributionData is not None:
				raise Exceptions.IncorrectTypeException(distributionData, "Root[%s]" % informationKey, (dict, None))

			def GetStringValue (targetKey: str) -> typing.Optional[str]:
				targetValue = distributionData.get(targetKey, None)  # type: typing.Optional[str]

				if not isinstance(targetValue, str) and targetValue is not None:
					raise Exceptions.IncorrectTypeException(targetValue, "Root[%s][%s]" % (informationKey, targetKey), (str, None))

				return targetValue

			updatesController = GetStringValue("UpdatesController")  # type: typing.Optional[str]
			updatesFileURL = GetStringValue("UpdatesFileURL")  # type: typing.Optional[str]
			downloadURL = GetStringValue("DownloadURL")  # type: typing.Optional[str]
			previewDownloadURL = GetStringValue("PreviewDownloadURL")  # type: typing.Optional[str]

			self.Mod.Distribution = Mods.Distribution(updatesController, updatesFileURL, downloadURL, previewDownloadURL)
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateRating (self, informationDictionary: dict) -> bool:
		informationKey = "Rating"  # type: str

		try:
			rating = informationDictionary.get(informationKey, Mods.Rating.Normal.name)  # type: str

			if not isinstance(rating, str):
				raise Exceptions.IncorrectTypeException(rating, "Root[%s]" % informationKey, (str,))

			self.Mod.Rating = Parse.ParsePythonEnum(rating, Mods.Rating)

			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateScriptPaths (self, informationDictionary: dict) -> bool:
		informationKey = "ScriptPaths"  # type: str

		scriptPathRootKey = "Root"  # type: str
		scriptPathPathKey = "Path"  # type: str

		try:
			scriptPaths = informationDictionary.get(informationKey, list())  # type: typing.List[str]

			if not isinstance(scriptPaths, list):
				raise Exceptions.IncorrectTypeException(scriptPaths, "Root[%s]" % informationKey, (list,))

			for index, scriptPath in enumerate(scriptPaths):  # type: int, str
				if not isinstance(scriptPath, str) and not isinstance(scriptPath, dict):
					raise Exceptions.IncorrectTypeException(scriptPath, "Root[%s][%d]" % (informationKey, index), (str, dict))

				if isinstance(scriptPath, dict):
					if not scriptPathRootKey in scriptPath:
						raise Exception("Missing dictionary entry '%s' in 'Root[%s][%d]'." % (scriptPathRootKey, informationKey, index))

					if not scriptPathPathKey in scriptPath:
						raise Exception("Missing dictionary entry '%s' in 'Root[%s][%d]'." % (scriptPathPathKey, informationKey, index))

					scriptPathRoot = scriptPath[scriptPathRootKey]  # type: str

					if not isinstance(scriptPathRoot, str):
						raise Exceptions.IncorrectTypeException(scriptPathRoot, "Root[%s][%d][%s]" % (informationKey, index, scriptPathRootKey), (str,))

					scriptPathPath = scriptPath[scriptPathPathKey]  # type: str

					if not isinstance(scriptPathPath, str):
						raise Exceptions.IncorrectTypeException(scriptPathRoot, "Root[%s][%d][%s]" % (informationKey, index, scriptPathPathKey), (str,))

					scriptPathRootLower = scriptPathRoot.lower()

					if scriptPathRootLower == "mods":
						scriptPathRootValue = Paths.ModsPath
					elif scriptPathRootLower == "s4":
						scriptPathRootValue = Paths.UserDataPath
					elif scriptPathRootLower == "current":
						scriptPathRootValue = self.Mod.InformationFileDirectoryPath
					else:
						raise Exception("'" + scriptPathPath + "' is not a valid path root, valid roots are 'mods', 's4' and 'current'.")

					scriptPaths[index] = os.path.join(scriptPathRootValue, os.path.normpath(scriptPathPath))
				else:
					scriptPaths[index] = os.path.join(Paths.ModsPath, os.path.normpath(scriptPath))

				if not os.path.exists(scriptPaths[index]):
					raise Exception("'" + scriptPaths[index] + "' does not exist.")

			self.Mod.ScriptPaths = scriptPaths

			for scriptPath in self.Mod.ScriptPaths:
				self.Mod.Modules.extend(_GetArchiveModules(scriptPath))

			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateRequiredMods (self, informationDictionary: dict) -> bool:
		informationKey = "RequiredMods"  # type: str

		try:
			requiredMods = informationDictionary.get(informationKey, list())  # type: typing.List[str]

			if not isinstance(requiredMods, list):
				raise Exceptions.IncorrectTypeException(requiredMods, "Root[%s]" % informationKey, (list,))

			for index, requiredMod in enumerate(requiredMods):  # type: int, str
				if not isinstance(requiredMod, str):
					raise Exceptions.IncorrectTypeException(requiredMod, "Root[%s][%d]" % (informationKey, index), (str,))

				if requiredMod == self.Mod.Namespace:
					raise Exception("A mod cannot be require its self.")

			self.Mod.RequiredMods = set(requiredMods)
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateIncompatibleMods (self, informationDictionary: dict) -> bool:
		informationKey = "IncompatibleMods"  # type: str

		try:
			incompatibleMods = informationDictionary.get(informationKey, list())  # type: typing.List[str]

			if not isinstance(incompatibleMods, list):
				raise Exceptions.IncorrectTypeException(incompatibleMods, "Root[%s]" % informationKey, (list,))

			for index, incompatibleMod in enumerate(incompatibleMods):  # type: int, str
				if not isinstance(incompatibleMod, str):
					raise Exceptions.IncorrectTypeException(incompatibleMod, "Root[%s][%d]" % (informationKey, index), (str,))

				if incompatibleMod == self.Mod.Namespace:
					raise Exception("A mod cannot be incompatible its self.")

			self.Mod.IncompatibleMods = set(incompatibleMods)
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateLoadBefore (self, informationDictionary: dict) -> bool:
		informationKey = "LoadBefore"  # type: str

		try:
			loadBeforeMods = informationDictionary.get(informationKey, list())  # type: typing.List[str]

			if not isinstance(loadBeforeMods, list):
				raise Exceptions.IncorrectTypeException(loadBeforeMods, "Root[%s]" % informationKey, (list,))

			for index, loadBeforeMod in enumerate(loadBeforeMods):  # type: int, str
				if not isinstance(loadBeforeMod, str):
					raise Exceptions.IncorrectTypeException(loadBeforeMod, "Root[%s][%d]" % (informationKey, index), (str,))

				if loadBeforeMod == self.Mod.Namespace:
					raise Exception("A mod cannot be loaded before its self.")

				if loadBeforeMod in self.Mod.LoadAfter:
					raise Exception("A mod cannot be loaded both before and after another one.")

			self.Mod.LoadBefore = set(loadBeforeMods)
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateLoadAfter (self, informationDictionary: dict) -> bool:
		informationKey = "LoadAfter"  # type: str

		try:
			loadAfterMods = informationDictionary.get(informationKey, list())  # type: typing.List[str]

			if not isinstance(loadAfterMods, list):
				raise Exceptions.IncorrectTypeException(loadAfterMods, "Root[%s]" % informationKey, (list,))

			for index, loadAfterMod in enumerate(loadAfterMods):  # type: int, str
				if not isinstance(loadAfterMod, str):
					raise Exceptions.IncorrectTypeException(loadAfterMod, "Root[%s][%d]" % (informationKey, index), (str,))

				if loadAfterMod == self.Mod.Namespace:
					raise Exception("A mod cannot be loaded after its self.")

				if loadAfterMod in self.Mod.LoadBefore:
					raise Exception("A mod cannot be loaded both before and after another one.")

			self.Mod.LoadAfter = set(loadAfterMods)
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateCompatibility (self, informationDictionary: dict) -> bool:
		informationKey = "Compatibility"  # type: str

		compatibilityLowestVersionKey = "LowestVersion"  # type: str
		compatibilityHighestVersionKey = "HighestVersion"  # type: str

		try:
			compatibility = informationDictionary.get(informationKey, dict())  # type: typing.Dict[str, dict]

			if not isinstance(compatibility, dict):
				raise Exceptions.IncorrectTypeException(compatibility, "Root[%s]" % informationKey, (dict,))

			for namespace, modDictionary in compatibility.items():  # type: str, typing.Dict[str, str]
				if not isinstance(namespace, str):
					raise Exceptions.IncorrectTypeException(namespace, "Root[%s]<Key>" % informationKey, (str,))

				if namespace == self.Mod.Namespace:
					raise Exception("A mod cannot have compatibility information for its self.")

				if not isinstance(modDictionary, dict):
					raise Exceptions.IncorrectTypeException(modDictionary, "Root[%s][%s]" % (informationKey, namespace), (dict,))

				if not compatibilityLowestVersionKey in modDictionary:
					lowestVersion = None
				else:
					lowestVersion = modDictionary[compatibilityLowestVersionKey]

				if not isinstance(lowestVersion, str) and lowestVersion is not None:
					raise Exceptions.IncorrectTypeException(lowestVersion, "Root[%s][%s][%s]" % (informationKey, namespace, compatibilityLowestVersionKey), (str, "None"))

				if not compatibilityHighestVersionKey in modDictionary:
					highestVersion = None
				else:
					highestVersion = modDictionary[compatibilityHighestVersionKey]

				if not isinstance(highestVersion, str) and highestVersion is not None:
					raise Exceptions.IncorrectTypeException(highestVersion, "Root[%s][%s][%s]" % (informationKey, namespace, compatibilityHighestVersionKey), (str, "None"))

				lowestVersionObject = Version.Version(versionString = lowestVersion) if lowestVersion is not None else None  # type: typing.Optional[Version.Version]
				highestVersionObject = Version.Version(versionString = highestVersion) if highestVersion is not None else None  # type: typing.Optional[Version.Version]

				self.Mod.Compatibility.append(Mods.Compatibility(namespace, lowestVersionObject, highestVersionObject))

			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateBuildDate (self, informationDictionary: dict) -> bool:
		informationKey = "BuildDate"  # type: str

		try:
			buildDate = informationDictionary.get(informationKey, None)

			if buildDate is None:
				return True

			if not isinstance(buildDate, str):
				raise Exceptions.IncorrectTypeException(buildDate, "Root[%s]" % informationKey, (str,))

			self.Mod.BuildDate = datetime.datetime.fromisoformat(buildDate)
			return True
		except Exception:
			Debug.Log("Failed to update build date for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateBuildGameVersion (self, informationDictionary: dict) -> bool:
		informationKey = "BuildGameVersion"  # type: str

		try:
			buildGameVersion = informationDictionary.get(informationKey, None)

			if buildGameVersion is None:
				return True

			if not isinstance(buildGameVersion, str):
				raise Exceptions.IncorrectTypeException(buildGameVersion, "Root[%s]" % informationKey, (str,))

			self.Mod.BuildGameVersion = Version.Version(buildGameVersion, translate = True)
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateAdditional (self, informationDictionary: dict) -> bool:
		informationKey = "Additional"  # type: str

		try:
			additional = informationDictionary.get(informationKey, None)

			if additional is None:
				return True

			if not isinstance(additional, dict):
				raise Exceptions.IncorrectTypeException(additional, "Root[%s]" % informationKey, (dict,))

			self.Mod.Additional = additional
			return True
		except Exception:
			Debug.Log("Failed to read mod information file value '%s' for '%s'." % (informationKey, self.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _ResetInformation (self) -> None:
		self.Mod.Author = ""
		self.Mod.Version = Version.Version()
		self.Mod.VersionDisplay = "0.0.0"
		self.Mod.Distribution = Mods.Distribution(None, None, None, None)
		self.Mod.Rating = Mods.Rating.Normal

		self.Mod.ScriptPaths = list()
		self.Mod.Modules = list()

		self.Mod.RequiredMods = set()
		self.Mod.IncompatibleMods = set()
		self.Mod.LoadAfter = set()
		self.Mod.LoadBefore = set()
		self.Mod.Compatibility = list()

		self.Mod.BuildDate = None
		self.Mod.BuildGameVersion = None

		self.Mod.Additional = dict()

	def _UnloadAndDisableRelatedMods (self) -> None:
		for testingModLoader in _allLoaders:  # type: _Loader
			if self.Mod.Namespace in testingModLoader.Mod.RequiredMods:
				testingModLoader.Disable(warningList = _cascadeFailureMods)

	def _ImportModules (self) -> bool:
		for scriptPath in self.Mod.ScriptPaths:  # type: str
			scriptPathNormalized = os.path.normpath(scriptPath)

			appendPath = True
			for path in sys.path:  # type: str
				if os.path.normpath(path) == scriptPathNormalized:
					appendPath = False

			if appendPath:
				sys.path.append(scriptPathNormalized)

		if len(self.Mod.Modules) != 0:
			_Import(self.Mod.Modules)
		else:
			if len(self.Mod.ScriptPaths) != 0:
				Debug.Log("Found no modules to import for the mod '" + self.Mod.Namespace + "', even though there are one or more script paths designated.'", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		self.Mod.Imported = True

		return True

	def _InitiateModules (self, cause: LoadingShared.LoadingCauses) -> None:
		for module in self.Mod.Modules:  # type: str
			if not module in _loadedModules:
				_loadedModules.append(module)

			OnInitiate = None  # type: typing.Optional[typing.Callable]

			try:
				OnInitiate = getattr(sys.modules[module], "_OnInitiate")
			except Exception:
				pass

			if isinstance(OnInitiate, types.FunctionType):
				if len(inspect.signature(OnInitiate).parameters) == 1:
					OnInitiate(cause)

		for module in self.Mod.Modules:  # type: str
			OnInitiateLate = None  # type: typing.Optional[typing.Callable]

			try:
				OnInitiateLate = getattr(sys.modules[module], "_OnInitiateLate")
			except Exception:
				pass

			if isinstance(OnInitiateLate, types.FunctionType):
				if len(inspect.signature(OnInitiateLate).parameters) == 1:
					OnInitiateLate(cause)

	def _StartModules (self, cause: LoadingShared.LoadingCauses) -> None:
		for module in self.Mod.Modules:  # type: str
			OnStart = None  # type: typing.Optional[typing.Callable]

			try:
				OnStart = getattr(sys.modules[module], "_OnStart")
			except Exception:
				pass

			if isinstance(OnStart, types.FunctionType):
				if len(inspect.signature(OnStart).parameters) == 1:
					OnStart(cause)

		for module in self.Mod.Modules:  # type: str
			OnStartLate = None  # type: typing.Optional[typing.Callable]

			try:
				OnStartLate = getattr(sys.modules[module], "_OnStartLate")
			except Exception:
				pass

			if isinstance(OnStartLate, types.FunctionType):
				if len(inspect.signature(OnStartLate).parameters) == 1:
					OnStartLate(cause)

	def _StopModules (self, cause: LoadingShared.UnloadingCauses) -> bool:
		successful = True  # type: bool

		for module in self.Mod.Modules:  # type: str
			if module in _loadedModules:
				_loadedModules.remove(module)

			OnStopEarly = None  # type: typing.Optional[typing.Callable]

			try:
				OnStopEarly = getattr(sys.modules[module], "_OnStopEarly")
			except Exception:
				pass

			if isinstance(OnStopEarly, types.FunctionType):
				if len(inspect.signature(OnStopEarly).parameters) == 1:
					try:
						OnStopEarly(cause)
					except Exception:
						Debug.Log("Failed to call '_StopEarly' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						successful = False

		for module in self.Mod.Modules:  # type: str
			OnStop = None  # type: typing.Optional[typing.Callable]

			try:
				OnStop = getattr(sys.modules[module], "_OnStop")
			except Exception:
				pass

			if isinstance(OnStop, types.FunctionType):
				if len(inspect.signature(OnStop).parameters) == 1:
					try:
						OnStop(cause)
					except Exception:
						Debug.Log("Failed to call '_Stop' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						successful = False

		return successful

	def _UnloadModules (self, cause: LoadingShared.UnloadingCauses) -> bool:
		successful = True  # type: bool

		for module in self.Mod.Modules:  # type: str
			OnUnloadEarly = None  # type: typing.Optional[typing.Callable]

			try:
				OnUnloadEarly = getattr(sys.modules[module], "_OnUnloadEarly")
			except Exception:
				pass

			if isinstance(OnUnloadEarly, types.FunctionType):
				if len(inspect.signature(OnUnloadEarly).parameters) == 1:
					try:
						OnUnloadEarly(cause)
					except Exception:
						Debug.Log("Failed to call '_UnloadEarly' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						successful = False

		for module in self.Mod.Modules:  # type: str
			OnUnload = None  # type: typing.Optional[typing.Callable]

			try:
				OnUnload = getattr(sys.modules[module], "_OnUnload")
			except Exception:
				pass

			if isinstance(OnUnload, types.FunctionType):
				if len(inspect.signature(OnUnload).parameters) == 1:
					try:
						OnUnload(cause)
					except Exception:
						Debug.Log("Failed to call '_Unload' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						successful = False

		return successful

class _Importer:
	def load_module (self, fullname: str):
		return importlib.import_module(fullname)

def LoadingAll () -> bool:
	"""
	Whether or not a load loop is currently active. A load loop cannot start if it was triggered from inside another load loop.
	"""

	return _inLoadLoop

def LoadAll () -> None:
	"""
	Begin loading all mods. If a load loop is already active, an exception will be raised.
	"""

	_LoadLoop()

def ForceLoadAll () -> None:
	"""
	Begin loading all mods. This will load all mods, even if they otherwise would not be loaded because a prerequisite mod has not been loaded. If a load
	loop is already active, an exception will be raised.
	"""

	_LoadLoop(unsafeAllowed = True)

def LoadMod (namespace: str, loadIfUnsafe: bool = True) -> None:
	"""
	Loads a specific mod by namespace. If the mod isn't installed the load request will be ignored without warning.
	:param namespace: The namespace of the mod to be loaded.
	:type namespace: str
	:param loadIfUnsafe: Whether or not we should abort this load if a mod meant to be already loaded is not.
	:type loadIfUnsafe: bool
	"""

	for modLoader in _allLoaders:  # type: _Loader
		if modLoader.Mod.Namespace == namespace:
			modLoader.Load(loadIfUnsafe = loadIfUnsafe)
			return

	Debug.Log("Tried to load '" + namespace + "' but no such mod exists.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

def DisableModAutoLoad (namespace: str) -> None:
	"""
	Disable the automatic loading of a mod to allow for it to be manually loaded at another time.
	"""

	for modLoader in _allLoaders:  # type: _Loader
		if modLoader.Mod.Namespace == namespace:
			if modLoader.Mod.IsLoaded():
				Debug.Log("Tried to block the automatic load of '" + namespace + "' but it is already loaded.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return

			modLoader.AutoLoad = False
			return

	Debug.Log("Tried to block the automatic load of '" + namespace + "' but no such mod exists.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

def EnableModAutoLoad (namespace: str) -> None:
	"""
	Allows for a mod to be loaded automatically if it was previously disabled.
	"""

	for modLoader in _allLoaders:  # type: _Loader
		if modLoader.Mod.Namespace == namespace:
			if modLoader.Mod.IsLoaded():
				Debug.Log("Tried to unblock the automatic load of '" + namespace + "' but it is already loaded.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				return

			modLoader.AutoLoad = True
			return

	Debug.Log("Tried to unblock the automatic load of '" + namespace + "' but no such mod exists.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

def PauseAutoLoad () -> None:
	"""
	Temporarily prevent mods from being automatically loaded when their requirements are loaded.
	"""

	global _autoLoad

	_autoLoad = False

def UnpauseAutoLoad () -> None:
	"""
	Allow mods to be automatically loaded when their requirements are loaded. By default, all mods will be automatically loaded when their requirements are loaded.
	"""

	global _autoLoad

	_autoLoad = True

def _Setup () -> None:
	for mod in Mods.GetAllMods():  # type: Mods.Mod
		modLoader = _Loader(mod)  # type: _Loader
		modLoader.GetInformation()

	registeredMods = ""  # type: str

	for mod in Mods.GetAllMods():  # type: Mods.Mod
		if not mod.ReadInformation:
			continue

		if registeredMods != "":
			registeredMods += "\n"

		versionString = str(mod.Version)

		if versionString == mod.VersionDisplay:
			registeredMods += "%s, v%s" % (mod.Namespace, versionString)
		else:
			registeredMods += "%s, v%s (%s)" % (mod.Namespace, versionString, mod.VersionDisplay)

	Debug.Log("Registered mods:\n" + registeredMods, This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

	_CheckInstallation()

	LoadingEvents.ModLoadedEvent += _ModLoadedCallback
	atexit.register(_OnExitCallback)
	_PatchOnLoadingScreenAnimationFinished()

def _LoadLoop (unsafeAllowed: bool = False) -> None:
	global _inLoadLoop

	if _inLoadLoop:
		raise Exception("Cannot start a load loop from inside another load loop.")

	loadableLoaders = [
		modLoader for modLoader in _allLoaders if \
		modLoader.Mod.IsLoadable(This.Mod.Namespace) and \
		modLoader.Mod.RequiredModsInstalled() and \
		not modLoader.Mod.IncompatibleModsInstalled()
	]

	while len(loadableLoaders) != 0:
		_inLoadLoop = True

		safeLoad = False  # type: bool
		selectedLoaderIndex = None  # type: typing.Optional[int]

		for modLoaderIndex in range(len(loadableLoaders)):  # type: int
			modLoader = loadableLoaders[modLoaderIndex]

			if not modLoader.AutoLoad:
				continue

			if not modLoader.Mod.IsReadyToLoad(This.Mod.Namespace):
				continue

			if not modLoader.Mod.PrerequisiteModsLoaded():
				if selectedLoaderIndex is None:
					selectedLoaderIndex = modLoaderIndex

				continue
			else:
				selectedLoaderIndex = modLoaderIndex
				safeLoad = True
				break

		if selectedLoaderIndex is not None and not (not unsafeAllowed and not safeLoad):
			selectedLoader = loadableLoaders[selectedLoaderIndex]  # type: _Loader

			selectedLoader.Load()
			loadableLoaders.pop(selectedLoaderIndex)
		else:
			_inLoadLoop = False
			break

def _Import (modules: list) -> None:
	importer = custom_import.CustomLoader(_Importer())  # type: custom_import.CustomLoader

	for module in modules:  # type: str
		if module.endswith(".__init__"):
			importer.load_module(module[:-len(".__init__")])
		else:
			importer.load_module(module)

def _GetArchiveModules (archivePath: str) -> typing.List[str]:
	modules = list()  # type: typing.List[str]
	archive = zipfile.ZipFile(archivePath, "r")  # type: zipfile.ZipFile

	for fileInfo in archive.filelist:  # type: zipfile.ZipInfo
		if fileInfo.filename[-1] != "/":
			path, extension = os.path.splitext(fileInfo.filename)  # type: str, str

			if extension.lower() == ".pyc":
				moduleName = path.replace("/", ".").replace("\\", ".")  # type: str

				if moduleName.endswith(".__init__"):
					moduleName = moduleName[:-len(".__init__")]

				modules.append(moduleName)

	archive.close()

	return modules

def _PatchOnLoadingScreenAnimationFinished ():
	originalFunction = zone.Zone.on_loading_screen_animation_finished  # type: typing.Callable

	@functools.wraps(originalFunction)
	def PatchedOnLoadingScreenAnimationFinished (*args, **kwargs):
		global _failedLoadingMods, _invalidSetupMods, _cascadeFailureMods, _showedNotLoadedFailureNotification

		originalFunction(*args, **kwargs)

		from sims4 import log

		try:
			if len(_failedLoadingMods) != 0:
				_WarnOfLoadingFailure()
				_failedLoadingMods = list()

			if len(_invalidSetupMods) != 0:
				_WarnOfInvalidSetup()
				_invalidSetupMods = list()

			if len(_cascadeFailureMods) != 0:
				_WarnOfCascadeFailure()
				_cascadeFailureMods = list()

			if not _showedNotLoadedFailureNotification:
				for mod in Mods.GetAllMods():
					if not mod.IsLoaded() and mod.IsLoadable(This.Mod.Namespace):
						_WarnOfNotLoadedFailure()
						_showedNotLoadedFailureNotification = True
						break

		except Exception as e:
			log.exception(This.Mod.Namespace, "Failed to show loading failure dialogs.", exc = e, owner = __name__)

	zone.Zone.on_loading_screen_animation_finished = PatchedOnLoadingScreenAnimationFinished

def _CheckInstallation () -> None:
	for modLoader in _allLoaders:  # type: _Loader
		if not modLoader.Mod.IsLoadable(This.Mod.Namespace):
			continue

		if not modLoader.Mod.ReadInformation:
			continue

		if not modLoader.Mod.RequiredModsInstalled():
			Debug.Log("One or more required mod for '%s' is not installed." % modLoader.Mod.Namespace, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			modLoader.Disable(cascade = False, warningList = _invalidSetupMods)
			continue

		if modLoader.Mod.IncompatibleModsInstalled():
			Debug.Log("One or more incompatible mod for '%s' is installed." % modLoader.Mod.Namespace, This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
			modLoader.Disable(cascade = False, warningList = _invalidSetupMods)
			continue

		for modCompatibility in modLoader.Mod.Compatibility:  # type: Mods.Compatibility
			if modCompatibility.LowestVersion is None and modCompatibility.HighestVersion is None:
				continue

			for checkingModLoader in _allLoaders:  # type: _Loader
				if not checkingModLoader.Mod.ReadInformation:
					continue

				if checkingModLoader.Mod.Namespace == modCompatibility.Namespace:
					if modCompatibility.LowestVersion is not None and modCompatibility.LowestVersion > checkingModLoader.Mod.Version:
						Debug.Log("Mod '%s' (%s) is too old for the mod '%s' (%s)." % (checkingModLoader.Mod.Namespace, str(checkingModLoader.Mod.Version), modLoader.Mod.Namespace, str(modLoader.Mod.Version)),
								  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

						modLoader.Disable(cascade = False, warningList = _invalidSetupMods)
						return

					if modCompatibility.HighestVersion is not None and modCompatibility.HighestVersion < checkingModLoader.Mod.Version:
						Debug.Log("Mod '%s' (%s) is too new for the mod '%s' (%s)." % (checkingModLoader.Mod.Namespace, str(checkingModLoader.Mod.Version), modLoader.Mod.Namespace, str(modLoader.Mod.Version)),
								  This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

						modLoader.Disable(cascade = False, warningList = _invalidSetupMods)
						return

					break

	_CheckInstallationLoop()

def _CheckInstallationLoop () -> None:
	for modLoader in _allLoaders:  # type: _Loader
		if not modLoader.Mod.IsLoadable(This.Mod.Namespace):
			continue

		if not modLoader.Mod.ReadInformation:
			continue

		for requiredModNamespace in modLoader.Mod.RequiredMods:  # type: str
			for checkingModLoader in _allLoaders:  # type: _Loader
				if checkingModLoader.Mod.Namespace == requiredModNamespace:
					if not checkingModLoader.Mod.IsLoadable(This.Mod.Namespace):
						Debug.Log("The mod '%s' is required for '%s' but is not loadable." % (requiredModNamespace, modLoader.Mod.Namespace), This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						modLoader.Disable(cascade = False, warningList = _cascadeFailureMods)
						_CheckInstallationLoop()
						return

def _WarnOfLoadingFailure () -> None:
	badMods = ""

	for modNamespace in _failedLoadingMods:  # type: str
		mod = Mods.GetMod(modNamespace)  # type: Mods.Mod

		if badMods != "":
			badMods += "\n"

		if mod.ReadInformation:
			badMods += mod.Namespace + ": v" + str(mod.Version)
		else:
			badMods += mod.Namespace

	Debug.Log("The following mods encountered an unrecoverable error while loading.\n" + badMods, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

	notificationArguments = {
		"title": LoadingFailureNotificationTitle.GetCallableLocalizationString(),
		"text": LoadingFailureNotificationText.GetCallableLocalizationString(badMods),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, ...]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _WarnOfInvalidSetup () -> None:
	badMods = ""

	for modNamespace in _invalidSetupMods:  # type: str
		mod = Mods.GetMod(modNamespace)  # type: Mods.Mod

		if badMods != "":
			badMods += "\n"

		if mod.ReadInformation:
			badMods += mod.Namespace + ": v" + str(mod.Version)
		else:
			badMods += mod.Namespace

	Debug.Log("The following mods could not be loaded due to missing required mods, incompatible mods, or incompatible mod versions.\n" + badMods, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

	notificationArguments = {
		"title": InvalidSetupNotificationTitle.GetCallableLocalizationString(),
		"text": InvalidSetupNotificationText.GetCallableLocalizationString(badMods),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, ...]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _WarnOfCascadeFailure () -> None:
	badMods = ""

	for modNamespace in _cascadeFailureMods:  # type: str
		mod = Mods.GetMod(modNamespace)  # type: Mods.Mod

		if badMods != "":
			badMods += "\n"

		if mod.ReadInformation:
			badMods += mod.Namespace + ": v" + str(mod.Version)
		else:
			badMods += mod.Namespace

	Debug.Log("The following mods could not be loaded due to failures in a mod they require.\n" + badMods, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

	notificationArguments = {
		"title": CascadeFailureNotificationTitle.GetCallableLocalizationString(),
		"text": CascadeFailureNotificationText.GetCallableLocalizationString(badMods),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, ...]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _WarnOfNotLoadedFailure () -> None:
	badMods = ""

	for mod in Mods.GetAllMods():  # type: Mods.Mod
		if not mod.IsLoaded() and mod.IsLoadable(This.Mod.Namespace):
			if badMods != "":
				badMods += "\n"

			if mod.ReadInformation:
				badMods += mod.Namespace + ": v" + str(mod.Version)
			else:
				badMods += mod.Namespace

	Debug.Log("The following mods have not been loaded, even though they should have been.\n" + badMods, This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

	notificationArguments = {
		"title": NotLoadedFailureNotificationTitle.GetCallableLocalizationString(),
		"text": NotLoadedFailureNotificationText.GetCallableLocalizationString(badMods),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, ...]

	Notifications.ShowNotification(queue = True, **notificationArguments)

# noinspection PyUnusedLocal
def _ModLoadedCallback (owner, eventArguments: LoadingEvents.ModLoadedEventArguments) -> None:
	if not LoadingAll() and _autoLoad:
		LoadAll()

def _OnExitCallback () -> None:
	for mod in _allLoaders:  # type: _Loader
		try:
			if mod.Mod.IsReadyToUnload(This.Mod.Namespace):
				mod.Unload(cause = LoadingShared.UnloadingCauses.Exiting)
		except:
			Debug.Log("Failed to unload the mod '" + mod.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

_Setup()
