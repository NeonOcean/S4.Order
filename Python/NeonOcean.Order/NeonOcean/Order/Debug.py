import datetime
import os
import platform
import traceback
import types
import typing
import uuid
from xml.sax import saxutils

import enum
import singletons
from NeonOcean.Order import Language, Paths, This
from NeonOcean.Order.Data import Global
from NeonOcean.Order.Tools import Exceptions
from NeonOcean.Order.UI import Notifications
from sims4 import common, log
from ui import ui_dialog_notification

_logger = None  # type: Logger

class LogLevels(enum.Int):
	Exception = 0  # type: LogLevels
	Error = 1  # type: LogLevels
	Warning = 2  # type: LogLevels
	Info = 3  # type: LogLevels
	Debug = 4  # type: LogLevels

class Logger:
	_logStartBytes = ("<?xml version=\"1.0\" encoding=\"utf-8\"?>" + os.linesep + "<LogFile>" + os.linesep).encode("utf-8")  # type: bytes
	_logEndBytes = (os.linesep + "</LogFile>").encode("utf-8")  # type: bytes

	_globalSessionID = "SessionID"  # type: str
	_globalSessionStartTime = "SessionStartTime"  # type: str
	_globalLoggingCount = "LoggingCount"  # type: str
	_globalLoggingNamespaceCounts = "LoggingNamespaceCounts"  # type: str
	_globalShownWriteFailureNotification = "ShownWriteFailureNotification"  # type: str

	def __init__ (self, loggingRootPath: str, separateNamespaces: bool = True, hostNamespace: str = This.Mod.Namespace):
		"""
		An object for logging debug information.
		Logs will be written to a folder named either by the global NeonOcean debugging start time, or the time ChangeLogFile() was last called for this object.

		:param loggingRootPath: The root path all logs sent to this logger object will be written.
		:type loggingRootPath: str
		:param separateNamespaces: Whether or not logs will be separated into different folders based on namespace.
								   If true logs will have the path '<loggingRootPath>/<namespace>/<debugging start time>.
								   If false the path will be similar but without the namespace part.
		:type: bool
		:param hostNamespace: Errors made by this logger object will show up under this namespace.
		:type hostNamespace: str
		"""

		if not isinstance(loggingRootPath, str):
			raise Exceptions.IncorrectTypeException(loggingRootPath, "loggingRootPath", (str,))

		if not isinstance(separateNamespaces, bool):
			raise Exceptions.IncorrectTypeException(separateNamespaces, "separateNamespaces", (bool,))

		if not isinstance(hostNamespace, str):
			raise Exceptions.IncorrectTypeException(hostNamespace, "hostNamespace", (str,))

		self.DebugGlobal = Global.GetModule("Debug")

		if not hasattr(self.DebugGlobal, self._globalSessionID):
			setattr(self.DebugGlobal, self._globalSessionID, uuid.UUID)

		if not hasattr(self.DebugGlobal, self._globalSessionStartTime):
			setattr(self.DebugGlobal, self._globalSessionStartTime, datetime.datetime.now())

		if not hasattr(self.DebugGlobal, self._globalLoggingCount):
			setattr(self.DebugGlobal, self._globalLoggingCount, 0)

		if not hasattr(self.DebugGlobal, self._globalLoggingNamespaceCounts):
			setattr(self.DebugGlobal, self._globalLoggingNamespaceCounts, dict())

		if not hasattr(self.DebugGlobal, self._globalShownWriteFailureNotification):
			setattr(self.DebugGlobal, self._globalShownWriteFailureNotification, False)

		self.HostNamespace = hostNamespace  # type: str

		self._loggingRootPath = loggingRootPath  # type: str
		self._loggingDirectoryName = self.GetDateTimePathString(getattr(self.DebugGlobal, self._globalSessionStartTime))  # type: str

		self._separateNamespaces = separateNamespaces  # type: bool

		self._writeFailureCount = 0  # type: int
		self._writeFailureLimit = 2  # type: int
		self._isContinuation = False  # type: bool

		self._sessionInformation = self._CreateSessionInformation()  # type: str
		self._modInformation = self._CreateModsInformation()  # type: str

	def Log (self, message, namespace: str, level: LogLevels, group: str = None, owner: str = None,
			 exception: BaseException = None, logStack: bool = False, frame: types.FrameType = None, logToGame: bool = True, retryOnError: bool = True) -> None:
		"""
		Logs a message even if no mod has enabled the game's logging system. It will also report the log to the module 'sims4.log' by default.
		Logs will be writen to '<Sims4 user data path>/NeonOcean/Debug/Mods/<Namespace>/<Game start time>/Log.xml'. This function is not recommended for logging in high volume
		intentionally as there is no filter, Using this too often may cause significant slow downs.
		:param message: The message is converted to a string with str(message) if it isn't one already.
		:param namespace: The namespace or mod the log is coming from. Logs will be separated in to their own directory named with this value.
						  This parameter will not be passed to the module 'sims4.log' in any way.
		:type namespace: str
		:type level: LogLevels
		:type group: str | None
		:type owner: str | None
		:param exception: Only passed to the sims logging if the level is an exception.
		:type exception: BaseException
		:param logStack: Forces a stacktrace to be logged even if the level is not an error or exception.
		:type logStack: bool
		:param frame: If this is not none the function will use it to get a stacktrace. The parameter not be used if the function is not logging a stacktrace.
		:type frame: types.FrameType | None
		:param logToGame: Controls whether or not this will also report to the module 'sims4.log'
		:type logToGame: bool
		:param retryOnError: Whether or not we should try to log this in the into the next log file when encountering a write error.
		"""

		if self._writeFailureCount >= self._writeFailureLimit:
			return

		if not isinstance(namespace, str):
			raise Exceptions.IncorrectTypeException(namespace, "namespace", (str,))

		if not isinstance(level, int):
			raise Exceptions.IncorrectTypeException(level, "level", (int,))

		if not isinstance(owner, str) and owner is not None:
			raise Exceptions.IncorrectTypeException(owner, "owner", (str,))

		if not isinstance(group, str) and group is not None:
			raise Exceptions.IncorrectTypeException(group, "group", (str,))

		if not isinstance(exception, BaseException) and exception is not None:
			raise Exceptions.IncorrectTypeException(exception, "exception", (BaseException,))

		if not isinstance(logStack, bool):
			raise Exceptions.IncorrectTypeException(logStack, "logStack", (bool,))

		if isinstance(frame, singletons.DefaultType):
			frame = None

		if not isinstance(frame, types.FrameType) and frame is not None:
			raise Exceptions.IncorrectTypeException(frame, "frame", (types.FrameType,))

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

		namespaceCounts = None  # type: typing.Dict[str, int]

		if self._separateNamespaces:
			namespaceCounts = getattr(self.DebugGlobal, self._globalLoggingNamespaceCounts)

			if namespace in namespaceCounts:
				logNumber = namespaceCounts[namespace]
			else:
				logNumber = 0
		else:
			logNumber = getattr(self.DebugGlobal, self._globalLoggingCount)

		logTemplate = "\t<Log Number=\"{}\" Level=\"{}\" Group =\"{}\""  # type: str

		logFormatting = [
			str(logNumber),
			level.name,
			str(group)
		]  # type: typing.List[str]

		if owner is not None:
			logTemplate += " Owner=\"{}\""
			logFormatting.append(owner)

		logTemplate += " LogTime=\"{}\">\n" \
					   "\t\t<Message><!--\n" \
					   "\t\t\t-->{}<!--\n" \
					   "\t\t--></Message>\n"

		logFormatting.append(datetime.datetime.now().isoformat())

		messageText = str(message)  # type: str
		messageText = messageText.replace("\r\n", "\n")
		messageText = saxutils.escape(messageText).replace("\n", "\n<!--\t\t-->")
		logFormatting.append(messageText)

		if exception is not None:
			logTemplate += "\t\t<Exception><!--\n" \
						   "\t\t\t-->{}<!--\n" \
						   "\t\t--></Exception>\n"

			exceptionText = FormatException(exception)  # type: str
			exceptionText = exceptionText.replace("\r\n", "\n")
			exceptionText = saxutils.escape(exceptionText).replace("\n", "\n<!--\t\t-->")
			logFormatting.append(exceptionText)

		if level <= LogLevels.Error or logStack:
			logTemplate += "\t\t<Stacktrace><!--\n" \
						   "\t\t\t-->{}<!--\n" \
						   "\t\t--></Stacktrace>\n"

			stackTraceText = str.join("", traceback.format_stack(f = frame))  # type: str
			stackTraceText = stackTraceText.replace("\r\n", "\n")
			stackTraceText = saxutils.escape(stackTraceText).replace("\n", "\n<!--\t\t-->")
			logFormatting.append(stackTraceText)

		logTemplate += "\t</Log>"

		logText = logTemplate.format(*logFormatting)  # type: str
		logText = logText.replace("\n", os.linesep)

		logTextBytes = logText.encode("utf-8")

		if self._separateNamespaces:
			logDirectory = os.path.join(self.GetLoggingRootPath(), namespace, self.GetLoggingDirectoryName())  # type: str
		else:
			logDirectory = os.path.join(self.GetLoggingRootPath(), self.GetLoggingDirectoryName())  # type: str

		logFilePath = os.path.join(logDirectory, "Log.xml")  # type: str
		logFirstWrite = False  # type: bool

		try:
			if not os.path.exists(logFilePath):
				logFirstWrite = True

				if not os.path.exists(logDirectory):
					os.makedirs(logDirectory)

			else:
				self._VerifyLogFile(logFilePath)

			sessionFilePath = os.path.join(logDirectory, "Session.txt")  # type: str
			modsFilePath = os.path.join(logDirectory, "Mods.txt")  # type: str

			if not os.path.exists(sessionFilePath):
				with open(sessionFilePath, mode = "w+") as sessionFile:
					sessionFile.write(self._sessionInformation)

			if not os.path.exists(modsFilePath):
				with open(modsFilePath, mode = "w+") as modsFile:
					modsFile.write(self._modInformation)

			if logFirstWrite:
				with open(logFilePath, mode = "wb+") as logFile:
					logFile.write(self._logStartBytes)
					logFile.write(logTextBytes)
					logFile.write(self._logEndBytes)
			else:
				with open(logFilePath, "r+b") as logFile:
					logFile.seek(-len(self._logEndBytes), os.SEEK_END)
					logFile.write((os.linesep + os.linesep).encode("utf-8") + logTextBytes)
					logFile.write(self._logEndBytes)

		except Exception as e:
			self._writeFailureCount += 1

			if not getattr(self.DebugGlobal, self._globalShownWriteFailureNotification):
				self._ShowWriteFailureDialog(e)
				setattr(self.DebugGlobal, self._globalShownWriteFailureNotification, True)

			if self._writeFailureCount < self._writeFailureLimit:
				self.ChangeLogFile()

				Log("Forced to start a new log file after encountering a write error.", self.HostNamespace, LogLevels.Exception, group = self.HostNamespace, owner = __name__, exception = e, retryOnError = False)

				if retryOnError:
					Log(message, namespace, level, group = group, owner = owner, exception = exception, logStack = logStack, frame = frame, logToGame = False, retryOnError = False)

			return

		if self._separateNamespaces:
			namespaceCounts[namespace] = logNumber + 1
		else:
			setattr(self.DebugGlobal, self._globalLoggingCount, logNumber + 1)

	def GetLoggingRootPath (self) -> str:
		return self._loggingRootPath

	def GetLoggingDirectoryName (self) -> str:
		return self._loggingDirectoryName

	def IsSeparatingNamespaces (self) -> bool:
		return self._separateNamespaces

	def IsContinuation (self) -> bool:
		return self._isContinuation

	def ChangeLogFile (self) -> None:
		"""
		Change the current directory name for a new one. The new directory name will be the time this method was called.
		:rtype: None
		"""

		self._loggingDirectoryName = self.GetDateTimePathString(datetime.datetime.now())
		self._isContinuation = True

		self._sessionInformation = self._CreateSessionInformation()
		self._modInformation = self._CreateModsInformation()

	@staticmethod
	def FormatException (exception: BaseException) -> str:
		if not isinstance(exception, BaseException):
			raise Exceptions.IncorrectTypeException(exception, "exception", (BaseException,))

		return str.join("", traceback.format_exception(type(exception), exception, exception.__traceback__))

	@staticmethod
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

	@staticmethod
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

	@staticmethod
	def GetDateTimePathString (dateTime: datetime.datetime) -> str:
		return dateTime.date().isoformat() + " " + dateTime.time().isoformat().replace(":", ".")  # type: str

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

					installedPacksText += packTuple[0]

			sessionFormatting = (str(getattr(self.DebugGlobal, self._globalSessionID)),
								 str(getattr(self.DebugGlobal, self._globalSessionStartTime)),
								 self.IsContinuation(),
								 platform.system(),
								 platform.version(),
								 installedPacksText)

			return sessionTemplate.format(*sessionFormatting)
		except Exception as e:
			Log("Failed to get session information", This.Mod.Namespace, LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
			return "Failed to get session information"

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
			Log("Failed to get mod information", This.Mod.Namespace, LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
			return "Failed to get mod information"

	def _VerifyLogFile (self, logFilePath: str) -> None:
		with open(logFilePath, "rb") as logFile:
			if self._logStartBytes != logFile.read(len(self._logStartBytes)):
				raise Exception("The start of the log file doesn't match what was expected.")

			logFile.seek(-len(self._logEndBytes), os.SEEK_END)

			if self._logEndBytes != logFile.read():
				raise Exception("The end of the log file doesn't match what was expected.")

	@staticmethod
	def _ShowWriteFailureDialog (exception: Exception) -> None:
		Notifications.ShowNotification(queue = True,
									   title = lambda *args, **kwargs: Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Debug.Write_Notification.Title"),
									   text = lambda *args, **kwargs: Language.GetLocalizationStringByIdentifier(This.Mod.Namespace + ".System.Debug.Write_Notification.Text", FormatException(exception)),
									   expand_behavior = ui_dialog_notification.UiDialogNotification.UiDialogNotificationExpandBehavior.FORCE_EXPAND,
									   urgency = ui_dialog_notification.UiDialogNotification.UiDialogNotificationUrgency.URGENT)

def Log (message, namespace: str, level: LogLevels, group: str = None, owner: str = None, exception: BaseException = None,
		 logStack: bool = False, frame: types.FrameType = None, logToGame: bool = True, retryOnError: bool = True) -> None:
	_logger.Log(message, namespace, level, group = group, owner = owner, exception = exception, logStack = logStack, frame = frame, logToGame = logToGame, retryOnError = retryOnError)

def ChangeLogFile () -> None:
	_logger.ChangeLogFile()

def FormatException (exception: BaseException) -> str:
	return _logger.FormatException(exception)

def ConvertEALevelToLogLevel (level: int) -> LogLevels:
	return _logger.ConvertEALevelToLogLevel(level)

def ConvertLogLevelToEALevel (level: LogLevels) -> int:
	return _logger.ConvertLogLevelToEALevel(level)

def GetDateTimePathString (dateTime: datetime.datetime) -> str:
	return _logger.GetDateTimePathString(dateTime)

def _Setup () -> None:
	global _logger

	_logger = Logger(os.path.join(Paths.DebugPath, "Mods"), True, hostNamespace = This.Mod.Namespace)  # type: Logger

_Setup()
