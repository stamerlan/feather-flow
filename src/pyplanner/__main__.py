import argparse
import os
import pathlib
import sys
import textwrap

from . import __version__
from .calendar import Calendar
from .dayinfo import DayInfoProvider
from .planner import Planner
from .progress import create_tracker
from .translations import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from .weekday import WeekDay

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pyplanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Generate digital planner files from Jinja2/HTML templates.

            Each planner lives in its own directory. The input can be a template
            file or a planner directory (the template is then
            <dirname>/<dirname>.html). Use --html or --pdf to select the output
            format (default: PDF). Use -o to set a custom output filename."""),
        epilog=textwrap.dedent("""\
            examples:
              pyplanner planners/ff-2026
                  Generate ff-2026.pdf in the current directory.

              pyplanner planners/ff-2026 --html
                  Generate ff-2026.html instead of PDF.

              pyplanner planners/ff-2026 -o planner.pdf
                  Generate PDF with a custom output filename.

              pyplanner planners/ff-2026 --country pl
                  Generate PDF with Polish public holidays.

              pyplanner planners/ff-2026 --country us
                  Holidays for the US; week starts on Sunday."""),
    )
    parser.add_argument("-v", "--version", action="version",
        version=f"%(prog)s {__version__}")
    parser.add_argument("file", type=pathlib.Path,
        metavar="FILE",
        help="planner template file or directory "
             "(if a directory, uses <dir>/<dirname>.html)")
    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument("--html", action="store_true",
        help="generate HTML output instead of PDF")
    fmt.add_argument("--pdf", action="store_true",
        help="generate PDF output (the default)")
    parser.add_argument("-o", "--output", default=None, metavar="FILE",
        help="output filename (default: <template_stem>.pdf or "
             "<template_stem>.html depending on format)")
    parser.add_argument("--pdf-optimize", action=argparse.BooleanOptionalAction,
        default=True,
        help="post-process PDF to deduplicate images/streams and strip "
             "obsolete metadata (default: enabled)")
    parser.add_argument("-c", "--country", default=None, metavar="CC",
        help=(
            "ISO 3166-1 alpha-2 country code for holidays / off-days "
            "(e.g., PL, US, DE, FR, etc.). "
            "Also sets the first day of the week for that country "
            "unless --first-weekday is given explicitly. "
            "Uses the built-in providers by default; combine with "
            "--provider to use a custom provider instead."
        ))
    parser.add_argument("-w", "--first-weekday", default=None, metavar="DAY",
        help=(
            "first day of the week: name (monday, tuesday, ..., sunday) "
            "or number (0=monday .. 6=sunday). "
            "Overrides the country default when --country is also set. "
            "Default: monday"
        ))
    parser.add_argument("--provider", action="append",
        metavar="MODULE",
        help="load custom day-info provider classes from the given Python "
             "module (may be specified multiple times); "
             "default: pyplanner.providers")
    parser.add_argument("-l", "--lang", default=DEFAULT_LANGUAGE,
        choices=SUPPORTED_LANGUAGES,
        help="display language for weekday and month names "
             f"(default: {DEFAULT_LANGUAGE})")
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-q", "--quiet", action="store_true",
        help="suppress informational output")
    verbosity.add_argument("--verbose", action="store_true",
        help="print per-job durations after each stage")
    args = parser.parse_args()

    if args.file.is_dir():
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
    planner_dir = args.file.parent
    outdir = pathlib.Path(output).parent

    if args.html:
        outdir_abs = outdir.resolve()
        planner_abs = planner_dir.resolve()
        if outdir_abs == planner_abs:
            base = "."
        else:
            base = os.path.relpath(
                planner_abs, outdir_abs,
            ).replace("\\", "/")
    else:
        base = args.file.parent.absolute().as_uri()

    calendar = Calendar(firstweekday=firstweekday, provider=dayinfo,
        lang=args.lang, country=args.country)
    planner = Planner(args.file, planner_dir=base, calendar=calendar)
    tracker = create_tracker(quiet=args.quiet, verbose=args.verbose)

    if args.html:
        with tracker(f"Generating {output}"):
            with open(output, "w", encoding="utf-8") as f:
                f.write(planner.html(tracker=tracker))
    else:
        with tracker(f"Generating {output}"):
            with open(output, "wb") as f:
                f.write(planner.pdf(
                    pdf_optimize=args.pdf_optimize,
                    tracker=tracker,
                ))

if __name__ == "__main__":
    main()
