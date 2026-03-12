"""Localized weekday and month name registry.

:class:`Lang` is a frozen dataclass that holds translated calendar strings for a
single language. Instances are stored in a global registry and retrieved with
:meth:`Lang.get`. Built-in languages are ``en``, ``ru`` and ``kr`` (with ``ko``
as an alias for ``kr``).
"""

from dataclasses import dataclass
from itertools import chain

_DEFAULT = "en"
_registry: dict[str, "Lang"] = {}
_aliases: dict[str, str] = {
    "ko": "kr",
}


@dataclass(frozen=True)
class Lang:
    """Translated calendar strings for a single language."""

    code: str
    weekday_names: tuple[str, ...]
    weekday_short_names: tuple[str, ...]
    weekday_letters: tuple[str, ...]
    month_names: tuple[str, ...]
    month_short_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.weekday_names) != 7:
            raise ValueError(f"{self.code}: weekday_names must have 7 entries")
        if len(self.weekday_short_names) != 7:
            raise ValueError(
                f"{self.code}: weekday_short_names must have 7 entries"
            )
        if len(self.weekday_letters) != 7:
            raise ValueError(
                f"{self.code}: weekday_letters must have 7 entries"
            )
        if len(self.month_names) != 12:
            raise ValueError(f"{self.code}: month_names must have 12 entries")
        if len(self.month_short_names) != 12:
            raise ValueError(
                f"{self.code}: month_short_names must have 12 entries"
            )

    @staticmethod
    def add(lang: "Lang") -> None:
        """Register a language in the global registry."""
        _registry[lang.code] = lang

    @staticmethod
    def get(code: str | None = None) -> "Lang":
        """Return the registered :class:`Lang` for *code*.

        When *code* is ``None`` the default language is returned.

        :raises KeyError: If *code* is not registered.
        """
        code = code or _DEFAULT
        code = _aliases.get(code, code)
        return _registry[code]

    @staticmethod
    def supported() -> tuple[str, ...]:
        """Return codes of all registered languages."""
        return tuple(sorted(chain(_registry.keys(), _aliases.keys())))


Lang.add(Lang(
    code="en",
    weekday_names=(
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
        "Sunday"
    ),
    weekday_short_names=("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    weekday_letters=("M", "T", "W", "T", "F", "S", "S"),
    month_names=(
        "January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"
    ),
    month_short_names=(
        "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct",
        "Nov", "Dec"
    ),
))

Lang.add(Lang(
    code="ru",
    weekday_names=(
        "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота",
        "Воскресенье"
    ),
    weekday_short_names=("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"),
    weekday_letters=("П", "В", "С", "Ч", "П", "С", "В"),
    month_names=(
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август",
        "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ),
    month_short_names=(
        "Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт",
        "Ноя", "Дек"
    ),
))

Lang.add(Lang(
    code="kr",
    weekday_names=(
        "월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일",
    ),
    weekday_short_names=("월", "화", "수", "목", "금", "토", "일"),
    weekday_letters=("월", "화", "수", "목", "금", "토", "일"),
    month_names=(
        "1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월",
        "11월", "12월"
    ),
    month_short_names=(
        "1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월",
        "11월", "12월"
    ),
))
