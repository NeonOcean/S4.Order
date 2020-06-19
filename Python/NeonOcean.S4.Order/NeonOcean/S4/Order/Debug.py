from __future__ import annotations

import datetime
import os
import shutil
import sys
import threading
import traceback
import types
import typing

import singletons
from NeonOcean.S4.Order import DebugShared, Paths, This
from NeonOcean.S4.Order.DebugShared import LogLevels, Report
from NeonOcean.S4.Order.Tools import Exceptions
from sims4 import log

# noinspection PyTypeChecker
_activeLogger = None  # type: Logger

class Logger(DebugShared.Logger):
	_globalLoggingNamespaceCounts = "LoggingNamespaceCounts"  # type: str
	_globalIncreaseNamespaceLoggingCount = "IncreaseNamespaceLoggingCount"  # type: str

	def __init__ (self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if not hasattr(self.DebugGlobal, self._globalLoggingNamespaceCounts):
			setattr(self.DebugGlobal, self._globalLoggingNamespaceCounts, dict())

		self._lockHandler = _Locking()  # type: _Locking
		self._lockHandlerLock = threading.Lock()  # type: threading.Lock

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
			 group: str = None, owner: str = None, exception: BaseException = None, logStack: bool = False, frame: types.FrameType = None, logToGame: bool = True,
			 lockIdentifier: typing.Optional[str] = None, lockReference: typing.Any = None, lockIncrement: int = 1, lockThreshold: int = 2,
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
		:param lockIdentifier: Future reports with this identifier may be ignored. If this parameter is None the report will never be locked.
		:type lockIdentifier: str | None
		:param lockReference: The reference value allows you to specify that a report should be logged only once for each instance of an object. If this value
		is None the report will only ever be logged once regardless of which object it came from.
		:type lockReference: typing.Any
		:param lockIncrement: The number of points towards locking off this report is gained from logging it.
		:type lockIncrement: int
		:param lockThreshold: The number of locking points needed to be gained before reports with the specified identifier and reference pair are blocked. Changing
		the threshold will not permit more reports to be logged after it has already been surpassed once.
		:type lockThreshold: int
		:param retryOnError: Whether or not we should try to log this in the into the next log file when encountering a write error.
		:type retryOnError: bool
		"""

		if not isinstance(namespace, str) and namespace is not None:
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str, "None"))

		if not isinstance(level, int):
			raise Exceptions.IncorrectTypeException(level, "level", (int,))

		if not isinstance(group, str) and group is not None:
			raise Exceptions.IncorrectTypeException(group, "group", (str, None))

		if not isinstance(owner, str) and owner is not None:
			raise Exceptions.IncorrectTypeException(owner, "owner", (str, None))

		if not isinstance(exception, BaseException) and exception is not None:
			raise Exceptions.IncorrectTypeException(exception, "exception", (BaseException, None))

		if not isinstance(logStack, bool):
			raise Exceptions.IncorrectTypeException(logStack, "logStack", (bool,))

		if isinstance(frame, singletons.DefaultType):
			frame = None

		if not isinstance(frame, types.FrameType) and frame is not None:
			raise Exceptions.IncorrectTypeException(frame, "frame", (types.FrameType,))

		if not isinstance(logToGame, bool):
			raise Exceptions.IncorrectTypeException(logToGame, "logToGame", (bool,))

		if not isinstance(lockIdentifier, str) and lockIdentifier is not None:
			raise Exceptions.IncorrectTypeException(lockIdentifier, "lockIdentifier", (str,))

		if not isinstance(lockIncrement, int):
			raise Exceptions.IncorrectTypeException(lockIncrement, "lockIncrement", (int,))

		if not isinstance(lockThreshold, int):
			raise Exceptions.IncorrectTypeException(lockThreshold, "lockThreshold", (int,))

		if not isinstance(retryOnError, bool):
			raise Exceptions.IncorrectTypeException(retryOnError, "retryOnError", (bool,))

		if lockIdentifier is not None:
			self._LockHandlerClearUnlockingPoints(lockIdentifier, lockReference)

			if self._LockHandlerIsLocked(lockIdentifier, lockReference):
				return

			self._LockHandlerAddLockingPoints(lockIdentifier, lockReference, lockIncrement, lockThreshold)

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

		logCount = self.GetNextLogNumber(namespace)  # type: int
		self.IncrementLogCount(namespace)

		lockable = True if lockIdentifier is not None else False  # type: bool

		report = Report(namespace, logCount + 1, datetime.datetime.now().isoformat(),
						str(message), level = level, group = str(group),
						owner = owner, exception = exception, logStack = logStack,
						stacktrace = str.join("", traceback.format_stack(f = frame)), lockable = lockable, retryOnError = retryOnError)  # type: Report

		self._reportStorage.append(report)
		self.Flush()

	def IsLocked (self, lockIdentifier: str, lockReference: typing.Any = None) -> bool:
		"""
		Determine whether a report has been blocked from repeating.
		:param lockIdentifier: The lock identifier specified for the report in question.
		:type lockIdentifier: str
		:param lockReference: The lock reference specified for the report in question.
		:type lockReference: typing.Any
		"""

		return self._LockHandlerIsLocked(lockIdentifier, lockReference)

	def Unlock (self, lockIdentifier: str, lockReference: typing.Any = None, unlockIncrement: int = 1, unlockThreshold: int = 2) -> None:
		"""
		Unlock a locked report. Running this method will cause points towards locking the specified report to be lost, and the same for unlocking points for the log method.
		Points gained for locking and unlocking must be gained consecutively. This can allow you block and unblock off a report if it has been logged or not logged multiple
		times in a row, preventing spam.

		:param lockIdentifier: The lock identifier specified for the report in question.
		:type lockIdentifier: str
		:param lockReference: The lock reference specified for the report in question.
		:type lockReference: typing.Any
		:param unlockIncrement: The number of points towards unlocking the specified report gained from this action.
		:type unlockIncrement: int
		:param unlockThreshold: The number of unlocking points needed to be gained before reports with the specified identifier and reference pair are unblocked.
		:type unlockThreshold: int
		"""

		self._LockHandlerClearLockingPoints(lockIdentifier, lockReference)
		self._LockHandlerAddUnlockingPoints(lockIdentifier, lockReference, unlockIncrement, unlockThreshold)

	def GetNextLogNumber (self, namespace: typing.Optional[str]) -> int:
		if not isinstance(namespace, str):
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str, "None"))

		return getattr(self.DebugGlobal, self._globalLoggingNamespaceCounts).get(namespace, 0)

	def IncrementLogCount (self, namespace: typing.Optional[str]) -> None:
		if not isinstance(namespace, str):
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str, "None"))

		getattr(self.DebugGlobal, self._globalIncreaseNamespaceLoggingCount)(namespace)

	def GetLogSizeLimit (self) -> int:
		return 5000000

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
			namespaceDirectory = os.path.join(self.GetLoggingRootPath(), str(namespace))  # type: str
			namespaceLoggingDirectory = os.path.join(namespaceDirectory, self.GetLoggingDirectoryName())  # type: str

			namespaceFilePath = os.path.join(namespaceLoggingDirectory, "Log.xml")  # type: str
			namespaceLatestFilePath = os.path.join(namespaceDirectory, "Latest.xml")  # type: str
			namespaceFirstWrite = False  # type: bool

			namespaceSessionFilePath = os.path.join(namespaceLoggingDirectory, "Session.json")  # type: str
			namespaceModsDirectoryFilePath = os.path.join(namespaceLoggingDirectory, "Mods.txt")  # type: str

			logSizeLimit = self.GetLogSizeLimit()  # type: int
			logSizeLimitReachedBytes = "<!--Log file size limit reached-->".encode("utf-8")  # type: bytes

			logStartBytes = self.GetLogStartBytes()  # type: bytes
			logEndBytes = self.GetLogEndBytes()  # type: bytes

			lineSeparatorBytes = (os.linesep + os.linesep).encode("utf-8")  # type: bytes

			try:
				if not os.path.exists(namespaceFilePath):
					namespaceFirstWrite = True

					if not os.path.exists(namespaceLoggingDirectory):
						os.makedirs(namespaceLoggingDirectory)
				else:
					self._VerifyLogFile(namespaceFilePath)

				if not os.path.exists(namespaceSessionFilePath):
					with open(namespaceSessionFilePath, mode = "w+") as sessionFile:
						sessionFile.write(self._sessionInformation)

				if not os.path.exists(namespaceModsDirectoryFilePath):
					with open(namespaceModsDirectoryFilePath, mode = "w+") as modsDirectoryFile:
						modsDirectoryFile.write(self._modsDirectoryInformation)

				if namespaceFirstWrite:
					if len(logStartBytes) + len(namespaceBytes) + len(logEndBytes) >= logSizeLimit:
						namespaceBytes += logSizeLimitReachedBytes

					with open(namespaceFilePath, mode = "wb+") as namespaceFile:
						namespaceFile.write(logStartBytes)
						namespaceFile.write(namespaceBytes)
						namespaceFile.write(logEndBytes)

					if os.path.exists(namespaceLatestFilePath):
						os.remove(namespaceLatestFilePath)

					with open(namespaceLatestFilePath, mode = "wb+") as namespaceLatestFile:
						namespaceLatestFile.write(logStartBytes)
						namespaceLatestFile.write(namespaceBytes)
						namespaceLatestFile.write(logEndBytes)
				else:
					logSize = os.path.getsize(namespaceFilePath)  # type: int

					if logSize >= logSizeLimit:
						continue

					if logSize + len(lineSeparatorBytes) + len(namespaceBytes) + len(logEndBytes) >= logSizeLimit:
						namespaceBytes += logSizeLimitReachedBytes

					with open(namespaceFilePath, "r+b") as namespaceFile:
						namespaceFile.seek(-len(logEndBytes), os.SEEK_END)
						namespaceFile.write(lineSeparatorBytes)
						namespaceFile.write(namespaceBytes)
						namespaceFile.write(logEndBytes)

					try:
						self._VerifyLogFile(namespaceLatestFilePath)

						with open(namespaceLatestFilePath, "r+b") as namespaceLatestFile:
							namespaceLatestFile.seek(-len(logEndBytes), os.SEEK_END)
							namespaceLatestFile.write(lineSeparatorBytes)
							namespaceLatestFile.write(namespaceBytes)
							namespaceLatestFile.write(logEndBytes)
					except:
						shutil.copy(namespaceFilePath, namespaceLatestFilePath)
			except Exception as e:
				self._writeFailureCount += 1

				if not getattr(self.DebugGlobal, self._globalShownWriteFailureNotification):
					self._ShowWriteFailureDialog(e)
					setattr(self.DebugGlobal, self._globalShownWriteFailureNotification, True)

				if self._writeFailureCount < self._writeFailureLimit:
					self.ChangeLogFile()

					retryingReports = list(filter(lambda filterReport: filterReport.RetryOnError, reports))  # type: typing.List[Report]
					retryingReportsLength = len(retryingReports)  # type: int

					Log("Forced to start a new log file after encountering a write error. " + str(len(reports) - retryingReportsLength) + " reports where lost because of this.", self.HostNamespace, LogLevels.Exception, group = self.HostNamespace, owner = __name__, retryOnError = False)

					for retryingReport in retryingReports:
						retryingReport.RetryOnError = False

					if retryingReportsLength != 0:
						self._LogAllReports(reports)

				return

	def _LockHandlerLock (self, identifier: str, reference: typing.Any) -> None:
		self._lockHandlerLock.acquire()
		self._lockHandler.Lock(identifier, reference)
		self._lockHandlerLock.release()

	def _LockHandlerUnlock (self, identifier: str, reference: typing.Any) -> None:
		self._lockHandlerLock.acquire()
		self._lockHandler.Unlock(identifier, reference)
		self._lockHandlerLock.release()

	def _LockHandlerIsLocked (self, identifier: str, reference: typing.Any) -> bool:
		self._lockHandlerLock.acquire()
		isLocked = self._lockHandler.IsLocked(identifier, reference)  # type: bool
		self._lockHandlerLock.release()

		return isLocked

	def _LockHandlerAddLockingPoints (self, identifier: str, reference: typing.Any, lockIncrement: int, lockThreshold: int) -> None:
		self._lockHandlerLock.acquire()
		self._lockHandler.AddLockingPoints(identifier, reference, lockIncrement, lockThreshold)
		self._lockHandlerLock.release()

	def _LockHandlerClearLockingPoints (self, identifier: str, reference: typing.Any) -> None:
		self._lockHandlerLock.acquire()
		self._lockHandler.ClearLockingPoints(identifier, reference)
		self._lockHandlerLock.release()

	def _LockHandlerAddUnlockingPoints (self, identifier: str, reference: typing.Any, unlockIncrement: int, unlockThreshold: int) -> None:
		self._lockHandlerLock.acquire()
		self._lockHandler.AddUnlockingPoints(identifier, reference, unlockIncrement, unlockThreshold)
		self._lockHandlerLock.release()

	def _LockHandlerClearUnlockingPoints (self, identifier: str, reference: typing.Any) -> None:
		self._lockHandlerLock.acquire()
		self._lockHandler.ClearUnlockingPoints(identifier, reference)
		self._lockHandlerLock.release()

class _Locking:
	def __init__ (self):
		self._locked = dict()  # type: typing.Dict[str, typing.Set[typing.Any]]
		self._lockingPoints = dict()  # type: typing.Dict[str, typing.Dict[typing.Any, int]]
		self._unlockingPoints = dict()  # type: typing.Dict[str, typing.Dict[typing.Any, int]]

	def Lock (self, identifier: str, reference: typing.Any) -> None:
		identifierLocked = self._locked.get(identifier, None)  # type: typing.Set[typing.Any]

		if identifierLocked is None:
			identifierReferences = set()
			identifierReferences.add(reference)
			self._locked[identifier] = identifierReferences

			return

		identifierLocked.add(reference)

		self.ClearLockingPoints(identifier, reference)

	def Unlock (self, identifier: str, reference: typing.Any) -> None:
		identifierLocked = self._locked.get(identifier, None)  # type: typing.Set[typing.Any]

		if identifierLocked is None:
			return

		identifierLocked.discard(reference)

		self.ClearUnlockingPoints(identifier, reference)

	def IsLocked (self, identifier: str, reference: typing.Any) -> bool:
		identifierLocked = self._locked.get(identifier, None)  # type: typing.Set[typing.Any]

		if identifierLocked is None:
			return False

		return reference in identifierLocked

	def AddLockingPoints (self, identifier: str, reference: typing.Any, lockIncrement: int, lockThreshold: int) -> None:
		if lockIncrement >= lockThreshold:
			self.Lock(identifier, reference)
			return

		identifierLockingPoints = self._lockingPoints.get(identifier, None)  # type: typing.Dict[typing.Any, int]

		if identifierLockingPoints is None:
			identifierReferences = {
				reference: lockIncrement
			}  # type: typing.Dict[typing.Any, int]

			self._lockingPoints[identifier] = identifierReferences
			return

		if reference not in identifierLockingPoints:
			identifierLockingPoints[reference] = lockIncrement
			return

		identifierLockingPoints[reference] += lockIncrement

		if identifierLockingPoints[reference] >= lockThreshold:
			self.Lock(identifier, reference)

	def ClearLockingPoints (self, identifier: str, reference: typing.Any) -> None:
		identifierLockingPoints = self._lockingPoints.get(identifier, None)  # type: typing.Dict[typing.Any, int]

		if identifierLockingPoints is not None:
			identifierLockingPoints.pop(reference, None)

			if len(identifierLockingPoints) == 0:
				self._lockingPoints.pop(identifier, None)

	def AddUnlockingPoints (self, identifier: str, reference: typing.Any, unlockIncrement: int, unlockThreshold: int) -> None:
		if unlockIncrement >= unlockThreshold:
			self.Unlock(identifier, reference)
			return

		identifierUnlockingPoints = self._unlockingPoints.get(identifier, None)  # type: typing.Dict[typing.Any, int]

		if identifierUnlockingPoints is None:
			identifierReferences = {
				reference: unlockIncrement
			}  # type: typing.Dict[typing.Any, int]

			self._unlockingPoints[identifier] = identifierReferences
			return

		if reference not in identifierUnlockingPoints:
			identifierUnlockingPoints[reference] = unlockIncrement
			return

		identifierUnlockingPoints[reference] += unlockIncrement

		if identifierUnlockingPoints[reference] >= unlockThreshold:
			self.Unlock(identifier, reference)

	def ClearUnlockingPoints (self, identifier: str, reference: typing.Any) -> None:
		identifierUnlockingPoints = self._unlockingPoints.get(identifier, None)  # type: typing.Dict[typing.Any, int]

		if identifierUnlockingPoints is not None:
			identifierUnlockingPoints.pop(reference, None)

			if len(identifierUnlockingPoints) == 0:
				self._unlockingPoints.pop(identifier, None)

def ActiveLogger () -> Logger:
	return _activeLogger

def _Setup () -> None:
	global _activeLogger

	_activeLogger = Logger(os.path.join(Paths.DebugPath, "Mods"), hostNamespace = This.Mod.Namespace)  # type: Logger

_Setup()

Log = ActiveLogger().Log
IsLocked = ActiveLogger().IsLocked
Unlock = ActiveLogger().Unlock
GetNextLogNumber = ActiveLogger().GetNextLogNumber
ChangeLogFile = ActiveLogger().ChangeLogFile
