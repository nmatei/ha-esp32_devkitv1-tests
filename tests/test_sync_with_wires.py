"""SYMBOLS must equal SETS[5] from bible-ai-preado, the source of truth.

Runs only when that checkout sits next to this one and node is installed.
"""

import json
import os
import shutil
import subprocess

import pytest

from alfabet_pe_fire.encoding import SYMBOLS

WIRES_JS = os.path.join(
    os.path.dirname(__file__), "..", "..", "bible-ai-preado", "src", "shared", "wires.js"
)


@pytest.mark.skipif(
    not os.path.exists(WIRES_JS) or not shutil.which("node"),
    reason="bible-ai-preado or node not available",
)
def test_symbols_match_wires_js():
    url = "file://" + os.path.abspath(WIRES_JS)
    out = subprocess.run(
        ["node", "--input-type=module", "-e",
         f'import {{ SETS }} from "{url}"; console.log(JSON.stringify(SETS[5].join("")))'],
        capture_output=True, text=True, check=True,
    ).stdout
    assert json.loads(out) == SYMBOLS
