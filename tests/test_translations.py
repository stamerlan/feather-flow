import pytest

from pyplanner.translations import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    WEEKDAY_NAMES,
    WEEKDAY_SHORT_NAMES,
    WEEKDAY_LETTERS,
    MONTH_NAMES,
    MONTH_SHORT_NAMES,
)


def test_default_language_is_english():
    """DEFAULT_LANGUAGE is 'en'."""
    assert DEFAULT_LANGUAGE == "en"


def test_default_language_in_supported():
    """DEFAULT_LANGUAGE appears in SUPPORTED_LANGUAGES."""
    assert DEFAULT_LANGUAGE in SUPPORTED_LANGUAGES


def test_supported_languages():
    """SUPPORTED_LANGUAGES contains exactly en, ru, kr."""
    assert set(SUPPORTED_LANGUAGES) == {"en", "ru", "kr"}


@pytest.mark.parametrize("mapping", [
    WEEKDAY_NAMES, WEEKDAY_SHORT_NAMES, WEEKDAY_LETTERS,
])
def test_weekday_keys_match_supported_languages(mapping):
    """Every weekday dict has one key per supported language."""
    assert set(mapping.keys()) == set(SUPPORTED_LANGUAGES)


@pytest.mark.parametrize("mapping", [
    WEEKDAY_NAMES, WEEKDAY_SHORT_NAMES, WEEKDAY_LETTERS,
])
def test_each_language_has_seven_weekday_entries(mapping):
    """Every language tuple in a weekday dict has exactly 7 entries."""
    for lang, values in mapping.items():
        assert len(values) == 7, f"{lang} has {len(values)} weekday entries"


def test_english_weekday_order():
    """English weekday names start with Monday and end with Sunday."""
    assert WEEKDAY_NAMES["en"][0] == "Monday"
    assert WEEKDAY_NAMES["en"][6] == "Sunday"


def test_english_short_names():
    """English short weekday names are Mon-Sun."""
    assert WEEKDAY_SHORT_NAMES["en"] == (
        "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
    )


def test_english_letters():
    """English weekday letters are M T W T F S S."""
    assert WEEKDAY_LETTERS["en"] == ("M", "T", "W", "T", "F", "S", "S")


@pytest.mark.parametrize("mapping", [MONTH_NAMES, MONTH_SHORT_NAMES])
def test_month_keys_match_supported_languages(mapping):
    """Every month dict has one key per supported language."""
    assert set(mapping.keys()) == set(SUPPORTED_LANGUAGES)


@pytest.mark.parametrize("mapping", [MONTH_NAMES, MONTH_SHORT_NAMES])
def test_each_language_has_twelve_month_entries(mapping):
    """Every language tuple in a month dict has exactly 12 entries."""
    for lang, values in mapping.items():
        assert len(values) == 12, f"{lang} has {len(values)} month entries"


def test_english_month_order():
    """English month names start with January and end with December."""
    assert MONTH_NAMES["en"][0] == "January"
    assert MONTH_NAMES["en"][11] == "December"


def test_english_short_month_names():
    """English short month names are Jan-Dec."""
    assert MONTH_SHORT_NAMES["en"] == (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )
