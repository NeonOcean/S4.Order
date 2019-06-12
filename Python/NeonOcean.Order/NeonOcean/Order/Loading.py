import atexit
import functools
import importlib
import inspect
import json
import os
import sys
import types
import typing
import zipfile

import zone
from NeonOcean.Order import Debug, Events, Language, LoadingShared, Mods, Paths, This
from NeonOcean.Order.Tools import Exceptions, Parse, Version
from NeonOcean.Order.UI import Notifications
from sims4.importer import custom_import
from ui import ui_dialog_notification

LoadingFailureNotificationTitle = Language.String(This.Mod.Namespace + ".System.Loading.Failure_Notification.Title")  # type: Language.String
LoadingFailureNotificationText = Language.String(This.Mod.Namespace + ".System.Loading.Failure_Notification.Text")  # type: Language.String

CompatibilityFailureNotificationTitle = Language.String(This.Mod.Namespace + ".System.Loading.Compatibility_Notification.Title")  # type: Language.String
CompatibilityFailureNotificationText = Language.String(This.Mod.Namespace + ".System.Loading.Compatibility_Notification.Text")  # type: Language.String

NotLoadedFailureNotificationTitle = Language.String(This.Mod.Namespace + ".System.Loading.Not_Loaded_Notification.Title")  # type: Language.String
NotLoadedFailureNotificationText = Language.String(This.Mod.Namespace + ".System.Loading.Not_Loaded_Notification.Text")  # type: Language.String

_allLoaders = list()  # type: typing.List[_Loader]

_loadedModules = list()  # type: typing.List[str]

_failedLoadingMods = list()  # type: typing.List[Mods.Mod]
_badCompatibilityMods = list()  # type: typing.List[Mods.Mod]
_showedNotLoadedFailureNotification = False  # type: bool

class _Loader:
	"""
	Loads each NeonOcean mod's modules.

	Startup:
	Startup will begin as soon as the game is launched and can occur in as many as four phases, Initiate, InitiateLate, Start and StartLate
	Initiate phase functions will be called first, then the Start phase functions. New phases will not be started until every module's phase function is called for the previous phase.
	For a phase to run on a module, a function of the same name, prefixed with '_On', must exist within said module.
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

		_allLoaders.append(self)

	def Disable (self, cascade: bool = True, warningList: typing.List[Mods.Mod] = None) -> None:
		if not self.Mod.IsLoadable(This.Mod.Namespace):
			return

		Debug.Log("Disabling mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

		if warningList is not None:
			if not self.Mod in warningList:
				warningList.append(self.Mod)

		self.Mod.Blocked = True

		if cascade:
			self._UnloadAndDisableRelatedMods(warningList = warningList)

		if self.Mod.IsCurrentlyUnloadable(This.Mod.Namespace):
			self.Unload()

	def GetInformation (self) -> None:
		try:
			with open(self.Mod.FilePath) as modInformationFile:
				modInformationDictionary = json.JSONDecoder().decode(modInformationFile.read())  # type: dict

			if not isinstance(modInformationDictionary, dict):
				raise TypeError("Cannot convert mod file to dictionary.")
		except:
			Debug.Log("Failed to read mod information for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return

		if not self._UpdateName(modInformationDictionary) or \
				not self._UpdateAuthor(modInformationDictionary) or \
				not self._UpdateVersion(modInformationDictionary) or \
				not self._UpdateDistribution(modInformationDictionary) or \
				not self._UpdateRating(modInformationDictionary) or \
				not self._UpdateScriptPaths(modInformationDictionary) or \
				not self._UpdateRequirements(modInformationDictionary) or \
				not self._UpdateCompatibility(modInformationDictionary):

			self._ResetInformation()
			self.Disable(warningList = _failedLoadingMods)
			return

		self.Mod.ReadInformation = True

	def Load (self, cause: LoadingShared.LoadingCauses = LoadingShared.LoadingCauses.Normal) -> bool:
		"""
		:return: Returns true if successful or false if not.
		:rtype: bool
		"""

		if not self.Mod.IsCurrentlyLoadable(This.Mod.Namespace):
			Debug.Log("Tried to load '" + self.Mod.Namespace + "' but it is not currently loadable.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
			return False

		Debug.Log("Loading mod: " + self.Mod.Namespace + "\nVersion: " + str(self.Mod.Version), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

		self.Mod.Loading = True

		if self.Mod.ControlsLoading:
			if not self._Import():
				self.Disable(warningList = _failedLoadingMods)
				self.Mod.Loading = False
				return False

			try:
				_InitiateModules(self.Mod, cause)
				Debug.Log("Successfully initiated mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
			except:
				Debug.Log("Failed to completely initiate '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

				self.Disable(warningList = _failedLoadingMods)
				self.Mod.Loading = False
				return False

			self.Mod.Initiated = True

			try:
				_StartModules(self.Mod, cause)
				Debug.Log("Successfully started mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
			except:
				Debug.Log("Failed to completely start '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)

				self.Disable(warningList = _failedLoadingMods)
				self.Mod.Loading = False

				return False

			self.Mod.Started = True

		self.Mod.Loading = False
		return True

	def Unload (self, cause: LoadingShared.UnloadingCauses = LoadingShared.UnloadingCauses.Normal) -> bool:
		"""
		:return: Returns true if there where no issues unloading or false if not.
		:rtype: bool
		"""

		if not self.Mod.IsCurrentlyUnloadable(This.Mod.Namespace):
			Debug.Log("Tried to unload '" + self.Mod.Namespace + "' but we cannot currently unload it.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

		Debug.Log("Unloading mod: " + self.Mod.Namespace + "\nVersion: " + str(self.Mod.Version), This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

		successful = True  # type: bool

		if self.Mod.ControlsLoading:
			if self.Mod.Started:

				if _StopModules(self.Mod, cause):
					Debug.Log("Successfully stopped mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
				else:
					Debug.Log("Failed to completely stop '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
					successful = False

			self.Mod.Started = False

			if self.Mod.Initiated:
				if _UnloadModules(self.Mod, cause):
					Debug.Log("Successfully unloaded mod '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)
				else:
					Debug.Log("Failed to completely unload '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
					successful = False

			self.Mod.Initiated = False
		else:
			Debug.Log("Unloading '" + self.Mod.Namespace + "' from it's mod object is not allowed.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
			return False

		return successful

	def Reload (self) -> bool:
		"""
		:return: Returns true if successful or false if not.
		:rtype: bool
		"""

		return False

	def _UpdateName (self, informationDictionary: dict) -> bool:
		try:
			if not "Name" in informationDictionary:
				raise Exception("Missing dictionary entry 'Name' in 'Root'.")

			name = informationDictionary["Name"]  # type: str

			if not isinstance(name, str):
				raise Exceptions.IncorrectTypeException(name, "Root[Name]", (str,))

			self.Mod.Name = name
			return True
		except:
			Debug.Log("Failed to update mod name for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateAuthor (self, informationDictionary: dict) -> bool:
		try:
			if not "Author" in informationDictionary:
				raise Exception("Missing dictionary entry 'Author' in 'Root'.")

			author = informationDictionary["Author"]  # type: str

			if not isinstance(author, str):
				raise Exceptions.IncorrectTypeException(author, "Root[Author]", (str,))

			self.Mod.Author = author
			return True
		except:
			Debug.Log("Failed to update mod author for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateVersion (self, informationDictionary: dict) -> bool:
		try:
			if not "Version" in informationDictionary:
				raise Exception("Missing dictionary entry 'Version' in 'Root'.")

			version = informationDictionary["Version"]  # type: str

			if not isinstance(version, str):
				raise Exceptions.IncorrectTypeException(version, "Root[Version]", (str,))

			self.Mod.Version = Version.Version(version)
			return True
		except:
			Debug.Log("Failed to update mod version for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateDistribution (self, informationDictionary: dict) -> bool:
		try:
			distribution = informationDictionary.get("Distribution")  # type: typing.Optional[str]

			if not isinstance(distribution, str) and distribution is not None:
				raise Exceptions.IncorrectTypeException(distribution, "Root[Distribution]", (str, "None"))

			self.Mod.Distribution = distribution
			return True
		except:
			Debug.Log("Failed to update mod distribution for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateRating (self, informationDictionary: dict) -> bool:
		try:
			if not "Rating" in informationDictionary:
				raise Exception("Missing dictionary entry 'Rating' in 'Root'.")

			rating = informationDictionary["Rating"]  # type: str

			if not isinstance(rating, str):
				raise Exceptions.IncorrectTypeException(rating, "Root[Rating]", (str,))

			self.Mod.Rating = Parse.ParseEnum(rating, Mods.Rating)
			return True
		except:
			Debug.Log("Failed to update mod rating for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateScriptPaths (self, informationDictionary: dict) -> bool:
		try:
			if not "ScriptPaths" in informationDictionary:
				raise Exception("Missing dictionary entry 'ScriptPaths' in 'Root'.")

			scriptPaths = informationDictionary["ScriptPaths"]  # type: typing.List[str]

			if not isinstance(scriptPaths, list):
				raise Exceptions.IncorrectTypeException(scriptPaths, "Root[ScriptPaths]", (list,))

			for index, scriptPath in enumerate(scriptPaths):  # type: int, str
				if not isinstance(scriptPath, str):
					raise Exceptions.IncorrectTypeException(scriptPath, "Root[ScriptPaths][%d]" % index, (str,))

				scriptPaths[index] = os.path.join(Paths.ModsPath, os.path.normpath(scriptPath))

				if not os.path.exists(scriptPaths[index]):
					raise Exception("'" + scriptPaths[index] + "' does not exist.")

			self.Mod.ScriptPaths = scriptPaths

			for scriptPath in self.Mod.ScriptPaths:
				self.Mod.Modules.extend(_GetArchiveModules(scriptPath))

			return True
		except:
			Debug.Log("Failed to update mod script paths for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateRequirements (self, informationDictionary: dict) -> bool:
		try:
			if not "Requirements" in informationDictionary:
				raise Exception("Missing dictionary entry 'Requirements' in 'Root'.")

			requirements = informationDictionary["Requirements"]  # type: typing.List[str]

			if not isinstance(requirements, list):
				raise Exceptions.IncorrectTypeException(requirements, "Root[Requirements]", (list,))

			for index, requirementsValue in enumerate(requirements):  # type: str
				if not isinstance(requirementsValue, str):
					raise Exceptions.IncorrectTypeException(requirementsValue, "Root[Requirements][%d]" % index, (str,))

				if requirementsValue == self.Mod.Namespace:
					raise ValueError("Mods cannot require them self.")

			self.Mod.Requirements = requirements
			return True
		except:
			Debug.Log("Failed to update mod requirements for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UpdateCompatibility (self, informationDictionary: dict) -> bool:
		try:
			if not "Compatibility" in informationDictionary:
				raise Exception("Missing dictionary entry 'Compatibility' in 'Root'.")

			compatibility = informationDictionary["Compatibility"]  # type: typing.Dict[str, dict]

			if not isinstance(compatibility, dict):
				raise Exceptions.IncorrectTypeException(compatibility, "Root[Compatibility]", (dict,))

			for namespace, modDictionary in compatibility.items():  # type: str, typing.Dict[str, str]
				if not isinstance(namespace, str):
					raise Exceptions.IncorrectTypeException(namespace, "Root[Compatibility]:Key" % namespace, (str,))

				if namespace == self.Mod.Namespace:
					raise ValueError("Mods cannot have compatibility information for them self.")

				if not isinstance(modDictionary, dict):
					raise Exceptions.IncorrectTypeException(modDictionary, "Root[Requirements][%s]" % namespace, (dict,))

				if not "LowestVersion" in modDictionary:
					lowestVersion = None
				else:
					lowestVersion = modDictionary["LowestVersion"]

				if not isinstance(lowestVersion, str) and lowestVersion is not None:
					raise Exceptions.IncorrectTypeException(lowestVersion, "Root[Compatibility][%s][LowestVersion]" % namespace, (str, "None"))

				if not "HighestVersion" in modDictionary:
					highestVersion = None
				else:
					highestVersion = modDictionary["HighestVersion"]

				if not isinstance(highestVersion, str) and highestVersion is not None:
					raise Exceptions.IncorrectTypeException(highestVersion, "Root[Compatibility][%s][HighestVersion]" % namespace, (str, "None"))

				lowestVersionObject = Version.Version(string = lowestVersion) if lowestVersion is not None else None  # type: typing.Optional[Version.Version]
				highestVersionObject = Version.Version(string = highestVersion) if highestVersion is not None else None  # type: typing.Optional[Version.Version]

				self.Mod.Compatibility.append(Mods.Compatibility(namespace, lowestVersionObject, highestVersionObject))

			return True
		except:
			Debug.Log("Failed to update mod compatibility for '" + self.Mod.Namespace + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _ResetInformation (self) -> None:
		self.Mod.Author = None
		self.Mod.Version = None
		self.Mod.Distribution = None
		self.Mod.Rating = Mods.Rating.Normal

		self.Mod.ScriptPaths = list()
		self.Mod.Modules = list()

		self.Mod.Requirements = list()
		self.Mod.Compatibility = list()

	def _Import (self) -> bool:
		try:
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
		except:
			Debug.Log("Failed to import '" + self.Mod.Namespace + "' modules.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
			return False

	def _UnloadAndDisableRelatedMods (self, warningList: typing.List[Mods.Mod] = None) -> None:
		for modLoader in _allLoaders:  # type: _Loader
			for modRequirement in modLoader.Mod.Requirements:  # type: str
				if self.Mod.Namespace == modRequirement:
					modLoader.Disable(warningList = warningList)

class _Importer:
	def load_module (self, fullname: str):
		return importlib.import_module(fullname)

def Load () -> None:
	waitingMods = 0

	for modLoader in _allLoaders:  # type _Loader
		if modLoader.Mod.IsLoadable(This.Mod.Namespace) and not modLoader.Mod.IsLoaded():
			waitingMods += 1

	if waitingMods == 0:
		Debug.Log("Tried to load mods but none are available to load.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
		return

	_LoadLoop(waitingMods)

def _LoadLoop (waitingMods: int = None) -> None:
	for modLoader in _allLoaders:  # type: _Loader
		if not modLoader.Mod.IsCurrentlyLoadable(This.Mod.Namespace):
			continue

		modLoader.Load()

		remainingMods = waitingMods - 1  # type: int

		if remainingMods > 0:
			_LoadLoop(waitingMods - 1)

		return

	Debug.Log("Cannot continue loading mods, even though there are still '" + str(waitingMods) + "' loadable mods left.\nThe remaining mods probably cannot be loaded because they have circular requirements.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	for modLoader in _allLoaders:  # type: _Loader
		if modLoader.Mod.IsCurrentlyLoadable(This.Mod.Namespace):
			_failedLoadingMods.append(modLoader.Mod)

def LoadMod (namespace: str) -> None:
	"""
	Loads a specific mod by namespace. If the mod isn't installed the load request will be ignored without warning.
	"""

	for modLoader in _allLoaders:
		if modLoader.Mod.Namespace == namespace:

			if not modLoader.Mod.IsCurrentlyLoadable(This.Mod.Namespace):
				Debug.Log("Tried to load '" + namespace + "' but it is not currently loadable.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
				return

			modLoader.Load()

def _Setup () -> None:
	for mod in Mods.GetAllMods():
		modLoader = _Loader(mod)  # type: _Loader
		modLoader.GetInformation()

	_CheckCompatibility()

	atexit.register(_OnExitCallback)

	_PatchOnLoadingScreenAnimationFinished()

def _PatchOnLoadingScreenAnimationFinished ():
	originalFunction = zone.Zone.on_loading_screen_animation_finished  # type: typing.Callable

	@functools.wraps(originalFunction)
	def PatchedOnLoadingScreenAnimationFinished (*args, **kwargs):
		global _failedLoadingMods, _badCompatibilityMods, _showedNotLoadedFailureNotification

		originalFunction(*args, **kwargs)

		from sims4 import log

		try:
			if len(_failedLoadingMods) != 0:
				_ShowLoadingFailureNotification()
				_failedLoadingMods = list()

			if len(_badCompatibilityMods) != 0:
				_ShowCompatibilityFailureNotification()
				_badCompatibilityMods = list()

			if not _showedNotLoadedFailureNotification:
				for mod in Mods.GetAllMods():
					if not mod.IsLoaded() and mod.IsLoadable(This.Mod.Namespace):
						_ShowNotLoadedFailureNotification()
						_showedNotLoadedFailureNotification = True
						break

		except Exception as e:
			log.exception(This.Mod.Namespace, "Failed to show loading failure dialogs.", exc = e, owner = __name__)

	zone.Zone.on_loading_screen_animation_finished = PatchedOnLoadingScreenAnimationFinished

def _Import (modules: list) -> None:
	importer = custom_import.CustomLoader(_Importer())  # type: custom_import.CustomLoader

	for module in modules:  # type: str
		importer.load_module(module)

def _GetArchiveModules (archivePath: str) -> typing.List[str]:
	modules = list()  # type: typing.List[str]
	archive = zipfile.ZipFile(archivePath, "r")  # type: zipfile.ZipFile

	for fileInfo in archive.filelist:  # type: zipfile.ZipInfo
		if fileInfo.filename[-1] != "/":
			path, extension = os.path.splitext(fileInfo.filename)  # type: str, str

			if extension.lower() == ".pyc":
				modules.append(path.replace("/", ".").replace("\\", "."))

	archive.close()

	return modules

def _CheckCompatibility () -> None:
	for modLoader in _allLoaders:  # type: _Loader
		if not modLoader.Mod.IsLoadable(This.Mod.Namespace):
			continue

		if not modLoader.Mod.ReadInformation:
			continue

		for modRequirement in modLoader.Mod.Requirements:  # type: str
			missingRequirement = True  # type: bool

			for checkingModLoader in _allLoaders:  # type: _Loader
				if checkingModLoader.Mod.Namespace == modRequirement:
					if not checkingModLoader.Mod.IsLoadable(This.Mod.Namespace):
						modLoader.Disable(cascade = False, warningList = _badCompatibilityMods)
						Debug.Log("Required mod '" + modRequirement + "' for mod '" + modLoader.Mod.Namespace + "' is not loadable.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						_CheckCompatibility()
						return

					missingRequirement = False  # type: bool

			if missingRequirement:
				modLoader.Disable(cascade = False, warningList = _badCompatibilityMods)
				Debug.Log("Required mod '" + modRequirement + "' for mod '" + modLoader.Mod.Namespace + "' is not installed.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
				_CheckCompatibility()
				return

		for modCompatibility in modLoader.Mod.Compatibility:  # type: Mods.Compatibility
			if modCompatibility.LowestVersion is None and modCompatibility.HighestVersion is None:
				continue

			for checkingModLoader in _allLoaders:  # type: _Loader
				if not checkingModLoader.Mod.ReadInformation:
					continue

				if checkingModLoader.Mod.Namespace == modCompatibility.Namespace:
					if modCompatibility.LowestVersion is not None:
						if modCompatibility.LowestVersion > checkingModLoader.Mod.Version:
							modLoader.Disable(cascade = False, warningList = _badCompatibilityMods)
							Debug.Log("Mod '" + checkingModLoader.Mod.Namespace + "' (" + str(checkingModLoader.Mod.Version) + ") is too old for the mod '" + modLoader.Mod.Namespace + "' (" + str(modLoader.Mod.Version) + ").", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
							_CheckCompatibility()
							return

					if modCompatibility.HighestVersion is not None:
						if modCompatibility.HighestVersion < checkingModLoader.Mod.Version:
							modLoader.Disable(cascade = False, warningList = _badCompatibilityMods)
							Debug.Log("Mod '" + checkingModLoader.Mod.Namespace + "' (" + str(checkingModLoader.Mod.Version) + ") is too new for the mod '" + modLoader.Mod.Namespace + "' (" + str(modLoader.Mod.Version) + ").", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
							_CheckCompatibility()
							return

					break

def _ShowLoadingFailureNotification () -> None:
	modsToken = ""

	for mod in _failedLoadingMods:  # type: Mods.Mod
		if modsToken != "":
			modsToken += "\n"

		modsToken += mod.Namespace + ": v" + str(mod.Version)

	notificationArguments = {
		"title": LoadingFailureNotificationTitle.GetCallableLocalizationString(),
		"text": LoadingFailureNotificationText.GetCallableLocalizationString(modsToken),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, ...]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowCompatibilityFailureNotification () -> None:
	modsToken = ""

	for mod in _badCompatibilityMods:  # type: Mods.Mod
		if modsToken != "":
			modsToken += "\n"

		modsToken += mod.Namespace + ": v" + str(mod.Version)

	notificationArguments = {
		"title": CompatibilityFailureNotificationTitle.GetCallableLocalizationString(),
		"text": CompatibilityFailureNotificationText.GetCallableLocalizationString(modsToken),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, ...]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _ShowNotLoadedFailureNotification () -> None:
	modsToken = ""

	for mod in Mods.GetAllMods():  # type: Mods.Mod
		if not mod.IsLoaded() and mod.IsLoadable(This.Mod.Namespace):
			if modsToken != "":
				modsToken += "\n"

			modsToken += mod.Namespace + ": v" + str(mod.Version)

	notificationArguments = {
		"title": NotLoadedFailureNotificationTitle.GetCallableLocalizationString(),
		"text": NotLoadedFailureNotificationText.GetCallableLocalizationString(modsToken),
		"expand_behavior": ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
		"urgency": ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT
	}  # type: typing.Dict[str, ...]

	Notifications.ShowNotification(queue = True, **notificationArguments)

def _InitiateModules (mod: Mods.Mod, cause: LoadingShared.LoadingCauses) -> None:
	for module in mod.Modules:  # type: str
		if not module in _loadedModules:
			_loadedModules.append(module)

		OnInitiate = None  # type: types.FunctionType

		try:
			OnInitiate = getattr(sys.modules[module], "_OnInitiate")
		except:
			pass

		if isinstance(OnInitiate, types.FunctionType):
			if len(inspect.signature(OnInitiate).parameters) == 1:
				OnInitiate(cause)

	for module in mod.Modules:  # type: str
		OnInitiateLate = None  # type: types.FunctionType

		try:
			OnInitiateLate = getattr(sys.modules[module], "_OnInitiateLate")
		except:
			pass

		if isinstance(OnInitiateLate, types.FunctionType):
			if len(inspect.signature(OnInitiateLate).parameters) == 1:
				OnInitiateLate(cause)

def _StartModules (mod: Mods.Mod, cause: LoadingShared.LoadingCauses) -> None:
	for module in mod.Modules:  # type: str
		OnStart = None  # type: types.FunctionType

		try:
			OnStart = getattr(sys.modules[module], "_OnStart")
		except:
			pass

		if isinstance(OnStart, types.FunctionType):
			if len(inspect.signature(OnStart).parameters) == 1:
				OnStart(cause)

	for module in mod.Modules:  # type: str
		OnStartLate = None  # type: types.FunctionType

		try:
			OnStartLate = getattr(sys.modules[module], "_OnStartLate")
		except:
			pass

		if isinstance(OnStartLate, types.FunctionType):
			if len(inspect.signature(OnStartLate).parameters) == 1:
				OnStartLate(cause)

def _StopModules (mod: Mods.Mod, cause: LoadingShared.UnloadingCauses) -> bool:
	successful = True  # type: bool

	for module in mod.Modules:  # type: str
		if module in _loadedModules:
			_loadedModules.remove(module)

		OnStopEarly = None  # type: types.FunctionType

		try:
			OnStopEarly = getattr(sys.modules[module], "_OnStopEarly")
		except:
			pass

		if isinstance(OnStopEarly, types.FunctionType):
			if len(inspect.signature(OnStopEarly).parameters) == 1:
				try:
					OnStopEarly(cause)
				except:
					Debug.Log("Failed to call '_StopEarly' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					successful = False

	for module in mod.Modules:  # type: str
		OnStop = None  # type: types.FunctionType

		try:
			OnStop = getattr(sys.modules[module], "_OnStop")
		except:
			pass

		if isinstance(OnStop, types.FunctionType):
			if len(inspect.signature(OnStop).parameters) == 1:
				try:
					OnStop(cause)
				except:
					Debug.Log("Failed to call '_Stop' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					successful = False

	return successful

def _UnloadModules (mod: Mods.Mod, cause: LoadingShared.UnloadingCauses) -> bool:
	successful = True  # type: bool

	for module in mod.Modules:  # type: str
		OnUnloadEarly = None  # type: types.FunctionType

		try:
			OnUnloadEarly = getattr(sys.modules[module], "_OnUnloadEarly")
		except:
			pass

		if isinstance(OnUnloadEarly, types.FunctionType):
			if len(inspect.signature(OnUnloadEarly).parameters) == 1:
				try:
					OnUnloadEarly(cause)
				except:
					Debug.Log("Failed to call '_UnloadEarly' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					successful = False

	for module in mod.Modules:  # type: str
		OnUnload = None  # type: types.FunctionType

		try:
			OnUnload = getattr(sys.modules[module], "_OnUnload")
		except:
			pass

		if isinstance(OnUnload, types.FunctionType):
			if len(inspect.signature(OnUnload).parameters) == 1:
				try:
					OnUnload(cause)
				except:
					Debug.Log("Failed to call '_Unload' for module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
					successful = False

	Events.ActivateOnModUnload(mod, True if cause == LoadingShared.UnloadingCauses.Exiting else False)

	return successful

def _OnExitCallback ():
	for mod in _allLoaders:  # type: _Loader
		if mod.Mod.IsCurrentlyUnloadable(This.Mod.Namespace):
			mod.Unload(cause = LoadingShared.UnloadingCauses.Exiting)

_Setup()