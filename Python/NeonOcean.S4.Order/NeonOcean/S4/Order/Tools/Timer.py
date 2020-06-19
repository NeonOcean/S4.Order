from __future__ import annotations

import threading
import time
import typing

from NeonOcean.S4.Order import Debug, This
from NeonOcean.S4.Order.Tools import Exceptions, Types

class Timer(threading.Thread):
	def __init__ (self, interval: typing.Union[float, int], callback: typing.Callable, repeat: bool = False, isDaemon: bool = True, *callbackArgs, **callbackKwargs):
		"""
		A repeatable timer that does not drift over time. The timer is not exact and will likely be a few milliseconds late or early.
		It is recommended to not set the timer's interval to be shorter than the time the callback function will take to run.
		:param interval: Type = int or float, Time in seconds until the callback value is called. It should be greater than zero.
		:type interval: float | int
		:param callback: Called after the timer is finished. Callbacks will be run in succession, if one cannot finish before the next one is queued by the timer
		a backlog will develop.
		:type callback: typing.Callable
		:param repeat: Whether or not the timer will restart after finishing.
		:type repeat: bool
		:param isDaemon: Timer thread will automatically be stopped when the main thread finishes if this is set to True otherwise the main thread will wait.
		:type isDaemon: bool
		:param callbackArgs: Arguments the callback value is called with.
		:type callbackArgs: tuple | None
		:param callbackKwargs: Arguments the callback value is called with.
		:type callbackKwargs: dict | None
		"""

		if not isinstance(interval, int) and not isinstance(interval, float):
			raise Exceptions.IncorrectTypeException(interval, "interval", (float, int))

		if interval <= 0:
			raise ValueError("Interval value must be greater than 0.")

		if not isinstance(callback, typing.Callable):
			raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

		if not isinstance(isDaemon, bool):
			raise Exceptions.IncorrectTypeException(isDaemon, "isDaemon", (bool,))

		if not isinstance(repeat, bool):
			raise Exceptions.IncorrectTypeException(repeat, "repeat", (bool,))

		if callbackArgs is None:
			callbackArgs = tuple()

		if not isinstance(callbackArgs, tuple):
			raise Exceptions.IncorrectTypeException(callbackArgs, "callbackArgs", (tuple,))

		if callbackKwargs is None:
			callbackKwargs = dict()

		if not isinstance(callbackKwargs, dict):
			raise Exceptions.IncorrectTypeException(callbackKwargs, "callbackKwargs", (dict,))

		super().__init__()

		self.Interval = interval  # type: float
		self.Callback = callback  # type: typing.Callable

		self.daemon = isDaemon

		self.CallbackArgs = callbackArgs  # type: typing.Tuple[typing.Any, ...]
		self.CallbackKwargs = callbackKwargs  # type: typing.Dict[str, typing.Any]

		self._repeat = repeat  # type: bool

		self._reportedMissedTick = False  # type: bool

		self._callbackThread = _TimerCallbackThread(self)  # type: _TimerCallbackThread
		self._callbackThread.start()

	@property
	def Interval (self) -> float:
		return self._interval

	@Interval.setter
	def Interval (self, value):
		if value <= 0:
			raise ValueError("Interval value must be greater than 0.")

		self._interval = value

	def run (self) -> None:
		if self._repeat:
			lastInterval = self.Interval  # type: float
			sleepStartTime = time.time()  # type: float
			targetTime = sleepStartTime + lastInterval  # type: float
			sleepTime = lastInterval  # type: float

			while self.isAlive():
				time.sleep(sleepTime)

				if self.isAlive():
					self._CallCallback()

					sleepEndTime = time.time()  # type: float

					sleepTimeOversleep = sleepEndTime - targetTime  # type: float

					if self.Interval != lastInterval:
						sleepTimeOversleep = max(min(sleepTimeOversleep, self.Interval), -self.Interval)

					sleepTime = self.Interval - sleepTimeOversleep  # type: float

					if sleepTime < 0:
						if not self._reportedMissedTick:
							actualSleepTime = sleepEndTime - sleepStartTime  # type: float

							Debug.Log("A timer slept over an interval. This will be the only warning though there may be more missed ticks. Interval: '" + str(self.Interval) + "' Actual Interval: '" + str(actualSleepTime) + "' Callback: '" + Types.GetFullName(self.Callback) + "'", This.Mod.Namespace, level = Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
							self._reportedMissedTick = True

						sleepTime = 0

					lastInterval = self.Interval
					sleepStartTime = time.time()  # type: float
					targetTime += lastInterval
		else:
			if self.isAlive():
				time.sleep(self.Interval)

				if self.isAlive():
					self._CallCallback()

	def Stop (self) -> None:
		# noinspection PyUnresolvedReferences
		self._stop()

	def _CallCallback (self) -> None:
		self._callbackThread.QueueCallback(self.Callback, self.CallbackArgs, self.CallbackKwargs)

		try:
			if not self._callbackThread.isAlive():
				self._callbackThread.start()
		except Exception:
			self._callbackThread = _TimerCallbackThread(self)
			self._callbackThread.QueueCallback(self.Callback, self.CallbackArgs, self.CallbackKwargs)
			self._callbackThread.start()

class _TimerCallbackThread(threading.Thread):
	def __init__ (self, parentTimer: Timer):
		super().__init__()

		self._parentTimer = parentTimer  # type: Timer
		self._queuedCallbacks = list()  # type: typing.List[tuple]

		self._reportedBacklog = False  # type: bool

	def run (self) -> None:
		while True:
			if not self.isAlive() or self._parentTimer is None or not self._parentTimer.isAlive():
				break

			if self.daemon != self._parentTimer.daemon:
				self.daemon = self._parentTimer.daemon

			currentlyQueued = len(self._queuedCallbacks)  # type: int

			if currentlyQueued == 0:
				time.sleep(0.05)
			else:
				callback = self._queuedCallbacks[0][0]  # type: typing.Callable
				callbackArguments = self._queuedCallbacks[0][1]  # type: tuple
				callbackKeywordArguments = self._queuedCallbacks[0][2]  # type: dict

				try:
					callback(*callbackArguments, **callbackKeywordArguments)
				except Exception:
					Debug.Log("Failed to call a timer callback. Callback '" + Types.GetFullName(callback) + "'", This.Mod.Namespace, level = Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)

				self._queuedCallbacks.pop(0)

				if currentlyQueued >= 10:
					if not self._reportedBacklog:
						Debug.Log("A timer's callback thread has developed a backlog. This might mean callbacks are being added faster than they can be dealt with. Last Callback: '" + Types.GetFullName(callback) + "'", This.Mod.Namespace, level = Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
						self._reportedBacklog = True

	def Stop (self) -> None:
		# noinspection PyUnresolvedReferences
		self._stop()

	def QueueCallback (self, callback: typing.Callable, callbackArgs, callbackKwargs) -> None:
		self._queuedCallbacks.append((callback, callbackArgs, callbackKwargs))
