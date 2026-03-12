import types

import pytest

from pyplanner.calendar import Calendar
from pyplanner.params import Params
from pyplanner.planner import Planner, _asset_route


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
    """Planner.html() renders Jinja2 variables and loops into HTML."""
    cal = Calendar(lang="en")
    planner = Planner(simple_template, calendar=cal)
    html = planner.html()
    assert "<h1>en</h1>" in html
    assert "<p>2026</p>" in html


def test_html_default_calendar(simple_template):
    """Planner creates a default Calendar when none is provided."""
    planner = Planner(simple_template)
    html = planner.html()
    assert "<h1>en</h1>" in html


def test_html_russian_lang(tmp_path):
    """Planner.html() renders Russian month names with lang='ru'."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        "%% set year = calendar.year(2026)\n"
        "%% for month in year.months\n"
        "<span>{{ month.name }}</span>\n"
        "%% endfor",
        encoding="utf-8",
    )
    cal = Calendar(lang="ru")
    planner = Planner(tpl, calendar=cal)
    html = planner.html()
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
    planner = Planner(tpl)
    html = planner.html()
    expected = sub.as_uri() + "/assets/style.css"
    assert expected in html
    assert 'href="#page1"' in html


def test_explicit_base_overrides_default(tmp_path):
    """html(base=...) uses the given value instead of file:// URI."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        '<link href="{{ base }}/style.css">',
        encoding="utf-8",
    )
    planner = Planner(tpl)
    html = planner.html(base="../assets")
    assert "../assets/style.css" in html
    assert "file://" not in html


def test_default_base_is_file_uri(tmp_path):
    """html() without base produces a file:// URI."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text("{{ base }}", encoding="utf-8")
    planner = Planner(tpl)
    html = planner.html()
    assert html.startswith("file:///")


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


def test_html_renders_params(tmp_path):
    """Planner passes params namespace into the template."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        '<p>{{ params.accent }}</p>',
        encoding="utf-8",
    )
    xml = tmp_path / "params.xml"
    xml.write_text(
        '<params>'
        '  <accent help="Color">#4A90D9</accent>'
        '</params>',
        encoding="utf-8",
    )
    params = Params.load_xml(xml).apply()
    planner = Planner(tpl, params=params)
    html = planner.html()
    assert "<p>#4A90D9</p>" in html


def test_html_renders_nested_params(tmp_path):
    """Planner renders nested namespace params."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        '<p>{{ params.colors.primary }}</p>',
        encoding="utf-8",
    )
    xml = tmp_path / "params.xml"
    xml.write_text(
        '<params>'
        '  <colors>'
        '    <primary help="Primary">#000</primary>'
        '  </colors>'
        '</params>',
        encoding="utf-8",
    )
    params = Params.load_xml(xml).apply(["colors.primary=#F00"])
    planner = Planner(tpl, params=params)
    html = planner.html()
    assert "<p>#F00</p>" in html


def test_html_default_params_is_empty_namespace(tmp_path):
    """Planner without params gets an empty SimpleNamespace."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text("<html>ok</html>", encoding="utf-8")
    planner = Planner(tpl)
    assert isinstance(planner.params, types.SimpleNamespace)
    html = planner.html()
    assert "ok" in html
