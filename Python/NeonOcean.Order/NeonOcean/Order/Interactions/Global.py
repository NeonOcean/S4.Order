import typing

from NeonOcean.Order import Debug, This, Websites
from NeonOcean.Order.Interactions.Support import Dependent, Events, Registration
from NeonOcean.Order.UI import Generic
from interactions.base import immediate_interaction

SupportNeonOceanInteractions = list()  # type: typing.List[typing.Type[SupportNeonOceanInteraction]]
VisitNeonOceanSiteInteractions = list()  # type: typing.List[typing.Type[VisitNeonOceanSiteInteraction]]

class SupportNeonOceanInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			SupportNeonOceanInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

	def OnStarted (self) -> None:
		try:
			Generic.ShowOpenBrowserDialog(Websites.GetNOSupportURL())
		except Exception as e:
			Debug.Log("Failed to show the support site with the open browser dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)

class VisitNeonOceanSiteInteraction(Dependent.DependentExtension, Events.EventsExtension, Registration.RegistrationExtension, immediate_interaction.ImmediateSuperInteraction):
	DependentMod = This.Mod

	def __init_subclass__ (cls, *args, **kwargs):
		try:
			super().__init_subclass__(*args, **kwargs)

			VisitNeonOceanSiteInteractions.append(cls)
		except Exception as e:
			Debug.Log("Failed to initialize new sub class for '" + cls.__name__ + "'.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
			raise e

	def OnStarted (self) -> None:
		try:
			Generic.ShowOpenBrowserDialog(Websites.GetNOMainURL())
		except Exception as e:
			Debug.Log("Failed to show the NeonOcean site with the open browser dialog.", This.Mod.Namespace, Debug.LogLevels.Exception, group = This.Mod.Namespace, owner = __name__, exception = e)
