import logging
import os
import pathlib
import sys
from .planner import Planner

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
    output: str | os.PathLike[str],
    base: str | None = None,
    *,
    defines: list[str] | None = None,
    verbose: bool = False,
) -> None:
    """Watch template directory and rebuild on changes.

    Starts a livereload server that monitors the planner template directory.
    On each change the HTML output is regenerated and connected browsers
    reload automatically. When a ``params.xml`` file exists next to the template
    it is reloaded on every regeneration so that parameter changes take effect
    immediately.

    .. warning::

        The ``livereload`` package is imported lazily inside this function
        rather than at module level. Importing ``livereload`` at module level
        has a side effect: it unconditionally configures the root logger via
        ``logging.basicConfig()``, which alters the global logging state of the
        host application. By deferring the import to call time the side effect
        is confined to the moment the user explicitly opts into live-preview,
        leaving the logging setup untouched for all other code paths. If you use
        ``pyplanner`` as a library, be aware that calling this function will
        trigger that ``logging.basicConfig()`` call and may affect your log
        handlers.

    :param planner: Planner instance for rendering.
    :param output: Output HTML file path.
    :param base: Base URL used to resolve assets paths. If not provided,
        the planner directory is used relative to output directory. During live
        reloading, browser doesn't generate requests for file:// URLs. This
        parameter is used to provide a base URI relative to the output
        directory. In this case, both live reloading and preview in browser will
        work.
    :param defines: ``-D`` overrides to re-apply on each reload.
    :param verbose: Show browser and rebuild events.
    """
    from livereload import Server
    from .params import Params

    output = pathlib.Path(output).resolve()
    params_xml = planner.path.parent / "params.xml"
    if base is None:
        base = "."

    def regenerate() -> None:
        try:
            if params_xml.exists():
                planner.params = Params.load_xml(params_xml).apply(defines)
            html = planner.html(base)
            with output.open("w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print(f"{e}", file=sys.stderr)

    logging.getLogger("livereload").addFilter(_LivereloadFilter(verbose))
    logging.getLogger("tornado.access").addFilter(_AccessFilter())

    regenerate()

    server = Server()
    server.watch(
        str(planner.path.parent), regenerate,
        ignore=lambda path: pathlib.Path(path).resolve() == output
    )

    host = "127.0.0.1"
    port = 5500
    print(f"Serving on http://{host}:{port}")
    print("Ctrl+C to exit")

    server.serve(
        host=host, port=port,
        default_filename=str(output),
        open_url_delay=1,
        root=str(planner.path.parent),
    )
