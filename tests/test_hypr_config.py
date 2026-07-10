"""Which Hyprland config files get written, per hypr_config_format setting."""

import pytest

from monique.hypr_config import hyprland_config_paths, write_hyprland_configs
from monique.utils import (
    get_hypr_config_format,
    hyprland_config_dir,
    normalize_hypr_format,
    save_app_settings,
)


def _written(conf_dir):
    return sorted(p.name for p in conf_dir.iterdir())


@pytest.mark.parametrize("fmt,expected", [
    ("both", ["monitors.conf", "monitors.lua"]),
    ("legacy", ["monitors.conf"]),
    ("lua", ["monitors.lua"]),
])
def test_format_selects_which_files_are_written(profile, fmt, expected):
    write_hyprland_configs(profile, fmt=fmt)

    assert _written(hyprland_config_dir()) == expected


@pytest.mark.parametrize("fmt", ["both", "legacy", "lua"])
def test_declared_paths_match_written_files(profile, fmt):
    """hyprland_config_paths() must not promise a file the writer skips."""
    declared = write_hyprland_configs(profile, fmt=fmt)

    assert declared == hyprland_config_paths(fmt)
    assert all(p.exists() for p in declared)


def test_format_defaults_to_the_setting_when_unset(profile):
    """apply_profile() passes no format; the daemon relies on this path."""
    save_app_settings({"hypr_config_format": "lua"})

    write_hyprland_configs(profile)

    assert _written(hyprland_config_dir()) == ["monitors.lua"]


@pytest.mark.parametrize("value", ["garbage", "", None, 42, ["lua"]])
def test_unknown_setting_falls_back_to_both(value):
    """A hand-edited settings.json must not break apply."""
    assert normalize_hypr_format(value) == "both"


def test_missing_setting_falls_back_to_both():
    save_app_settings({})

    assert get_hypr_config_format() == "both"


def test_existing_config_is_backed_up_before_overwrite(profile):
    write_hyprland_configs(profile, fmt="legacy")
    conf = hyprland_config_dir() / "monitors.conf"
    original = conf.read_text()

    profile.monitors[0].width = 1920
    write_hyprland_configs(profile, fmt="legacy")

    assert conf.read_text() != original
    assert conf.with_suffix(".conf.bak").read_text() == original
