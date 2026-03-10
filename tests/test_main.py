from unittest.mock import patch, MagicMock

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


def test_no_flags_generates_pdf_by_default(simple_template):
    """No --html/--pdf flag generates PDF by default."""
    with patch("pyplanner.__main__.Planner") as mock_planner_cls, \
         patch("pyplanner.__main__.optimize", side_effect=lambda d: d):
        mock_instance = MagicMock()
        mock_instance.pdf.return_value = b"%PDF-1.4"
        mock_planner_cls.return_value = mock_instance

        with patch("builtins.open", MagicMock()):
            main([str(simple_template), "-q"])

        mock_instance.pdf.assert_called_once_with()


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
