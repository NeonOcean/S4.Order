import datetime
import os
import sys
import threading
import traceback
import types
import typing

import singletons
from NeonOcean.Order import DebugShared, Paths, This
from NeonOcean.Order.DebugShared import LogLevels, Report
from NeonOcean.Order.Tools import Exceptions
from sims4 import log

_logger = None  # type: Logger

class Logger(DebugShared.Logger):
	_globalLoggingNamespaceCounts = "LoggingNamespaceCounts"  # type: str
	_globalIncreaseNamespaceLoggingCount = "IncreaseNamespaceLoggingCount"  # type: str

	def __init__ (self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if not hasattr(self.DebugGlobal, self._globalLoggingNamespaceCounts):
			setattr(self.DebugGlobal, self._globalLoggingNamespaceCounts, dict())

		def _CreateIncreaseNamespaceLoggingCount () -> None:
			increaseLock = threading.Lock()

			def IncreaseLoggingNamespaceCount (key: str) -> None:
				increaseLock.acquire()
				loggingNamespaceCounts = getattr(self.DebugGlobal, self._globalLoggingNamespaceCounts)  # type:  typing.Dict[str, int]

				if not key in loggingNamespaceCounts:
					loggingNamespaceCounts[key] = 1
				else:
					loggingNamespaceCounts[key] += 1

				increaseLock.release()

			if not hasattr(self.DebugGlobal, self._globalIncreaseNamespaceLoggingCount):
				setattr(self.DebugGlobal, self._globalIncreaseNamespaceLoggingCount, IncreaseLoggingNamespaceCount)

		_CreateIncreaseNamespaceLoggingCount()

	def Log (self, message, namespace: typing.Optional[str], level: LogLevels,
			 group: str = None, owner: str = None, exception: BaseException = None,
			 logStack: bool = False, frame: types.FrameType = None, logToGame: bool = True,
			 retryOnError: bool = True) -> None:
		"""
		Logs a message even if no mod has enabled the game's logging system. It will also report the log to the module 'sims4.log' by default.
		Logs will be writen to '<Sims4 user data path>/NeonOcean/Debug/Mods/<Namespace>/<Game start time>/Log.xml'. This system is not recommended for
		logging in high volume.
		:param message: The message is converted to a string with str(message) if it isn't one already.
		:param namespace: The namespace or mod the log is coming from, it can Be None. Logs will be separated in to their own directory named with this value.
						  This parameter will not be passed to the module 'sims4.log' in any way.
		:type namespace: typing.Optional[str]
		:type level: LogLevels
		:type group: str | None
		:type owner: str | None
		:param exception: The 'exception' argument is not necessary as it will automatically find it for you. This argument is only required if the
		level is set to 'exception' and you are calling this function from where the exception won't be found by sys.exc_info().
		:type exception: BaseException
		:param logStack: Forces a stacktrace to be logged even if the level is not an error or exception.
		:type logStack: bool
		:param frame: If this is not none the function will use it to get a stacktrace. The parameter not be used if the function is not logging a stacktrace.
		:type frame: types.FrameType | None
		:param logToGame: Controls whether or not this will also report to the module 'sims4.log'
		:type logToGame: bool
		:param retryOnError: Whether or not we should try to log this in the into the next log file when encountering a write error.
		"""

		if not isinstance(namespace, str) and namespace is not None:
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str, "None"))

		if not isinstance(level, int):
			raise Exceptions.IncorrectTypeException(level, "level", (int,))

		if not isinstance(group, str) and group is not None:
			raise Exceptions.IncorrectTypeException(group, "group", (str,))

		if not isinstance(owner, str) and owner is not None:
			raise Exceptions.IncorrectTypeException(owner, "owner", (str,))

		if not isinstance(exception, BaseException) and exception is not None:
			raise Exceptions.IncorrectTypeException(exception, "exception", (BaseException,))

		if not isinstance(logStack, bool):
			raise Exceptions.IncorrectTypeException(logStack, "logStack", (bool,))

		if isinstance(frame, singletons.DefaultType):
			frame = None

		if not isinstance(frame, types.FrameType) and frame is not None:
			raise Exceptions.IncorrectTypeException(frame, "frame", (types.FrameType,))

		if exception is None:
			exception = sys.exc_info()[1]

		if logToGame:
			if level == LogLevels.Debug:
				log.debug(group, str(message), owner = owner)
			elif level == LogLevels.Info:
				log.info(group, str(message), owner = owner)
			elif level == LogLevels.Warning:
				log.warn(group, str(message), owner = owner)
			elif level == LogLevels.Error:
				log.error(group, str(message), owner = owner)
			elif level == LogLevels.Exception:
				log.exception(group, str(message), exc = exception, frame = (frame if frame is not None else log.DEFAULT), owner = owner)

		if self._writeFailureCount >= self._writeFailureLimit:
			return

		logNumber = getattr(self.DebugGlobal, self._globalLoggingNamespaceCounts).get(namespace, 0)
		getattr(self.DebugGlobal, self._globalIncreaseNamespaceLoggingCount)(namespace)

		report = Report(namespace, logNumber, datetime.datetime.now().isoformat(),
						str(message), level = level, group = str(group),
						owner = owner, exception = exception, logStack = logStack,
						stacktrace = str.join("", traceback.format_stack(f = frame)), retryOnError = retryOnError)  # type: Report

		self._reportStorage.append(report)
		self.Flush()

	def _LogAllReports (self, reports: typing.List[Report]) -> None:
		namespaceTextBytes = dict()  # type: typing.Dict[str, bytes]

		writeTime = datetime.datetime.now().isoformat()  # type: str

		for report in reports:  # type: Report
			reportTextBytes = report.GetBytes(writeTime = writeTime)  # type: bytes

			if report.Namespace in namespaceTextBytes:
				namespaceTextBytes[report.Namespace] += (os.linesep + os.linesep).encode("utf-8") + reportTextBytes
			else:
				namespaceTextBytes[report.Namespace] = reportTextBytes

		for namespace, namespaceBytes in namespaceTextBytes.items():  # type: str, bytes
			if namespace is not None:
				namespaceDirectory = os.path.join(self.GetLoggingRootPath(), namespace, self.GetLoggingDirectoryName())  # type: str
			else:
				namespaceDirectory = os.path.join(self.GetLoggingRootPath(), self.GetLoggingDirectoryName())  # type: str

			namespaceFilePath = os.path.join(namespaceDirectory, "Log.xml")  # type: str
			namespaceFirstWrite = False  # type: bool

			try:
				if not os.path.exists(namespaceFilePath):
					namespaceFirstWrite = True

					if not os.path.exists(namespaceDirectory):
						os.makedirs(namespaceDirectory)

				else:
					self._VerifyLogFile(namespaceFilePath)

				namespaceSessionFilePath = os.path.join(namespaceDirectory, "Session.txt")  # type: str
				namespaceModsFilePath = os.path.join(namespaceDirectory, "Mods.txt")  # type: str

				if not os.path.exists(namespaceSessionFilePath):
					with open(namespaceSessionFilePath, mode = "w+") as sessionFile:
						sessionFile.write(self._sessionInformation)

				if not os.path.exists(namespaceModsFilePath):
					with open(namespaceModsFilePath, mode = "w+") as modsFile:
						modsFile.write(self._modInformation)

				if namespaceFirstWrite:
					with open(namespaceFilePath, mode = "wb+") as namespaceFile:
						namespaceFile.write(self._logStartBytes)
						namespaceFile.write(namespaceBytes)
						namespaceFile.write(self._logEndBytes)
				else:
					with open(namespaceFilePath, "r+b") as namespaceFile:
						namespaceFile.seek(-len(self._logEndBytes), os.SEEK_END)
						namespaceFile.write((os.linesep + os.linesep).encode("utf-8") + namespaceBytes)
						namespaceFile.write(self._logEndBytes)

			except Exception as e:
				self._writeFailureCount += 1

				if not getattr(self.DebugGlobal, self._globalShownWriteFailureNotification):
					self._ShowWriteFailureDialog(e)
					setattr(self.DebugGlobal, self._globalShownWriteFailureNotification, True)

				if self._writeFailureCount < self._writeFailureLimit:
					self.ChangeLogFile()

					retryingReports = filter(lambda filterReport: filterReport.RetryOnError, reports)  # type: typing.List[Report]
					retryingReportsLength = len(retryingReports)  # type: int

					Log("Forced to start a new log file after encountering a write error. " + str(len(reports) - retryingReportsLength) + " reports where lost because of this.", self.HostNamespace, LogLevels.Exception, group = self.HostNamespace, owner = __name__, retryOnError = False)

					for retryingReport in retryingReports:
						retryingReport.RetryOnError = False

					if retryingReportsLength != 0:
						self._LogAllReports(reports)

				return

def Log (message, namespace: str, level: LogLevels, group: str = None, owner: str = None, exception: BaseException = None,
		 logStack: bool = False, frame: types.FrameType = None, logToGame: bool = True, retryOnError: bool = True) -> None:
	_logger.Log(message, namespace, level, group = group, owner = owner, exception = exception, logStack = logStack, frame = frame, logToGame = logToGame, retryOnError = retryOnError)

def ChangeLogFile () -> None:
	_logger.ChangeLogFile()

def _Setup () -> None:
	global _logger

	_logger = Logger(os.path.join(Paths.DebugPath, "Mods"), hostNamespace = This.Mod.Namespace)  # type: Logger

_Setup()
