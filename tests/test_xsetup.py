"""Xsetup layout: logical compositor coordinates to physical xrandr positions."""

from monique.models import MonitorConfig, Profile, Transform


def _positions(*monitors: MonitorConfig) -> dict[str, tuple[int, int]]:
    return Profile(name="test", monitors=list(monitors))._compute_physical_positions()


def test_side_by_side_monitors_are_not_stacked():
    """Issue #39: neighbours aligned bottom/centre have different y, same row."""
    left = MonitorConfig(name="DP-1", width=2560, height=1440, x=0, y=360)
    middle = MonitorConfig(name="DP-2", width=1920, height=1080, x=2560, y=0)
    right = MonitorConfig(name="HDMI-A-1", width=1920, height=1080, x=4480, y=0)

    assert _positions(left, middle, right) == {
        "DP-1": (0, 360), "DP-2": (2560, 0), "HDMI-A-1": (4480, 0),
    }


def test_unscaled_layout_is_already_physical():
    """With scale 1 the logical coordinates need no conversion at all."""
    top = MonitorConfig(name="DP-1", width=1920, height=1080, x=0, y=0)
    bottom = MonitorConfig(name="DP-2", width=1920, height=1080, x=0, y=1080)

    assert _positions(top, bottom) == {"DP-1": (0, 0), "DP-2": (0, 1080)}


def test_scaled_neighbour_is_pushed_out_by_the_physical_width():
    """A 4K at scale 2 is 1920 logical but 3840 physical: xrandr needs the real width."""
    hidpi = MonitorConfig(name="eDP-1", width=3840, height=2160, x=0, y=0, scale=2.0)
    external = MonitorConfig(name="DP-1", width=1920, height=1080, x=1920, y=0)

    assert _positions(hidpi, external) == {"eDP-1": (0, 0), "DP-1": (3840, 0)}


def test_vertical_offset_within_a_row_is_converted_to_physical_pixels():
    hidpi = MonitorConfig(name="eDP-1", width=3840, height=2160, x=0, y=0, scale=2.0)
    external = MonitorConfig(name="DP-1", width=1920, height=1080, x=1920, y=270)

    assert _positions(hidpi, external) == {"eDP-1": (0, 0), "DP-1": (3840, 270)}


def test_rows_stack_by_physical_height_not_logical():
    """The scaled monitor is 1080 logical tall but occupies 2160 physical pixels."""
    top = MonitorConfig(name="eDP-1", width=3840, height=2160, x=0, y=0, scale=2.0)
    bottom = MonitorConfig(name="DP-1", width=1920, height=1080, x=0, y=1080)

    assert _positions(top, bottom) == {"eDP-1": (0, 0), "DP-1": (0, 2160)}


def test_rotated_monitor_occupies_its_rotated_width():
    landscape = MonitorConfig(name="DP-1", width=2560, height=1440, x=0, y=0)
    portrait = MonitorConfig(
        name="DP-2", width=1920, height=1080, x=2560, y=0, transform=Transform.ROTATE_90,
    )
    right = MonitorConfig(name="DP-3", width=1920, height=1080, x=3640, y=0)

    positions = _positions(landscape, portrait, right)

    assert positions["DP-2"] == (2560, 0)
    assert positions["DP-3"] == (2560 + 1080, 0)  # portrait is 1080 wide once rotated


def test_disabled_monitors_are_left_out():
    active = MonitorConfig(name="DP-1", width=1920, height=1080, x=0, y=0)
    off = MonitorConfig(name="DP-2", width=1920, height=1080, x=1920, y=0, enabled=False)

    assert _positions(active, off) == {"DP-1": (0, 0)}


def test_generated_script_carries_the_layout_and_framebuffer():
    left = MonitorConfig(name="DP-1", description="LG", width=2560, height=1440, x=0, y=360)
    right = MonitorConfig(name="DP-2", description="AOC", width=1920, height=1080, x=2560, y=0)

    script = Profile(name="test", monitors=[left, right]).generate_xsetup_script()

    assert "--pos 0x360" in script
    assert "--pos 2560x0" in script
    assert "4480x1800" in script  # framebuffer spans the whole layout
