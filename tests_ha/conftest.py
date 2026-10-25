"""Integration tests against a real Home Assistant core (heavier, optional).

Needs ``pytest-homeassistant-custom-component`` (it pulls in homeassistant), in
its own venv: see README "Development".
"""

import os
import sys

# Import our custom_components before the plugin puts its own testing_config
# package of the same name on sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import custom_components  # noqa: E402,F401
import pytest  # noqa: E402

pytest_plugins = "pytest_homeassistant_custom_component"


def pytest_configure(config):
    config.option.asyncio_mode = "auto"


@pytest.fixture(autouse=True)
def auto_enable(enable_custom_integrations):
    yield
