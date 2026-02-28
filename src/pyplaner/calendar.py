import calendar
from typing import Iterator, Iterable
from .dayinfo import DayInfo, DayInfoProvider
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
    def __init__(self, value: int, name: str, days: Iterable[Day],
                 table: Iterable[Iterable[Day | None]], id: str) -> None:
        self.value = value
        self.name  = name
        self.days  = days
        self.table = table
        self.id    = id

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
                 provider: DayInfoProvider | None = None) -> None:
        self._all_weekdays = (
            WeekDay(0, "Monday",    False),
            WeekDay(1, "Tuesday",   False),
            WeekDay(2, "Wednesday", False),
            WeekDay(3, "Thursday",  False),
            WeekDay(4, "Friday",    False),
            WeekDay(5, "Saturday",  True),
            WeekDay(6, "Sunday",    True),
        )

        self.firstweekday = firstweekday
        n = firstweekday
        self.weekdays = self._all_weekdays[n:] + self._all_weekdays[:n]
        self._cal = calendar.Calendar(firstweekday)
        self._provider: DayInfoProvider = (
            provider if provider is not None else _EmptyDayInfoProvider("")
        )

    def year(self, the_year: int) -> Year:
        """Construct a :class:`Year` calendar object.

        When a provider was supplied at construction time it is queried
        for supplementary day information (holidays, transferred
        workdays, etc.).

        :param the_year: Calendar year to build.
        :returns: Fully populated :class:`Year` instance.
        """
        day_info = self._provider.fetch_day_info(the_year) or {}

        MONTHS = (
            ( 1, "January",   31),
            ( 2, "February",  28 if not calendar.isleap(the_year) else 29),
            ( 3, "March",     31),
            ( 4, "April",     30),
            ( 5, "May",       31),
            ( 6, "June",      30),
            ( 7, "July",      31),
            ( 8, "August",    31),
            ( 9, "September", 30),
            (10, "October",   31),
            (11, "November",  30),
            (12, "December",  31),
        )

        months = list[Month]()
        for month, name, days_cnt in MONTHS:
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
                Month(month, name, days, table, f"{the_year}-{month:02d}")
            )
        return Year(the_year, months, f"{the_year}")
