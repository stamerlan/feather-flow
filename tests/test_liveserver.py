import logging
import sys
from unittest.mock import patch, MagicMock

import pytest

from pyplanner.liveserver import (
    _LivereloadFilter,
    _AccessFilter,
    watch,
)


def _make_record(msg):
    """Create a minimal LogRecord with the given message."""
    return logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg=msg, args=(), exc_info=None,
    )


@pytest.fixture(autouse=True)
def _clean_log_filters():
    """Restore logger filters after each test."""
    lr = logging.getLogger('livereload')
    ta = logging.getLogger('tornado.access')
    old_lr = lr.filters[:]
    old_ta = ta.filters[:]
    yield
    lr.filters = old_lr
    ta.filters = old_ta


@pytest.fixture()
def planner_stub(tmp_path):
    """Minimal Planner mock with a working html() method."""
    stub = MagicMock()
    stub.html.return_value = "<html>ok</html>"
    stub.path.parent = tmp_path
    return stub


def _run_watch(planner, output, **kwargs):
    """Call watch() with a mocked Server that exits immediately.

    Returns the mock Server instance for assertions.
    """
    mock_server = MagicMock()
    mock_cls = MagicMock(return_value=mock_server)
    mock_server.serve.side_effect = KeyboardInterrupt

    with patch("livereload.Server", mock_cls):
        try:
            watch(planner, output, **kwargs)
        except KeyboardInterrupt:
            pass

    return mock_server


def test_livereload_filter_always_blocks():
    """_LivereloadFilter returns False for every record."""
    f = _LivereloadFilter(verbose=False)
    assert f.filter(_make_record("anything")) is False

    f = _LivereloadFilter(verbose=True)
    assert f.filter(_make_record("anything")) is False


def test_livereload_filter_silent_when_not_verbose(capsys):
    """_LivereloadFilter produces no output when verbose=False."""
    f = _LivereloadFilter(verbose=False)
    f.filter(_make_record(
        "Browser Connected: http://localhost/",
    ))
    f.filter(_make_record(
        "Running task: regenerate (delay: None)",
    ))
    assert capsys.readouterr().out == ""


def test_livereload_filter_prints_browser_connected(capsys):
    """_LivereloadFilter prints 'Browser connected' when verbose."""
    f = _LivereloadFilter(verbose=True)
    f.filter(_make_record(
        "Browser Connected: http://localhost/",
    ))
    assert "Browser connected" in capsys.readouterr().out


def test_livereload_filter_prints_regenerating(capsys):
    """_LivereloadFilter prints 'Regenerating...' when verbose."""
    f = _LivereloadFilter(verbose=True)
    f.filter(_make_record(
        "Running task: regenerate (delay: None)",
    ))
    assert "Regenerating..." in capsys.readouterr().out


def test_livereload_filter_skips_unrelated_when_verbose(capsys):
    """_LivereloadFilter suppresses unrelated messages in verbose."""
    f = _LivereloadFilter(verbose=True)
    f.filter(_make_record("Start watching changes"))
    f.filter(_make_record("Reload 1 waiters: file.html"))
    assert capsys.readouterr().out == ""


def test_access_filter_emits_to_stderr(capsys):
    """_AccessFilter prints every record to stderr."""
    f = _AccessFilter()
    f.filter(_make_record(
        "404 GET /missing.css (127.0.0.1) 0.5ms",
    ))
    assert "404 GET /missing.css" in capsys.readouterr().err


def test_access_filter_emits_non_error_status(capsys):
    """_AccessFilter passes non-error status codes too."""
    f = _AccessFilter()
    f.filter(_make_record(
        "200 GET /index.html (127.0.0.1) 1.2ms",
    ))
    assert "200 GET /index.html" in capsys.readouterr().err


def test_access_filter_always_returns_false():
    """_AccessFilter blocks records from reaching handlers."""
    f = _AccessFilter()
    record = _make_record("200 GET / (127.0.0.1) 0.1ms")
    assert f.filter(record) is False


def test_watch_raises_without_livereload(
    planner_stub, tmp_path,
):
    """watch() raises ImportError when livereload is missing."""
    saved = sys.modules.pop("livereload", None)
    try:
        with patch.dict(sys.modules, {"livereload": None}):
            with pytest.raises(
                ImportError,
                match="livereload is required",
            ):
                watch(planner_stub, tmp_path / "out.html")
    finally:
        if saved is not None:
            sys.modules["livereload"] = saved


def test_watch_writes_initial_html(
    planner_stub, tmp_path,
):
    """watch() regenerates HTML before starting the server."""
    output = tmp_path / "out.html"
    _run_watch(planner_stub, output)

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert content == "<html>ok</html>"


def test_watch_prints_address(
    planner_stub, tmp_path, capsys,
):
    """watch() prints the serving address and exit hint."""
    _run_watch(planner_stub, tmp_path / "out.html")

    out = capsys.readouterr().out
    assert "http://127.0.0.1:5500" in out
    assert "Ctrl+C to exit" in out


def test_watch_registers_planner_dir(
    planner_stub, tmp_path,
):
    """watch() registers the template directory for watching."""
    server = _run_watch(planner_stub, tmp_path / "out.html")

    server.watch.assert_called_once()
    args = server.watch.call_args
    assert args[0][0] == str(tmp_path)


def test_watch_serves_on_expected_port(
    planner_stub, tmp_path,
):
    """watch() starts the server with the right host, port and root."""
    server = _run_watch(planner_stub, tmp_path / "out.html")

    server.serve.assert_called_once()
    kwargs = server.serve.call_args.kwargs
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 5500
    assert kwargs["root"] == str(tmp_path)


def test_watch_ignore_matches_output(
    planner_stub, tmp_path,
):
    """The ignore callback returns True only for the output file."""
    output = tmp_path / "out.html"
    server = _run_watch(planner_stub, output)

    ignore = server.watch.call_args.kwargs["ignore"]
    assert ignore(str(output)) is True
    assert ignore(str(tmp_path / "other.html")) is False


def test_watch_handles_render_error(tmp_path, capsys):
    """watch() prints render errors to stderr without crashing."""
    stub = MagicMock()
    stub.html.side_effect = RuntimeError("template broken")
    stub.path.parent = tmp_path

    _run_watch(stub, tmp_path / "out.html")

    assert "template broken" in capsys.readouterr().err


def test_watch_installs_log_filters(
    planner_stub, tmp_path,
):
    """watch() adds filters to livereload and tornado loggers."""
    _run_watch(planner_stub, tmp_path / "out.html")

    lr = logging.getLogger('livereload')
    ta = logging.getLogger('tornado.access')
    assert any(
        isinstance(f, _LivereloadFilter) for f in lr.filters
    )
    assert any(
        isinstance(f, _AccessFilter) for f in ta.filters
    )


def test_watch_verbose_flag_propagates(
    planner_stub, tmp_path,
):
    """watch(verbose=True) creates a verbose LivereloadFilter."""
    _run_watch(
        planner_stub, tmp_path / "out.html",
        verbose=True,
    )

    lr = logging.getLogger('livereload')
    filters = [
        f for f in lr.filters
        if isinstance(f, _LivereloadFilter)
    ]
    assert len(filters) == 1
    assert filters[0].verbose is True


def test_watch_passes_relative_base(tmp_path):
    """watch() computes a relative base and passes it to html()."""
    planner_dir = tmp_path / "planners" / "my"
    planner_dir.mkdir(parents=True)
    stub = MagicMock()
    stub.html.return_value = "<html>ok</html>"
    stub.path.parent = planner_dir

    output = tmp_path / "build" / "out.html"
    output.parent.mkdir()
    _run_watch(stub, output)

    stub.html.assert_called_once()
    base = stub.html.call_args[0][0]
    assert base == "../planners/my"


def test_watch_base_is_dot_when_same_dir(
    planner_stub, tmp_path,
):
    """watch() sets base to '.' when output is in the template dir."""
    _run_watch(planner_stub, tmp_path / "out.html")

    planner_stub.html.assert_called_once()
    base = planner_stub.html.call_args[0][0]
    assert base == "."
