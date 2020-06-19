from __future__ import annotations

import inspect

def GetLineNumber () -> int:
	"""
	Get the line number at which this function was called.
	"""

	lastFrame = inspect.currentframe().f_back

	if lastFrame is None:
		return -1

	return lastFrame.f_lineno
