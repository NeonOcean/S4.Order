import codecs

from NeonOcean.S4.Order import Debug, LoadingShared, This
from NeonOcean.S4.Order.Console import Command
from NeonOcean.S4.Order.Tools import Exceptions
from NeonOcean.S4.Order.UI import Generic

ShowURLCommand: Command.ConsoleCommand

def _Setup () -> None:
	global ShowURLCommand

	commandPrefix = This.Mod.Namespace.lower() + ".distribution"

	ShowURLCommand = Command.ConsoleCommand(_ShowURL, commandPrefix + ".show_url")

def _OnStart (cause: LoadingShared.LoadingCauses) -> None:
	if cause:
		pass

	ShowURLCommand.RegisterCommand()

def _OnStop (cause: LoadingShared.UnloadingCauses) -> None:
	if cause:
		pass

	ShowURLCommand.UnregisterCommand()

def _ShowURL (urlHex: str, _connection: int = None) -> None:
	try:
		if not isinstance(urlHex, str):
			raise Exceptions.IncorrectTypeException(urlHex, "urlHex", (str,))
	except Exception as e:
		Debug.Log("Incorrect types for command.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

	try:
		url = codecs.decode(urlHex, "hex").decode("utf-8")
		Generic.ShowOpenBrowserDialog(url)
	except Exception as e:
		Debug.Log("Failed to show distribution url.\nURL hex '" + str(urlHex) + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
		return

_Setup()
