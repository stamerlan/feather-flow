import calendar
from typing import Iterator, Iterable
from .dayinfo import DayInfo, DayInfoProvider
from .translations import (
    MONTH_NAMES, MONTH_SHORT_NAMES,
    DEFAULT_LANGUAGE,
)
from .weekday import WeekDay

_EMPTY_DAY_INFO = DayInfo()

class _EmptyDayInfoProvider(DayInfoProvider):
    def __init__(self, country_code: str) -> None:
        pass

    def fetch_day_info(self, year: int) -> dict[str, DayInfo]:
        return {}

class Day:
    def __init__(self, day: int, weekday: WeekDay, id: str,
                 info: DayInfo = _EMPTY_DAY_INFO) -> None:
        self.value   = day
        self.weekday = weekday
        self.id      = id
        self.info    = info

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @property
    def is_off_day(self) -> bool:
        if self.info.is_off_day is not None:
            return self.info.is_off_day
        return self.weekday.is_off_day


class Month:
    def __init__(self, value: int, name: str, short_name: str,
                 days: Iterable[Day],
                 table: Iterable[Iterable[Day | None]], id: str) -> None:
        self.value      = value
        self.name       = name
        self.short_name = short_name
        self.days       = days
        self.table      = table
        self.id         = id

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return self.name


class Year:
    def __init__(self, year: int, months: Iterable[Month], id: str) -> None:
        self.value    = year
        self.months   = months
        self.id       = id

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @property
    def isleap(self) -> bool:
        return calendar.isleap(self.value)

    def days(self) -> Iterator[Day]:
        for m in self.months:
            for d in m.days:
                yield d


class Calendar:
    def __init__(self, firstweekday: int = 0,
                 provider: DayInfoProvider | None = None,
                 lang: str = DEFAULT_LANGUAGE) -> None:
        self._all_weekdays = WeekDay.all_weekdays(lang)
        self.lang = lang
        self._cal = calendar.Calendar(firstweekday)
        self._provider: DayInfoProvider = (
            provider if provider is not None else _EmptyDayInfoProvider("")
        )

        self.firstweekday = firstweekday
        n = firstweekday
        self.weekdays = self._all_weekdays[n:] + self._all_weekdays[:n]

    def year(self, the_year: int) -> Year:
        """Construct a :class:`Year` calendar object.

        When a provider was supplied at construction time it is queried
        for supplementary day information (holidays, transferred
        workdays, etc.).

        :param the_year: Calendar year to build.
        :returns: Fully populated :class:`Year` instance.
        """
        day_info = self._provider.fetch_day_info(the_year) or {}

        month_names = MONTH_NAMES[self.lang]
        month_short = MONTH_SHORT_NAMES[self.lang]
        MONTHS = (
            ( 1, month_names[ 0], month_short[ 0], 31),
            ( 2, month_names[ 1], month_short[ 1],
                28 if not calendar.isleap(the_year) else 29
            ),
            ( 3, month_names[ 2], month_short[ 2], 31),
            ( 4, month_names[ 3], month_short[ 3], 30),
            ( 5, month_names[ 4], month_short[ 4], 31),
            ( 6, month_names[ 5], month_short[ 5], 30),
            ( 7, month_names[ 6], month_short[ 6], 31),
            ( 8, month_names[ 7], month_short[ 7], 31),
            ( 9, month_names[ 8], month_short[ 8], 30),
            (10, month_names[ 9], month_short[ 9], 31),
            (11, month_names[10], month_short[10], 30),
            (12, month_names[11], month_short[11], 31),
        )

        months = list[Month]()
        for month, name, short_name, days_cnt in MONTHS:
            days = list[Day]()
            for day in range(1, days_cnt + 1):
                date_id = f"{the_year}-{month:02d}-{day:02d}"
                days.append(Day(day,
                    self._all_weekdays[calendar.weekday(the_year, month, day)],
                    date_id,
                    day_info.get(date_id, _EMPTY_DAY_INFO),
                ))

            # Month table (columns match self.weekdays order)
            table = list[list[Day | None]]()
            for week in self._cal.monthdayscalendar(the_year, month):
                row = []
                for col, day in enumerate(week):
                    row.append(days[day - 1] if day else None)
                table.append(row)
            months.append(
                Month(month, name, short_name, days, table,
                      f"{the_year}-{month:02d}")
            )
        return Year(the_year, months, f"{the_year}")
