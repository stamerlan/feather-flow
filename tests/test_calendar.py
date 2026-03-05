import calendar as stdlib_calendar

import pytest

from pyplanner.calendar import Calendar, Year, Month, Day
from pyplanner.dayinfo import DayInfo, DayInfoProvider
from pyplanner.weekday import WeekDay


class _StubProvider(DayInfoProvider):
    """Provider that marks Jan 1 and Dec 25 as off-days."""

    def __init__(self, country_code: str) -> None:
        self._cc = country_code

    def fetch_day_info(self, year: int) -> dict[str, DayInfo]:
        return {
            f"{year}-01-01": DayInfo(is_off_day=True),
            f"{year}-12-25": DayInfo(is_off_day=True),
        }


# -- Day --

def test_day_int_and_str():
    """int(Day) returns the day number; str(Day) returns it as a string."""
    wd = WeekDay.create(2)
    d = Day(15, wd, "2026-01-15")
    assert int(d) == 15
    assert str(d) == "15"


def test_day_is_off_day_defaults_to_weekday():
    """Day.is_off_day falls back to the weekday when DayInfo is empty."""
    sat = WeekDay.create(5)
    mon = WeekDay.create(0)
    d_sat = Day(1, sat, "2026-01-03")
    d_mon = Day(5, mon, "2026-01-05")
    assert d_sat.is_off_day is True
    assert d_mon.is_off_day is False


def test_day_dayinfo_overrides_weekday():
    """DayInfo.is_off_day=True overrides a workday weekday."""
    mon = WeekDay.create(0)
    d = Day(1, mon, "2026-01-01", DayInfo(is_off_day=True))
    assert d.is_off_day is True


def test_day_dayinfo_none_falls_through():
    """DayInfo.is_off_day=None defers to the weekday's off-day status."""
    mon = WeekDay.create(0)
    d = Day(1, mon, "2026-01-01", DayInfo(is_off_day=None))
    assert d.is_off_day is False


# -- Month --

def test_month_int_and_str():
    """int(Month) returns the month number; str(Month) returns the name."""
    m = Month(1, "January", "Jan", [], [], "2026-01")
    assert int(m) == 1
    assert str(m) == "January"


# -- Year --

def test_year_int_and_str():
    """int(Year) returns the year number; str(Year) returns it as a string."""
    y = Year(2026, [], "2026")
    assert int(y) == 2026
    assert str(y) == "2026"


def test_year_isleap_true():
    """Year.isleap is True for leap years like 2024."""
    y = Year(2024, [], "2024")
    assert y.isleap is True


def test_year_isleap_false():
    """Year.isleap is False for non-leap years like 2026."""
    y = Year(2026, [], "2026")
    assert y.isleap is False


def test_year_days_iterator():
    """Year.days() yields 365 days for a non-leap year."""
    cal = Calendar()
    y = cal.year(2026)
    days = list(y.days())
    assert len(days) == 365


def test_year_days_leap_year():
    """Year.days() yields 366 days for a leap year."""
    cal = Calendar()
    y = cal.year(2024)
    assert len(list(y.days())) == 366


# -- Calendar --

def test_calendar_default_firstweekday():
    """Calendar defaults to Monday (0) as the first weekday."""
    cal = Calendar()
    assert cal.firstweekday == 0


def test_calendar_custom_firstweekday():
    """Calendar(firstweekday=6) puts Sunday first in the weekdays tuple."""
    cal = Calendar(firstweekday=6)
    assert cal.firstweekday == 6
    assert cal.weekdays[0].value == 6


def test_calendar_weekdays_rotated():
    """Calendar(firstweekday=2) rotates weekdays to start on Wednesday."""
    cal = Calendar(firstweekday=2)
    values = [wd.value for wd in cal.weekdays]
    assert values == [2, 3, 4, 5, 6, 0, 1]


def test_calendar_year_months_count():
    """A calendar year always has 12 months."""
    cal = Calendar()
    y = cal.year(2026)
    assert len(list(y.months)) == 12


def test_calendar_year_month_names_english():
    """English month names run from January to December."""
    cal = Calendar(lang="en")
    y = cal.year(2026)
    months = list(y.months)
    assert months[0].name == "January"
    assert months[11].name == "December"


def test_calendar_year_month_names_russian():
    """Russian month names start with Январь."""
    cal = Calendar(lang="ru")
    y = cal.year(2026)
    months = list(y.months)
    assert months[0].name == "Январь"


def test_calendar_month_days_count():
    """January has 31, February (non-leap) has 28, April has 30 days."""
    cal = Calendar()
    y = cal.year(2026)
    months = list(y.months)
    assert len(list(months[0].days)) == 31
    assert len(list(months[1].days)) == 28
    assert len(list(months[3].days)) == 30


def test_calendar_february_leap():
    """February in a leap year (2024) has 29 days."""
    cal = Calendar()
    y = cal.year(2024)
    months = list(y.months)
    assert len(list(months[1].days)) == 29


def test_calendar_day_ids_format():
    """Day IDs follow the YYYY-MM-DD format."""
    cal = Calendar()
    y = cal.year(2026)
    months = list(y.months)
    days = list(months[0].days)
    assert days[0].id == "2026-01-01"
    assert days[30].id == "2026-01-31"


def test_calendar_month_ids_format():
    """Month IDs follow the YYYY-MM format."""
    cal = Calendar()
    y = cal.year(2026)
    months = list(y.months)
    assert months[0].id == "2026-01"
    assert months[11].id == "2026-12"


def test_calendar_year_id_format():
    """Year ID is the year number as a string."""
    cal = Calendar()
    y = cal.year(2026)
    assert y.id == "2026"


def test_calendar_table_structure():
    """Each week row in the month table has exactly 7 cells."""
    cal = Calendar()
    y = cal.year(2026)
    months = list(y.months)
    table = list(months[0].table)
    for week in table:
        assert len(list(week)) == 7


def test_calendar_table_none_padding():
    """Days before the first of the month are padded with None."""
    cal = Calendar(firstweekday=0)
    y = cal.year(2026)
    months = list(y.months)
    table = [list(w) for w in months[0].table]
    first_week = table[0]
    jan1_weekday = stdlib_calendar.weekday(2026, 1, 1)
    for i in range(jan1_weekday):
        assert first_week[i] is None
    assert first_week[jan1_weekday] is not None


def test_calendar_weekday_assignment_correct():
    """Each Day object gets the correct stdlib weekday value."""
    cal = Calendar()
    y = cal.year(2026)
    months = list(y.months)
    day1 = list(months[0].days)[0]
    expected_wd = stdlib_calendar.weekday(2026, 1, 1)
    assert day1.weekday.value == expected_wd


def test_calendar_with_provider():
    """DayInfoProvider data is attached to the corresponding Day objects."""
    provider = _StubProvider("xx")
    cal = Calendar(provider=provider)
    y = cal.year(2026)
    months = list(y.months)
    jan1 = list(months[0].days)[0]
    assert jan1.info.is_off_day is True
    assert jan1.is_off_day is True


def test_calendar_without_provider_empty_info():
    """Without a provider, DayInfo.is_off_day is None for every day."""
    cal = Calendar()
    y = cal.year(2026)
    months = list(y.months)
    jan1 = list(months[0].days)[0]
    assert jan1.info.is_off_day is None
