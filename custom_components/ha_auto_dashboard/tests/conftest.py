"""Shared fixtures for ha_auto_dashboard tests."""
import shutil
from pathlib import Path

import pytest

from custom_components.ha_auto_dashboard.const import DASHBOARD_OUTPUT_DIR

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make custom_components/ discoverable during tests."""
    yield


@pytest.fixture(scope="session", autouse=True)
def _warm_up_pycares_shutdown_thread():
    """`aiodns`/`pycares` (a hard `homeassistant` dependency, used by
    aiohttp's DNS resolver) lazily starts a process-global background
    thread named `_run_safe_shutdown_loop` the first time any test opens
    a real aiohttp client (e.g. via the `hass_ws_client` fixture). That
    thread is a permanent daemon for the life of the test process, so
    whichever test happens to trigger it first fails this suite's
    per-test "no lingering threads" check. Start it once here, before any
    test's thread snapshot is taken, so it's already present for all of
    them."""
    import pycares

    pycares.Channel()


@pytest.fixture(autouse=True)
def _clean_dashboards_output(hass):
    """The test hass fixture's config dir is a fixed on-disk path shared
    across test runs, not a fresh tmp dir per test - clear out any
    dashboard files a previous test left behind so tests that assert on
    "nothing written yet"/diff content aren't polluted by leftover state."""
    output_dir = Path(hass.config.config_dir) / DASHBOARD_OUTPUT_DIR
    shutil.rmtree(output_dir, ignore_errors=True)
    yield
    shutil.rmtree(output_dir, ignore_errors=True)
