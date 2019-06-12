import importlib
import inspect
import json
import os
import pathlib
import sys
import types
import typing
import zipfile
from functools import wraps

from NeonOcean.Order import Debug, Events, LoadingShared, Paths, This
from NeonOcean.Order.Tools import Exceptions
from sims4.importer import custom_import, utils

Imported = False  # type: bool
Importing = False  # type: bool

_loadedPaths = list()  # type: typing.List[pathlib.Path]

class Level:
	def __init__ (self, level: typing.Union[int, float], paths: typing.List[pathlib.Path], functions: typing.List[dict]):
		self.Level = level  # type: typing.Union[int, float]
		self.Paths = paths  # type: typing.List[pathlib.Path]
		self.Functions = functions  # type: typing.List[dict]

	def ImportModules (self) -> None:
		for path in self.Paths:  # type: pathlib.Path
			importer = custom_import.CustomLoader(_Importer())  # type: custom_import.CustomLoader

			modules = _GetModules(path)  # type: list

			for module in modules:  # type: str
				try:
					importer.load_module(module)
				except:
					Debug.Log("Failed to import module '" + module + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

			_loadedPaths.append(path)

	def CallFunctions (self) -> None:
		for functionDictionary in self.Functions:  # type: dict
			moduleName = functionDictionary["Module"]  # type: str
			functionName = functionDictionary["Function"]  # type: str
			Arguments = functionDictionary["Arguments"]  # type: list
			KeywordArguments = functionDictionary["Keyword Arguments"]  # type: dict
	
			try:
				if not moduleName in sys.modules:
					raise Exception("Module '" + moduleName + "' is not imported.")

				currentObject = sys.modules[moduleName]

				path = functionName.split(".")  # type: list
				callObject = None  # type: typing.Callable

				for index, attribute in enumerate(path):
					currentObject = getattr(currentObject, attribute)

					if index != len(path) - 1:
						if not isinstance(currentObject, type):
							raise Exception("Cannot find function, path is not followable.")
					else:
						if isinstance(currentObject, types.BuiltinFunctionType) or isinstance(currentObject, types.FunctionType):
							callObject = currentObject
						else:
							raise Exception("Function path does not lead to a built-in function or function.")

				if callObject is not None:
					callObject(*Arguments, **KeywordArguments)

			except:
				Debug.Log("Failed to call function: '" + moduleName + "." + functionName + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

class _Importer:
	def __init__ (self):
		pass

	def load_module (self, fullname: str):
		return importlib.import_module(fullname)

def ImportModules () -> None:
	global Importing, Imported

	if Importing or Imported:
		raise Exception("Cannot import modules twice.")

	Importing = True

	levels = _GetLevels()

	moduleRootPathObject = pathlib.Path(Paths.ModuleRootPath)  # type: pathlib.Path
	moduleRootPathIndex = -1  # type: int

	for sysPathIndex in range(len(sys.path)):  # type: int
		sysPathObject = pathlib.Path(sys.path[sysPathIndex])  # type: pathlib.Path

		if sysPathObject == moduleRootPathObject:
			moduleRootPathIndex = sysPathIndex
			continue

	if moduleRootPathIndex == -1:
		raise Exception("Failed to find this module's root path in sys.path.")

	sysLoadedPaths = sys.path[:moduleRootPathIndex + 1]  # type: typing.List[typing.Union[pathlib.Path, str]]

	for sysLoadedPathIndex in range(len(sysLoadedPaths)):  # type: int
		sysLoadedPaths[sysLoadedPathIndex] = pathlib.Path(sysLoadedPaths[sysLoadedPathIndex])

	for level in levels:  # type: Level
		levelPathsIndex = 0  # type: int

		while levelPathsIndex < len(level.Paths):
			if not level.Paths[levelPathsIndex].exists():
				Debug.Log("Cannot import modules from '" + str(level.Paths[levelPathsIndex]) + "' because it doesnt exist.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
				level.Paths.pop(levelPathsIndex)
				continue

			if level.Paths[levelPathsIndex] in sysLoadedPaths:
				Debug.Log("Cannot import modules from '" + str(level.Paths[levelPathsIndex]) + "' because it seems to be already loaded.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
				level.Paths.pop(levelPathsIndex)
				continue

			levelPathsIndex += 1

	sysRemovingPaths = list()

	for sysPath in sys.path[moduleRootPathIndex:]:  # type: str
		if sysPath == sys.path[0]:
			continue

		sysPathObject = pathlib.Path(sysPath)  # type: pathlib.Path

		for level in levels:  # type: Level
			if sysPathObject in level.Paths:
				sysRemovingPaths.append(sysPath)

	for sysRemovingPath in sysRemovingPaths:
		sys.path.remove(sysRemovingPath)

	sysInsertedPathCount = 0  # type: int

	for level in levels:  # type: Level
		for levelPath in level.Paths:  # type: pathlib.Path
			sys.path.insert(moduleRootPathIndex + 1 + sysInsertedPathCount, str(levelPath))
			sysInsertedPathCount += 1

	for level in levels:  # type: Level
		level.ImportModules()
		level.CallFunctions()

	Importing = False
	Imported = True

	Events.ActivateOnLoaded()

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ImportModules()

def _GetLevels () -> typing.List[Level]:
	levels = list()  # type: list

	defaultLevel = Level(0.0, list(), list())

	modsPathObject = pathlib.Path(Paths.ModsPath)  # type: pathlib.Path
	moduleRootPathObject = pathlib.Path(Paths.ModuleRootPath)  # type: pathlib.Path
	moduleRootPathIndex = -1  # type: int

	for sysPathIndex in range(len(sys.path)):  # type: int
		sysPathObject = pathlib.Path(sys.path[sysPathIndex])  # type: pathlib.Path

		if sysPathObject == moduleRootPathObject:
			moduleRootPathIndex = sysPathIndex
			continue

	if moduleRootPathIndex == -1:
		raise Exception("Failed to find this module's root path in sys.path.")

	sysUnloadedPaths = sys.path[moduleRootPathIndex + 1:]  # type: typing.List[typing.Union[pathlib.Path, str]]

	for sysUnloadedPathIndex in range(len(sysUnloadedPaths)):  # type: int
		sysUnloadedPaths[sysUnloadedPathIndex] = pathlib.Path(sysUnloadedPaths[sysUnloadedPathIndex])

	for sysUnloadedPath in sysUnloadedPaths:  # type: pathlib.Path
		if modsPathObject in sysUnloadedPath.parents:
			appendPath = True  # type: bool

			if moduleRootPathObject == sysUnloadedPath:
				appendPath = False

			if not appendPath:
				for scriptPath in This.Mod.ScriptPaths:  # type: str
					scriptPathObject = pathlib.Path(scriptPath)  # type: pathlib.Path

					if scriptPathObject == sysUnloadedPath:
						appendPath = False
						break

			if appendPath:
				defaultLevel.Paths.append(sysUnloadedPath)

	_RemoveDuplicates(defaultLevel.Paths)
	levels.append(defaultLevel)

	for directoryRoot, directoryNames, fileNames in os.walk(Paths.ModsPath):  # type: str, list, list
		for fileName in fileNames:  # type: str
			fileNameLower = fileName.lower()  # type: str

			if os.path.splitext(fileNameLower)[1] == ".json" and fileNameLower.startswith((This.Mod.Namespace + "-load_order").lower()):
				orderFilePath = os.path.join(directoryRoot, fileName)  # type: str

				try:
					Debug.Log("Loading order file at '" + Paths.StripUserDataPath(orderFilePath) + "'.", This.Mod.Namespace, Debug.LogLevels.Info, group = This.Mod.Namespace, owner = __name__)

					try:
						with open(orderFilePath) as orderFile:
							orderInformation = json.JSONDecoder().decode(orderFile.read())  # type: typing.List[dict]
					except:
						Debug.Log("Failed to read load order file '" + Paths.StripUserDataPath(os.path.join(directoryRoot, fileName)) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)
						continue

					if not isinstance(orderInformation, list):
						raise Exceptions.IncorrectTypeException(orderInformation, "Root", (list,))

					for levelIndex, levelDictionary in enumerate(orderInformation):  # type: int, dict
						if not isinstance(levelDictionary, dict):
							raise Exceptions.IncorrectTypeException(levelDictionary, "Root[%d]" % levelIndex, (dict,))

						if not "Paths" in levelDictionary and not "Functions" in levelDictionary:
							raise Exception("Missing dictionary entry 'Paths' or 'Functions' in 'Root[%d]'" % levelIndex)

						levelLevelValue = levelDictionary.get("Level", 0.0)  # type: typing.Union[int, float]

						levelPathsValue = levelDictionary.get("Paths", list())  # type: typing.List[typing.Union[pathlib.Path, dict]]
						levelFunctionsValue = levelDictionary.get("Functions", list())  # type: typing.List[dict]

						if not isinstance(levelLevelValue, int) and not isinstance(levelLevelValue, float):
							raise Exceptions.IncorrectTypeException(levelLevelValue, "Root[%d][Level]" % levelIndex, (int, float))

						if not isinstance(levelPathsValue, list):
							raise Exceptions.IncorrectTypeException(levelPathsValue, "Root[%d][Paths]" % levelIndex, (list,))

						if not isinstance(levelFunctionsValue, list):
							raise Exceptions.IncorrectTypeException(levelFunctionsValue, "Root[%d][Functions]" % levelIndex, (list,))

						for pathIndex, pathDictionary in enumerate(levelPathsValue):  # type: int, typing.Dict[str, str]
							if not isinstance(pathDictionary, dict):
								raise Exceptions.IncorrectTypeException(pathDictionary, "Root[%d][Paths][%d]" % (levelIndex, pathIndex), (dict,))

							if not "Root" in pathDictionary:
								raise Exception("Missing dictionary entry 'Root' in 'Root[%d][Paths][%d]'" % (levelIndex, pathIndex))

							if not "Path" in pathDictionary:
								raise Exception("Missing dictionary entry 'Path' in 'Root[%d][Paths][%d]'" % (levelIndex, pathIndex))

							pathsRootValue = pathDictionary.get("Root")  # type: str
							pathsPathValue = pathDictionary.get("Path")  # type: str

							if not isinstance(pathsRootValue, str):
								raise Exceptions.IncorrectTypeException(pathsRootValue, "Root[%d][Paths][%d][Root]" % (levelIndex, pathIndex), (str,))

							if not isinstance(pathsPathValue, str):
								raise Exceptions.IncorrectTypeException(pathsPathValue, "Root[%d][Paths][%d][Root]" % (levelIndex, pathIndex), (str,))

							pathsRootValue = pathsRootValue.lower()

							if pathsRootValue == "mods":
								pathsRootValue = Paths.ModsPath
							elif pathsRootValue == "s4":
								pathsRootValue = Paths.UserDataPath
							elif pathsRootValue == "current":
								pathsRootValue = directoryRoot

							levelPathsValue[pathIndex] = pathlib.Path(os.path.join(pathsRootValue, pathsPathValue))

							for defaultPath in defaultLevel.Paths:  # type: pathlib.Path
								if defaultPath == levelPathsValue[pathIndex]:
									defaultLevel.Paths.remove(defaultPath)

						_RemoveDuplicates(levelPathsValue)

						for functionIndex, functionDictionary in enumerate(levelFunctionsValue):  # type: int, dict
							if not isinstance(functionDictionary, dict):
								raise Exceptions.IncorrectTypeException(functionDictionary, "Root[%d][Functions][%d]" % (levelIndex, functionIndex), (dict,))

							if not "Module" in functionDictionary:
								raise Exception("Missing dictionary entry 'Module' in 'Root[%d][Functions][%d]'" % (levelIndex, functionIndex))

							if not "Function" in functionDictionary:
								raise Exception("Missing dictionary entry 'Function' in 'Root[%d][Functions][%d]'" % (levelIndex, functionIndex))

							if not "Arguments" in functionDictionary:
								raise Exception("Missing dictionary entry 'Arguments' in 'Root[%d][Functions][%d]'" % (levelIndex, functionIndex))

							if not "Keyword Arguments" in functionDictionary:
								raise Exception("Missing dictionary entry 'Keyword Arguments' in 'Root[%d][Functions][%d]'" % (levelIndex, functionIndex))

							functionModuleValue = functionDictionary["Module"]  # type: str
							functionFunctionValue = functionDictionary["Function"]  # type: str
							functionArgumentsValue = functionDictionary["Arguments"]  # type: list
							functionKeywordArgumentsValue = functionDictionary["Keyword Arguments"]  # type: dict

							if not isinstance(functionModuleValue, str):
								raise Exceptions.IncorrectTypeException(functionModuleValue, "Root[%d][Functions][%d][Module]" % (levelIndex, functionIndex), (str,))

							if not isinstance(functionFunctionValue, str):
								raise Exceptions.IncorrectTypeException(functionFunctionValue, "Root[%d][Functions][%d][Function]" % (levelIndex, functionIndex), (str,))

							if not isinstance(functionArgumentsValue, list):
								raise Exceptions.IncorrectTypeException(functionArgumentsValue, "Root[%d][Functions][%d][Arguments]" % (levelIndex, functionIndex), (list,))

							if not isinstance(functionKeywordArgumentsValue, dict):
								raise Exceptions.IncorrectTypeException(functionArgumentsValue, "Root[%d][Functions][%d][Keyword Arguments]" % (levelIndex, functionIndex), (dict,))

							for functionKeywordArgumentsValueKey in functionKeywordArgumentsValue.keys():  # type: int, dict
								if not isinstance(functionKeywordArgumentsValueKey, str):
									raise Exceptions.IncorrectTypeException(functionKeywordArgumentsValueKey, "Root[%d][Functions][%d][Function][Key]" % (levelIndex, functionIndex), (str,))

						_RemoveDuplicates(levelFunctionsValue)

						if levelLevelValue == 0.0:
							defaultLevel.Paths.extend(levelPathsValue)
							defaultLevel.Functions.extend(levelFunctionsValue)
							_RemoveDuplicates(defaultLevel.Paths)
							_RemoveDuplicates(defaultLevel.Functions)
						else:
							matchedLevel = False  # type: bool

							for level in levels:  # type: Level
								if level.Level == levelLevelValue:
									level.Paths.extend(levelPathsValue)
									level.Functions.extend(levelFunctionsValue)
									_RemoveDuplicates(level.Paths)
									_RemoveDuplicates(level.Paths)

									matchedLevel = True
									break

							if not matchedLevel:
								levels.append(Level(levelLevelValue, levelPathsValue, levelFunctionsValue))
				except:
					Debug.Log("Encountered a problem while reading load order file '" + Paths.StripUserDataPath(os.path.join(directoryRoot, fileName)) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	return _SortLevels(levels)

def _SortLevels (levels: typing.List[Level]) -> typing.List[Level]:
	"""
	:param levels: A list of levels needing to be sorted.
	:type levels: typing.List[Level]
	:return: A new list containing the input levels in order from lowest level to highest level.
	:rtype: typing.List[Level]
	"""

	if not isinstance(levels, list):
		raise Exceptions.IncorrectTypeException(levels, "levels", (list,))

	for levelIndex in range(len(levels)):  # type: int
		if not isinstance(levels[levelIndex], Level):
			raise Exceptions.IncorrectTypeException(levels[levelIndex], "levels[%d]" % levelIndex, (Level,))

	levels = levels.copy()
	sortedLevels = list()

	while len(levels) != 0:
		selectedIndex = -1  # type: int

		for checkingIndex in range(len(levels)):  # type: int
			if selectedIndex == -1:
				selectedIndex = checkingIndex

			if levels[selectedIndex].Level > levels[checkingIndex].Level:
				selectedIndex = checkingIndex
				continue

		sortedLevels.append(levels[selectedIndex])
		levels.pop(selectedIndex)

	return sortedLevels

def _RemoveDuplicates (array: list) -> None:
	arrayIndex = 0  # type: int
	while arrayIndex < len(array):

		comparingArrayIndex = 0  # type: int
		while comparingArrayIndex < len(array):
			if array[arrayIndex] == array[comparingArrayIndex] and arrayIndex != comparingArrayIndex:
				array.pop(comparingArrayIndex)
				continue

			comparingArrayIndex += 1

		arrayIndex += 1

def _GetModules (path: pathlib.Path) -> list:
	modules = list()  # type: list

	try:
		if path.is_file():
			archive = zipfile.ZipFile(str(path), "r")  # type: zipfile.ZipFile

			for fileInfo in archive.filelist:  # type: zipfile.ZipInfo
				if fileInfo.filename[-1] != "/":
					file, extension = os.path.splitext(fileInfo.filename)  # type: str, str
					if extension.lower() == ".pyc":
						modules.append(file.replace("/", ".").replace("\\", "."))

			archive.close()
		elif path.is_dir():
			for directoryRoot, directoryNames, fileNames in os.walk(str(path)):  # type: str, list, list
				for fileName in fileNames:  # type: str
					filePathObject = pathlib.Path(directoryRoot).joinpath(fileName)  # type: pathlib.Path

					fileRelativePath, fileExtension = os.path.splitext(str(filePathObject.relative_to(path)))  # type: str, str

					if fileExtension.lower() == ".py":
						modules.append(fileRelativePath.replace("/", ".").replace("\\", "."))
		else:
			raise Exception("Invalid path.")
	except:
		Debug.Log("Failed to get modules in '" + Paths.StripUserDataPath(str(path)) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__)

	return modules

def _WrapFunctions () -> None:
	utils.import_modules_by_path = _ImportModulesByPathWrapper(utils.import_modules_by_path)

def _ImportModulesByPathWrapper (original: typing.Callable) -> typing.Callable:
	@wraps(original)
	def _ImportModulesByPathWrapperInternal (path):
		if len(inspect.stack()) <= 1:
			if pathlib.Path(path) in _loadedPaths:
				return 0

		return original(path)

	return _ImportModulesByPathWrapperInternal

_WrapFunctions()
