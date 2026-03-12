"""Weekday names, first-weekday rules and weekend rules by country.

:class:`WeekDay` carries a day's localized name, abbreviation and whether it
counts as an off day. Country-specific lookup tables determine which day starts
the week and which days form the weekend.
"""

from .lang import Lang

# Countries where the week starts on Sunday (6).
_SUNDAY_START: frozenset[str] = frozenset((
    "ag", "as", "au", "bd", "br", "bs", "bt", "bw", "bz", "ca", "cn",
    "co", "dm", "do", "et", "gt", "gu", "hk", "hn", "id", "il", "in",
    "jm", "jp", "ke", "kh", "kr", "la", "mh", "mm", "mo", "mt", "mx",
    "mz", "ni", "np", "pa", "pe", "ph", "pk", "pr", "pt", "py", "sa",
    "sg", "sv", "th", "tt", "tw", "um", "us", "ve", "vi", "ws", "ye",
    "za", "zw",
))

# Countries where the week starts on Saturday (5).
_SATURDAY_START: frozenset[str] = frozenset((
    "af", "bh", "dj", "dz", "eg", "ir", "iq", "jo", "kw", "ly",
    "om", "qa", "sd", "sy", "ae",
))

# Countries where the weekend is Friday-Saturday (4, 5) instead of Sat-Sun.
_FRIDAY_SATURDAY_OFF: frozenset[str] = frozenset((
    "ae", "af", "bh", "bd", "dj", "dz", "eg", "iq", "ir", "jo",
    "kw", "ly", "mv", "om", "ps", "qa", "sa", "sd", "so", "sy", "ye",
))

# Countries where only Friday (4) is the weekly day off.
_FRIDAY_ONLY_OFF: frozenset[str] = frozenset(("mr",))

_DEFAULT_COUNTRY = "gb"


class WeekDay:
    """A weekday with localized names and an off-day flag.

    :param day: Weekday number (0 = Monday ... 6 = Sunday).
    :param name: Full localized name (e.g. ``"Monday"``).
    :param short_name: Abbreviated name (e.g. ``"Mon"``).
    :param letter: Single-letter abbreviation (e.g. ``"M"``).
    :param is_off_day: Whether this weekday is a day off or not.

    Use the :meth:`create` factory to build instances with the correct names and
    weekend flag for a given country and language.
    """

    def __init__(self, day: int, name: str, short_name: str,
                 letter: str, is_off_day: bool) -> None:
        self.value      = day
        self.name       = name
        self.short_name = short_name
        self.letter     = letter
        self.is_off_day = is_off_day

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def first_weekday_for_country(country_code: str) -> int:
        """Return the conventional first weekday for *country_code*.

        :param country_code: ISO 3166-1 alpha-2 country code (case-insensitive).
        :returns: Python :mod:`calendar` weekday constant
                  (0 = Monday ... 6 = Sunday). Falls back to ``0`` (Monday) when
                  the country is unknown.
        """
        cc = country_code.lower()
        if cc in _SUNDAY_START:
            return 6
        if cc in _SATURDAY_START:
            return 5
        return 0

    @staticmethod
    def create(day: int, country: str | None = None,
               lang: str | None = None) -> "WeekDay":
        """Create a :class:`WeekDay` for the given weekday number and country.

        The *country* determines which days of the week are considered off
        days (e.g. Friday-Saturday for ``AE``, Saturday-Sunday for ``GB``).

        :param day: Weekday number (0 = Monday ... 6 = Sunday).
        :param country: ISO 3166-1 alpha-2 country code (case-insensitive).
            Defaults to Saturday-Sunday weekend when ``None``.
        :param lang: Language for weekday names. Default language when ``None``.
        """
        cc = (country or _DEFAULT_COUNTRY).lower()
        if cc in _FRIDAY_SATURDAY_OFF:
            is_off = day in (4, 5)
        elif cc in _FRIDAY_ONLY_OFF:
            is_off = day == 4
        else:
            is_off = day >= 5

        return WeekDay(
            day,
            Lang.get(lang).weekday_names[day],
            Lang.get(lang).weekday_short_names[day],
            Lang.get(lang).weekday_letters[day],
            is_off,
        )

    @staticmethod
    def parse_weekday(value: str) -> int:
        """Parse a weekday given as a name or integer string.

        Accepts any supported language names (case-insensitive) or an integer
        ``0``-``6`` where ``0`` = Monday and ``6`` = Sunday.

        :raises ValueError: If *value* is not a recognized weekday.
        """
        low = value.strip().lower()

        for code in Lang.supported():
            lang = Lang.get(code)
            for weekdays in (lang.weekday_names, lang.weekday_short_names):
                names = [s.lower() for s in weekdays]
                try:
                    return names.index(low)
                except ValueError:
                    continue

        try:
            n = int(low)
        except ValueError:
            pass
        else:
            if 0 <= n <= 6:
                return n

        raise ValueError(
            f"Invalid weekday {value!r}. Use a name "
            f"(monday..sunday) or a number (0=monday .. 6=sunday)."
        )

    @staticmethod
    def all_weekdays(
        lang: str | None = None,
        country: str | None = None,
    ) -> tuple["WeekDay", ...]:
        return tuple(WeekDay.create(i, country, lang) for i in range(7))
