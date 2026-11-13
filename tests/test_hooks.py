"""Tests for the plugin API surface."""

from krizky.hooks import KrizkySpec
from krizky.plugin_manager import get_plugin_manager

EXPECTED_HOOKS = {
    "prepare_jinja2_environment",
    "extra_template_vars",
    "register_commands",
    "after_page_written",
    "inject_head",
    "inject_body_end",
}


def test_hookspecs_match_expected_list() -> None:
    specs = {name for name in vars(KrizkySpec) if not name.startswith("_")}
    assert specs == EXPECTED_HOOKS


def test_plugin_manager_hooks_match_expected_list() -> None:
    pm = get_plugin_manager()
    registered = {name for name in vars(pm.hook) if not name.startswith("_")}
    assert registered == EXPECTED_HOOKS
