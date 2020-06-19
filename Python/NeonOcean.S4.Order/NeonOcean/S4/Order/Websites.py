from __future__ import annotations

import typing

from NeonOcean.S4.Order import Mods
from NeonOcean.S4.Order.Abstract import Settings as AbstractSettings

def GetNOMainURL () -> str:
	return _noMainURL

def GetNOMainModURL (mod: Mods.Mod) -> str:
	return GetNOMainURL() + "/mods/s4/" + mod.Name.lower()

def GetNODocumentationURL () -> str:
	return _noDocumentationBaseURL

def GetNODocumentationModURL (mod: Mods.Mod) -> str:
	return GetNODocumentationURL() + "/s4/" + mod.Name.lower()

def GetNODocumentationModSettingURL (setting: typing.Type[AbstractSettings.SettingAbstract], mod: Mods.Mod) -> str:
	return GetNODocumentationModURL(mod) + "/settings/mod/" + setting.Key.replace("_", "-").lower()

def GetNOSupportURL () -> str:
	return _noSupportBaseURL

def GetNOSupportModPreviewPostsURL (mod: Mods.Mod) -> str:
	return GetNOSupportURL() + "/posts?tag=" + mod.Name.lower() + "%20preview"

_noMainURL = "https://www.neonoceancreations.com"  # type: str
_noDocumentationBaseURL = "https://doc.mods.neonoceancreations.com"  # type: str
_noSupportBaseURL = "https://www.patreon.com/neonocean"  # type: str
