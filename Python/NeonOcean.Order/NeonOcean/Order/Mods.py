import json
import os
import typing

import enum
from NeonOcean.Order import Information, Paths
from NeonOcean.Order.Tools import Exceptions, Version
from sims4 import log

ModFileName = Information.Author + "-Mod.json"  # type: str

_allMods = list()  # type: typing.List[Mod]

class Mod:
	def __init__ (self, namespace: str, name: str, loadController: str, filePath: str):
		"""
		A container for mod information.

		:param namespace: The namespace of the mod, it should be the root of all the mod's modules.
		:type namespace: str
		:param name: The actual name of the mod. This will be used as the name of the attribute in this module that points to this mod.
		:type name: str
		:param loadController: The namespace of the mod that can load this mod.
		:type loadController: str
		:param filePath: The file path of the mod information file.
		:type filePath: str
		"""

		if not isinstance(namespace, str):
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str,))

		if not isinstance(name, str):
			raise Exceptions.IncorrectTypeException(name, "name", (str,))

		if not isinstance(loadController, str):
			raise Exceptions.IncorrectTypeException(loadController, "loadController", (str,))

		if not isinstance(filePath, str):
			raise Exceptions.IncorrectTypeException(filePath, "filePath", (str,))

		self.Namespace = namespace  # type: str
		self.Name = name  # type: str
		self.LoadController = loadController  # type: str
		self.FilePath = filePath  # type: str

		self.Author = None  # type: typing.Optional[str]
		self.Version = None  # type: typing.Optional[Version.Version]
		self.Distribution = None  # type: typing.Optional[str]
		self.Rating = Rating.Normal  # type: Rating

		self.ScriptPaths = list()  # type: typing.List[str]
		self.Modules = list()  # type: typing.List[str]

		self.Requirements = list()  # type: typing.List[str]
		self.Compatibility = list()  # type: typing.List[Compatibility]

		self.Path = os.path.join(Paths.ModsPath, self.Namespace)  # type: str
		self.PersistentPath = os.path.join(Paths.PersistentPath, self.Namespace)  # type: str

		self.Blocked = False  # type: bool
		self.Loading = False  # type: bool

		self.ReadInformation = False  # type: bool
		self.Imported = False  # type: bool
		self.Initiated = False  # type: bool
		self.Started = False  # type: bool

		_allMods.append(self)

	def ControlsLoading (self, hostNamespace: str) -> bool:
		return self.LoadController == hostNamespace

	def IsLoadable (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod can ever be loaded by the host.
		:param hostNamespace: The namespace of the mod that will be doing the loading
		:type hostNamespace: str
		:rtype: bool
		"""

		return not self.Blocked and \
			   self.ControlsLoading(hostNamespace)

	def IsCurrentlyLoadable (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod can be loaded by the host right now.
		:param hostNamespace: The namespace of the mod that will be doing the loading
		:type hostNamespace: str
		:rtype: bool
		"""

		return self.IsLoadable(hostNamespace) and \
			   self.ReadInformation and \
			   not self.Loading and \
			   not self.Imported and \
			   not self.Initiated and \
			   not self.Started and \
			   self.RequirementsLoaded()

	# noinspection SpellCheckingInspection
	def IsUnloadable (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod can ever be unloaded by the host.
		:param hostNamespace: The namespace of the mod that will be doing the loading
		:type hostNamespace: str
		:rtype: bool
		"""

		return self.ControlsLoading(hostNamespace)
		pass

	# noinspection SpellCheckingInspection
	def IsCurrentlyUnloadable (self, hostNamespace: str) -> bool:
		"""
		Whether or not this mod can be unloaded by the host right now.
		:param hostNamespace: The namespace of the mod that will be doing the loading
		:type hostNamespace: str
		:rtype: bool
		"""

		return self.IsUnloadable(hostNamespace) and \
			   self.Imported

	def IsLoaded (self) -> bool:
		return self.ReadInformation and \
			   self.Imported and \
			   self.Initiated and \
			   self.Started

	def RequirementsLoaded (self) -> bool:
		loadedRequirements = 0  # type: int

		for requirement in self.Requirements:
			for mod in GetAllMods():  # type: Mod
				if mod.Namespace == requirement:
					if not mod.IsLoaded():
						return False

					loadedRequirements += 1

		if len(self.Requirements) != loadedRequirements:
			return False

		return True

class Compatibility:
	def __init__ (self, namespace: str, lowestVersion: Version.Version, highestVersion: Version.Version):
		self.Namespace = namespace  # type: str
		self.LowestVersion = lowestVersion  # type: Version.Version
		self.HighestVersion = highestVersion  # type: Version.Version

class Rating(enum.Int):
	Normal = 0  # type: Rating
	# noinspection SpellCheckingInspection
	NSFW = 1  # type: Rating

def GetMod (namespace: str) -> Mod:
	for mod in _allMods:  # type: Mod
		if mod.Namespace == namespace:
			return mod

	raise Exception("No mod with the namespace '" + namespace + "' exists.")

def IsInstalled (namespace: str) -> bool:
	for mod in _allMods:  # type: Mod
		if mod.Namespace == namespace:
			return True

	return False

def GetAllMods () -> typing.List[Mod]:
	return list(_allMods)

def _Setup () -> None:
	for directoryRoot, directoryNames, fileNames in os.walk(Paths.ModsPath):  # type: str, list, list
		for fileName in fileNames:  # type: str
			modFilePath = os.path.join(directoryRoot, fileName)  # type: str

			try:
				if fileName.lower() == ModFileName.lower():
					with open(modFilePath) as modFile:
						modInformation = json.JSONDecoder().decode(modFile.read())  # type: dict

					modNamespace = modInformation["Namespace"]  # type: str
					modName = modInformation["Name"]  # type: str
					modLoadControl = modInformation["Load Controller"]  # type: str

					duplicateMod = False  # type: bool

					for mod in GetAllMods():
						if modNamespace == mod.Namespace:
							log.exception("NeonOcean", "Duplicate mod with the namespace '" + modNamespace + "' at: \n" + modFilePath, owner = __name__)
							duplicateMod = True

					if duplicateMod:
						continue

					mod = Mod(modNamespace, modName, modLoadControl, modFilePath)

					globals()[modName] = mod
			except Exception as e:
				log.exception("NeonOcean", "Failed to read basic data from mod information dictionary at: \n" + modFilePath, exc = e, owner = __name__)

_Setup()

Order: Mod
