"""
sheets.py — Space Black Google Sheets API Tool
Provides a single tool entry point `sheets_act` for managing Google Sheets.
"""

from typing import Optional
from langchain_core.tools import tool


def _get_sheets_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("sheets", "v4")


def _get_drive_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("drive", "v3")


@tool
def sheets_act(
    action: str,
    spreadsheet_id: Optional[str] = None,
    title: Optional[str] = None,
    range: Optional[str] = None,
    values: Optional[str] = None,
    max_results: Optional[int] = 20,
) -> str:
    """
    A unified tool for interacting with Google Sheets.

    Actions:
    - 'create_sheet': Create a new spreadsheet. (Requires 'title')
    - 'read_range': Read cells from a range. (Requires 'spreadsheet_id', 'range' e.g. 'Sheet1!A1:D10')
    - 'write_range': Write values to a range. (Requires 'spreadsheet_id', 'range', 'values' as JSON string e.g. '[["A","B"],["C","D"]]')
    - 'append_row': Append a row to a sheet. (Requires 'spreadsheet_id', 'range', 'values' as JSON string e.g. '[["val1","val2"]]')
    - 'list_sheets': List sheets in a spreadsheet. (Requires 'spreadsheet_id')
    - 'clear_range': Clear a range of cells. (Requires 'spreadsheet_id', 'range')
    - 'list_spreadsheets': List recent spreadsheets from Drive.
    """
    try:
        service = _get_sheets_service()
    except Exception as e:
        return f"Sheets Auth Error: {e}"

    try:
        if action == "create_sheet":
            if not title:
                return "Error: Missing 'title'"
            spreadsheet = service.spreadsheets().create(
                body={"properties": {"title": title}}, fields="spreadsheetId,spreadsheetUrl"
            ).execute()
            return (
                f"Spreadsheet created: '{title}'\n"
                f"ID: {spreadsheet['spreadsheetId']}\n"
                f"URL: {spreadsheet['spreadsheetUrl']}"
            )

        elif action == "read_range":
            if not spreadsheet_id or not range:
                return "Error: Missing 'spreadsheet_id' or 'range'"
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range
            ).execute()
            rows = result.get("values", [])
            if not rows:
                return "No data found in range."
            output = []
            for i, row in enumerate(rows):
                output.append(f"Row {i+1}: {' | '.join(row)}")
            return "\n".join(output)

        elif action == "write_range":
            if not spreadsheet_id or not range or not values:
                return "Error: Missing 'spreadsheet_id', 'range', or 'values'"
            import json
            parsed_values = json.loads(values)
            body = {"values": parsed_values}
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range,
                valueInputOption="USER_ENTERED", body=body
            ).execute()
            return f"Updated {result.get('updatedCells', 0)} cells."

        elif action == "append_row":
            if not spreadsheet_id or not range or not values:
                return "Error: Missing 'spreadsheet_id', 'range', or 'values'"
            import json
            parsed_values = json.loads(values)
            body = {"values": parsed_values}
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range=range,
                valueInputOption="USER_ENTERED", body=body
            ).execute()
            return f"Appended {result.get('updates', {}).get('updatedRows', 0)} row(s)."

        elif action == "list_sheets":
            if not spreadsheet_id:
                return "Error: Missing 'spreadsheet_id'"
            info = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = info.get("sheets", [])
            output = []
            for s in sheets:
                props = s.get("properties", {})
                output.append(f"ID: {props.get('sheetId')} | Name: {props.get('title')}")
            return "\n".join(output)

        elif action == "clear_range":
            if not spreadsheet_id or not range:
                return "Error: Missing 'spreadsheet_id' or 'range'"
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id, range=range, body={}
            ).execute()
            return f"Cleared range '{range}' in spreadsheet {spreadsheet_id}."

        elif action == "list_spreadsheets":
            drive_service = _get_drive_service()
            results = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet'",
                pageSize=max_results,
                fields="files(id, name, modifiedTime)"
            ).execute()
            files = results.get("files", [])
            if not files:
                return "No spreadsheets found."
            return "\n".join([
                f"ID: {f['id']} | {f['name']} | Modified: {f.get('modifiedTime', 'N/A')}"
                for f in files
            ])

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Sheets Error: {str(e)}\n{traceback.format_exc()}"
