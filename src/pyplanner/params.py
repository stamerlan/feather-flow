"""Template parameter definitions and CLI override handling.

Provides :class:`Params` for loading typed parameter schemas from XML and
applying ``-D KEY=VALUE`` overrides into a :class:`~types.SimpleNamespace` tree
that Jinja2 templates consume as ``params``.
"""
import keyword
import os
import types
import xml.etree.ElementTree as ET
from typing import Any

_BOOL_TRUTHY = frozenset({"true", "yes", "y", "on", "1"})
_BOOL_FALSY = frozenset({"false", "no", "n", "off", "0"})

def parse_bool(value: str) -> bool:
    """Parse a boolean string (case-insensitive).

    Accepted truthy values: ``true``, ``yes``, ``y``, ``on``, ``1``.
    Accepted falsy values: ``false``, ``no``, ``n``, ``off``, ``0``.

    :param value: String to parse.
    :returns: Parsed boolean.
    :raises ValueError: If *value* is not a recognized boolean string.
    """
    lower = value.lower()
    if lower in _BOOL_TRUTHY:
        return True
    if lower in _BOOL_FALSY:
        return False
    raise ValueError(
        f"invalid bool value {value!r}, expected one of: "
        f"true/false, yes/no, y/n, on/off, 1/0"
    )


_TYPE_PARSERS: dict[str, Any] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": parse_bool,
}

def _parse_value(value: str, type_name: str) -> Any:
    """Convert a string *value* to the given *type_name*."""
    parser = _TYPE_PARSERS.get(type_name)
    if parser is None:
        raise ValueError(f"unknown type {type_name!r}")
    return parser(value)


def _validate_name(name: str, path: str) -> None:
    """Ensure *name* is a valid Python identifier."""
    if not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError(
            f"invalid parameter name {name!r} at {path}: "
            f"must be a valid Python identifier"
        )


class Params:
    """Typed parameter schema with defaults.

    Use :meth:`load_xml` to construct from an XML file or pass a *schema* dict
    directly for programmatic / test usage.

    A *schema* is a nested dict where each leaf is a dict with keys
    ``"type"`` (str) and ``"default"`` (parsed value or ``None``), and each
    namespace is a dict whose values are either leaves or nested namespace
    dicts.

    :param schema: Nested parameter definition dict.
    """

    def __init__(self, schema: dict[str, Any]) -> None:
        self._schema = schema

    @staticmethod
    def load_xml(path: str | os.PathLike[str]) -> "Params":
        """Construct a :class:`Params` from an XML file.

        The XML schema uses ``<params>`` as the root element. Each child element
        defines a parameter or a namespace:

        - **Leaf parameter** - has a ``type`` or ``help`` attribute and no child
          elements. The element's text content is the default value (use CDATA
          for values containing XML special characters). The ``help`` attribute
          is a human-readable description. Omitting ``type`` defaults to
          ``str``. Empty or absent text content defaults to ``None``.
        - **Namespace** - has child elements and no ``type`` attribute. An
          optional ``help`` attribute is allowed for documentation. Groups
          related parameters under a nested :class:`~types.SimpleNamespace`.

        Allowed types: ``str``, ``int``, ``float``, ``bool``. Element names must
        be valid Python identifiers (no hyphens - use underscores).

        Example ``params.xml``::

            <?xml version="1.0" encoding="UTF-8"?>
            <params>
              <year type="int" help="Planner year">
                2026
              </year>
              <accent help="Primary accent color">
                #4A90D9
              </accent>
              <show_notes type="bool" help="Include notes">
                yes
              </show_notes>
              <colors help="Brand colors">
                <primary help="Primary brand color">
                  #4A90D9
                </primary>
                <weekend help="Weekend highlight">
                  #FDD
                </weekend>
              </colors>
            </params>

        :param path: Path to a ``params.xml`` file.
        :returns: New :class:`Params` instance.
        :raises ValueError: On malformed XML structure or invalid parameter
            names.
        """
        tree = ET.parse(path)  # noqa: S314
        root = tree.getroot()
        if root.tag != "params":
            raise ValueError(
                f"expected <params> root element, got <{root.tag}>"
            )
        schema = Params._parse_children(root, "")
        return Params(schema)

    @staticmethod
    def _parse_children(parent: ET.Element, parent_path: str) -> dict[str, Any]:
        """Recursively parse child XML elements to build a schema dictionary.

        For each child element, this method checks for a valid parameter name
        and correctly structured attributes or children. It builds and returns a
        dictionary representing the schema of parameters, where:

        - Each key is the parameter or namespace name.
        - If the value is a leaf parameter, it is a dictionary with keys:
            - "type": The type of the parameter as a string
                      ("int"/"str"/"float"/"bool").
            - "default": The default value for the parameter, parsed to the
                         appropriate Python type, or None if no default is
                         given.
        - If the value is a nested namespace, it is a dictionary representing
          further nested parameters.

        Example returned dictionary (schema):

        {
            "colors": {
                "primary": {"type": "str", "default": "#FFF"},
                "secondary": {"type": "str", "default": "#000"},
            },
            "year": {"type": "int", "default": 2026},
            "options": {
                "enabled": {"type": "bool", "default": True}
            }
        }

        :param parent: XML element whose child elements define parameters or
            namespaces.
        :param parent_path: Dot-delimited path to the current parent (for error
            reporting).
        :returns: Dictionary mapping parameter (or namespace) names to their
            type/default info or further nested schema dictionaries.
        :raises ValueError: If structure, names, or types are invalid.
        """
        schema: dict[str, Any] = {}
        for elem in parent:
            name = elem.tag
            path = f"{parent_path}.{name}" if parent_path else name
            _validate_name(name, path)

            has_type = "type" in elem.attrib
            has_help = "help" in elem.attrib
            has_children = len(elem) > 0

            if has_type and has_children:
                raise ValueError(
                    f"parameter {path!r} has both "
                    f"type attribute and child elements"
                )
            if not has_type and not has_help and not has_children:
                raise ValueError(
                    f"element {path!r} has neither "
                    f"type/help attributes "
                    f"nor children"
                )

            if has_children:
                schema[name] = Params._parse_children(
                    elem, path,
                )
            else:
                type_name = elem.attrib.get("type", "str")
                if type_name not in _TYPE_PARSERS:
                    raise ValueError(
                        f"unknown type {type_name!r} "
                        f"for parameter {path!r}"
                    )
                default_str = (
                    (elem.text or "").strip() or None
                )
                if default_str is not None:
                    try:
                        default = _parse_value(
                            default_str, type_name,
                        )
                    except ValueError as e:
                        raise ValueError(
                            f"bad default for {path!r}: "
                            f"{e}"
                        ) from e
                else:
                    default = None
                schema[name] = {
                    "type": type_name,
                    "default": default,
                }
        return schema

    def apply(self, defines: list[str] | None = None) -> types.SimpleNamespace:
        """Build a namespace from defaults and provided defines.

        :param defines: List of ``KEY=VALUE`` strings. Dot notation addresses
            nested namespaces (e.g. ``colors.primary=#FFF``).
        :returns: :class:`~types.SimpleNamespace` tree with all parameters
            resolved.
        :raises ValueError: On unknown keys or type mismatches.
        """
        ns = self._build_namespace(self._schema)

        for raw in defines or []:
            if "=" not in raw:
                raise ValueError(f"invalid define {raw!r}: expected KEY=VALUE")
            key, value = raw.split("=", 1)
            parts = key.split(".")
            self._set_value(ns, parts, value, self._schema)

        return ns

    @staticmethod
    def _build_namespace(schema: dict[str, Any]) -> types.SimpleNamespace:
        """Recursively build a SimpleNamespace from schema defaults."""
        attrs: dict[str, Any] = {}
        for name, entry in schema.items():
            if "type" in entry:
                attrs[name] = entry["default"]
            else:
                attrs[name] = Params._build_namespace(entry)
        return types.SimpleNamespace(**attrs)

    @staticmethod
    def _set_value(
        ns: types.SimpleNamespace,
        parts: list[str],
        value: str,
        schema: dict[str, Any],
    ) -> None:
        """Walk dot-path and set the parsed value."""
        current_ns = ns
        current_schema = schema

        for i, part in enumerate(parts):
            dotted = ".".join(parts[: i + 1])
            if part not in current_schema:
                raise ValueError(
                    f"unknown parameter {dotted!r}"
                )
            entry = current_schema[part]

            if i < len(parts) - 1:
                if "type" in entry:
                    raise ValueError(
                        f"{dotted!r} is a leaf parameter, "
                        f"not a namespace"
                    )
                current_ns = getattr(current_ns, part)
                current_schema = entry
            else:
                if "type" not in entry:
                    raise ValueError(
                        f"{dotted!r} is a namespace, "
                        f"not a leaf parameter"
                    )
                type_name = entry["type"]
                try:
                    parsed = _parse_value(value, type_name)
                except ValueError as e:
                    raise ValueError(
                        f"invalid value {value!r} for parameter {dotted!r} "
                        f"(expected {type_name})"
                    ) from e
                setattr(current_ns, part, parsed)
