import sys
import types

from NeonOcean.Order import Information

def CreateGlobalModule () -> None:
	globalModule = sys.modules.get(Information.GlobalNamespace)

	if globalModule is None:
		sys.modules[Information.GlobalNamespace] = types.ModuleType(Information.GlobalNamespace)

def GetModule (relativeModuleName: str):
	CreateGlobalModule()

	moduleName = Information.GlobalNamespace + "." + relativeModuleName  # type: str
	module = sys.modules.get(moduleName)  # type: types.ModuleType

	if module is None:
		module = types.ModuleType(moduleName)
		sys.modules[moduleName] = module

	return module

def SetAttributeValue (relativeModuleName: str, attributeName: str, value) -> None:
	CreateGlobalModule()

	moduleName = Information.GlobalNamespace + "." + relativeModuleName  # type: str
	module = sys.modules.get(moduleName)  # type: types.ModuleType

	if module is None:
		module = types.ModuleType(moduleName)
		sys.modules[moduleName] = module

	setattr(module, attributeName, value)

def GetAttributeValue (relativeModuleName: str, attributeName: str):
	CreateGlobalModule()

	moduleName = Information.GlobalNamespace + "." + relativeModuleName  # type: str
	module = sys.modules.get(moduleName)  # type: types.ModuleType

	if module is None:
		module = types.ModuleType(moduleName)
		sys.modules[moduleName] = module

	return getattr(module, attributeName)

def HasAttribute (relativeModuleName: str, attributeName: str) -> bool:
	CreateGlobalModule()

	moduleName = Information.GlobalNamespace + "." + relativeModuleName  # type: str
	module = sys.modules.get(moduleName)  # type: types.ModuleType

	if module is None:
		module = types.ModuleType(moduleName)
		sys.modules[moduleName] = module

	return hasattr(module, attributeName)

CreateGlobalModule()
