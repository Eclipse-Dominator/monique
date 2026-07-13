"""Default monitor: Niri focus-at-startup and Hyprland cursor:default_monitor."""

import pytest

from monique.hypr_config import read_default_monitor, write_hyprland_configs
from monique.models import MonitorConfig, Profile, monitor_matches_identifier
from monique.niri import read_focus_at_startup


@pytest.fixture
def two_monitors():
    primary = MonitorConfig(
        name="DP-1", description="Mon A", width=2560, height=1440, x=0, y=0,
        focus_at_startup=True,
    )
    secondary = MonitorConfig(
        name="DP-2", description="Mon B", width=1920, height=1080, x=2560, y=0,
    )
    return Profile(name="test", monitors=[primary, secondary])


def test_niri_block_marks_the_default_monitor(two_monitors):
    primary, secondary = two_monitors.monitors

    assert "focus-at-startup" in primary.to_niri_block()
    assert "focus-at-startup" not in secondary.to_niri_block()


def test_niri_skips_the_flag_on_a_disabled_monitor():
    off = MonitorConfig(name="DP-1", width=1920, height=1080, focus_at_startup=True,
                        enabled=False)

    assert "focus-at-startup" not in off.to_niri_block()


def test_hyprland_config_sets_cursor_default_monitor(two_monitors):
    config = two_monitors.generate_config(use_description=True)

    assert "cursor:default_monitor = desc:Mon A" in config


def test_hyprland_config_falls_back_to_the_port_name(two_monitors):
    config = two_monitors.generate_config(use_description=False)

    assert "cursor:default_monitor = DP-1" in config


def test_lua_config_sets_cursor_default_monitor(two_monitors):
    """hl.config() maps cursor:default_monitor to cursor.default_monitor."""
    config = two_monitors.generate_lua_config(use_description=True)

    assert 'cursor = { default_monitor = "desc:Mon A" }' in config


def test_no_flag_means_no_cursor_line(two_monitors):
    for m in two_monitors.monitors:
        m.focus_at_startup = False

    assert "default_monitor" not in two_monitors.generate_config()
    assert "default_monitor" not in two_monitors.generate_lua_config()


def test_only_the_first_flagged_monitor_reaches_hyprland(two_monitors):
    """The Hyprland option holds a single name, so generation must be decisive."""
    for m in two_monitors.monitors:
        m.focus_at_startup = True

    config = two_monitors.generate_config(use_description=True)

    assert config.count("cursor:default_monitor") == 1
    assert "cursor:default_monitor = desc:Mon A" in config


def test_round_trip_preserves_the_flag(two_monitors):
    primary = two_monitors.monitors[0]

    assert MonitorConfig.from_dict(primary.to_dict()).focus_at_startup is True


@pytest.mark.parametrize("fmt", ["legacy", "lua", "both"])
def test_hyprland_flag_survives_a_reload(two_monitors, fmt):
    """Neither hyprctl nor niri report it: the config is the only source."""
    write_hyprland_configs(two_monitors, fmt=fmt, use_description=True, use_v2=True)

    assert read_default_monitor(fmt) == "desc:Mon A"


def test_niri_flag_survives_a_reload(two_monitors):
    from monique.config_paths import niri_monitors_path

    conf = niri_monitors_path()
    conf.parent.mkdir(parents=True, exist_ok=True)
    conf.write_text(two_monitors.generate_niri_config(use_description=False))

    assert read_focus_at_startup() == ["DP-1"]


@pytest.mark.parametrize("identifier,expected", [
    ("DP-1", True),
    ("desc:Mon A", True),
    ("Mon A", True),
    ("PNP(Mon) A", True),  # forma nativa di Niri, normalizzata come in __post_init__
    ("DP-2", False),
    ("desc:Mon B", False),
    ("", False),
])
def test_identifier_matching(identifier, expected):
    monitor = MonitorConfig(name="DP-1", description="Mon A")

    assert monitor_matches_identifier(monitor, identifier) is expected
