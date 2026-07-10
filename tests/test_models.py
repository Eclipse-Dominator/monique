"""WorkspaceRule serialisation to and from the Hyprland Lua config."""

import pytest

from monique.models import WorkspaceRule


def _round_trip(rule: WorkspaceRule) -> WorkspaceRule:
    """Serialise a rule to a Lua line and parse it back."""
    parsed = WorkspaceRule.from_hyprland_lua_line(rule.to_hyprland_lua_line())
    assert parsed is not None
    return parsed


def test_round_trip_preserves_plain_fields():
    rule = WorkspaceRule(workspace="1", monitor="DP-1", default=True,
                         persistent=True, gapsin=5, gapsout=10, bordersize=2)
    parsed = _round_trip(rule)

    assert parsed.workspace == "1"
    assert parsed.monitor == "DP-1"
    assert parsed.default is True
    assert parsed.persistent is True
    assert parsed.gapsin == 5
    assert parsed.gapsout == 10
    assert parsed.bordersize == 2


def test_round_trip_survives_comma_inside_string():
    """A naive split(",") would truncate on_created_empty here."""
    command = "foot -e sh -c 'echo a,b'"
    parsed = _round_trip(WorkspaceRule(workspace="2", on_created_empty=command))

    assert parsed.on_created_empty == command


@pytest.mark.parametrize("command", [
    'echo "quoted"',
    "back\\slash",
    "trailing\\",
])
def test_round_trip_survives_escaped_characters(command):
    parsed = _round_trip(WorkspaceRule(workspace="3", on_created_empty=command))

    assert parsed.on_created_empty == command


def test_monitor_identifier_keeps_desc_prefix():
    rule = WorkspaceRule(workspace="1", monitor="DP-1")
    line = rule.to_hyprland_lua_line(name_to_id={"DP-1": "desc:Mon A"})

    assert WorkspaceRule.from_hyprland_lua_line(line).monitor == "desc:Mon A"


@pytest.mark.parametrize("field,lua_field", [("rounding", "no_rounding"),
                                             ("border", "no_border")])
def test_negated_flags_invert_on_the_way_out(field, lua_field):
    """Lua spells these as no_* booleans; legacy uses 0/1 integers."""
    disabled = WorkspaceRule(workspace="1", **{field: 0})
    assert f"{lua_field} = true" in disabled.to_hyprland_lua_line()
    assert getattr(_round_trip(disabled), field) == 0

    enabled = WorkspaceRule(workspace="1", **{field: 1})
    assert f"{lua_field} = false" in enabled.to_hyprland_lua_line()
    assert getattr(_round_trip(enabled), field) == 1


@pytest.mark.parametrize("line", [
    "",
    "-- a comment",
    'hl.monitor({ output = "DP-1", })',
    "workspace=1, monitor:DP-1",          # the legacy format, not Lua
    "hl.workspace_rule({ monitor = 1 })",  # no workspace field
    "hl.workspace_rule(",                  # truncated
])
def test_non_rule_lines_are_ignored(line):
    assert WorkspaceRule.from_hyprland_lua_line(line) is None


def test_unset_fields_are_omitted_from_the_lua_line():
    line = WorkspaceRule(workspace="1").to_hyprland_lua_line()

    for absent in ("monitor", "default", "persistent", "gaps_in", "no_border"):
        assert absent not in line
