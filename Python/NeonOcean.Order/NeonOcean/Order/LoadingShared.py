import enum

class LoadingCauses(enum.Int):
	Normal = 0  # type: LoadingCauses
	Reloading = 1  # type: LoadingCauses

class UnloadingCauses(enum.Int):
	Normal = 0  # type: UnloadingCauses
	Reloading = 1  # type: UnloadingCauses
	Exiting = 2  # type: UnloadingCauses
