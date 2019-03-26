import typing

import zone
from NeonOcean.Order import Debug, This, Mods
from NeonOcean.Order.Tools import Exceptions, Patcher, Types
from sims4.tuning import instance_manager

_controllers = list()  # type: typing.List[typing.Type[Controller]]

class Controller:
	Host = This.Mod  # type: Mods.Mod
	Enabled = True  # type: bool
	Reliable = False  # type: bool

	_level = 0  # type: float

	def __init_subclass__ (cls, **kwargs):
		SetupController(cls)

	@classmethod
	def GetLevel (cls) -> float:
		return cls._level

	@classmethod
	def SetLevel (cls, value) -> None:
		cls._level = value
		_SortControllers()

	@classmethod
	def OnInitializeSubclass (cls) -> None:
		pass

	@classmethod
	def OnInstanceManagerLoaded (cls, instanceManager: instance_manager.InstanceManager) -> None:
		pass

	@classmethod
	def OnLoadingScreenAnimationFinished (cls, zoneReference: zone.Zone) -> None:
		pass

def SetupController (controller: typing.Type[Controller]) -> None:
	if not issubclass(controller, Controller):
		raise Exceptions.IncorrectTypeException(controller, "controller", (Controller,))

	if controller in _controllers:
		return

	_Register(controller)

	_SortControllers()
	OnInitializeSubclass()

def OnInitializeSubclass () -> None:
	for controller in _controllers:  # type: typing.Type[Controller]
		try:
			if not controller.Enabled:
				continue

			if not controller.Host.IsLoaded() and not controller.Reliable:
				continue

			controller.OnInitializeSubclass()
		except Exception as e:
			Debug.Log("Failed to run 'OnInitializeSubclass' for '" + Types.GetFullName(controller) + "'", controller.Host.Namespace, Debug.LogLevels.Exception, group = controller.Host.Namespace, owner = __name__, exception = e)

@Patcher.Decorator(instance_manager.InstanceManager, "on_start", permanent = True)
def OnInstanceManagerLoaded (self: instance_manager.InstanceManager) -> None:
	for controller in _controllers:  # type: typing.Type[Controller]
		try:
			if not controller.Enabled:
				continue

			if not controller.Host.IsLoaded() and not controller.Reliable:
				continue

			controller.OnInstanceManagerLoaded(self)
		except Exception as e:
			Debug.Log("Failed to run 'OnInstanceManagerLoaded' for '" + Types.GetFullName(controller) + "'", controller.Host.Namespace, Debug.LogLevels.Exception, group = controller.Host.Namespace, owner = __name__, exception = e)

@Patcher.Decorator(zone.Zone, "on_loading_screen_animation_finished", permanent = True)
def OnLoadingScreenAnimationFinished (self: zone.Zone) -> None:
	for controller in _controllers:  # type: typing.Type[Controller]
		try:
			if not controller.Enabled:
				continue

			if not controller.Host.IsLoaded() and not controller.Reliable:
				continue

			controller.OnLoadingScreenAnimationFinished(self)
		except Exception as e:
			Debug.Log("Failed to run 'OnLoadingScreenAnimationFinished' for '" + Types.GetFullName(controller) + "'", controller.Host.Namespace, Debug.LogLevels.Exception, group = controller.Host.Namespace, owner = __name__, exception = e)

def _Register (controller: typing.Type[Controller]) -> None:
	if not controller in _controllers:
		_controllers.append(controller)

def _SortControllers () -> None:
	global _controllers

	controllers = _controllers.copy()  # type: typing.List[typing.Type[Controller]]

	sortedControllers = list()

	for loopCount in range(len(controllers)):  # type: int
		targetIndex = None  # type: int

		for currentIndex in range(len(controllers)):
			if targetIndex is None:
				targetIndex = currentIndex
				continue

			if controllers[currentIndex].GetLevel() != controllers[targetIndex].GetLevel():
				if controllers[currentIndex].GetLevel() < controllers[targetIndex].GetLevel():
					targetIndex = currentIndex
					continue
			else:
				if controllers[currentIndex].__module__ < controllers[targetIndex].__module__:
					targetIndex = currentIndex
					continue

		sortedControllers.append(controllers[targetIndex])
		controllers.pop(targetIndex)

		_controllers = sortedControllers