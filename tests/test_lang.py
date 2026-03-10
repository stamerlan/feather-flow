import pytest

from pyplanner.lang import Lang


def test_default_language_is_english():
    """Default language is 'en'."""
    assert Lang.get().code == "en"


def test_get_none_returns_default():
    """Lang.get(None) returns the default language."""
    assert Lang.get(None) is Lang.get()


def test_get_explicit_code():
    """Lang.get('ru') returns Russian."""
    assert Lang.get("ru").code == "ru"


def test_get_unknown_raises():
    """Lang.get() raises KeyError for unknown code."""
    with pytest.raises(KeyError):
        Lang.get("zz")


def test_ko_alias_resolves_to_kr():
    """'ko' is a transparent alias for 'kr'."""
    assert Lang.get("ko") is Lang.get("kr")


def test_supported_languages():
    """Supported languages contain en, ru, kr and the ko alias."""
    assert set(Lang.supported()) == {"en", "ko", "kr", "ru"}


def test_default_in_supported():
    """Default language appears in supported()."""
    assert Lang.get().code in Lang.supported()


def test_langs_are_frozen():
    """Each registered Lang is a frozen dataclass."""
    for code in Lang.supported():
        loc = Lang.get(code)
        assert isinstance(loc, Lang)
        with pytest.raises(AttributeError):
            loc.code = "xx"  # type: ignore[misc]


@pytest.mark.parametrize("code", Lang.supported())
def test_each_lang_has_seven_weekday_names(code):
    assert len(Lang.get(code).weekday_names) == 7


@pytest.mark.parametrize("code", Lang.supported())
def test_each_lang_has_seven_weekday_short_names(code):
    assert len(Lang.get(code).weekday_short_names) == 7


@pytest.mark.parametrize("code", Lang.supported())
def test_each_lang_has_seven_weekday_letters(code):
    assert len(Lang.get(code).weekday_letters) == 7


@pytest.mark.parametrize("code", Lang.supported())
def test_each_lang_has_twelve_month_names(code):
    assert len(Lang.get(code).month_names) == 12


@pytest.mark.parametrize("code", Lang.supported())
def test_each_lang_has_twelve_month_short_names(code):
    assert len(Lang.get(code).month_short_names) == 12


def test_english_weekday_order():
    """English weekday names start with Monday and end with Sunday."""
    en = Lang.get("en")
    assert en.weekday_names[0] == "Monday"
    assert en.weekday_names[6] == "Sunday"


def test_english_short_names():
    """English short weekday names are Mon-Sun."""
    assert Lang.get("en").weekday_short_names == (
        "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
    )


def test_english_letters():
    """English weekday letters are M T W T F S S."""
    assert Lang.get("en").weekday_letters == (
        "M", "T", "W", "T", "F", "S", "S",
    )


def test_english_month_order():
    """English month names start with January, end with December."""
    en = Lang.get("en")
    assert en.month_names[0] == "January"
    assert en.month_names[11] == "December"


def test_english_short_month_names():
    """English short month names are Jan-Dec."""
    assert Lang.get("en").month_short_names == (
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    )


def test_validation_rejects_bad_weekday_count():
    """Lang raises ValueError if weekday tuple has wrong length."""
    with pytest.raises(ValueError, match="weekday_names"):
        Lang(
            code="xx",
            weekday_names=("Mon",),
            weekday_short_names=("M",) * 7,
            weekday_letters=("M",) * 7,
            month_names=("Jan",) * 12,
            month_short_names=("J",) * 12,
        )


def test_validation_rejects_bad_month_count():
    """Lang raises ValueError if month tuple has wrong length."""
    with pytest.raises(ValueError, match="month_names"):
        Lang(
            code="xx",
            weekday_names=("Mon",) * 7,
            weekday_short_names=("M",) * 7,
            weekday_letters=("M",) * 7,
            month_names=("Jan",),
            month_short_names=("J",) * 12,
        )
