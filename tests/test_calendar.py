from datetime import datetime
from unittest.mock import MagicMock

import pytest
import pytz

from startpage.components.calendar import (
    fetch_icloud_calendars,
    get_icloud_calendar_events,
    parse_event,
)


@pytest.fixture
def mock_dav_client(mocker):
    mock_principal = MagicMock()
    mock_calendar = MagicMock()
    mock_calendar.name = "Personal"
    mock_principal.calendars.return_value = [mock_calendar]
    mock_client_instance = MagicMock()
    mock_client_instance.principal.return_value = mock_principal
    return mocker.patch("caldav.DAVClient", return_value=mock_client_instance)


def test_fetch_icloud_calendars_success(mock_dav_client):
    calendars = fetch_icloud_calendars("user", "pass")
    assert len(calendars) == 1
    assert calendars[0].name == "Personal"
    mock_dav_client.assert_called_once_with("https://user:pass@caldav.icloud.com")


def test_fetch_icloud_calendars_missing_credentials():
    with pytest.raises(ValueError):
        fetch_icloud_calendars("", "")


def test_fetch_icloud_calendars_connection_error(mocker):
    mocker.patch("caldav.DAVClient", side_effect=RuntimeError("Connection failed"))
    with pytest.raises(RuntimeError, match="Connection failed"):
        fetch_icloud_calendars("user", "pass")


def test_parse_event():
    mock_vevent = MagicMock()
    mock_vevent.summary.value = "Test Event"
    mock_vevent.dtstart.value = datetime(2026, 1, 30, 10, 0, tzinfo=pytz.utc)
    mock_vevent.dtend.value = datetime(2026, 1, 30, 11, 0, tzinfo=pytz.utc)
    mock_vobject = MagicMock()
    mock_vobject.vevent = mock_vevent
    mock_event = MagicMock()
    mock_event.vobject_instance = mock_vobject
    start_day = datetime(2026, 1, 30)
    end_day = datetime(2026, 1, 31)

    parsed = parse_event(mock_event, "Work", start_day, end_day)
    assert parsed is not None
    assert parsed["title"] == "Test Event"
    assert parsed["calendar"] == "Work"
    assert parsed["start"] == datetime(2026, 1, 30, 10, 0, tzinfo=pytz.utc)


def test_parse_event_all_day():
    mock_vevent = MagicMock()
    mock_vevent.summary.value = "All Day Event"
    mock_vevent.dtstart.value = datetime(2026, 1, 30).date()
    mock_vevent.dtend.value = datetime(2026, 1, 31).date()
    mock_vobject = MagicMock()
    mock_vobject.vevent = mock_vevent
    mock_event = MagicMock()
    mock_event.vobject_instance = mock_vobject
    start_day = datetime(2026, 1, 30)
    end_day = datetime(2026, 1, 31)

    parsed = parse_event(mock_event, "Personal", start_day, end_day)
    assert parsed is not None
    assert parsed["title"] == "All Day Event"
    assert parsed["start"] == start_day


@pytest.mark.asyncio
async def test_get_icloud_calendar_events(mocker):
    mock_calendar = MagicMock()
    mock_calendar.name = "TestCal"
    mock_vevent = MagicMock()
    mock_vevent.summary.value = "Async Event"
    mock_vevent.dtstart.value = datetime.now(pytz.utc)
    mock_vevent.dtend.value = datetime.now(pytz.utc)
    mock_vobject = MagicMock()
    mock_vobject.vevent = mock_vevent
    mock_event = MagicMock()
    mock_event.vobject_instance = mock_vobject
    mock_calendar.search.return_value = [mock_event]
    mocker.patch(
        "startpage.components.calendar.fetch_icloud_calendars",
        return_value=[mock_calendar],
    )

    blocks = await get_icloud_calendar_events("Today's Events", "user", "pass", "UTC")
    assert len(blocks) > 1
    assert blocks[0]["heading_2"]["rich_text"][0]["text"]["content"] == "Today's Events"
    assert "Async Event" in str(blocks)


@pytest.mark.asyncio
async def test_get_icloud_calendar_events_no_events(mocker):
    mock_calendar = MagicMock()
    mock_calendar.name = "EmptyCal"
    mock_calendar.search.return_value = []
    mocker.patch(
        "startpage.components.calendar.fetch_icloud_calendars",
        return_value=[mock_calendar],
    )

    blocks = await get_icloud_calendar_events("Today's Events", "user", "pass", "UTC")
    assert len(blocks) == 2
    assert (
        "No events today."
        in blocks[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
    )
