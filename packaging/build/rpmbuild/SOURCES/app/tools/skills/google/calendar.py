"""
calendar.py — Space Black Google Calendar API Tool
Provides a single tool entry point `calendar_act` for managing Google Calendar.
"""

from typing import Optional
from langchain_core.tools import tool
import datetime


def _get_calendar_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("calendar", "v3")


@tool
def calendar_act(
    action: str,
    event_id: Optional[str] = None,
    calendar_id: Optional[str] = "primary",
    summary: Optional[str] = None,
    description: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    location: Optional[str] = None,
    email: Optional[str] = None,
    max_results: Optional[int] = 10,
    timezone: Optional[str] = None,
) -> str:
    """
    A unified tool for interacting with Google Calendar.

    Actions:
    - 'list_events': List upcoming events. (Optional 'max_results', 'calendar_id')
    - 'create_event': Create a calendar event. (Requires 'summary', 'start', 'end' in ISO format e.g. '2026-03-15T09:00:00')
    - 'delete_event': Delete an event. (Requires 'event_id')
    - 'update_event': Update an event. (Requires 'event_id', plus any fields to update)
    - 'find_conflicts': Find overlapping events in a time range. (Requires 'start', 'end')
    - 'invite_participant': Add attendee to event. (Requires 'event_id', 'email')
    - 'list_calendars': List available calendars.
    - 'get_event': Get event details. (Requires 'event_id')
    """
    try:
        service = _get_calendar_service()
    except Exception as e:
        return f"Calendar Auth Error: {e}"

    try:
        if action == "list_events":
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId=calendar_id, timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            if not events:
                return "No upcoming events found."
            output = []
            for event in events:
                s = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "N/A"))
                e = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "N/A"))
                output.append(
                    f"ID: {event['id']} | {event.get('summary', 'No Title')} | "
                    f"Start: {s} | End: {e}"
                )
            return "\n".join(output)

        elif action == "create_event":
            if not summary or not start or not end:
                return "Error: Missing 'summary', 'start', or 'end'"
            tz = timezone or "America/New_York"
            event_body = {
                "summary": summary,
                "start": {"dateTime": start, "timeZone": tz},
                "end": {"dateTime": end, "timeZone": tz},
            }
            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location
            event = service.events().insert(
                calendarId=calendar_id, body=event_body
            ).execute()
            return f"Event created: '{summary}' (ID: {event['id']})\nLink: {event.get('htmlLink')}"

        elif action == "delete_event":
            if not event_id:
                return "Error: Missing 'event_id'"
            service.events().delete(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            return f"Event {event_id} deleted."

        elif action == "update_event":
            if not event_id:
                return "Error: Missing 'event_id'"
            event = service.events().get(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            if summary:
                event["summary"] = summary
            if description:
                event["description"] = description
            if location:
                event["location"] = location
            tz = timezone or "America/New_York"
            if start:
                event["start"] = {"dateTime": start, "timeZone": tz}
            if end:
                event["end"] = {"dateTime": end, "timeZone": tz}
            updated = service.events().update(
                calendarId=calendar_id, eventId=event_id, body=event
            ).execute()
            return f"Event {event_id} updated. Link: {updated.get('htmlLink')}"

        elif action == "find_conflicts":
            if not start or not end:
                return "Error: Missing 'start' or 'end'"
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=start + "Z" if not start.endswith("Z") else start,
                timeMax=end + "Z" if not end.endswith("Z") else end,
                singleEvents=True, orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            if not events:
                return "No conflicts found in this time range."
            output = [f"Found {len(events)} event(s) in this time range:"]
            for event in events:
                s = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "N/A"))
                output.append(f"  - {event.get('summary', 'No Title')} at {s}")
            return "\n".join(output)

        elif action == "invite_participant":
            if not event_id or not email:
                return "Error: Missing 'event_id' or 'email'"
            event = service.events().get(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            attendees = event.get("attendees", [])
            attendees.append({"email": email})
            event["attendees"] = attendees
            updated = service.events().update(
                calendarId=calendar_id, eventId=event_id, body=event,
                sendUpdates="all"
            ).execute()
            return f"Invited {email} to event '{updated.get('summary')}'."

        elif action == "list_calendars":
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            output = []
            for cal in calendars:
                output.append(
                    f"ID: {cal['id']} | {cal.get('summary', 'Unnamed')} | "
                    f"Primary: {cal.get('primary', False)}"
                )
            return "\n".join(output)

        elif action == "get_event":
            if not event_id:
                return "Error: Missing 'event_id'"
            event = service.events().get(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            s = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "N/A"))
            e_time = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "N/A"))
            attendees = ", ".join([a.get("email", "") for a in event.get("attendees", [])])
            return (
                f"Summary: {event.get('summary', 'No Title')}\n"
                f"Start: {s}\nEnd: {e_time}\n"
                f"Location: {event.get('location', 'N/A')}\n"
                f"Description: {event.get('description', 'N/A')}\n"
                f"Attendees: {attendees or 'None'}\n"
                f"Link: {event.get('htmlLink', 'N/A')}"
            )

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Calendar Error: {str(e)}\n{traceback.format_exc()}"
