import dataclasses
import types

import pytest

from pyplanner.dayinfo import DayInfo, DayInfoProvider


# -- DayInfo --

def test_dayinfo_defaults_to_none():
    """DayInfo() has all fields set to None by default."""
    info = DayInfo()
    assert info.is_off_day is None
    assert info.name is None
    assert info.local_name is None
    assert info.launch_year is None
    assert info.holiday_types is None


def test_dayinfo_is_off_day_true():
    """DayInfo(is_off_day=True) stores True."""
    info = DayInfo(is_off_day=True)
    assert info.is_off_day is True


def test_dayinfo_is_off_day_false():
    """DayInfo(is_off_day=False) stores False."""
    info = DayInfo(is_off_day=False)
    assert info.is_off_day is False


def test_dayinfo_is_dataclass():
    """DayInfo is a dataclass."""
    assert dataclasses.is_dataclass(DayInfo)


def test_dayinfo_has_slots():
    """DayInfo uses __slots__ for memory efficiency."""
    assert hasattr(DayInfo, "__slots__")


# -- is_provider_class --

def test_is_provider_class_real_subclass():
    """A concrete DayInfoProvider subclass is recognised as a provider."""
    class FakeProvider(DayInfoProvider):
        def __init__(self, country_code: str) -> None:
            pass
        def fetch_day_info(self, year: int):
            return {}
    assert DayInfoProvider.is_provider_class(FakeProvider) is True


def test_is_provider_class_duck_typed():
    """A class with fetch_day_info is recognised via duck typing."""
    class DuckProvider:
        def fetch_day_info(self, year: int):
            return {}
    assert DayInfoProvider.is_provider_class(DuckProvider) is True


def test_is_provider_class_rejects_instance():
    """An instance (not a class) is not a provider class."""
    class DuckProvider:
        def fetch_day_info(self, year: int):
            return {}
    assert DayInfoProvider.is_provider_class(DuckProvider()) is False


def test_is_provider_class_rejects_no_method():
    """A class without fetch_day_info is not a provider class."""
    class NotAProvider:
        pass
    assert DayInfoProvider.is_provider_class(NotAProvider) is False


def test_is_provider_class_rejects_non_callable():
    """A class where fetch_day_info is not callable is not a provider."""
    class BadProvider:
        fetch_day_info = "not callable"
    assert DayInfoProvider.is_provider_class(BadProvider) is False


# -- load --

def test_load_builtin_providers():
    """load() discovers IsDayOff and NagerDate providers."""
    classes = DayInfoProvider.load("pyplanner.providers")
    assert len(classes) >= 2
    names = {c.__name__ for c in classes}
    assert "IsDayOffProvider" in names
    assert "NagerDateProvider" in names


def test_load_nonexistent_raises():
    """load() raises ModuleNotFoundError for a missing module."""
    with pytest.raises(ModuleNotFoundError):
        DayInfoProvider.load("nonexistent_module_xyz_987")


def test_load_module_without_providers_raises():
    """load() raises TypeError when no provider class is found."""
    with pytest.raises(TypeError, match="No day information provider"):
        DayInfoProvider.load("json")


# -- _load_from_file --

def test_load_from_file_nonexistent_raises():
    """_load_from_file() raises ModuleNotFoundError for a missing file."""
    with pytest.raises(ModuleNotFoundError):
        DayInfoProvider._load_from_file("totally_missing_file_xyz")


def test_load_from_file_real_file(tmp_path):
    """_load_from_file() loads a .py file and returns a module object."""
    plugin = tmp_path / "myplugin.py"
    plugin.write_text(
        "class MyProv:\n"
        "    def __init__(self, cc): pass\n"
        "    def fetch_day_info(self, year): return {}\n",
        encoding="utf-8",
    )
    mod = DayInfoProvider._load_from_file(str(plugin))
    assert isinstance(mod, types.ModuleType)
    assert hasattr(mod, "MyProv")


def test_load_from_file_without_suffix(tmp_path):
    """_load_from_file() resolves a bare name by appending .py."""
    plugin = tmp_path / "myplugin.py"
    plugin.write_text(
        "class MyProv:\n"
        "    def fetch_day_info(self, year): return {}\n",
        encoding="utf-8",
    )
    mod = DayInfoProvider._load_from_file(str(tmp_path / "myplugin"))
    assert hasattr(mod, "MyProv")


def test_load_and_discover_providers(tmp_path):
    """load() from a file discovers providers, ignores non-providers."""
    plugin = tmp_path / "custom_provider.py"
    plugin.write_text(
        "class HolidayProvider:\n"
        "    def __init__(self, cc): pass\n"
        "    def fetch_day_info(self, year): return {}\n"
        "\n"
        "class NotAProvider:\n"
        "    pass\n",
        encoding="utf-8",
    )
    classes = DayInfoProvider.load(str(plugin))
    names = {c.__name__ for c in classes}
    assert "HolidayProvider" in names
    assert "NotAProvider" not in names
