"""Fixture condivise: ogni test gira contro una config dir isolata."""

import pytest

from monique import utils


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point every ``*_config_dir()`` at a throwaway directory.

    Also clears the ``--config-dir`` runtime override, which is module-level
    state and would otherwise leak between tests.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr(utils, "_runtime_config_dir", None)
    return tmp_path


@pytest.fixture
def monitor():
    """A single enabled monitor, enough to render every config format."""
    from monique.models import MonitorConfig

    return MonitorConfig(
        name="DP-1", description="Mon A", width=2560, height=1440,
        refresh_rate=165.0, x=0, y=0, scale=1.0,
    )


@pytest.fixture
def profile(monitor):
    from monique.models import Profile

    return Profile(name="test", monitors=[monitor])
