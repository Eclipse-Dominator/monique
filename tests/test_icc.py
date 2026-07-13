"""ICC profiles: config output, version gating, and read-back after a reload."""

import pytest

from monique.hypr_config import read_icc_profiles, write_hyprland_configs
from monique.models import MonitorConfig, Profile

ICC = "/usr/share/color/icc/LG-4K.icc"


@pytest.fixture
def icc_monitor(monitor):
    """A monitor with both an ICC profile and a cm preset set."""
    monitor.icc_profile = ICC
    monitor.color_management = "srgb"
    return monitor


def test_v2_block_emits_icc_when_supported(icc_monitor):
    assert f"icc = {ICC}" in icc_monitor.to_hyprland_v2_block(supports_icc=True)


def test_lua_block_emits_icc_when_supported(icc_monitor):
    assert f'icc = "{ICC}"' in icc_monitor.to_hyprland_lua_block(supports_icc=True)


@pytest.mark.parametrize("render", ["to_hyprland_v2_block", "to_hyprland_lua_block"])
def test_icc_replaces_cm(icc_monitor, render):
    """Hyprland ignores cm when an ICC profile is set (CMonitor::applyMonitorRule)."""
    block = getattr(icc_monitor, render)(supports_icc=True)

    assert "icc" in block
    assert "cm" not in block


@pytest.mark.parametrize("render", ["to_hyprland_v2_block", "to_hyprland_lua_block"])
def test_older_hyprland_gets_cm_instead_of_icc(icc_monitor, render):
    """Both writers must gate on supports_icc; the Lua one used to ignore it."""
    block = getattr(icc_monitor, render)(supports_icc=False)

    assert "icc" not in block
    assert "srgb" in block


def test_round_trip_preserves_the_icc_profile(icc_monitor):
    assert MonitorConfig.from_dict(icc_monitor.to_dict()).icc_profile == ICC


def test_profile_saved_before_icc_existed_still_loads(monitor):
    saved = monitor.to_dict()
    del saved["icc_profile"]

    assert MonitorConfig.from_dict(saved).icc_profile == ""


@pytest.mark.parametrize("fmt", ["legacy", "lua", "both"])
def test_icc_survives_a_reload_from_the_written_config(icc_monitor, fmt):
    """hyprctl never reports the ICC profile, so the config is the only source."""
    profile = Profile(name="test", monitors=[icc_monitor])
    write_hyprland_configs(profile, fmt=fmt, use_v2=True, supports_icc=True)

    assert read_icc_profiles(fmt) == {"DP-1": ICC}


def test_read_back_keys_by_description_when_the_config_uses_it(icc_monitor):
    profile = Profile(name="test", monitors=[icc_monitor])
    write_hyprland_configs(
        profile, fmt="both", use_description=True, use_v2=True, supports_icc=True,
    )

    assert read_icc_profiles("both") == {"desc:Mon A": ICC}


def test_read_back_is_empty_when_no_monitor_has_an_icc_profile(profile):
    write_hyprland_configs(profile, fmt="both", use_v2=True, supports_icc=True)

    assert read_icc_profiles("both") == {}


def test_read_back_is_empty_for_legacy_monitor_lines(icc_monitor):
    """``monitor=`` lines predate ICC support: there is nothing to read back."""
    profile = Profile(name="test", monitors=[icc_monitor])
    write_hyprland_configs(profile, fmt="legacy", use_v2=False, supports_icc=True)

    assert read_icc_profiles("legacy") == {}
