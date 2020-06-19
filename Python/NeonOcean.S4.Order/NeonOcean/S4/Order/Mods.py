from __future__ import annotations

import datetime
import enum_lib
import json
import os
import typing

from NeonOcean.S4.Order import Information, Paths
from NeonOcean.S4.Order.Tools import Exceptions, Version
from sims4 import log

_allMods = dict()  # type: typing.Dict[str, Mod]

class Mod:
	def __init__ (self, namespace: str, name: str, loadController: str, informationFilePath: str):
		"""
		A container for mod information.

		:param namespace: The namespace of the mod, it should be the root of all the mod's modules.
		:type namespace: str
		:param name: The actual name of the mod.
		:type name: str
		:param loadController: The namespace of the mod that can load this mod.
		:type loadController: typing.Optional[str]
		:param informationFilePath: The file path of the mod information file.
		:type informationFilePath: str
		"""

		if not isinstance(namespace, str):
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str,))

		if not isinstance(name, str):
			raise Exceptions.IncorrectTypeException(name, "name", (str,))

		if not isinstance(loadController, str) and loadController is not None:
			raise Exceptions.IncorrectTypeException(loadController, "loadController", (str, "None"))

		if not isinstance(informationFilePath, str):
			raise Exceptions.IncorrectTypeException(informationFilePath, "informationFilePath", (str,))

		self.InformationFilePath = informationFilePath  # type: str
		self.InformationFileDirectoryPath = os.path.dirname(self.InformationFilePath)  # type: str

		self._namespace = namespace  # type: str

		self.Name = name  # type: str
		self.LoadController = loadController  # type: typing.Optional[str]

		self.Path = os.path.join(Paths.ModsPath, self.Namespace)  # type: str
		self.PersistentPath = os.path.join(Paths.PersistentPath, self.Namespace)  # type: str

		self.Author = ""  # type: str
		self.Version = Version.Version()  # type: Version.Version
		self.VersionDisplay = "0.0.0"  # type: str
		self.Distribution = Distribution(None, None, None, None)  # type: Distribution
		self.Rating = Rating.Normal  # type: Rating

		self.ScriptPaths = list()  # type: typing.List[str]
		self.Modules = list()  # type: typing.List[str]

		self.RequiredMods = set()  # type: typing.Set[str]
		self.IncompatibleMods = set()  # type: typing.Set[str]
		self.LoadAfter = set()  # type: typing.Set[str]
		self.LoadBefore = set()  # type: typing.Set[str]
		self.Compatibility = list()  # type: typing.List[Compatibility]

		self.BuildDate = None  # type: typing.Optional[datetime.datetime]
		self.BuildGameVersion = None  # type: typing.Optional[Version.Version]

		self.Additional = dict()  # type: dict

		self.Blocked = False  # type: bool
		self.Loading = False  # type: bool

		self.ReadInformation = False  # type: bool
		self.Imported = False  # type: bool
		self.Initiated = False  # type: bool
		self.Started = False  # type: bool

		self.LoadTime = None  # type: typing.Optional[float]

	@property
	def Namespace (self) -> str:
		"""
		This mod's namespace, a unique identifier for the mod. Ideally, it should be the root of all the mod's python modules.
		"""

		return self._namespace

	def IsLoaded (self) -> bool:
		"""
		Whether or not this mod is currently loaded.
		:rtype: bool
		"""

		return self.ReadInformation and \
			   self.Imported and \
			   self.Initiated and \
			   self.Started

	def ControlsLoading (self, hostNamespace: str) -> bool:
		"""
		Whether or not the host controls the mod's loading.
		:param hostNamespace: The namespace of the mod that will be doing the loading
		:type hostNamespace: str
		:rtype: bool
		"""

		if self.LoadController is None:
			return False

		return self.LoadController == hostNamespace

	def IsLoadable (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod can be loaded by the host. This returns false if the mod is blocked, the mod is not controlled by the host, or the
		mod has no python files to load.
		:param hostNamespace: The namespace of the mod that will be doing the loading.
		:type hostNamespace: str
		:rtype: bool
		"""

		return not self.Blocked and \
			   self.ControlsLoading(hostNamespace) and \
			   len(self.ScriptPaths) != 0

	def IsReadyToLoad (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod is ready to be loaded right now. This returns false if this mod is not loadable the mod, its information hasn't been
		read, its already loaded, or is currently loading. This does not take into account whether or not it is safe to load.
		:param hostNamespace:
		:return:
		"""

		return self.IsLoadable(hostNamespace) and \
			   not self.Loading and \
			   self.ReadInformation and \
			   not self.Imported and \
			   not self.Initiated and \
			   not self.Started

	# noinspection SpellCheckingInspection
	def IsUnloadable (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod can ever be unloaded by the host.
		:param hostNamespace: The namespace of the mod that will be doing the loading
		:type hostNamespace: str
		:rtype: bool
		"""

		return self.ControlsLoading(hostNamespace)

	# noinspection SpellCheckingInspection
	def IsReadyToUnload (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod is ready to be unloaded right now. This returns false if this mod is not loadable the mod, or the mod is not loaded at all.
		:param hostNamespace: The namespace of the mod that will be doing the loading
		:type hostNamespace: str
		:rtype: bool
		"""

		return self.IsUnloadable(hostNamespace) and \
			   self.Imported

	def RequiredModsInstalled (self) -> bool:
		"""
		Whether or not all required mod are installed.
		"""

		for requiredModNamespace in self.RequiredMods:  # type: str
			if not IsInstalled(requiredModNamespace):
				return False

		return True

	def IncompatibleModsInstalled (self) -> bool:
		"""
		Whether or not a mod is installed that is completely incompatible with this one.
		"""

		for incompatibleModNamespace in self.IncompatibleMods:  # type: str
			if IsInstalled(incompatibleModNamespace):
				return True

		return False

	def PrerequisiteModsLoaded (self) -> bool:
		"""
		Whether or not the mods meant to be loaded before this one are loaded.
		"""

		for testingModNamespace, testingMod in GetAllModsByNamespace().items():  # type: str, Mod
			if len(testingMod.ScriptPaths) == 0:
				continue

			if testingModNamespace in self.LoadAfter:
				if not testingMod.IsLoaded():
					return False

			if self.Namespace in testingMod.LoadBefore:
				if not testingMod.IsLoaded():
					return False

		return True

class Compatibility:
	def __init__ (self, namespace: str, lowestVersion: typing.Optional[Version.Version], highestVersion: typing.Optional[Version.Version]):
		if not isinstance(namespace, str):
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str,))

		if not isinstance(lowestVersion, Version.Version) and lowestVersion is not None:
			raise Exceptions.IncorrectTypeException(lowestVersion, "lowestVersion", (Version.Version, None))

		if not isinstance(highestVersion, Version.Version) and highestVersion is not None:
			raise Exceptions.IncorrectTypeException(highestVersion, "highestVersion", (Version.Version, None))

		self.Namespace = namespace  # type: str
		self.LowestVersion = lowestVersion  # type: typing.Optional[Version.Version]
		self.HighestVersion = highestVersion  # type: typing.Optional[Version.Version]

class Rating(enum_lib.IntFlag):
	Normal = 1  # type: Rating
	# noinspection SpellCheckingInspection
	NSFW = 2  # type: Rating

class Distribution:
	def __init__ (self, updatesController: typing.Optional[str],
				  updatesFileURL: typing.Optional[str],
				  downloadURL: typing.Optional[str],
				  previewDownloadURL: typing.Optional[str]):

		if not isinstance(updatesController, str) and updatesController is not None:
			raise Exceptions.IncorrectTypeException(updatesController, "updatesController", (str, None))

		if not isinstance(updatesFileURL, str) and updatesFileURL is not None:
			raise Exceptions.IncorrectTypeException(updatesFileURL, "updatesFileURL", (str, None))

		if not isinstance(downloadURL, str) and downloadURL is not None:
			raise Exceptions.IncorrectTypeException(downloadURL, "downloadURL", (str, None))

		self.UpdatesController = updatesController  # type: typing.Optional[str]
		self.UpdatesFileURL = updatesFileURL  # type: typing.Optional[str]
		self.DownloadURL = downloadURL  # type: typing.Optional[str]
		self.PreviewDownloadURL = previewDownloadURL  # type: typing.Optional[str]

def RegisterMod (mod: Mod) -> None:
	"""
	Register this mod to the list of all mods.
	"""

	if mod.Namespace in _allMods:
		raise Exception("A mod with the namespace '" + mod.Namespace + " is already registered.")

	_allMods[mod.Namespace] = mod

def GetMod (namespace: str) -> Mod:
	"""
	Get a specific mod by its namespace.
	:param namespace: This mod's namespace, a unique identifier for the mod.
	:type namespace: str
	"""

	mod = _allMods.get(namespace, None)  # type: typing.Optional[Mod]

	if mod is not None:
		return mod

	raise Exception("No mod with the namespace '" + namespace + "' exists.")

def GetModSafely (namespace: str) -> typing.Optional[Mod]:
	"""
	Get a specific mod by its namespace.
	:param namespace: This mod's namespace, a unique identifier for the mod. If the mod is not installed we will return None instead.
	:type namespace: str
	"""

	mod = _allMods.get(namespace, None)  # type: typing.Optional[Mod]

	if mod is not None:
		return mod

	return None

def GetAllMods () -> typing.List[Mod]:
	"""
	Get all mods.
	"""

	return list(_allMods.values())

def GetAllModsByNamespace () -> typing.Dict[str, Mod]:
	"""
	Get all mods listed in a dictionary by their namespaces
	"""

	return dict(_allMods)

def IsInstalled (namespace: str) -> bool:
	"""
	Get whether or not a mod with this namespace is installed.
	"""

	return _allMods.get(namespace, None) is not None

def _Setup () -> None:
	for directoryRoot, directoryNames, fileNames in os.walk(Paths.ModsPath):  # type: str, list, list
		for fileName in fileNames:  # type: str
			fileNameLower = fileName.lower()  # type: str

			modFilePath = os.path.join(directoryRoot, fileName)  # type: str

			if os.path.splitext(fileNameLower)[1] == ".json":
				if (Information.RootNamespace + "-mod").lower() in fileNameLower:
					try:
						with open(modFilePath) as modFile:
							modInformation = json.JSONDecoder().decode(modFile.read())  # type: dict

						modNamespace = modInformation["Namespace"]  # type: str
						modName = modInformation["Name"]  # type: str
						modLoadControl = modInformation.get("LoadController")  # type: typing.Optional[str]

						duplicateMod = False  # type: bool

						for mod in _allMods.values():  # type: Mod
							if modNamespace == mod.Namespace:
								log.exception("NeonOcean", "Duplicate mod with the namespace '" + modNamespace + "' at: \n" + modFilePath, owner = __name__)
								duplicateMod = True

						if duplicateMod:
							continue

						mod = Mod(modNamespace, modName, modLoadControl, modFilePath)
						RegisterMod(mod)

					except Exception as e:
						log.exception("NeonOcean", "Failed to read basic data from mod information dictionary at: \n" + modFilePath, exc = e, owner = __name__)

_Setup()
