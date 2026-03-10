import pytest

from pyplanner.weekday import WeekDay


def test_weekday_value():
    """WeekDay stores the numeric day value."""
    wd = WeekDay(0, "Monday", "Mon", "M", False)
    assert wd.value == 0


def test_weekday_int_conversion():
    """int(WeekDay) returns the numeric day value."""
    wd = WeekDay(2, "Wednesday", "Wed", "W", False)
    assert int(wd) == 2


def test_weekday_str_conversion():
    """str(WeekDay) returns the full weekday name."""
    wd = WeekDay(0, "Monday", "Mon", "M", False)
    assert str(wd) == "Monday"


def test_weekday_is_off_day():
    """WeekDay.is_off_day reflects the constructor argument."""
    wd = WeekDay(5, "Saturday", "Sat", "S", True)
    assert wd.is_off_day is True


@pytest.mark.parametrize("country,expected", [
    ("us", 6),
    ("US", 6),
    ("jp", 6),
    ("ca", 6),
])
def test_sunday_start_countries(country, expected):
    """Countries like US, JP, CA start their week on Sunday (6)."""
    assert WeekDay.first_weekday_for_country(country) == expected


@pytest.mark.parametrize("country", ["ae", "ir", "af", "AE"])
def test_saturday_start_countries(country):
    """Countries like AE, IR, AF start their week on Saturday (5)."""
    assert WeekDay.first_weekday_for_country(country) == 5


@pytest.mark.parametrize("country", ["gb", "de", "fr", "pl", "xx"])
def test_monday_start_countries(country):
    """European and unknown countries default to Monday (0)."""
    assert WeekDay.first_weekday_for_country(country) == 0


def test_create_default_english():
    """create() with no lang/country uses English and default weekend."""
    wd = WeekDay.create(0)
    assert wd.name == "Monday"
    assert wd.short_name == "Mon"
    assert wd.letter == "M"
    assert wd.value == 0


def test_create_explicit_language():
    """WeekDay.create() with lang='ru' produces Russian names."""
    wd = WeekDay.create(0, lang="ru")
    assert wd.name == "Понедельник"


def test_create_default_country_weekend():
    """Default country marks Saturday and Sunday as off-days."""
    sat = WeekDay.create(5)
    sun = WeekDay.create(6)
    fri = WeekDay.create(4)
    assert sat.is_off_day is True
    assert sun.is_off_day is True
    assert fri.is_off_day is False


def test_create_friday_saturday_weekend():
    """UAE (ae) weekend is Friday-Saturday."""
    fri = WeekDay.create(4, country="ae")
    sat = WeekDay.create(5, country="ae")
    sun = WeekDay.create(6, country="ae")
    assert fri.is_off_day is True
    assert sat.is_off_day is True
    assert sun.is_off_day is False


def test_create_friday_only_off():
    """Mauritania (mr) has only Friday as the weekly off-day."""
    fri = WeekDay.create(4, country="mr")
    sat = WeekDay.create(5, country="mr")
    assert fri.is_off_day is True
    assert sat.is_off_day is False


def test_create_case_insensitive_country():
    """Country code lookup is case-insensitive."""
    wd_lower = WeekDay.create(0, country="ae")
    wd_upper = WeekDay.create(0, country="AE")
    assert wd_lower.is_off_day == wd_upper.is_off_day


@pytest.mark.parametrize("name,expected", [
    ("monday", 0), ("Monday", 0), ("MONDAY", 0),
    ("tuesday", 1), ("wednesday", 2), ("thursday", 3),
    ("friday", 4), ("saturday", 5), ("sunday", 6),
])
def test_parse_english_full_names(name, expected):
    """parse_weekday() accepts full English names case-insensitively."""
    assert WeekDay.parse_weekday(name) == expected


@pytest.mark.parametrize("name,expected", [
    ("Mon", 0), ("Tue", 1), ("Wed", 2), ("Thu", 3),
    ("Fri", 4), ("Sat", 5), ("Sun", 6),
])
def test_parse_english_short_names(name, expected):
    """parse_weekday() accepts short English names."""
    assert WeekDay.parse_weekday(name) == expected


@pytest.mark.parametrize("num", range(7))
def test_parse_numeric(num):
    """parse_weekday() accepts numeric strings 0-6."""
    assert WeekDay.parse_weekday(str(num)) == num


def test_parse_with_whitespace():
    """parse_weekday() strips surrounding whitespace."""
    assert WeekDay.parse_weekday("  monday  ") == 0


def test_parse_invalid_raises():
    """parse_weekday() raises ValueError on unrecognized input."""
    with pytest.raises(ValueError, match="Invalid weekday"):
        WeekDay.parse_weekday("notaday")


def test_parse_out_of_range_raises():
    """parse_weekday() raises ValueError for numeric value 7."""
    with pytest.raises(ValueError):
        WeekDay.parse_weekday("7")


def test_parse_negative_raises():
    """parse_weekday() raises ValueError for negative numbers."""
    with pytest.raises(ValueError):
        WeekDay.parse_weekday("-1")


def test_all_weekdays_returns_seven():
    """all_weekdays() returns a tuple of exactly 7 WeekDay objects."""
    days = WeekDay.all_weekdays()
    assert len(days) == 7


def test_all_weekdays_values_zero_to_six():
    """all_weekdays() values are 0 through 6 in order."""
    days = WeekDay.all_weekdays()
    assert [d.value for d in days] == list(range(7))


def test_all_weekdays_respects_language():
    """all_weekdays(lang='ru') uses Russian weekday names."""
    days = WeekDay.all_weekdays(lang="ru")
    assert days[0].name == "Понедельник"


def test_all_weekdays_respects_country_weekend():
    """all_weekdays(country='ae') marks Friday-Saturday as off-days."""
    days = WeekDay.all_weekdays(country="ae")
    assert days[4].is_off_day is True   # Friday
    assert days[5].is_off_day is True   # Saturday
    assert days[6].is_off_day is False  # Sunday
