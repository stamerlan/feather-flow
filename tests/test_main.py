from unittest.mock import patch
import pytest
from pyplanner.__main__ import main


@pytest.fixture()
def simple_template(tmp_path):
    tpl = tmp_path / "planner.html"
    tpl.write_text(
        "<html>\n"
        "%% for y in range(2026, 2027)\n"
        "%% set year = calendar.year(y)\n"
        "{{ year }}\n"
        "%% endfor\n"
        "</html>",
        encoding="utf-8",
    )
    return tpl


def test_generates_html(simple_template, tmp_path):
    """--html -o writes rendered HTML to the given file."""
    out = tmp_path / "out.html"
    main([
        str(simple_template),
        "--html", "-o", str(out), "-q",
    ])
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "2026" in content


def test_directory_input(tmp_path):
    """Passing a directory resolves to <dir>/<dirname>.html."""
    planner_dir = tmp_path / "myplanner"
    planner_dir.mkdir()
    tpl = planner_dir / "myplanner.html"
    tpl.write_text(
        "<html>{{ calendar.year(2026) }}</html>",
        encoding="utf-8",
    )
    out = tmp_path / "out.html"
    main([
        str(planner_dir),
        "--html", "-o", str(out), "-q",
    ])
    assert out.exists()
    assert "2026" in out.read_text(encoding="utf-8")


def test_html_base_resolves_asset_paths(tmp_path):
    """base variable resolves to the planner directory."""
    planner_dir = tmp_path / "myplanner"
    planner_dir.mkdir()
    tpl = planner_dir / "myplanner.html"
    tpl.write_text(
        '<link href="{{ base }}/assets/style.css">',
        encoding="utf-8",
    )
    out = tmp_path / "out.html"
    main([
        str(planner_dir),
        "--html", "-o", str(out), "-q",
    ])
    content = out.read_text(encoding="utf-8")
    assert "myplanner/assets/style.css" in content
    assert "//assets" not in content


def test_default_html_filename(simple_template, tmp_path, monkeypatch):
    """--html without -o defaults to <template_stem>.html."""
    monkeypatch.chdir(tmp_path)
    main([str(simple_template), "--html", "-q"])
    out = tmp_path / "planner.html"
    assert out.exists()


def test_no_flags_generates_html_by_default(simple_template, tmp_path):
    """No --html/--pdf flag generates HTML by default."""
    out = tmp_path / "out.html"
    main([str(simple_template), "-o", str(out), "-q"])
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "2026" in content


def test_country_sets_provider(simple_template, tmp_path):
    """--country ru loads the isdayoff provider."""
    out = tmp_path / "out.html"
    with patch(
        "pyplanner.providers.isdayoff"
        ".IsDayOffProvider.fetch_day_info",
        return_value={},
    ):
        main([
            str(simple_template),
            "--html", "-o", str(out),
            "--country", "ru", "-q",
        ])
    assert out.exists()


def test_unsupported_country_raises(simple_template):
    """Unsupported country code raises ValueError."""
    mock_cls = type("RejectAll", (), {
        "__init__": lambda self, cc: (
            (_ for _ in ()).throw(ValueError(cc))
        ),
        "fetch_day_info": lambda self, y: {},
    })

    with patch(
        "pyplanner.dayinfo.DayInfoProvider.load",
        return_value=[mock_cls],
    ), pytest.raises(
        ValueError, match="No day-info provider found"
    ):
        main([
            str(simple_template),
            "--html", "--country", "zz",
            "--provider", "some_module", "-q",
        ])


def test_explicit_weekday_override(simple_template, tmp_path):
    """--first-weekday sunday overrides the country default."""
    out = tmp_path / "out.html"
    main([
        str(simple_template),
        "--html", "-o", str(out),
        "--first-weekday", "sunday", "-q",
    ])
    assert out.exists()


def test_numeric_weekday(simple_template, tmp_path):
    """--first-weekday 6 sets Sunday as the first weekday."""
    out = tmp_path / "out.html"
    main([
        str(simple_template),
        "--html", "-o", str(out),
        "--first-weekday", "6", "-q",
    ])
    assert out.exists()


def test_html_base_with_output_in_subdirectory(tmp_path):
    """base resolves to a walk-up path when output is in a subdir."""
    planner_dir = tmp_path / "myplanner"
    planner_dir.mkdir()
    tpl = planner_dir / "myplanner.html"
    tpl.write_text(
        '<link href="{{ base }}/style.css">',
        encoding="utf-8",
    )
    build = tmp_path / "build"
    build.mkdir()
    out = build / "out.html"
    main([
        str(planner_dir),
        "--html", "-o", str(out), "-q",
    ])
    content = out.read_text(encoding="utf-8")
    assert "../myplanner/style.css" in content


def test_directory_input_dot(tmp_path, monkeypatch):
    """Passing '.' resolves to <cwd>/<cwd_name>.html."""
    tpl = tmp_path / f"{tmp_path.name}.html"
    tpl.write_text("<html>{{ base }}</html>", encoding="utf-8")
    out = tmp_path / "out.html"
    monkeypatch.chdir(tmp_path)
    main([
        ".", "--html", "-o", str(out), "-q",
    ])
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "file://" not in content


def test_russian_language(simple_template, tmp_path):
    """--lang ru generates output using Russian locale data."""
    out = tmp_path / "out.html"
    main([
        str(simple_template),
        "--html", "-o", str(out),
        "--lang", "ru", "-q",
    ])
    assert out.exists()


def test_define_overrides_param(tmp_path):
    """-D accent=#FFF overrides the template parameter."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        '<p>{{ params.accent }}</p>',
        encoding="utf-8",
    )
    xml = tmp_path / "params.xml"
    xml.write_text(
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>',
        encoding="utf-8",
    )
    out = tmp_path / "out.html"
    main([
        str(tpl), "--html", "-o", str(out), "-q",
        "-D", "accent=#FFF",
    ])
    content = out.read_text(encoding="utf-8")
    assert "<p>#FFF</p>" in content


def test_define_dotted_namespace(tmp_path):
    """-D with dot notation overrides nested params."""
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
    out = tmp_path / "out.html"
    main([
        str(tpl), "--html", "-o", str(out), "-q",
        "-D", "colors.primary=#F00",
    ])
    content = out.read_text(encoding="utf-8")
    assert "<p>#F00</p>" in content


def test_define_without_params_xml_errors(simple_template):
    """-D without params.xml next to template raises."""
    with pytest.raises(SystemExit):
        main([
            str(simple_template), "--html", "-q",
            "-D", "accent=#FFF",
        ])


def test_define_multiple_values(tmp_path):
    """-D with multiple KEY=VALUE pairs in one flag."""
    tpl = tmp_path / "tpl.html"
    tpl.write_text(
        '<p>{{ params.a }}-{{ params.b }}</p>',
        encoding="utf-8",
    )
    xml = tmp_path / "params.xml"
    xml.write_text(
        '<params>'
        '  <a help="A">x</a>'
        '  <b help="B">y</b>'
        '</params>',
        encoding="utf-8",
    )
    out = tmp_path / "out.html"
    main([
        str(tpl), "--html", "-o", str(out), "-q",
        "-D", "a=1", "b=2",
    ])
    content = out.read_text(encoding="utf-8")
    assert "<p>1-2</p>" in content


def test_no_define_uses_defaults(tmp_path):
    """Without -D, template uses default values from params.xml."""
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
    out = tmp_path / "out.html"
    main([
        str(tpl), "--html", "-o", str(out), "-q",
    ])
    content = out.read_text(encoding="utf-8")
    assert "<p>#4A90D9</p>" in content
