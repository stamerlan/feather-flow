import os
import pathlib
import jinja2
from urllib.parse import urlparse, unquote
from playwright.sync_api import Route, sync_playwright
from .calendar import Calendar

try:
    import pikepdf
    import io
except ImportError:
    pikepdf = None

class Planer:
    def __init__(self, template_path: str | os.PathLike,
                 base: str, calendar: "Calendar" = Calendar()
    ) -> None:
        self._path = pathlib.Path(template_path).absolute()
        self.base  = base

        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._path.parent),
            autoescape=jinja2.select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
            line_statement_prefix="%%",
            line_comment_prefix="##"
        )
        self._template = self._env.get_template(self._path.name)
        self.calendar = calendar

    def html(self) -> str:
        """Performs parameter substitution and returns resulting HTML"""
        return self._template.render(
            base=self.base,
            calendar=self.calendar
        )

    def pdf(self, html: str | None = None,
            margin_top: str | float | None = None,
            margin_right: str | float | None = None,
            margin_bottom: str | float | None = None,
            margin_left: str | float | None = None,
            *,
            debug = False
            ) -> bytes:
        """Print PDF"""
        if html is None:
            html = self.html()

        with sync_playwright() as p:
            browser = p.chromium.launch(args=[
                # allows file access
                "--allow-file-access-from-files",
                "--disable-web-security"
            ])

            page = browser.new_page()

            if debug:
                page.on("request",       lambda r: print(f"REQ:   '{r.url}'"))
                page.on("requestfailed", lambda r: print(f"FAIL:  '{r.url}'"))

            def asset_route(r: Route) -> None:
                parse_result = urlparse(r.request.url)
                path = unquote(parse_result.path)

                if parse_result.netloc:
                    # file://hostname/path -> ignore hostname for local files
                    path = f"{parse_result.netloc}{path}"
                elif path.startswith("/") and ":" in path[1:3]:
                    # Windows: strip leading slash in /C:/path
                    path = path[1:]

                if debug:
                    print(f"ROUTE: '{r.request.url} -> '{path}'")
                r.fulfill(path=path)
            page.route(f"file://**/*", asset_route)

            page.set_content(html, wait_until="networkidle")

            pdf = page.pdf(
                print_background=True,
                prefer_css_page_size=True,
                margin={
                    "top": margin_top,
                    "right": margin_right,
                    "bottom": margin_bottom,
                    "left": margin_left
                }
            )

            browser.close()

        if pikepdf is None:
            return pdf

        with pikepdf.open(io.BytesIO(pdf)) as pike_pdf_obj:
            bio = io.BytesIO()
            pike_pdf_obj.save(bio,
                object_stream_mode=pikepdf.ObjectStreamMode.generate
            )
            return bio.getvalue()
