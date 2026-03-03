"""Watch mode: monitor template and assets, rebuild on change.

Uses the ``livereload`` library for file watching, HTTP serving,
and automatic browser reload via WebSocket.
"""

import pathlib
import sys
from datetime import datetime

from livereload import Server

from .calendar import Calendar
from .planer import Planer
from .progress import QuietTracker


def _timestamp() -> str:
    """Return the current time as ``[HH:MM:SS]``."""
    return datetime.now().strftime("[%H:%M:%S]")


def _rebuild(
    template_path: pathlib.Path,
    calendar: Calendar,
    output_path: pathlib.Path,
) -> bool:
    """Render HTML and write *output_path*.

    :returns: ``True`` on success, ``False`` on error.
    """
    try:
        planer = Planer(template_path, calendar=calendar)
        html = planer.html(tracker=QuietTracker())
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    except Exception as exc:
        sys.stderr.write(
            f"{_timestamp()} Error: {exc}\n"
        )
        sys.stderr.flush()
        return False


def _is_subpath(
    child: pathlib.Path, parent: pathlib.Path,
) -> bool:
    """Return ``True`` if *child* is equal to or under *parent*."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def watch(
    template_path: pathlib.Path,
    calendar: Calendar,
    output_path: pathlib.Path,
) -> None:
    """Watch *template_path* and assets, rebuild HTML on change.

    Performs an initial render, starts an HTTP server with
    live-reload, then monitors the CWD (and the template's
    parent directory if outside CWD) for file changes.

    Blocks until interrupted with ``Ctrl+C``.

    :param template_path: Path to the Jinja2/HTML template.
    :param calendar: Calendar instance for rendering.
    :param output_path: Destination path for the rendered HTML.
    """
    sys.stdout.write(
        f"{_timestamp()} Building {output_path} ...\n"
    )
    sys.stdout.flush()
    if not _rebuild(template_path, calendar, output_path):
        sys.exit(1)
    sys.stdout.write(
        f"{_timestamp()} Rebuilt {output_path}\n"
    )
    sys.stdout.flush()

    def on_change():
        sys.stdout.write(
            f"{_timestamp()} Change detected\n"
        )
        sys.stdout.flush()
        if _rebuild(template_path, calendar, output_path):
            sys.stdout.write(
                f"{_timestamp()} Rebuilt {output_path}\n"
            )
            sys.stdout.flush()

    server = Server()

    cwd = pathlib.Path.cwd().resolve()
    tpl_parent = template_path.resolve().parent
    output_resolved = output_path.resolve()

    def ignore_output(path):
        return pathlib.Path(path).resolve() == output_resolved

    server.watch(str(cwd), on_change, ignore=ignore_output)
    if not _is_subpath(tpl_parent, cwd):
        server.watch(
            str(tpl_parent), on_change,
            ignore=ignore_output,
        )

    server.serve(
        root=str(cwd),
        open_url_delay=1,
        default_filename=output_path.name,
    )
