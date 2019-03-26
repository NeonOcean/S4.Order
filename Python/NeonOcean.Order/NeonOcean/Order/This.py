from NeonOcean.Order import Mods

try:
	Mod = Mods.Order  # type: Mods.Mod
except Exception as e:
	raise Exception("Cannot find self in mod list.") from e
