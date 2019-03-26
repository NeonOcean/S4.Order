import threading
import time
import typing

from NeonOcean.Order import Debug, This
from NeonOcean.Order.Tools import Exceptions, Types

class Timer(threading.Thread):
	def __init__ (self, interval: typing.Union[int, float], callback: typing.Callable, repeat: bool = False, isDaemon: bool = True, *callbackArgs, **callbackKwargs):
		"""
		A repeatable timer that does not drift over time. The timer is not exact and will likely be a few milliseconds late or early.
		:param interval: Type = int or float, Time in seconds until the callback value is called. It should be greater than zero.
		:type interval: int | float
		:param callback: Called after the timer is finished.
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

		self.Interval = interval  # type: float
		self.Callback = callback  # type: typing.Callable
		self._Repeat = repeat  # type: bool
		self.CallbackArgs = callbackArgs  # type: typing.Tuple[typing.Any, ...]
		self.CallbackKwargs = callbackKwargs  # type: typing.Dict[str, typing.Any]

		self._ReportedMissedTick = False

		super().__init__()

		self.daemon = isDaemon

	def run (self) -> None:
		if self._Repeat:
			lastInterval = self.Interval
			targetTime = time.time() + lastInterval  # type: float
			sleepTime = lastInterval

			while self.isAlive():
				time.sleep(sleepTime)

				if self.isAlive():
					self._CallCallback()

					sleepTime = lastInterval - (time.time() - targetTime)

					if sleepTime < 0:
						if not self._ReportedMissedTick:
							Debug.Log("A timer missed a tick; This will be the only warning though there may be more missed ticks. Interval: '" + str(self.Interval) + "' Callback: '" + Types.GetFullName(self.Callback) + "'", This.Mod.Namespace, level = Debug.LogLevels.Warning, group = This.Mod.Namespace, owner = __name__)
							self._ReportedMissedTick = True

						sleepTime = 0

					lastInterval = self.Interval
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
		threading.Thread(target = self.Callback, args = self.CallbackArgs, kwargs = self.CallbackKwargs).start()
