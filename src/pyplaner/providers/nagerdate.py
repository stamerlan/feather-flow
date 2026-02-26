import json
import urllib.error
import urllib.request
import warnings

from ..dayinfo import DayInfo, DayInfoProvider


class NagerDateProvider(DayInfoProvider):
    """DayInfoProvider backed by the Nager.Date public-holiday API.

    Covers 100+ countries (ISO 3166-1 alpha-2 codes). Unlike isdayoff.ru
    this source only knows about public holidays - it cannot tell whether
    a weekend day has been transferred to a workday.

    Free, no API key required. https://date.nager.at
    """

    def __init__(self, country_code: str, *, timeout: float = 10) -> None:
        """Initialize the provider.

        :param country_code: ISO 3166-1 alpha-2 country code.
        :param timeout: HTTP request timeout in seconds.
        """
        self._cc = country_code.upper()
        self._timeout = timeout

    def fetch_day_info(self, year: int) -> dict[str, DayInfo] | None:
        """Fetch public holidays for *year* from the Nager.Date API.

        :param year: Calendar year to fetch data for.
        :returns: Mapping of ``YYYY-MM-DD`` strings to
            :class:`~pyplaner.dayinfo.DayInfo` instances, or ``None`` if the
            request fails or the response is unusable.
        """
        url = (
            f"https://date.nager.at/api/v3/PublicHolidays/{year}/{self._cc}"
        )
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except (urllib.error.URLError, OSError, ValueError):
            warnings.warn(
                f"Failed to fetch public holidays from date.nager.at "
                f"for {year}/{self._cc}.",
                stacklevel=2,
            )
            return None

        try:
            holidays = json.loads(raw)
        except json.JSONDecodeError:
            warnings.warn(
                f"Invalid JSON from date.nager.at "
                f"for {year}/{self._cc}.",
                stacklevel=2,
            )
            return None

        if not isinstance(holidays, list):
            warnings.warn(
                f"Unexpected response from date.nager.at "
                f"for {year}/{self._cc}.",
                stacklevel=2,
            )
            return None

        result: dict[str, DayInfo] = {}
        for entry in holidays:
            date_str = entry.get("date")
            if isinstance(date_str, str):
                result[date_str] = DayInfo(is_off_day=True)

        return result
