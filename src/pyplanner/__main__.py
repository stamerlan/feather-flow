import argparse
import pathlib
import sys
import textwrap

from . import __version__
from .calendar import Calendar
from .dayinfo import DayInfoProvider
from .lang import Lang
from .liveserver import watch
from .pdfopt import optimize
from .planner import Planner
from .tracker import setup_tracker, tracker
from .weekday import WeekDay


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="pyplanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Generate digital planner files from Jinja2/HTML templates.

            Each planner lives in its own directory. The input can be a template
            file or a planner directory (the template is then
            <dirname>/<dirname>.html). Use --html or --pdf to select the output
            format (default: HTML). Use -o to set a custom output filename."""),
        epilog=textwrap.dedent("""\
            examples:
              pyplanner planners/ff-2026
                  Generate ff-2026.html in the current directory.

              pyplanner planners/ff-2026 --pdf
                  Generate ff-2026.pdf instead of HTML.

              pyplanner planners/ff-2026 -o planner.html
                  Generate HTML with a custom output filename.

              pyplanner planners/ff-2026 --country pl
                  Generate HTML with Polish public holidays.

              pyplanner planners/ff-2026 --country us
                  Holidays for the US; week starts on Sunday.

              pyplanner planners/ff-2026 --watch
                  Serve HTML with live reload on file changes."""),
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "file", type=pathlib.Path, metavar="FILE",
        help="planner template file or directory "
             "(if a directory, uses <dir>/<dirname>.html)"
    )
    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument(
        "--html", action="store_true", help="generate HTML output (the default)"
    )
    fmt.add_argument(
        "--pdf", action="store_true", help="generate PDF output instead of HTML"
    )
    parser.add_argument(
        "-o", "--output", default=None, metavar="FILE",
        help="output filename (default: <template_stem>.html or "
             "<template_stem>.pdf depending on format)"
    )
    parser.add_argument(
        "--opt", action=argparse.BooleanOptionalAction, default=True,
        help="post-process PDF to deduplicate images/streams and strip "
             "obsolete metadata (default: enabled)"
    )
    parser.add_argument(
        "-c", "--country", default=None, metavar="CC",
        help="ISO 3166-1 alpha-2 country code for holidays / off-days "
             "(e.g., PL, US, DE, FR, etc.). Also sets the first day of the "
             "week for that country unless --first-weekday is given "
             "explicitly. Uses the built-in providers by default; combine with "
             "--provider to use a custom provider instead."
    )
    parser.add_argument(
        "--first-weekday", default=None, metavar="DAY",
        help="first day of the week: name (monday, tuesday, ..., sunday) "
             "or number (0=monday .. 6=sunday). Overrides the country default "
             "when --country is also set. Default: monday"
    )
    parser.add_argument(
        "--provider", action="append", metavar="MODULE",
        help="load custom day-info provider classes from the given Python "
             "module (may be specified multiple times); "
             "default: pyplanner.providers",
    )
    parser.add_argument(
        "-l", "--lang", default=Lang.get().code, choices=Lang.supported(),
        help=f"display language for weekday and month names "
             f"(default: {Lang.get().code})",
    )
    parser.add_argument(
        "-w", "--watch", action="store_true",
        help="watch template directory for changes and serve HTML with live "
             "reload"
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-q", "--quiet", action="store_true",
        help="suppress informational output"
    )
    verbosity.add_argument(
        "--verbose", action="store_true",
        help="print per-job durations after each stage; "
             "in --watch mode, also show livereload logs"
    )
    args = parser.parse_args(argv)

    if args.watch and args.pdf:
        parser.error("--watch cannot be combined with --pdf")
    if args.watch:
        args.html = True

    if not args.html and not args.pdf:
        args.html = True

    if args.file.is_dir():
        # Resolve the directory name so that "." or ".." produce a real name.
        args.file = args.file.resolve()
        args.file = args.file / f"{args.file.name}.html"

    if args.html:
        output = args.output or f"{args.file.stem}.html"
    else:
        output = args.output or f"{args.file.stem}.pdf"

    dayinfo: DayInfoProvider | None = None
    if args.country:
        if args.provider is None:
            args.provider = ["pyplanner.providers"]

        for mod_name in args.provider:
            try:
                providers_cls = DayInfoProvider.load(mod_name)
            except (ModuleNotFoundError, ImportError, TypeError) as e:
                print(f"Warning: {e}", file=sys.stderr)
                continue
            for cls in providers_cls:
                try:
                    dayinfo = cls(args.country)
                    break
                except ValueError:
                    continue
            if dayinfo is not None:
                break

        if dayinfo is None:
            raise ValueError(
                f"No day-info provider found for country {args.country!r}."
            )

    # Resolve first weekday: explicit flag > country default > Monday.
    if args.first_weekday is not None:
        firstweekday = WeekDay.parse_weekday(args.first_weekday)
    elif args.country:
        firstweekday = WeekDay.first_weekday_for_country(args.country)
    else:
        firstweekday = 0

    # Generate the output files.
    calendar = Calendar(
        firstweekday=firstweekday, provider=dayinfo, lang=args.lang,
        country=args.country
    )
    planner = Planner(args.file, calendar=calendar)
    setup_tracker(quiet=args.quiet, verbose=args.verbose)

    if args.watch:
        watch(planner, output, verbose=args.verbose)
    elif args.html:
        outdir = pathlib.Path(output).resolve().parent
        template_dir = args.file.parent.resolve()
        base = template_dir.relative_to(outdir, walk_up=True).as_posix()

        with (
            tracker(f"Generating {output}"),
            pathlib.Path(output).open("w", encoding="utf-8") as f
        ):
            f.write(planner.html(base=base))
    else:
        total = 6 if args.opt else 5
        with tracker(f"Generating {output}", total=total):
            pdf_bytes = planner.pdf()
            if args.opt:
                with tracker().job("Optimize PDF"):
                    pdf_bytes = optimize(pdf_bytes)
            with pathlib.Path(output).open("wb") as f:
                f.write(pdf_bytes)


if __name__ == "__main__":
    main()
