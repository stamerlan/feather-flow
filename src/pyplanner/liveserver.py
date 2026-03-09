import logging
import os
import pathlib
import sys

from .planner import Planner

try:
    from livereload import Server
except ImportError:
    Server = None

class _LivereloadFilter(logging.Filter):
    """Intercept livereload log records.

    Prints selected messages without timestamps and blocks all records from
    reaching handlers (preventing the default LogFormatter output).
    """

    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose

    def filter(self, record: logging.LogRecord) -> bool:
        if self.verbose:
            msg = record.getMessage()
            if "Browser Connected" in msg:
                print("Browser connected")
            elif "Running task" in msg:
                print("Regenerating...")
        return False


class _AccessFilter(logging.Filter):
    """Intercept tornado HTTP access log records.

    Re-emits every access log entry to stderr without timestamps and suppresses
    the default LogFormatter output.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        print(record.getMessage(), file=sys.stderr)
        return False


def watch(
    planner: Planner,
    output: str | os.PathLike,
    *,
    verbose: bool = False,
) -> None:
    """Watch template directory and rebuild on changes.

    Starts a livereload server that monitors the planner template directory. On
    each change the HTML output is regenerated and connected browsers reload
    automatically.

    :param planner: Planner instance for rendering.
    :param output: Output HTML file path.
    :param verbose: Show browser and rebuild events.
    """
    if Server is None:
        raise ImportError(
            "livereload is required for --watch mode.\n"
            "Install with: pip install pyplanner[full]"
        )

    output_path = pathlib.Path(output).resolve()
    output_str = str(output_path)

    def regenerate() -> None:
        try:
            with open(output_str, "w", encoding="utf-8") as f:
                f.write(planner.html())
        except Exception as e:
            print(f"{e}", file=sys.stderr)

    logging.getLogger('livereload').addFilter(_LivereloadFilter(verbose))
    logging.getLogger('tornado.access').addFilter(_AccessFilter())

    regenerate()

    server = Server()
    server.watch(
        planner.planner_dir, regenerate,
        ignore=lambda path: pathlib.Path(path).resolve() == output_path,
    )

    host = '127.0.0.1'
    port = 5500
    print(f"Serving on http://{host}:{port}")
    print("Ctrl+C to exit")

    server.serve(
        host=host, port=port,
        default_filename=output_str,
        root=str(planner.path.parent),
    )
