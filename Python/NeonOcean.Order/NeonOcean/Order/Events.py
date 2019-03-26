import typing

from NeonOcean.Order import Mods
from NeonOcean.Order.Tools import Exceptions

_onModUnloadLevels = list()  # type: typing.List[Level]
_onModReloadLevels = list()  # type: typing.List[Level]
_onLoaded = list()  # type: typing.List[Level]

class Level:
	def __init__ (self, level: typing.Union[int, float]):
		"""
		A container for callbacks of a specific level.
		Register a callback by using the Register method, to call the callbacks use the Activate method.
		:type level: int | float
		"""

		if not isinstance(level, int) and not isinstance(level, float):
			raise Exceptions.IncorrectTypeException(level, "level", (int, float))

		self.Level = level  # type: typing.Union[int, float]
		self.Callbacks = list()  # type: typing.List[typing.Callable]

	def Activate (self, *args, **kwargs) -> None:
		"""
		Activates the callbacks, Callbacks will be called in the order they are registered.
		:rtype: None
		"""

		for callback in self.Callbacks:
			callback(*args, **kwargs)

	def Register (self, callback: typing.Callable) -> None:
		"""
		Registers a callback to this level.
		Callbacks will be called in the order they are registered, The first callback to be registered will also be the first to be called.
		:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
		:type callback: typing.Callable
		:rtype: None
		"""

		if not isinstance(callback, typing.Callable):
			raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

		if not callback in self.Callbacks:
			self.Callbacks.append(callback)

	def Unregister (self, callback: typing.Callable) -> None:
		"""
		Removes a callback from the registry
		:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
		:type callback: typing.Callable
		:rtype: None
		"""

		if not isinstance(callback, typing.Callable):
			raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

		if callback in self.Callbacks:
			self.Callbacks.remove(callback)

def SortLevels (levels: typing.List[Level]) -> typing.List[Level]:
	"""
	:param levels: A list of levels needing to be sorted.
	:type levels: typing.List[Level]
	:return: A new list containing the input levels in order from lowest level to highest level.
	:rtype: typing.List[Level]
	"""

	if not isinstance(levels, list):
		raise Exceptions.IncorrectTypeException(levels, "levels", (list,))

	for levelIndex in range(len(levels)):  # type: int
		if not isinstance(levels[levelIndex], Level):
			raise Exceptions.IncorrectTypeException(levels[levelIndex], "levels[%d]" % levelIndex, (Level,))

	levels = levels.copy()
	sortedLevels = list()

	while len(levels) != 0:
		selectedIndex = -1  # type: int

		for checkingIndex in range(len(levels)):  # type: int
			if selectedIndex == -1:
				selectedIndex = checkingIndex

			if levels[selectedIndex].Level > levels[checkingIndex].Level:
				selectedIndex = checkingIndex
				continue

		sortedLevels.append(levels[selectedIndex])
		levels.pop(selectedIndex)

	return sortedLevels

def ActivateOnModUnload (mod: Mods.Mod, exiting: bool) -> None:
	"""
	Activates the event 'OnModUnload'
	Callbacks will be called based on their level from lowest to highest, callbacks with the same level will be called in the order they were registered.

	:param mod: A reference the the unloading mod in question.
	:type mod: Mods.Mod
	:param exiting: Whether or not the mod is unloading because the application is closing.
	:type exiting: bool
	:rtype: None
	"""

	if not isinstance(mod, Mods.Mod):
		raise Exceptions.IncorrectTypeException(mod, "mod", (Mods.Mod,))

	if not isinstance(exiting, bool):
		raise Exceptions.IncorrectTypeException(exiting, "exiting", (bool,))

	sortedLevels = SortLevels(_onModUnloadLevels)  # type: typing.List[Level]

	for level in sortedLevels:  # type: Level
		level.Activate(mod, exiting)

def RegisterOnModUnload (callback: typing.Callable, level: typing.Union[int, float] = None) -> None:
	"""
	Registers a callback for the event 'OnModUnload'
	This event is typically called just before a mod is unloaded.

	:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
					 Callbacks for this event should take two arguments with the types: NeonOcean.Main.Mods.Mod and bool.
					 The first argument is a reference to the mod being unloaded.
					 The second argument is a boolean denoting whether or not the mod is being unloaded because the application is closing.

	:type callback: typing.Callable
	:param level: Determines what order the callbacks will be called in, lower levels are called first followed by higher levels.
					 Callbacks with the same level will be called in the order they were registered.
	:type level: int | float
	:rtype: None
	"""

	if level is None:
		level = 0

	if not isinstance(level, int) and not isinstance(level, float):
		raise Exceptions.IncorrectTypeException(level, "level", (int, float))

	if not isinstance(callback, typing.Callable):
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	levelObject = None  # type: Level

	for checkingLevelObject in _onModUnloadLevels:  # type: Level
		if checkingLevelObject.Level == level:
			levelObject = checkingLevelObject

	if levelObject is None:
		levelObject = Level(level)

	levelObject.Register(callback)
	_onModUnloadLevels.append(levelObject)

def UnregisterOnModUnload (callback: typing.Callable) -> None:
	"""
	Removes the callback from the registry in all levels for the event 'OnModUnload'.
	This will do nothing if no such callback is registered.

	:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
	:type callback: typing.Callable
	:rtype: None
	"""

	if not isinstance(callback, typing.Callable):
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	for level in _onModUnloadLevels:  # type: Level
		level.Unregister(callback)

def ActivateOnModReload (mod: Mods.Mod) -> None:
	"""
	Activates the event 'OnModReload'
	Callbacks will be called based on their level from lowest to highest, callbacks with the same level will be called in the order they were registered.

	:param mod: A reference the the reloading mod in question.
	:type mod: Mods.Mod
	:rtype: None
	"""

	if not isinstance(mod, Mods.Mod):
		raise Exceptions.IncorrectTypeException(mod, "mod", (Mods.Mod,))

	sortedLevels = SortLevels(_onModUnloadLevels)  # type: typing.List[Level]

	for level in sortedLevels:  # type: Level
		level.Activate(mod)

def RegisterOnModReload (callback: typing.Callable, level: typing.Union[int, float] = None) -> None:
	"""
	Registers a callback for the event 'OnModReload'
	This event is typically called just before a mod is reloaded.

	:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
					 Callbacks for this event should take one argument with the type: NeonOcean.Main.Mods.Mod.
					 The argument is a reference to the mod being reloaded.

	:type callback: typing.Callable
	:param level: Determines what order the callbacks will be called in, lower levels are called first followed by higher levels.
					 Callbacks with the same level will be called in the order they were registered.
	:type level: int | float
	:rtype: None
	"""

	if level is None:
		level = 0

	if not isinstance(level, int) and not isinstance(level, float):
		raise Exceptions.IncorrectTypeException(level, "level", (int, float))

	if not isinstance(callback, typing.Callable):
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	levelObject = None  # type: Level

	for checkingLevelObject in _onModReloadLevels:  # type: Level
		if checkingLevelObject.Level == level:
			levelObject = checkingLevelObject

	if levelObject is None:
		levelObject = Level(level)

	levelObject.Register(callback)
	_onModReloadLevels.append(levelObject)

def UnregisterOnModReload (callback: typing.Callable) -> None:
	"""
	Removes the callback from the registry in all levels for the event 'OnModReload'.
	This will do nothing if no such callback is registered.

	:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
	:type callback: typing.Callable
	:rtype: None
	"""

	if not isinstance(callback, typing.Callable):
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	for level in _onModReloadLevels:  # type: Level
		level.Unregister(callback)

def ActivateOnLoaded () -> None:
	"""
	Activates the event 'OnLoaded'
	Callbacks will be called based on their level from lowest to highest, callbacks with the same level will be called in the order they were registered.

	:rtype: None
	"""

	sortedLevels = SortLevels(_onLoaded)  # type: typing.List[Level]

	for level in sortedLevels:  # type: Level
		level.Activate()

def RegisterOnLoaded (callback: typing.Callable, level: typing.Union[int, float] = None) -> None:
	"""
	Registers a callback for the event 'OnLoaded'
	This event is typically called after all modules are loaded.

	:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
					 Callbacks for this event should take no arguments.

	:type callback: typing.Callable
	:param level: Determines what order the callbacks will be called in, lower levels are called first followed by higher levels.
					 Callbacks with the same level will be called in the order they were registered.
	:type level: int | float
	:rtype: None
	"""

	if level is None:
		level = 0

	if not isinstance(level, int) and not isinstance(level, float):
		raise Exceptions.IncorrectTypeException(level, "level", (int, float))

	if not isinstance(callback, typing.Callable):
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	levelObject = None  # type: Level

	for checkingLevelObject in _onLoaded:  # type: Level
		if checkingLevelObject.Level == level:
			levelObject = checkingLevelObject

	if levelObject is None:
		levelObject = Level(level)

	levelObject.Register(callback)
	_onLoaded.append(levelObject)

def UnregisterOnLoaded (callback: typing.Callable) -> None:
	"""
	Removes the callback from the registry in all levels for the event 'OnLoaded'.
	This will do nothing if no such callback is registered.

	:param callback: Callbacks should be functions, the use of callbacks that are not functions has not been tested.
	:type callback: typing.Callable
	:rtype: None
	"""

	if not isinstance(callback, typing.Callable):
		raise Exceptions.IncorrectTypeException(callback, "callback", ("Callable",))

	for level in _onLoaded:  # type: Level
		level.Unregister(callback)
