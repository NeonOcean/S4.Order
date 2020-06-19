from __future__ import annotations

from __future__ import annotations

from NeonOcean.S4.Order import Mods

try:
	Mod = Mods.GetMod("NeonOcean.S4.Order")  # type: Mods.Mod
except Exception as e:
	raise Exception("Cannot find self in mod list.") from e
