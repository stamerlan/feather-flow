import types

import pytest

from pyplanner.params import Params, parse_bool


@pytest.mark.parametrize("value", [
    "true", "True", "TRUE", "yes", "Yes", "YES",
    "y", "Y", "on", "On", "ON", "1",
])
def test_parse_bool_truthy(value):
    """parse_bool returns True for all truthy variants."""
    assert parse_bool(value) is True


@pytest.mark.parametrize("value", [
    "false", "False", "FALSE", "no", "No", "NO",
    "n", "N", "off", "Off", "OFF", "0",
])
def test_parse_bool_falsy(value):
    """parse_bool returns False for all falsy variants."""
    assert parse_bool(value) is False


@pytest.mark.parametrize("value", ["maybe", "2", "", "tru", "nope"])
def test_parse_bool_invalid(value):
    """parse_bool raises ValueError on unrecognized input."""
    with pytest.raises(ValueError, match="invalid bool value"):
        parse_bool(value)


def _write_xml(tmp_path, content):
    xml = tmp_path / "params.xml"
    xml.write_text(content, encoding="utf-8")
    return xml


def test_load_xml_str_default_type(tmp_path):
    """Omitting type= defaults to str."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#4A90D9</accent>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.accent == "#4A90D9"


def test_load_xml_explicit_str(tmp_path):
    """Explicit type='str' works the same as omitted."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <title type="str" help="Title">Hello</title>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.title == "Hello"


def test_load_xml_int(tmp_path):
    """type='int' parses text content to Python int."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <year type="int" help="Year">2026</year>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.year == 2026
    assert isinstance(ns.year, int)


def test_load_xml_float(tmp_path):
    """type='float' parses text content to Python float."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <spacing type="float" help="Spacing">1.5</spacing>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.spacing == 1.5
    assert isinstance(ns.spacing, float)


def test_load_xml_bool(tmp_path):
    """type='bool' parses text with full bool vocabulary."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <notes type="bool" help="Notes">yes</notes>'
        '  <grid type="bool" help="Grid">off</grid>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.notes is True
    assert ns.grid is False


def test_load_xml_no_text_yields_none(tmp_path):
    """A leaf with empty text content gets None."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <subtitle type="str" help="Subtitle"/>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.subtitle is None


def test_load_xml_type_only_text_default(tmp_path):
    """type attr alone with text content uses text as default."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <year type="int">2026</year>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.year == 2026


def test_load_xml_namespace(tmp_path):
    """Child elements form a namespace."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <colors>'
        '    <primary help="Primary">#000</primary>'
        '    <bg help="Background">#FFF</bg>'
        '  </colors>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert isinstance(ns.colors, types.SimpleNamespace)
    assert ns.colors.primary == "#000"
    assert ns.colors.bg == "#FFF"


def test_load_xml_namespace_with_help(tmp_path):
    """Namespace elements can have a help attribute."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <colors help="Color settings">'
        '    <primary help="Primary">#000</primary>'
        '  </colors>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert isinstance(ns.colors, types.SimpleNamespace)
    assert ns.colors.primary == "#000"


def test_load_xml_deeply_nested(tmp_path):
    """Namespaces can be nested multiple levels deep."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <cover>'
        '    <font>'
        '      <family help="Font">Inter</family>'
        '      <size type="int" help="Size">48</size>'
        '    </font>'
        '  </cover>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.cover.font.family == "Inter"
    assert ns.cover.font.size == 48


def test_load_xml_cdata_default(tmp_path):
    """CDATA in text content is used as default."""
    svg = '<circle cx="5" cy="5" r="2"/>'
    xml = _write_xml(tmp_path, (
        '<params>'
        f'  <pattern help="SVG pattern">'
        f'<![CDATA[{svg}]]>'
        f'</pattern>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.pattern == svg


def test_load_xml_whitespace_stripped(tmp_path):
    """Leading/trailing whitespace is stripped from text."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <x help="desc">  hello  </x>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.x == "hello"


def test_load_xml_error_type_and_children(tmp_path):
    """Element with type attr and children raises."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <bad type="str">'
        '    <child help="C">y</child>'
        '  </bad>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="both"):
        Params.load_xml(xml)


def test_load_xml_error_empty_element(tmp_path):
    """Element with neither attrs nor children raises."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <empty>Description only</empty>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="neither"):
        Params.load_xml(xml)


def test_load_xml_error_invalid_identifier(tmp_path):
    """Element names that are not valid identifiers raise."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <show_notes help="OK">x</show_notes>'
        '  <not-valid help="Hyphenated">x</not-valid>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="invalid parameter name"):
        Params.load_xml(xml)


def test_load_xml_error_keyword_name(tmp_path):
    """Python keywords are rejected as parameter names."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <class help="Bad">x</class>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="invalid parameter name"):
        Params.load_xml(xml)


def test_load_xml_error_unknown_type(tmp_path):
    """Unrecognized type= value raises."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <x type="date" help="Date">2026-01-01</x>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="unknown type"):
        Params.load_xml(xml)


def test_load_xml_error_bad_default(tmp_path):
    """Text content that doesn't match declared type raises."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <year type="int" help="Year">abc</year>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="bad default"):
        Params.load_xml(xml)


def test_load_xml_error_wrong_root(tmp_path):
    """Root element must be <params>."""
    xml = _write_xml(tmp_path, (
        '<config>'
        '  <x help="X">1</x>'
        '</config>'
    ))
    with pytest.raises(ValueError, match="expected <params>"):
        Params.load_xml(xml)


def test_apply_single_override(tmp_path):
    """A single -D override replaces the default."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(["accent=#FFF"])
    assert ns.accent == "#FFF"


def test_apply_dotted_override(tmp_path):
    """Dot notation overrides nested namespace values."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <colors>'
        '    <primary help="Primary">#000</primary>'
        '  </colors>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(["colors.primary=#F00"])
    assert ns.colors.primary == "#F00"


def test_apply_int_coercion(tmp_path):
    """Override values are coerced to the declared type."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <year type="int" help="Year">2026</year>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(["year=2027"])
    assert ns.year == 2027
    assert isinstance(ns.year, int)


def test_apply_float_coercion(tmp_path):
    """Float override is coerced."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <spacing type="float" help="S">1.5</spacing>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(["spacing=2.0"])
    assert ns.spacing == 2.0


def test_apply_bool_coercion(tmp_path):
    """Bool override accepts the full vocabulary."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <notes type="bool" help="N">yes</notes>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(["notes=off"])
    assert ns.notes is False


def test_apply_none_default_override(tmp_path):
    """Override a param that had no default (was None)."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <subtitle type="str" help="S"/>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(["subtitle=Hello"])
    assert ns.subtitle == "Hello"


def test_apply_unknown_key_raises(tmp_path):
    """Override with unknown key raises ValueError."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="unknown parameter"):
        Params.load_xml(xml).apply(["acent=#FFF"])


def test_apply_type_mismatch_raises(tmp_path):
    """Override value that can't be parsed to type raises."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <year type="int" help="Year">2026</year>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="invalid value"):
        Params.load_xml(xml).apply(["year=abc"])


def test_apply_no_equals_raises(tmp_path):
    """Override without = sign raises ValueError."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="expected KEY=VALUE"):
        Params.load_xml(xml).apply(["accent"])


def test_apply_override_namespace_raises(tmp_path):
    """Overriding a namespace (not leaf) raises."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <colors>'
        '    <primary help="P">#000</primary>'
        '  </colors>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="namespace"):
        Params.load_xml(xml).apply(["colors=#FFF"])


def test_apply_leaf_as_namespace_raises(tmp_path):
    """Dot-path through a leaf param raises."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>'
    ))
    with pytest.raises(ValueError, match="leaf parameter"):
        Params.load_xml(xml).apply(["accent.sub=#FFF"])


def test_apply_empty_defines(tmp_path):
    """apply() with no defines returns defaults unchanged."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply([])
    assert ns.accent == "#000"


def test_apply_none_defines(tmp_path):
    """apply(None) returns defaults unchanged."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(None)
    assert ns.accent == "#000"


def test_apply_no_args(tmp_path):
    """apply() with no arguments returns defaults unchanged."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <accent help="Color">#000</accent>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply()
    assert ns.accent == "#000"


def test_params_from_dict():
    """Params can be constructed from a dict directly."""
    schema = {
        "accent": {"type": "str", "default": "#000"},
        "year": {"type": "int", "default": 2026},
    }
    ns = Params(schema).apply()
    assert ns.accent == "#000"
    assert ns.year == 2026


def test_params_from_dict_with_namespace():
    """Dict schema with nested namespaces."""
    schema = {
        "colors": {
            "primary": {"type": "str", "default": "#000"},
        },
    }
    ns = Params(schema).apply(["colors.primary=#F00"])
    assert ns.colors.primary == "#F00"


def test_apply_value_with_equals_sign(tmp_path):
    """Values containing = are preserved (split on first =)."""
    xml = _write_xml(tmp_path, (
        '<params>'
        '  <formula help="Formula"/>'
        '</params>'
    ))
    ns = Params.load_xml(xml).apply(["formula=a=b+c"])
    assert ns.formula == "a=b+c"
