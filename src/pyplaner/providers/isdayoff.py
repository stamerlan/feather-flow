import calendar
import urllib.error
import urllib.request
import warnings

from ..dayinfo import DayInfo, DayInfoProvider

_SUPPORTED_CC = frozenset(("ru", "ua", "by", "kz", "uz", "tr", "ge", "us"))


class IsDayOffProvider(DayInfoProvider):
    """DayInfoProvider backed by the isdayoff.ru production-calendar API.

    Provides complete workday/off-day data including public holidays and
    transferred workdays. Free, no API key required.

    Supported countries: RU, UA, BY, KZ, UZ, TR, GE, US.
    """

    def __init__(self, country_code: str, *, timeout: float = 10) -> None:
        """Initialize the provider.

        :param country_code: ISO 3166-1 alpha-2 country code.
        :param timeout: HTTP request timeout in seconds.
        :raises ValueError: If *country_code* is not supported.
        """
        cc = country_code.lower()
        if cc not in _SUPPORTED_CC:
            raise ValueError(
                f"Country code {country_code!r} is not supported by "
                f"isdayoff.ru."
            )
        self._cc = cc
        self._timeout = timeout

    def fetch_day_info(self, year: int) -> dict[str, DayInfo] | None:
        """Fetch workday/off-day data for *year* from the isdayoff.ru API.

        :param year: Calendar year to fetch data for.
        :returns: Mapping of ``YYYY-MM-DD`` strings to
            :class:`~pyplaner.dayinfo.DayInfo` instances, or ``None`` if the
            request fails or the response is unusable.
        """
        url = f"https://isdayoff.ru/api/getdata?year={year}&cc={self._cc}"
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as resp:
                data = resp.read().decode("ascii")
        except (urllib.error.URLError, OSError, ValueError):
            warnings.warn(
                f"Failed to fetch production calendar from isdayoff.ru "
                f"for {year}/{self._cc}.",
                stacklevel=2,
            )
            return None

        days_in_year = 366 if calendar.isleap(year) else 365
        if len(data) != days_in_year or not all(c in "01" for c in data):
            warnings.warn(
                f"Unexpected response from isdayoff.ru "
                f"for {year}/{self._cc}.",
                stacklevel=2,
            )
            return None

        result: dict[str, DayInfo] = {}
        idx = 0
        for month in range(1, 13):
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                result[f"{year}-{month:02d}-{day:02d}"] = DayInfo(
                    is_off_day=(data[idx] == "1"),
                )
                idx += 1

        return result
