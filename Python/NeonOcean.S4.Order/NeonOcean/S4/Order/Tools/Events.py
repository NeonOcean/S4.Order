from __future__ import annotations

import inspect
import typing
import weakref

from NeonOcean.S4.Order.Tools import Exceptions

class EventArguments:
	pass

class _EventIterator:
	def __init__ (self, callbackReferences: typing.List[typing.Union[weakref.WeakMethod, weakref.ReferenceType]]):
		self._callbackReferences = callbackReferences  # type: typing.List[typing.Callable]
		self._currentIndex = 0  # type: int

	def __iter__ (self):
		return self

	def __next__ (self) -> typing.Callable:
		if self._currentIndex < len(self._callbackReferences):
			callback = self._callbackReferences[self._currentIndex]()  # type: typing.Callable

			if callback is None:
				self._callbackReferences.pop(self._currentIndex)
				return self.__next__()

			self._currentIndex += 1
			return callback
		else:
			raise StopIteration()

class EventHandler:
	"""
	Use this to create events. Add and remove callbacks with the plus and minus operator, call this object to invoke all callbacks, iterate through callbacks
	to invoke them in special ways by using this object with a for loop. All callbacks are tracked with weak references, its not necessary to remove callbacks
	before letting a callback's owner be collected by the garbage collector.

	Event callbacks should take two parameters, firstly the object that owns the event and secondly the event arguments, preferably an object inheriting from
	the 'EventArguments' class located in this module.
	"""

	def __init__ (self):
		self._callbackReferences = list()  # type: typing.List[typing.Union[weakref.WeakMethod, weakref.ReferenceType]]

	def __add__ (self, other: typing.Callable):
		if not callable(other):
			raise Exceptions.IncorrectTypeException(other, "addition", ("Callable",))

		if inspect.ismethod(other):
			otherWeakRef = weakref.WeakMethod(other)  # type: typing.Union[weakref.WeakMethod, weakref.ReferenceType]
		else:
			otherWeakRef = weakref.ref(other)  # type: typing.Union[weakref.WeakMethod, weakref.ReferenceType]

		newEventHandler = EventHandler()
		newCallbackReferences = list(self._callbackReferences)
		newCallbackReferences.append(otherWeakRef)
		newEventHandler._callbackReferences = newCallbackReferences

		return newEventHandler

	def __sub__ (self, other: typing.Callable):
		if not callable(other):
			raise Exceptions.IncorrectTypeException(other, "subtraction", ("Callable",))

		newEventHandler = EventHandler()
		newCallbackReferences = list(self._callbackReferences)

		callbackReferenceIndex = 0
		while callbackReferenceIndex < len(newCallbackReferences):
			callback = newCallbackReferences[callbackReferenceIndex]()  # type: typing.Callable

			if callback is None or callback is other:
				newCallbackReferences.pop(callbackReferenceIndex)
				continue

			callbackReferenceIndex += 1

		newEventHandler._callbackReferences = newCallbackReferences

		return newEventHandler

	def __contains__ (self, item: typing.Callable) -> bool:
		if not callable(item):
			raise Exceptions.IncorrectTypeException(item, "item", ("Callable",))

		return item in self.Callbacks

	def __sizeof__ (self) -> int:
		return len(self.Callbacks)

	def __iter__ (self) -> _EventIterator:
		return _EventIterator(self._callbackReferences)

	def __call__ (self, owner: typing.Any, eventArguments: EventArguments) -> None:
		self.Invoke(owner, eventArguments)

	def __copy__ (self):
		newEventHandler = EventHandler()
		newCallbackReferences = list()

		for callbackReference in self._callbackReferences:
			callback = callbackReference()

			if callback is None:
				continue

			if inspect.ismethod(callback):
				newCallbackReference = weakref.WeakMethod(callback)  # type: typing.Union[weakref.WeakMethod, weakref.ReferenceType]
			else:
				newCallbackReference = weakref.ref(callback)  # type: typing.Union[weakref.WeakMethod, weakref.ReferenceType]

			newCallbackReferences.append(newCallbackReference)

		newEventHandler._callbackReferences = newCallbackReferences

		return newEventHandler

	@property
	def Callbacks (self) -> typing.List[typing.Callable]:
		"""
		Get all event callbacks subscribed to this event.
		"""

		callbacks = list()

		callbackReferenceIndex = 0
		while callbackReferenceIndex < len(self._callbackReferences):
			callback = self._callbackReferences[callbackReferenceIndex]()

			if callback is None:
				self._callbackReferences.pop(callbackReferenceIndex)
				continue

			callbacks.append(callback)
			callbackReferenceIndex += 1

		return callbacks

	def Invoke (self, owner: typing.Any, eventArguments: typing.Optional[EventArguments]) -> None:
		"""
		Invoke this event. Exceptions raised by any callback will not be handled by this method, they will fall through.
		:param owner: The object that owns this event. This will be passed to callbacks as the first parameter.
		:param eventArguments: The arguments for this event.
		:type eventArguments: EventArguments | None
		"""

		if not isinstance(eventArguments, EventArguments) and eventArguments is not None:
			raise Exceptions.IncorrectTypeException(eventArguments, "eventArguments", (EventArguments, None))

		for callback in self:  # type: typing.Callable
			callback(owner, eventArguments)
