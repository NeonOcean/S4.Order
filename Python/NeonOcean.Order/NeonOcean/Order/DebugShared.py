import datetime
import os
import platform
import threading
import traceback
import typing
import uuid
from xml.sax import saxutils

import enum
from NeonOcean.Order import Language, Paths, This
from NeonOcean.Order.Data import Global
from NeonOcean.Order.Tools import Exceptions, Threading as ThreadingTools
from NeonOcean.Order.UI import Notifications
from sims4 import common, log
from ui import ui_dialog_notification

class LogLevels(enum.Int):
	Exception = 0  # type: LogLevels
	Error = 1  # type: LogLevels
	Warning = 2  # type: LogLevels
	Info = 3  # type: LogLevels
	Debug = 4  # type: LogLevels

class Report:
	def __init__ (self, namespace: typing.Optional[str], logNumber: int, logTime: str,
				  message: str, level: LogLevels, group: str = None,
				  owner: str = None, exception: BaseException = None, logStack: bool = False,
				  stacktrace: str = None, retryOnError: bool = False):
		self.Namespace = namespace  # type: typing.Optional[str]
		self.LogNumber = logNumber  # type: int
		self.LogTime = logTime  # type: str
		self.Message = message  # type: str
		self.Level = level  # type: LogLevels
		self.Group = group  # type: typing.Optional[str]
		self.Owner = owner  # type: typing.Optional[str]
		self.Exception = exception  # type: typing.Optional[BaseException]
		self.LogStack = logStack  # type: bool
		self.Stacktrace = stacktrace  # type: typing.Optional[str]
		self.RetryOnError = retryOnError  # type: bool

	def GetBytes (self, writeTime: str = None) -> bytes:
		return self.GetText(writeTime).encode("utf-8")

	def GetText (self, writeTime: str = None) -> str:
		logTemplate = "\t<Log Number=\"{}\" Level=\"{}\" Group=\"{}\""  # type: str

		logFormatting = [
			str(self.LogNumber),
			self.Level.name,
			str(self.Group)
		]  # type: typing.List[str]

		if self.Owner is not None:
			logTemplate += " Owner=\"{}\""
			logFormatting.append(self.Owner)

		logTemplate += " LogTime=\"{}\""
		logFormatting.append(self.LogTime)

		if writeTime is not None:
			logTemplate += " WriteTime=\"{}\""
			logFormatting.append(writeTime)

		logTemplate += ">\n" \
					   "\t\t<Message><!--\n" \
					   "\t\t\t-->{}<!--\n" \
					   "\t\t--></Message>\n"

		messageText = str(self.Message)  # type: str
		messageText = messageText.replace("\r\n", "\n")
		messageText = saxutils.escape(messageText).replace("\n", "\n<!--\t\t-->")
		logFormatting.append(messageText)

		if self.Exception is not None:
			logTemplate += "\t\t<Exception><!--\n" \
						   "\t\t\t-->{}<!--\n" \
						   "\t\t--></Exception>\n"

			exceptionText = FormatException(self.Exception)  # type: str
			exceptionText = exceptionText.replace("\r\n", "\n")
			exceptionText = saxutils.escape(exceptionText).replace("\n", "\n<!--\t\t-->")
			logFormatting.append(exceptionText)

		if self.Level <= LogLevels.Error or self.LogStack:
			logTemplate += "\t\t<Stacktrace><!--\n" \
						   "\t\t\t-->{}<!--\n" \
						   "\t\t--></Stacktrace>\n"

			stackTraceText = self.Stacktrace  # type: str
			stackTraceText = stackTraceText.replace("\r\n", "\n")
			stackTraceText = saxutils.escape(stackTraceText).replace("\n", "\n<!--\t\t-->")
			logFormatting.append(stackTraceText)

		logTemplate += "\t</Log>"

		logText = logTemplate.format(*logFormatting)  # type: str
		logText = logText.replace("\n", os.linesep)

		return logText

class Logger:
	WriteFailureNotificationTitle = Language.String(This.Mod.Namespace + ".System.Debug.Write_Failure_Notification.Title")
	WriteFailureNotificationText = Language.String(This.Mod.Namespace + ".System.Debug.Write_Failure_Notification.Text")

	_logStartBytes = ("<?xml version=\"1.0\" encoding=\"utf-8\"?>" + os.linesep + "<LogFile>" + os.linesep).encode("utf-8")  # type: bytes
	_logEndBytes = (os.linesep + "</LogFile>").encode("utf-8")  # type: bytes

	_globalSessionID = "SessionID"  # type: str
	_globalSessionStartTime = "SessionStartTime"  # type: str

	_globalShownWriteFailureNotification = "ShownWriteFailureNotification"  # type: str

	def __init__ (self, loggingRootPath: str, hostNamespace: str = This.Mod.Namespace):
		"""
		An object for logging debug information.
		Logs will be written to a folder named either by the global NeonOcean debugging start time, or the time ChangeLogFile() was last called for this object.

		:param loggingRootPath: The root path all reports sent to this logger object will be written.
		:type loggingRootPath: str
		:param hostNamespace: Errors made by this logger object will show up under this namespace.
		:type hostNamespace: str
		"""

		if not isinstance(loggingRootPath, str):
			raise Exceptions.IncorrectTypeException(loggingRootPath, "loggingRootPath", (str,))

		if not isinstance(hostNamespace, str):
			raise Exceptions.IncorrectTypeException(hostNamespace, "hostNamespace", (str,))

		self.DebugGlobal = Global.GetModule("Debug")

		if not hasattr(self.DebugGlobal, self._globalSessionID):
			setattr(self.DebugGlobal, self._globalSessionID, uuid.uuid4())

		if not hasattr(self.DebugGlobal, self._globalSessionStartTime):
			setattr(self.DebugGlobal, self._globalSessionStartTime, datetime.datetime.now())

		if not hasattr(self.DebugGlobal, self._globalShownWriteFailureNotification):
			setattr(self.DebugGlobal, self._globalShownWriteFailureNotification, False)

		self.HostNamespace = hostNamespace  # type: str

		self._reportStorage = list()  # type: typing.List[Report]
		self._flushThread = None  # type: threading.Thread

		self._loggingRootPath = loggingRootPath  # type: str
		self._loggingDirectoryName = GetDateTimePathString(getattr(self.DebugGlobal, self._globalSessionStartTime))  # type: str

		self._writeFailureCount = 0  # type: int
		self._writeFailureLimit = 2  # type: int
		self._isContinuation = False  # type: bool

		self._sessionInformation = self._CreateSessionInformation()  # type: str
		self._modInformation = self._CreateModsInformation()  # type: str

	def Log (self, *args, **kwargs) -> None:
		raise NotImplementedError()

	def GetLoggingRootPath (self) -> str:
		return self._loggingRootPath

	def GetLoggingDirectoryName (self) -> str:
		return self._loggingDirectoryName

	def IsContinuation (self) -> bool:
		return self._isContinuation

	def ChangeLogFile (self) -> None:
		"""
		Change the current directory name for a new one. The new directory name will be the time this method was called.
		:rtype: None
		"""

		self._loggingDirectoryName = GetDateTimePathString(datetime.datetime.now())
		self._isContinuation = True

		self._sessionInformation = self._CreateSessionInformation()
		self._modInformation = self._CreateModsInformation()

	def Flush (self) -> None:
		mainThread = threading.main_thread()  # type: threading.Thread
		mainThreadAlive = mainThread.is_alive()  # type: bool

		currentThreadIsMain = mainThread == threading.current_thread()  # type: bool

		if not mainThreadAlive and not currentThreadIsMain:
			# Unfortunately any daemonic thread's reports will not be written unless they are logged before the last reports from the main thread are written.
			# At this point, any flush thread started will not finish in time before it all comes to an end. Though the flush thread is not daemonic, Python will
			# not stop for it while a shutdown is already in progress. The best way of getting any more reports out during this time would be to co-opt the
			# main thread and make it wait while we write the stored reports.
			return

		if self._flushThread is not None:
			if not mainThreadAlive:
				if self._flushThread.is_alive():
					self._flushThread.join(1)

					if self._flushThread.is_alive():
						return
				else:
					self._flushThread = None
			else:
				return

		if not mainThreadAlive:
			flushThread = self._CreateFlushThread()  # type: threading.Thread
			self._SetFlushThreadUnsafe(flushThread)

			flushThread.start()
			flushThread.join(1)
		else:
			flushThread = self._CreateFlushThread()  # type: threading.Thread

			try:
				self._SetFlushThread(flushThread)
			except ThreadingTools.SimultaneousCallException:
				return

			mainThreadStateChanged = not mainThread.is_alive()  # type: bool

			if mainThreadStateChanged:
				self.Flush()
				return

			flushThread.start()

	def _CreateFlushThread (self) -> threading.Thread:
		mainThread = threading.main_thread()  # type: threading.Thread
		mainThreadAlive = mainThread.is_alive()  # type: bool

		def _FlushThread () -> None:
			nonlocal mainThreadAlive

			mainThreadAlive = mainThread.is_alive()

			try:
				while len(self._reportStorage) != 0:
					reportStorageLength = len(self._reportStorage)  # type: int
					targetReports = self._reportStorage[:reportStorageLength]
					self._reportStorage = self._reportStorage[reportStorageLength:]

					filteredReports = self._FilterReports(targetReports)

					self._LogAllReports(filteredReports)

					mainThreadAlive = mainThread.is_alive()

					if not mainThreadAlive:
						break
			finally:
				self._flushThread = None

			if mainThreadAlive:
				if len(self._reportStorage) != 0:
					self.Flush()

		return threading.Thread(target = _FlushThread, daemon = False)

	@ThreadingTools.NotThreadSafe(raiseException = True)
	def _SetFlushThread (self, flushThread: threading.Thread) -> None:
		self._SetFlushThreadUnsafe(flushThread)

	def _SetFlushThreadUnsafe (self, flushThread: threading.Thread) -> None:
		self._flushThread = flushThread

	def _FilterReports (self, reports: typing.List[Report]) -> typing.List[Report]:
		return list(reports)

	def _LogAllReports (self, reports: typing.List[Report]) -> None:
		raise NotImplementedError()

	def _CreateSessionInformation (self) -> str:
		try:
			sessionTemplate = "Debugging session ID '{}'\n" \
							  "Debugging session start time '{}'\n" \
							  "Log is a continuation of another '{}'\n" \
							  "\n" \
							  "Operation system '{}'\n\n" \
							  "Version '{}'\n" \
							  "\n" \
							  "Installed Packs:\n" \
							  "{}"  # type: str

			installedPacksText = ""  # type: str

			for packTuple in common.Pack.items():  # type: typing.Tuple[str, common.Pack]
				if packTuple[1] == common.Pack.BASE_GAME:
					continue

				packAvailable = common.is_available_pack(packTuple[1])

				if packAvailable:
					if installedPacksText != "":
						installedPacksText += "\n"

					prefixExpansionPairs = {
						"EP": "Expansion Pack ",
						"GP": "Game Pack ",
						"SP": "Stuff Pack "
					}  # type: typing.Dict[str, str]

					packText = packTuple[0]  # type: str

					for prefix, prefixExpansion in prefixExpansionPairs.items():  # type: str
						if packText.startswith(prefix):
							packText = packText.replace(prefix, prefixExpansion, 1)
							break

					installedPacksText += packText

			sessionFormatting = (str(getattr(self.DebugGlobal, self._globalSessionID)),
								 str(getattr(self.DebugGlobal, self._globalSessionStartTime)),
								 self.IsContinuation(),
								 platform.system(),
								 platform.version(),
								 installedPacksText)

			return sessionTemplate.format(*sessionFormatting)
		except Exception as e:
			return "Failed to get session information\n" + FormatException(e)

	def _CreateModsInformation (self) -> str:
		try:
			modFolderString = os.path.split(Paths.ModsPath)[1] + " {" + os.path.split(Paths.ModsPath)[1] + "}"  # type: str

			for directoryRoot, directoryNames, fileNames in os.walk(Paths.ModsPath):  # type: str, list, list
				depth = 1

				if directoryRoot != Paths.ModsPath:
					depth = len(directoryRoot.replace(Paths.ModsPath + os.path.sep, "").split(os.path.sep)) + 1  # type: int

				indention = "\t" * depth  # type: str

				newString = ""  # type: str

				for directory in directoryNames:
					newString += "\n" + indention + directory + " {" + directory + "}"

				for file in fileNames:
					newString += "\n" + indention + file + " (" + str(os.path.getsize(os.path.join(directoryRoot, file))) + " B)"

				if len(newString) == 0:
					newString = "\n"

				newString += "\n"

				modFolderString = modFolderString.replace("{" + os.path.split(directoryRoot)[1] + "}", "{" + newString + "\t" * (depth - 1) + "}", 1)

			return modFolderString
		except Exception as e:
			return "Failed to get mod information\n" + FormatException(e)

	def _VerifyLogFile (self, logFilePath: str) -> None:
		with open(logFilePath, "rb") as logFile:
			if self._logStartBytes != logFile.read(len(self._logStartBytes)):
				raise Exception("The start of the log file doesn't match what was expected.")

			logFile.seek(-len(self._logEndBytes), os.SEEK_END)

			if self._logEndBytes != logFile.read():
				raise Exception("The end of the log file doesn't match what was expected.")

	def _ShowWriteFailureDialog (self, exception: Exception) -> None:
		Notifications.ShowNotification(queue = True,
									   title = self.WriteFailureNotificationTitle.GetCallableLocalizationString(),
									   text = self.WriteFailureNotificationText.GetCallableLocalizationString(FormatException(exception)),
									   expand_behavior = ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
									   urgency = ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT)

def FormatException (exception: BaseException) -> str:
	if not isinstance(exception, BaseException):
		raise Exceptions.IncorrectTypeException(exception, "exception", (BaseException,))

	return str.join("", traceback.format_exception(type(exception), exception, exception.__traceback__))

def ConvertEALevelToLogLevel (level: int) -> LogLevels:
	if not isinstance(level, int):
		raise Exceptions.IncorrectTypeException(level, "level", (int,))

	if level == log.LEVEL_DEBUG or level == log.LEVEL_UNDEFINED:
		return LogLevels.Debug
	elif level == log.LEVEL_INFO:
		return LogLevels.Info
	elif level == log.LEVEL_WARN:
		return LogLevels.Warning
	elif level == log.LEVEL_ERROR:
		return LogLevels.Error
	elif level == log.LEVEL_EXCEPTION or level == log.LEVEL_FATAL:
		return LogLevels.Exception

	raise ValueError("Level value '" + str(level) + "' is not a valid EA log level.")

def ConvertLogLevelToEALevel (level: LogLevels) -> int:
	if not isinstance(level, LogLevels):
		raise Exceptions.IncorrectTypeException(level, "level", (LogLevels,))

	if level == LogLevels.Debug:
		return log.LEVEL_DEBUG
	elif level == LogLevels.Info:
		return log.LEVEL_INFO
	elif level == LogLevels.Warning:
		return log.LEVEL_WARN
	elif level == LogLevels.Error:
		return log.LEVEL_ERROR
	elif level == LogLevels.Exception:
		return log.LEVEL_EXCEPTION

	return log.LEVEL_DEBUG

def GetDateTimePathString (dateTime: datetime.datetime) -> str:
	return dateTime.date().isoformat() + " " + dateTime.time().isoformat().replace(":", ".")  # type: str
