from __future__ import annotations

import enum_lib

class LoadingCauses(enum_lib.IntEnum):
	Normal = 0  # type: LoadingCauses
	Reloading = 1  # type: LoadingCauses

class UnloadingCauses(enum_lib.IntEnum):
	Normal = 0  # type: UnloadingCauses
	Reloading = 1  # type: UnloadingCauses
	Exiting = 2  # type: UnloadingCauses
