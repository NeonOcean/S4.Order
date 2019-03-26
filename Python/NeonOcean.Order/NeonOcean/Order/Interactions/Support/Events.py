class EventsExtension:
	def __init__ (self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# noinspection PyUnusedLocal
		def OnFinishingCallback (interaction) -> None:
			self.OnFinishing()

		if hasattr(self, "register_on_finishing_callback"):
			self.register_on_finishing_callback(OnFinishingCallback)

	def OnStarted (self) -> None:
		pass

	def OnFinishing (self) -> None:
		pass

	def _trigger_interaction_start_event (self):
		superObject = super()

		if hasattr(superObject, "_trigger_interaction_start_event"):
			# noinspection PyProtectedMember
			superObject._trigger_interaction_start_event()

		self.OnStarted()
