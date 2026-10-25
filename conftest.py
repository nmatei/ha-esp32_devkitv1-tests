"""Test bootstrap.

The package ``__init__`` imports Home Assistant, which isn't available in a
lightweight unit-test environment. ``const``, ``encoding``, ``morse`` and ``player`` are
deliberately HA-free, so we load them under a synthetic ``alfabet_pe_fire``
package that skips the real ``__init__`` while still supporting their relative
imports.
"""

import importlib.util
import os
import sys
import types

ROOT = os.path.dirname(__file__)
_BASE = os.path.join(ROOT, "custom_components", "alfabet_pe_fire")
_PKG = "alfabet_pe_fire"

if _PKG not in sys.modules:
    pkg = types.ModuleType(_PKG)
    pkg.__path__ = [_BASE]
    sys.modules[_PKG] = pkg

    for _name in ("const", "encoding", "morse", "player"):
        _spec = importlib.util.spec_from_file_location(
            f"{_PKG}.{_name}", os.path.join(_BASE, f"{_name}.py")
        )
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules[f"{_PKG}.{_name}"] = _mod
        _spec.loader.exec_module(_mod)
