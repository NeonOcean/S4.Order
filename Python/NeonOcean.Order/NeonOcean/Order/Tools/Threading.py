import threading
import typing
from functools import wraps

from NeonOcean.Order.Tools import Types

class SimultaneousCallException(Exception):
	def __init__ (self, targetFunction: typing.Callable = None):
		self.TargetFunction = targetFunction  # type: typing.Optional[typing.Callable]
		pass

	def __str__ (self):
		if self.TargetFunction is not None:
			return "Failed to invoke the function at '" + Types.GetFullName(self.TargetFunction) + "' as it was already active in another thread."
		else:
			return "Failed to invoke a function as it was already active in another thread."

def NotThreadSafe (targetFunction: typing.Callable = None, raiseException: bool = False, returnValue: typing.Any = None) -> typing.Callable:
	"""
	A decorator that prevents a function from being called simultaneously from different threads.
	:param targetFunction: The target function, this argument should be automatically filled when using NotThreadSafe as a decorator.
	:type targetFunction: Typing.Callable
	:param raiseException: Whether or not an SimultaneousCallException will be raise when another thread is already calling the target function.
	:type raiseException: bool
	:param returnValue: A value the function will return when it is already busy in another thread.
	:type returnValue: Typing.Any
	:return:
	"""

	requestingThreads = list()  # type: typing.List[int]

	def NotThreadSafeInternal (internalTargetFunction: typing.Callable) -> typing.Callable:

		@wraps(internalTargetFunction)
		def TargetFunctionWrapper (*args, **kwargs) -> typing.Any:
			nonlocal requestingThreads

			currentThreadIdentifier = threading.current_thread().ident  # type: int

			assert isinstance(currentThreadIdentifier, int)

			requestingThreads.append(currentThreadIdentifier)

			if requestingThreads[0] != currentThreadIdentifier:
				if raiseException:
					requestingThreads.remove(currentThreadIdentifier)
					raise SimultaneousCallException(targetFunction = internalTargetFunction)
				else:
					requestingThreads.remove(currentThreadIdentifier)
					return returnValue

			try:
				internalTargetFunction(*args, **kwargs)
			finally:
				requestingThreads.remove(currentThreadIdentifier)

		return TargetFunctionWrapper

	if targetFunction is not None:
		return NotThreadSafeInternal(targetFunction)

	return NotThreadSafeInternal
