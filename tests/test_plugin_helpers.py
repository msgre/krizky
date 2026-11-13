"""Tests for krizky.plugin_helpers."""

from pathlib import Path

import jinja2
import pytest

from krizky.plugin_helpers import register_plugin_templates, replace_tree, resolve_path


def _make_dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    dirs = []
    for name in ("project", "plugin", "builtin"):
        d = tmp_path / name
        d.mkdir()
        dirs.append(d)
    return dirs[0], dirs[1], dirs[2]


def _env(project: Path, builtin: Path) -> jinja2.Environment:
    return jinja2.Environment(
        loader=jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(str(project)), jinja2.FileSystemLoader(str(builtin))]
        )
    )


def test_register_plugin_templates_order(tmp_path):
    project, plugin, builtin = _make_dirs(tmp_path)
    env = _env(project, builtin)
    register_plugin_templates(env, plugin)
    paths = [loader.searchpath for loader in env.loader.loaders]
    assert paths == [[str(project)], [str(plugin)], [str(builtin)]]


def test_register_plugin_templates_precedence(tmp_path):
    project, plugin, builtin = _make_dirs(tmp_path)
    for d in (project, plugin, builtin):
        (d / "all.html").write_text(d.name)
    for d in (plugin, builtin):
        (d / "plugin_only.html").write_text(d.name)
    env = _env(project, builtin)
    register_plugin_templates(env, str(plugin))
    assert env.get_template("all.html").render() == "project"
    assert env.get_template("plugin_only.html").render() == "plugin"


def test_register_plugin_templates_idempotent(tmp_path):
    project, plugin, builtin = _make_dirs(tmp_path)
    env = _env(project, builtin)
    register_plugin_templates(env, str(plugin))
    register_plugin_templates(env, plugin)
    assert len(env.loader.loaders) == 3


def test_register_plugin_templates_non_choice_loader(tmp_path):
    project, plugin, _ = _make_dirs(tmp_path)
    loader = jinja2.FileSystemLoader(str(project))
    env = jinja2.Environment(loader=loader)
    register_plugin_templates(env, plugin)
    assert env.loader is loader


def test_register_plugin_templates_no_loader(tmp_path):
    env = jinja2.Environment()
    register_plugin_templates(env, tmp_path)
    assert env.loader is None


@pytest.mark.parametrize("as_str", [True, False])
def test_replace_tree_copies_and_removes_stale(tmp_path, as_str):
    source = tmp_path / "source"
    (source / "sub").mkdir(parents=True)
    (source / "a.txt").write_text("a")
    (source / "sub" / "b.txt").write_text("b")
    target = tmp_path / "target"
    target.mkdir()
    (target / "stale.txt").write_text("old")
    replace_tree(str(source) if as_str else source, str(target) if as_str else target)
    assert (target / "a.txt").read_text() == "a"
    assert (target / "sub" / "b.txt").read_text() == "b"
    assert not (target / "stale.txt").exists()


def test_replace_tree_missing_parent(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("a")
    target = tmp_path / "x" / "y" / "target"
    replace_tree(source, target)
    assert (target / "a.txt").read_text() == "a"


@pytest.mark.parametrize("value", [None, ""])
def test_resolve_path_empty(tmp_path, value):
    assert resolve_path(value, tmp_path) is None


@pytest.mark.parametrize("convert", [str, Path])
def test_resolve_path_relative(tmp_path, convert):
    assert resolve_path(convert("sub/../data"), tmp_path) == (tmp_path / "data").resolve()


@pytest.mark.parametrize("convert", [str, Path])
def test_resolve_path_absolute(tmp_path, convert):
    absolute = tmp_path / "abs" / ".." / "file"
    result = resolve_path(convert(absolute), tmp_path / "other")
    assert result == absolute.resolve()
