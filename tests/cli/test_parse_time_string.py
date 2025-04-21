import pytest
from datetime import datetime, timezone, timedelta
from safie_mediafile._cli._cli_app import _parse_time_string


def test_parse_iso_format_with_timezone():
    """Test parsing ISO format strings with timezone information"""
    # With UTC offset
    dt = _parse_time_string("2023-01-01T12:00:00+00:00", timezone.utc)
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # With JST offset
    dt = _parse_time_string("2023-01-01T12:00:00+09:00", timezone.utc)
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=9)))

    # Timezone specified in string takes precedence over default timezone
    dt = _parse_time_string("2023-01-01T12:00:00+09:00", timezone.utc)
    assert dt != datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert dt.utcoffset() == timedelta(hours=9)


def test_parse_iso_format_without_timezone():
    """Test parsing ISO format strings without timezone information"""
    # Using UTC as default timezone
    dt = _parse_time_string("2023-01-01T12:00:00", timezone.utc)
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Using JST as default timezone
    jst = timezone(timedelta(hours=9), "JST")
    dt = _parse_time_string("2023-01-01T12:00:00", jst)
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=jst)


def test_parse_with_z_suffix():
    """Test parsing time strings with Z suffix (UTC indicator)"""
    dt = _parse_time_string("2023-01-01T12:00:00Z", timezone(timedelta(hours=9)))
    # Z is treated as +00:00 (UTC)
    assert dt == datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert dt.utcoffset() == timedelta(0)


def test_parse_invalid_format():
    """Test that invalid time formats raise ValueError"""
    with pytest.raises(ValueError) as exc_info:
        _parse_time_string("not-a-date", timezone.utc)
    assert "Invalid time format" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        _parse_time_string("2023/01/01 12:00:00", timezone.utc)
    assert "Invalid time format" in str(exc_info.value)
