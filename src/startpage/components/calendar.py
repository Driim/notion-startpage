from datetime import datetime, timedelta
from urllib.parse import quote

import caldav
import pytz


def fetch_icloud_calendars(username: str, password: str):
    if not username or not password:
        raise ValueError(
            "Missing iCloud credentials. Set ICLOUD_USERNAME and ICLOUD_APP_PASSWORD environment variables."
        )

    calendars = []
    # iCloud CalDAV URL
    url = f"https://{quote(username)}:{quote(password)}@caldav.icloud.com"

    try:
        client = caldav.DAVClient(url)
        principal = client.principal()
        calendars = principal.calendars()

        if not calendars:
            raise Exception("No calendars found")

    except Exception as e:
        print(f"Failed to connect to iCloud calendar: {e}")
        raise

    return calendars


def parse_event(event, name, start, end) -> dict | None:
    vobj = event.vobject_instance
    if vobj and hasattr(vobj, "vevent"):
        vevent = vobj.vevent
        title = vevent.summary.value if hasattr(vevent, "summary") else "No title"
        start_time = vevent.dtstart.value if hasattr(vevent, "dtstart") else None
        end_time = vevent.dtend.value if hasattr(vevent, "dtend") else None

        # avoid sorting issues with all-day events
        if not isinstance(start_time, datetime):
            start_time = start
        if not isinstance(end_time, datetime):
            end_time = end

        return {
            "calendar": name,
            "title": title,
            "start": start_time,
            "end": end_time,
        }

    return None


async def get_icloud_calendar_events(
    text: str, username: str, password: str, timezone: str = "UTC"
):
    calendars = fetch_icloud_calendars(username, password)

    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    all_events = []
    for calendar in calendars:
        print(f"Fetching events from calendar: {calendar.name}")
        try:
            events = calendar.search(start=start, end=end)
            for event in events:
                parsed_event = parse_event(event, calendar.name, start, end)
                if parsed_event:
                    all_events.append(parsed_event)
        except Exception as e:
            print(f"Error fetching events from {calendar.name}: {e}")

    # Sort events by start time
    all_events.sort(key=lambda x: x["start"] if x["start"] else datetime.min)

    blocks = [
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }
    ]
    if not all_events:
        return blocks + [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "No events today."}}
                    ]
                },
            }
        ]

    # Print today's events
    for event in all_events:
        start_time = event["start"]
        if start_time != start:
            time_str = start_time.strftime("%H:%M")
            item = f"{event['title']} at {time_str} (from {event['calendar']})"
        else:
            item = f"{event['title']} all day (from {event['calendar']})"

        blocks.append(
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": item}}]
                },
            }
        )

    return blocks
