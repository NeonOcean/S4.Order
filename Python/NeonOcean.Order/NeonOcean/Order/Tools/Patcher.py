import functools
import sys
import types
import typing

import enum
from NeonOcean.Order import Debug, Events, Mods, This
from NeonOcean.Order.Tools import Exceptions, Types
from sims4 import log

_storage = list()  # type: typing.List[_Information]

class PatchTypes(enum.Int):
	After = 0
	Before = 1
	Replace = 2
	Custom = 3

class _Information:
	def __init__ (self, originalCallable: typing.Callable, targetFunction: typing.Callable, patchType: PatchTypes, permanent: bool):
		self.OriginalCallable = originalCallable  # type: typing.Callable
		# noinspection PyUnresolvedReferences
		self.OriginalModule = originalCallable.__module__  # type: str

		if isinstance(self.OriginalCallable, types.BuiltinFunctionType):
			self.OriginalName = originalCallable.__name__  # type: str
		else:
			self.OriginalName = originalCallable.__qualname__  # type: str

		if isinstance(self.OriginalCallable, types.MethodType):
			self.OriginalReloadable = False
		else:
			self.OriginalReloadable = True

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

	def OnReload (self, modules: list) -> None:
		if self.Permanent:
			return

		if self.OriginalModule in modules and self.OriginalCallable is None:
			self._ReconnectOriginal()

		if self.OriginalModule in modules and self.TargetFunction is None:
			self._ReconnectTarget()

	def _ReconnectOriginal (self) -> None:
		if self.OriginalReloadable:
			return

		try:
			currentObject = sys.modules[self.OriginalModule]  # type
			path = self.OriginalName.split(".")  # type: typing.List[str]
			callObject = None  # type: typing.Callable

			for index, attribute in enumerate(path):  # type: str
				try:
					currentObject = getattr(currentObject, attribute)
				except Exception as e:
					Debug.Log("Cannot find attribute '" + attribute + "' in '" + Types.GetFullName(currentObject), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

				if index != len(path) - 1:
					if not isinstance(currentObject, type):
						Debug.Log("Cannot reconnect original callable, path is not followable.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
						return
				else:
					if isinstance(currentObject, types.BuiltinFunctionType):
						if self.OriginalName != currentObject.__name__:
							Debug.Log("Reconnected original '" + Types.GetFullName(currentObject) + "' name no longer match. Expected name: '" + self.OriginalName + "' Reconnected name: '" + currentObject.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
							return

						callObject = currentObject
					elif isinstance(currentObject, types.FunctionType):
						if self.OriginalName != currentObject.__name__:
							Debug.Log("Reconnected original '" + Types.GetFullName(currentObject) + "' name no longer match. Expected name: '" + self.OriginalName + "' Reconnected name: '" + currentObject.__qualname__ + "'.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
							return

						callObject = currentObject
					else:
						Debug.Log("Reconnected original '" + Types.GetFullName(currentObject) + "' is no longer a function or built-in function.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
						return

			if callObject is not None:
				self.OriginalCallable = callObject
				setattr(self.OriginalModule, self.OriginalName, _Wrapper(self))
		except Exception as e:
			Debug.Log("Failed to reconnect patch original.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
			return

	def _ReconnectTarget (self) -> None:
		try:
			currentObject = sys.modules[self.TargetModule]
			path = self.TargetName.split(".")  # type: typing.List[str]
			callObject = None  # type: typing.Callable

			for index, attribute in enumerate(path):  # type: str
				try:
					currentObject = getattr(currentObject, attribute)
				except Exception as e:
					Debug.Log("Cannot find attribute '" + attribute + "' in '" + Types.GetFullName(currentObject), This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

				if index != len(path) - 1:
					if not isinstance(currentObject, type):
						Debug.Log("Cannot reconnect target function path is not followable.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
						return
				else:
					if isinstance(currentObject, types.BuiltinFunctionType):
						if self.TargetName != currentObject.__name__:
							Debug.Log("Reconnected target '" + Types.GetFullName(currentObject) + "' name no longer match. Expected name: '" + self.TargetName + "' Reconnected name: '" + currentObject.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
							return
						callObject = currentObject
					elif isinstance(currentObject, types.FunctionType):
						if self.TargetName != currentObject.__name__:
							Debug.Log("Reconnected target '" + Types.GetFullName(currentObject) + "' name no longer match. Expected name: '" + self.TargetName + "' Reconnected name: '" + currentObject.__qualname__ + "'.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
							return
						callObject = currentObject
					else:
						Debug.Log("Reconnected target '" + Types.GetFullName(currentObject) + "' is no longer a built-in function or function.", This.Mod.Namespace, Debug.LogLevels.Error, group = This.Mod.Namespace, owner = __name__)
						return

			if callObject is not None:
				self.TargetFunction = callObject
		except Exception as e:
			Debug.Log("Failed to reconnect patch target.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
			return

def OnUnload (mod: Mods.Mod, exiting: bool) -> None:
	if exiting:
		return

	for patchInfo in _storage:  # type: _Information
		patchInfo.OnUnload(mod.Modules)

def OnReload (mod: Mods.Mod) -> None:
	for patchInfo in _storage:  # type: _Information
		patchInfo.OnReload(mod.Modules)

def Decorator (originalObject, originalCallableName: str, patchType: PatchTypes = PatchTypes.After, permanent: bool = False) -> typing.Callable:
	"""
	Combine a function with another function or method into one replacing the original. The target can only be a function or a built in function.
	:param originalObject: The object the original callable resides in.
	:param originalCallableName: The name of the callable to be combined, Can be a reference to a function, built in function, or method.
	:type originalCallableName: str
	:param patchType: Controls when the original callable is called. A value of PatchTypes.Custom requires that the target callable take an extra argument
					  for its first, The extra argument will be a reference to the original callable.
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
	Combine a function with another function or method into one replacing the original. The target can only be a function or a built in function.
	:param originalObject: The object the original callable resides in.
	:param originalCallableName: The name of the callable to be combined, Can be a reference to a function, built in function, or method.
	:type originalCallableName: str
	:param targetFunction: The function object that will be combined with the original.
	:type targetFunction: typing.Callable
	:param patchType: Controls when the original callable is called. A value of PatchTypes.Custom requires that the target function take an extra argument
					  for its first, The extra argument will be a reference to the original callable.
	:type patchType: PatchTypes
	:param permanent: Whether or not the patch will be disabled if the mod the patching function resides in is unloaded.
	:type permanent: bool
	:return: Returns the target callable.
	:rtype: typing.Callable
	"""

	if originalObject is None:
		raise TypeError("originalObject cannot be none.")

	if not isinstance(originalCallableName, str):
		raise Exceptions.IncorrectTypeException(originalCallableName, "originalCallableName", (str,))

	if not isinstance(targetFunction, types.FunctionType) and not isinstance(targetFunction, types.BuiltinFunctionType):
		raise Exceptions.IncorrectTypeException(targetFunction, "targetFunction", (types.FunctionType, types.BuiltinFunctionType))

	if not isinstance(patchType, PatchTypes):
		raise Exceptions.IncorrectTypeException(patchType, "patchType", (PatchTypes,))

	originalCallable = getattr(originalObject, originalCallableName)  # type: typing.Callable

	if originalCallable is None:
		raise Exception("Cannot find attribute named '" + originalCallableName + "' in '" + Types.GetFullName(originalObject) + "'.")

	if not isinstance(originalCallable, types.BuiltinFunctionType) and not isinstance(originalCallable, types.FunctionType) and not isinstance(originalCallable, types.MethodType):
		raise Exception("Attribute '" + originalCallableName + "' in '" + Types.GetFullName(originalObject) + "' is not a function, built-in function or a method.")

	information = _Information(originalCallable, targetFunction, patchType, permanent)  # type: _Information
	setattr(originalObject, originalCallableName, _Wrapper(information))
	_storage.append(information)

def _Setup () -> None:
	Events.RegisterOnModUnload(OnUnload)
	Events.RegisterOnModReload(OnReload)

def _Wrapper (information: _Information) -> typing.Callable:
	@functools.wraps(information.OriginalCallable)
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
				information.TargetFunction(*args, **kwargs)
			except Exception as e:
				_TargetException(e)

				if information.OriginalCallable is not None:
					return information.OriginalCallable(*args, **kwargs)
				else:
					raise Exception("Cannot call original callable '" + ("" if information.OriginalModule is None else information.OriginalModule + ".") + information.OriginalName + "' it is None.")
		else:
			if information.OriginalCallable is not None:
				return information.OriginalCallable(*args, **kwargs)
			else:
				raise Exception("Cannot call original callable '" + ("" if information.OriginalModule is None else information.OriginalModule + ".") + information.OriginalName + "' it is None.")

	def _Custom (*args, **kwargs):
		if information.TargetFunction is not None:
			try:
				information.TargetFunction(information.OriginalCallable, *args, **kwargs)
			except Exception as e:
				_TargetException(e)
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

	return _WrapperInternal

_Setup()
