import types
import typing

from NeonOcean.Order import Debug, This
from NeonOcean.Order.Tools import Exceptions, Patcher, Types
from sims4.tuning import serialization

_onLoadedTuningCallbacks = list()  # type: typing.List[typing.Tuple[typing.Any, typing.Callable]]

def RegisterOnLoadedTuningCallback (module: types.ModuleType, callback: typing.Callable):
	if not isinstance(module, types.ModuleType):
		raise Exceptions.IncorrectTypeException(module, "module", (types.ModuleType,))

	if not isinstance(callback, typing.Callable):
		raise Exceptions.IncorrectTypeException(callback, "callback", (typing.Callable,))

	_onLoadedTuningCallbacks.append((module, callback))

def _Setup ():
	Patcher.Patch(serialization, "load_module_tuning", LoadModuleTuning)

# noinspection PyUnusedLocal
def LoadModuleTuning (module: types.ModuleType, tuning_filename_or_key: str) -> None:
	for callbackModule, callbackCallable in _onLoadedTuningCallbacks:  # type: types.ModuleType, typing.Callable
		try:
			if callbackModule is module:
				callbackCallable()
		except Exception as e:
			Debug.Log("Failed to call callback for 'OnLoadedTuning'. Callback: " + Types.GetFullName(callbackCallable) + " Tuned module: " + callbackModule.__name__, This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

_Setup()
