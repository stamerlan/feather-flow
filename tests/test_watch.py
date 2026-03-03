import pathlib
import sys
from unittest.mock import patch
import pytest
from pyplaner.watch import _rebuild, _is_subpath, watch


@pytest.fixture()
def simple_template(tmp_path):
    tpl = tmp_path / "pages" / "planner.html"
    tpl.parent.mkdir(parents=True, exist_ok=True)
    tpl.write_text(
        "<html>{{ planner_head }}\n"
        "%% for y in range(2026, 2027)\n"
        "%% set year = calendar.year(y)\n"
        "{{ year }}\n"
        "%% endfor\n"
        "</html>",
        encoding="utf-8",
    )
    return tpl


def test_rebuild_writes_html(simple_template, tmp_path):
    from pyplaner.calendar import Calendar
    out = tmp_path / "out.html"
    ok = _rebuild(simple_template, Calendar(), out)
    assert ok is True
    assert out.exists()
    assert "2026" in out.read_text(encoding="utf-8")


def test_rebuild_returns_false_on_error(tmp_path):
    from pyplaner.calendar import Calendar
    missing = tmp_path / "no_such.html"
    out = tmp_path / "out.html"
    ok = _rebuild(missing, Calendar(), out)
    assert ok is False


def test_is_subpath_child_under_parent(tmp_path):
    assert _is_subpath(
        tmp_path / "a" / "b", tmp_path,
    ) is True


def test_is_subpath_same_path(tmp_path):
    assert _is_subpath(tmp_path, tmp_path) is True


def test_is_subpath_unrelated_paths(tmp_path):
    other = pathlib.Path("/some/other/path")
    assert _is_subpath(other, tmp_path) is False


def test_watch_implies_html(simple_template, tmp_path):
    """--watch without --html still resolves an HTML output."""
    with patch.object(sys, "argv", [
        "pyplaner", str(simple_template), "--watch",
    ]):
        with patch(
            "pyplaner.watch.watch",
        ) as mock_watch:
            from pyplaner.__main__ import main
            main()
            mock_watch.assert_called_once()
            _, _, out_path = mock_watch.call_args[0]
            assert str(out_path).endswith(".html")


def test_watch_missing_livereload(simple_template):
    """--watch prints an error when livereload is missing."""
    with patch.object(sys, "argv", [
        "pyplaner", str(simple_template), "--watch",
    ]):
        with patch.dict(
            sys.modules, {"pyplaner.watch": None},
        ):
            with pytest.raises(SystemExit):
                from pyplaner.__main__ import main
                main()


def test_initial_build_writes_output(
    simple_template, tmp_path, monkeypatch,
):
    """watch() performs an initial build before serving."""
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "planner.html"
    from pyplaner.calendar import Calendar

    with patch("pyplaner.watch.Server") as MockSrv:
        watch(simple_template, Calendar(), out)
        MockSrv.return_value.serve.assert_called_once()

    assert out.exists()
    assert "2026" in out.read_text(encoding="utf-8")


def test_watch_registers_cwd(
    simple_template, tmp_path, monkeypatch,
):
    """watch() registers the CWD with livereload."""
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "planner.html"
    from pyplaner.calendar import Calendar

    with patch("pyplaner.watch.Server") as MockSrv:
        srv_inst = MockSrv.return_value
        watch(simple_template, Calendar(), out)
        watched = [
            c.args[0] for c in srv_inst.watch.call_args_list
        ]
        assert str(tmp_path.resolve()) in watched


def test_watch_rebuilds_only_on_html(
    simple_template, tmp_path, monkeypatch,
):
    """Template glob has a rebuild callback; CWD watch does not."""
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "planner.html"
    from pyplaner.calendar import Calendar

    with patch("pyplaner.watch.Server") as MockSrv:
        srv_inst = MockSrv.return_value
        watch(simple_template, Calendar(), out)
        calls = srv_inst.watch.call_args_list
        tpl_call = calls[0]
        cwd_call = calls[1]
        assert tpl_call.args[0].endswith("*.html")
        assert tpl_call.args[1] is not None
        assert len(cwd_call.args) == 1
