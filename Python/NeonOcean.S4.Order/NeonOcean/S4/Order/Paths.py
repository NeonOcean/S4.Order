from __future__ import annotations

import os
import pathlib

from NeonOcean.S4.Order import Information

ModuleRootPath: str
UserDataPath: str

ModsPath: str
SavesPath: str
DebugPath: str
PersistentPath: str
TemporaryPath: str

def StripUserDataPath (filePath: str) -> str:
	"""
	Removes the s4 user data path from this file path.
	:type filePath: str
	:returns: The file path relative to the user data path, If the file path doesnt start with the user data path, the input will be returned.
	:rtype: str
	"""

	if not isinstance(filePath, str):
		raise Exception("'filePath' is not a string.")

	try:
		userDataPathObject = pathlib.Path(UserDataPath)  # type: pathlib.Path
		filePathObject = pathlib.Path(filePath)  # type: pathlib.Path

		return str(filePathObject.relative_to(userDataPathObject))
	except Exception:
		return filePath

def _GetModuleRootPath () -> str:
	pathPartCount = __name__.count(".") + 1  # type: int

	rootPath = os.path.normpath(__file__)  # type: str

	partPosition = 0  # type: int
	while partPosition < pathPartCount:
		rootPath = os.path.dirname(rootPath)
		partPosition += 1

	return rootPath

def _GetS4UserDataPath () -> str:
	moduleRootPath = _GetModuleRootPath()  # type: str
	s4PointerPath = os.path.join(os.path.dirname(moduleRootPath), "S4Path.txt")  # type: str

	if os.path.exists(s4PointerPath):
		with open(s4PointerPath, "r") as s4PointerFile:
			return s4PointerFile.read()

	moduleFilePath = os.path.normpath(__file__)  # type: str

	s4Directories = os.path.normpath("electronic Arts\\the sims 4")  # type: str
	s4DirectoriesMods = os.path.join(s4Directories, "mods")  # type: str
	s4DirectoriesStartIndex = moduleFilePath.lower().rfind(s4DirectoriesMods.lower())

	if s4DirectoriesStartIndex != -1:
		s4DirectoriesEndIndex = s4DirectoriesStartIndex + len(s4Directories) + 1

		return moduleFilePath[:s4DirectoriesEndIndex]

	raise Exception("Cannot find The Sims 4 user data path")

def _Setup () -> None:
	global ModuleRootPath, UserDataPath, ModsPath, SavesPath, DebugPath, PersistentPath, TemporaryPath

	ModuleRootPath = _GetModuleRootPath()  # type: str
	UserDataPath = _GetS4UserDataPath()  # type: str

	ModsPath = os.path.join(UserDataPath, "Mods")  # type: str
	SavesPath = os.path.join(UserDataPath, "Saves")  # type: str
	DebugPath = os.path.join(UserDataPath, Information.RootNamespace, "Debug")  # type: str
	PersistentPath = os.path.join(UserDataPath, Information.RootNamespace, "Persistent")  # type: str
	TemporaryPath = os.path.join(UserDataPath, Information.RootNamespace, "Temporary")  # type: str

_Setup()
