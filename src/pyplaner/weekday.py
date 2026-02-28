WEEKDAY_NAMES: tuple[str, ...] = (
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday",
)

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


class WeekDay:
    def __init__(self, day: int, name: str, is_off_day: bool) -> None:
        self.value      = day
        self.name       = name
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
    def parse_weekday(value: str) -> int:
        """Parse a weekday given as a name or integer string.

        Accepts full English names (case-insensitive) or an integer ``0``-``6``
        where ``0`` = Monday and ``6`` = Sunday.

        :raises ValueError: If *value* is not a recognized weekday.
        """
        low = value.strip().lower()
        if low in WEEKDAY_NAMES:
            return WEEKDAY_NAMES.index(low)

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
