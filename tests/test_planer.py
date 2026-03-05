import pytest

from pyplaner.calendar import Calendar
from pyplaner.planer import Planer, _asset_route


@pytest.fixture()
def simple_template(tmp_path):
    tpl = tmp_path / "template.html"
    tpl.write_text(
        "<html><body>\n"
        "<h1>{{ calendar.lang }}</h1>\n"
        "%% for year_num in range(2026, 2027)\n"
        "%% set year = calendar.year(year_num)\n"
        "<p>{{ year }}</p>\n"
        "%% endfor\n"
        "</body></html>",
        encoding="utf-8",
    )
    return tpl


def test_html_renders_template(simple_template):
    """Planer.html() renders Jinja2 variables and loops into HTML."""
    cal = Calendar(lang="en")
    planer = Planer(simple_template, calendar=cal)
    html = planer.html()
    assert "<h1>en</h1>" in html
    assert "<p>2026</p>" in html


def test_html_default_calendar(simple_template):
    """Planer creates a default Calendar when none is provided."""
    planer = Planer(simple_template)
    html = planer.html()
    assert "<h1>en</h1>" in html


def test_html_russian_lang(tmp_path):
    """Planer.html() renders Russian month names with lang='ru'."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        "%% set year = calendar.year(2026)\n"
        "%% for month in year.months\n"
        "<span>{{ month.name }}</span>\n"
        "%% endfor",
        encoding="utf-8",
    )
    cal = Calendar(lang="ru")
    planer = Planer(tpl, calendar=cal)
    html = planer.html()
    assert "\u042f\u043d\u0432\u0430\u0440\u044c" in html


def test_base_is_template_directory(tmp_path):
    """base is set to the template's parent directory."""
    sub = tmp_path / "planner"
    sub.mkdir()
    tpl = sub / "tpl.html"
    tpl.write_text(
        '<link href="{{ base }}/assets/style.css">'
        '<a href="#page1">link</a>',
        encoding="utf-8",
    )
    planer = Planer(tpl)
    html = planer.html()
    expected = sub.as_uri() + "/assets/style.css"
    assert expected in html
    assert 'href="#page1"' in html


def test_asset_route_windows_path():
    """_asset_route strips the leading slash from Windows file:// URLs."""
    class _FakeRequest:
        url = "file:///C:/Users/test/assets/style.css"

    class _FakeRoute:
        request = _FakeRequest()
        fulfilled_path = None
        def fulfill(self, path):
            self.fulfilled_path = path

    route = _FakeRoute()
    _asset_route(route)
    assert route.fulfilled_path == "C:/Users/test/assets/style.css"


def test_asset_route_unix_path():
    """_asset_route preserves the leading slash for Unix file:// URLs."""
    class _FakeRequest:
        url = "file:///home/user/assets/style.css"

    class _FakeRoute:
        request = _FakeRequest()
        fulfilled_path = None
        def fulfill(self, path):
            self.fulfilled_path = path

    route = _FakeRoute()
    _asset_route(route)
    assert route.fulfilled_path == "/home/user/assets/style.css"
