from __future__ import annotations

import collections
import enum_lib
import inspect
import types
import typing

from NeonOcean.S4.Order import Debug, LoadingEvents, This
from NeonOcean.S4.Order.Tools import Exceptions, Types
from sims4 import log

_storage = list()  # type: typing.List[_Information]

class PatchTypes(enum_lib.IntEnum):
	After = 0  # type: PatchTypes
	Before = 1  # type: PatchTypes
	Replace = 2  # type: PatchTypes
	Custom = 3  # type: PatchTypes

class _Information:
	def __init__ (self, originalCallable: typing.Callable, targetFunction: typing.Callable, patchType: PatchTypes, permanent: bool):
		self.OriginalCallable = originalCallable  # type: typing.Callable
		# noinspection PyUnresolvedReferences
		self.OriginalModule = originalCallable.__module__  # type: str

		if isinstance(self.OriginalCallable, types.BuiltinFunctionType):
			self.OriginalName = originalCallable.__name__  # type: str
		else:
			self.OriginalName = originalCallable.__qualname__  # type: str

		self.TargetFunction = targetFunction  # type: typing.Callable
		# noinspection PyUnresolvedReferences
		self.TargetModule = targetFunction.__module__  # type: str

		if isinstance(self.TargetFunction, types.BuiltinFunctionType):
			self.TargetName = targetFunction.__name__  # type: str
		else:
			self.TargetName = targetFunction.__qualname__  # type: str

		self.PatchType = patchType  # type: PatchTypes
		self.Permanent = permanent  # type: bool

	def OnUnload (self, modules: list) -> None:
		if self.Permanent:
			return

		for module in modules:  # type: str
			if module == self.TargetModule:
				self.TargetFunction = None
			elif module == self.OriginalModule:
				self.OriginalCallable = None

# noinspection PyUnusedLocal
def OnUnload (owner: typing.Any, eventArguments: typing.Optional[LoadingEvents.ModUnloadedEventArguments]) -> None:
	if eventArguments is None:
		return

	if eventArguments.Exiting:
		return

	for patchInfo in _storage:  # type: _Information
		patchInfo.OnUnload(eventArguments.Mod.Modules)

def Decorator (originalObject, originalCallableName: str, patchType: PatchTypes = PatchTypes.After, permanent: bool = False) -> typing.Callable:
	"""
	Combine a function with another function or method, the original callable located in the original object will then be replaced by the patch automatically.
	The decorator can only be attached to a function or a built in function.
	:param originalObject: The object the original callable resides in.
	:type originalObject: typing.Any
	:param originalCallableName: The name of the callable to be combined, Can be a reference to a function, built in function, or method.
	:type originalCallableName: str
	:param patchType: Controls when the original callable is called. A value of PatchTypes.Custom requires that the target callable take an extra argument
					  in the first argument position. The extra argument will be a reference to the original callable.
	:type patchType: PatchTypes
	:param permanent: Whether or not the patch will be disabled if the mod the patching function resides in is unloaded.
	:type permanent: bool
	:return: Returns the target callable.
	:rtype: typing.Callable
	"""

	def _DecoratorInternal (targetFunction: typing.Callable) -> typing.Callable:
		"""
		:param targetFunction: The function object that will be combined with the original.
		:type targetFunction: typing.Callable
		"""

		Patch(originalObject, originalCallableName, targetFunction, patchType = patchType, permanent = permanent)
		return targetFunction

	return _DecoratorInternal

def Patch (originalObject: typing.Any, originalCallableName: str, targetFunction: typing.Callable, patchType: PatchTypes = PatchTypes.After, permanent: bool = False) -> None:
	"""
	Combine a function with another function or method, the original callable located in the original object will then be replaced by the patch automatically.
	:param originalObject: The object the original callable resides in.
	:type originalObject: typing.Any
	:param originalCallableName: The name of the callable to be combined, Can be a reference to a function, built in function, or method.
	:type originalCallableName: str
	:param targetFunction: The function object that will be combined with the original. This can only be a function or a built in function.
	:type targetFunction: typing.Callable
	:param patchType: Controls when the original callable is called. A value of PatchTypes.Custom requires that the target function take an extra argument
					  in the first argument position. The extra argument will be a reference to the original callable.
	:type patchType: PatchTypes
	:param permanent: Whether or not the patch will be disabled if the module the patching function resides in is unloaded.
	:type permanent: bool
	"""

	if originalObject is None:
		raise TypeError("originalObject cannot be none.")

	if not isinstance(originalCallableName, str):
		raise Exceptions.IncorrectTypeException(originalCallableName, "originalCallableName", (str,))

	originalCallable = getattr(originalObject, originalCallableName)  # type: typing.Callable

	if originalCallable is None:
		raise Exception("Cannot find attribute named '" + originalCallableName + "' in '" + Types.GetFullName(originalObject) + "'.")

	patchedFunction = PatchDirectly(originalCallable, targetFunction, patchType = patchType, permanent = permanent)
	setattr(originalObject, originalCallableName, patchedFunction)

def PatchDirectly (originalCallable: typing.Callable, targetFunction: typing.Callable, patchType: PatchTypes = PatchTypes.After, permanent: bool = False) -> typing.Callable:
	"""
	Combine a function with another function or method, the patched function will be returned upon completion.
	:param originalCallable: The original callable object to be patched.
	:param targetFunction: The function object that will be combined with the original. This can only be a function or a built in function.
	:type targetFunction: typing.Callable
	:param patchType: Controls when the original callable is called. A value of PatchTypes.Custom requires that the target function take an extra argument
					  in the first argument position. The extra argument will be a reference to the original callable.
	:type patchType: PatchTypes
	:param permanent: Whether or not the patch will be disabled if the module the patching function resides in is unloaded.
	:type permanent: bool
	:return: Returns the patched function.
	:rtype: typing.Callable
	"""

	if not isinstance(originalCallable, types.BuiltinFunctionType) and not isinstance(originalCallable, types.FunctionType) and not isinstance(originalCallable, types.MethodType):
		raise Exception(Types.GetFullName(originalCallable) + " is not a function, built-in function or a method.")

	if not isinstance(targetFunction, types.FunctionType) and not isinstance(targetFunction, types.BuiltinFunctionType):
		raise Exceptions.IncorrectTypeException(targetFunction, "targetFunction", (types.FunctionType, types.BuiltinFunctionType))

	if not isinstance(patchType, PatchTypes):
		raise Exceptions.IncorrectTypeException(patchType, "patchType", (PatchTypes,))

	if not isinstance(permanent, bool):
		raise Exceptions.IncorrectTypeException(permanent, "permanent", (bool,))

	information = _Information(originalCallable, targetFunction, patchType, permanent)  # type: _Information
	patchedFunction = _Wrapper(information)
	_storage.append(information)

	return patchedFunction

def _Setup () -> None:
	LoadingEvents.ModUnloadedEvent += OnUnload

def _Wrapper (information: _Information) -> typing.Callable:
	def _WrapperInternal (*args, **kwargs):
		if information.PatchType == PatchTypes.After:
			return _After(*args, **kwargs)
		elif information.PatchType == PatchTypes.Before:
			return _Before(*args, **kwargs)
		elif information.PatchType == PatchTypes.Replace:
			return _Replace(*args, **kwargs)
		elif information.PatchType == PatchTypes.Custom:
			return _Custom(*args, **kwargs)

	def _After (*args, **kwargs):
		if information.OriginalCallable is not None:
			returnObject = information.OriginalCallable(*args, **kwargs)
		else:
			raise Exception("Cannot call original callable '" + ("" if information.OriginalModule is None else information.OriginalModule + ".") + information.OriginalName + "' it is None.")

		if information.TargetFunction is not None:
			try:
				information.TargetFunction(*args, **kwargs)
			except Exception as e:
				_TargetException(e)

		return returnObject

	def _Before (*args, **kwargs):
		if information.TargetFunction is not None:
			try:
				information.TargetFunction(*args, **kwargs)
			except Exception as e:
				_TargetException(e)

		if information.OriginalCallable is not None:
			return information.OriginalCallable(*args, **kwargs)
		else:
			raise Exception("Cannot call original callable '" + ("" if information.OriginalModule is None else information.OriginalModule + ".") + information.OriginalName + "' it is None.")

	def _Replace (*args, **kwargs):
		if information.TargetFunction is not None:
			try:
				return information.TargetFunction(*args, **kwargs)
			except Exception as e:
				_TargetException(e)
				raise e
		else:
			if information.OriginalCallable is not None:
				return information.OriginalCallable(*args, **kwargs)
			else:
				raise Exception("Cannot call original callable '" + ("" if information.OriginalModule is None else information.OriginalModule + ".") + information.OriginalName + "' it is None.")

	def _Custom (*args, **kwargs):
		if information.TargetFunction is not None:
			try:
				return information.TargetFunction(information.OriginalCallable, *args, **kwargs)
			except Exception as e:
				_TargetException(e)
				raise e
		else:
			if information.OriginalCallable is not None:
				return information.OriginalCallable(*args, **kwargs)
			else:
				raise Exception("Cannot call original callable '" + ("" if information.OriginalModule is None else information.OriginalModule + ".") + information.OriginalName + "' it is None.")

	def _TargetException (exception: BaseException) -> None:
		originalCallableFullName = Types.GetFullName(information.OriginalCallable)  # type: str
		if originalCallableFullName == Types.GetFullName(log.exception):
			Debug.Log("Failed to call target function '" + Types.GetFullName(information.TargetFunction) + "'. Original callable: '" + originalCallableFullName + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = exception, logToGame = False)
			information.OriginalCallable(This.Mod.Namespace, "Failed to call target function '" + Types.GetFullName(information.TargetFunction) + "'. Original callable: '" + originalCallableFullName + "'.", exc = exception)
		else:
			if originalCallableFullName == Types.GetFullName(log.Logger.exception):
				Debug.Log("Failed to call target function '" + Types.GetFullName(information.TargetFunction) + "'. Original callable: '" + originalCallableFullName + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = exception, logToGame = False)
				information.OriginalCallable(log.Logger(This.Mod.Namespace), "Failed to call target function '" + Types.GetFullName(information.TargetFunction) + "'. Original callable: '" + originalCallableFullName + "'.", exc = exception)
			else:
				Debug.Log("Failed to call target function '" + Types.GetFullName(information.TargetFunction) + "'. Original callable: '" + originalCallableFullName + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = exception)

	return _CreateDummyWrapper(information.OriginalCallable, _WrapperInternal)

def _CreateDummyWrapper (originalCallable: typing.Callable, targetCallable: typing.Callable) -> typing.Callable:
	"""
	Create a dummy function that looks more like the original but funnels the arguments through the target.
	"""

	# noinspection SpellCheckingInspection
	dummyFormattingTemplate = \
		"import functools\n" \
		"\n" \
		"@functools.wraps(originalCallable)\n" \
		"def DummyWrapper ({Arguments}):\n" \
		"	return targetCallable({CallArguments})"

	originalSignature = inspect.signature(originalCallable)  # type: inspect.Signature

	originalArgumentsString = ""
	targetCallArgumentsString = ""

	originalArguments = originalSignature.parameters  # type: collections.OrderedDict
	originalDefaults = dict()  # type: typing.Dict[str, typing.Any]

	for originalArgument in originalArguments.values():  # type: inspect.Parameter
		originalArgumentString = originalArgument.name
		targetCallArgumentString = originalArgument.name

		if originalArgument.kind == originalArgument.KEYWORD_ONLY:
			targetCallArgumentString = targetCallArgumentString + " = " + targetCallArgumentString
		elif originalArgument.kind == originalArgument.VAR_POSITIONAL:
			originalArgumentString = "*" + originalArgumentString
			targetCallArgumentString = "*" + targetCallArgumentString
		elif originalArgument.kind == originalArgument.VAR_KEYWORD:
			originalArgumentString = "**" + originalArgumentString
			targetCallArgumentString = "**" + targetCallArgumentString

		if originalArgument.default is not inspect.Signature.empty:
			originalDefaults[originalArgument.name] = originalArgument.default
			originalArgumentString += " = originalDefaults['" + originalArgument.name + "']"

		if originalArgumentsString != "":
			originalArgumentString = ", " + originalArgumentString

		if targetCallArgumentsString != "":
			targetCallArgumentString = ", " + targetCallArgumentString

		originalArgumentsString += originalArgumentString
		targetCallArgumentsString += targetCallArgumentString

	dummyFormatting = {
		"Name": originalCallable.__name__,
		"Arguments": originalArgumentsString,
		"CallArguments": targetCallArgumentsString
	}

	dummyContainerGlobals = {
		"originalCallable": originalCallable,
		"originalDefaults": originalDefaults,
		"targetCallable": targetCallable
	}

	dummyContainerLocals = dict()

	dummyExecutionString = dummyFormattingTemplate.format_map(dummyFormatting)  # type: str
	exec(dummyExecutionString, dummyContainerGlobals, dummyContainerLocals)
	dummyWrapper = dummyContainerLocals["DummyWrapper"]  # type: typing.Callable

	return dummyWrapper

_Setup()
