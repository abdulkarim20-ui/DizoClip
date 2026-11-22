"""
Idle memory helpers.

trim_working_set() hands unused physical pages back to Windows (they fault back in on demand).
It lowers what Task Manager shows for an idle app; it does not change what the app has allocated.
"""
from __future__ import annotations

import gc
import sys


def trim_working_set() -> None:
    gc.collect()
    if sys.platform != "win32":
        return
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        k32.SetProcessWorkingSetSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
        k32.SetProcessWorkingSetSize(k32.GetCurrentProcess(), ctypes.c_size_t(-1), ctypes.c_size_t(-1))
    except Exception:
        pass


def freeze_startup_objects() -> None:
    """Call once after the first window is up: startup objects are long-lived, GC can skip them."""
    gc.collect()
    if hasattr(gc, "freeze"):
        gc.freeze()
