from __future__ import annotations

import types

def GetFullName (obj) -> str:
	"""
	:param obj: Takes builtin function, function, method, type, or object.
	:return: The full name of a built-in function, function, method, type or object's type, including the module.
	"""

	if isinstance(obj, types.BuiltinFunctionType):
		return _GetBuiltinFunctionFullName(obj)
	if isinstance(obj, types.FunctionType):
		return _GetFunctionFullName(obj)
	if isinstance(obj, types.MethodType):
		return _GetMethodFullName(obj)
	if isinstance(obj, type):
		return _GetTypeFullName(obj)
	else:
		return _GetTypeFullName(type(obj))

def _GetBuiltinFunctionFullName (obj: types.BuiltinFunctionType) -> str:
	if obj.__module__ is not None:
		return obj.__module__ + "." + obj.__name__
	else:
		return obj.__name__

def _GetFunctionFullName (obj: types.FunctionType) -> str:
	if obj.__module__ is not None:
		return obj.__module__ + "." + obj.__qualname__
	else:
		return obj.__qualname__

def _GetMethodFullName (obj: types.MethodType) -> str:
	if obj.__module__ is not None:
		return obj.__module__ + "." + obj.__func__.__qualname__
	else:
		return obj.__func__.__qualname__

def _GetTypeFullName (obj: type) -> str:
	if obj.__module__ is not None:
		return obj.__module__ + "." + obj.__qualname__
	else:
		return obj.__qualname__
