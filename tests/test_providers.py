import json
from unittest.mock import patch, MagicMock

import pytest

from pyplanner.dayinfo import DayInfo
from pyplanner.providers.isdayoff import IsDayOffProvider
from pyplanner.providers.nagerdate import NagerDateProvider


# -- IsDayOffProvider --

def test_isdayoff_supported_country():
    """IsDayOffProvider accepts and lowercases a supported country code."""
    provider = IsDayOffProvider("ru")
    assert provider._cc == "ru"


def test_isdayoff_case_insensitive():
    """IsDayOffProvider lowercases the country code on init."""
    provider = IsDayOffProvider("RU")
    assert provider._cc == "ru"


def test_isdayoff_unsupported_country_raises():
    """IsDayOffProvider raises ValueError for unsupported countries."""
    with pytest.raises(ValueError, match="not supported"):
        IsDayOffProvider("us")


@pytest.mark.parametrize("cc", ["ru", "ua", "by", "kz", "uz", "tr", "ge"])
def test_isdayoff_all_supported_countries(cc):
    """IsDayOffProvider initialises without error for each supported code."""
    provider = IsDayOffProvider(cc)
    assert provider._cc == cc


def test_isdayoff_fetch_success():
    """fetch_day_info parses a valid all-workday response into DayInfo objects."""
    days_in_2026 = 365
    response_data = "0" * days_in_2026
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_data.encode("ascii")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = IsDayOffProvider("ru")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = provider.fetch_day_info(2026)

    assert result is not None
    assert len(result) == days_in_2026
    assert all(isinstance(v, DayInfo) for v in result.values())
    assert result["2026-01-01"].is_off_day is False


def test_isdayoff_fetch_with_off_days():
    """fetch_day_info correctly maps '1' characters to is_off_day=True."""
    days_in_2026 = 365
    response_data = "1" + "0" * (days_in_2026 - 1)
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_data.encode("ascii")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = IsDayOffProvider("ru")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = provider.fetch_day_info(2026)

    assert result["2026-01-01"].is_off_day is True
    assert result["2026-01-02"].is_off_day is False


def test_isdayoff_fetch_network_error():
    """fetch_day_info returns None and warns on a network error."""
    import urllib.error
    provider = IsDayOffProvider("ru")
    with patch("urllib.request.urlopen",
                side_effect=urllib.error.URLError("timeout")):
        with pytest.warns(UserWarning, match="Failed to fetch"):
            result = provider.fetch_day_info(2026)
    assert result is None


def test_isdayoff_fetch_bad_response_length():
    """fetch_day_info returns None and warns when response length is wrong."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"010"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = IsDayOffProvider("ru")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.warns(UserWarning, match="Unexpected response"):
            result = provider.fetch_day_info(2026)
    assert result is None


def test_isdayoff_fetch_bad_response_chars():
    """fetch_day_info returns None and warns when response has invalid chars."""
    days_in_2026 = 365
    mock_resp = MagicMock()
    mock_resp.read.return_value = ("x" * days_in_2026).encode("ascii")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = IsDayOffProvider("ru")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.warns(UserWarning, match="Unexpected response"):
            result = provider.fetch_day_info(2026)
    assert result is None


def test_isdayoff_fetch_leap_year():
    """fetch_day_info produces 366 entries for a leap year including Feb 29."""
    days_in_2024 = 366
    response_data = "0" * days_in_2024
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_data.encode("ascii")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = IsDayOffProvider("ru")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = provider.fetch_day_info(2024)

    assert result is not None
    assert len(result) == days_in_2024
    assert "2024-02-29" in result


# -- NagerDateProvider --

def test_nagerdate_stores_country_upper():
    """NagerDateProvider uppercases the country code on init."""
    provider = NagerDateProvider("de")
    assert provider._cc == "DE"


def test_nagerdate_fetch_success():
    """fetch_day_info parses a JSON holiday list into DayInfo objects."""
    holidays = [
        {"date": "2026-01-01", "name": "New Year"},
        {"date": "2026-12-25", "name": "Christmas"},
    ]
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(holidays).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = NagerDateProvider("de")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = provider.fetch_day_info(2026)

    assert result is not None
    assert len(result) == 2
    assert result["2026-01-01"].is_off_day is True
    assert result["2026-12-25"].is_off_day is True


def test_nagerdate_fetch_network_error():
    """fetch_day_info returns None and warns on a network error."""
    import urllib.error
    provider = NagerDateProvider("de")
    with patch("urllib.request.urlopen",
                side_effect=urllib.error.URLError("timeout")):
        with pytest.warns(UserWarning, match="Failed to fetch"):
            result = provider.fetch_day_info(2026)
    assert result is None


def test_nagerdate_fetch_invalid_json():
    """fetch_day_info returns None and warns on invalid JSON."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"not json"
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = NagerDateProvider("de")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.warns(UserWarning, match="Invalid JSON"):
            result = provider.fetch_day_info(2026)
    assert result is None


def test_nagerdate_fetch_non_list_response():
    """fetch_day_info returns None and warns when JSON is not a list."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"error": "bad"}).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = NagerDateProvider("de")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with pytest.warns(UserWarning, match="Unexpected response"):
            result = provider.fetch_day_info(2026)
    assert result is None


def test_nagerdate_fetch_entries_without_date():
    """fetch_day_info silently skips holiday entries that lack a 'date' key."""
    holidays = [
        {"date": "2026-01-01", "name": "New Year"},
        {"name": "Mystery Holiday"},
    ]
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(holidays).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    provider = NagerDateProvider("de")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = provider.fetch_day_info(2026)

    assert result is not None
    assert len(result) == 1
