import interactions
from NeonOcean.Order import Language, Mods, This
from event_testing import results, test_base
from sims4.tuning import tunable

DisabledTooltip = Language.String(This.Mod.Namespace + ".System.Interactions.Support.Dependent.Disabled_Tooltip")

class DependentTest(test_base.BaseTest):
	# noinspection SpellCheckingInspection
	def __call__ (self, affordance):
		if affordance is None:
			return results.TestResult.NONE

		if not issubclass(affordance, DependentExtension):
			return results.TestResult.TRUE

		if affordance.DependentOnMod:
			if affordance.DependentMod is not None:
				if not affordance.DependentMod.IsLoaded():
					return results.TestResult(False, tooltip = DisabledTooltip.GetCallableLocalizationString(affordance.DependentMod.Namespace))

		return results.TestResult.TRUE

	def get_expected_args (self):
		# noinspection SpellCheckingInspection
		return {
			'affordance': interactions.ParticipantType.Affordance
		}

class DependentExtension:
	# noinspection SpellCheckingInspection
	INSTANCE_TUNABLES = {
		"DependentOnMod": tunable.Tunable(description = "Whether or not the interaction will be disabled it the mod is not loaded.", tunable_type = bool, default = True),
	}

	DependentMod = None  # type: Mods.Mod

	DependentOnMod: bool

	def __init_subclass__ (cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)

		if hasattr(cls, "add_additional_test"):
			cls.add_additional_test(DependentTest())
