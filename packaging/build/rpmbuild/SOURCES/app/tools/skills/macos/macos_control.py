"""
macos_control.py — Space Black macOS Native Control Tool
Provides a single tool entry point `macos_act` for controlling macOS via AppleScript.
Only available on macOS (Darwin).
"""

import subprocess
import platform
import json
from typing import Optional
from langchain_core.tools import tool


def _run_applescript(script: str) -> str:
    """Execute an AppleScript via osascript and return the output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return f"AppleScript Error: {result.stderr.strip()}"
        return result.stdout.strip() or "Success (no output)"
    except subprocess.TimeoutExpired:
        return "Error: AppleScript timed out after 30s"
    except Exception as e:
        return f"Error running AppleScript: {e}"


def _run_shell(cmd: str) -> str:
    """Execute a shell command and return the output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return f"Shell Error: {result.stderr.strip()}"
        return result.stdout.strip() or "Success (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30s"
    except Exception as e:
        return f"Error: {e}"


@tool
def macos_act(
    action: str,
    to: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    message_index: Optional[int] = None,
    mailbox: Optional[str] = "INBOX",
    account: Optional[str] = None,
    title: Optional[str] = None,
    content: Optional[str] = None,
    folder: Optional[str] = None,
    path: Optional[str] = None,
    destination: Optional[str] = None,
    app_name: Optional[str] = None,
    value: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    calendar_name: Optional[str] = None,
    event_summary: Optional[str] = None,
    location: Optional[str] = None,
    query: Optional[str] = None,
    max_results: Optional[int] = 10,
    due_date: Optional[str] = None,
    reminder_list: Optional[str] = None,
) -> str:
    """
    A unified tool for controlling macOS natively via AppleScript.
    Only works on macOS.

    === APPLE MAIL ===
    - 'mail_send': Send email. (Requires 'to','subject','body')
    - 'mail_read_inbox': List recent inbox messages. (Optional 'max_results','account')
    - 'mail_read_message': Read specific message. (Requires 'message_index', optional 'mailbox','account')
    - 'mail_reply': Reply to message. (Requires 'message_index','body')
    - 'mail_search': Search mailbox. (Requires 'query')

    === APPLE CALENDAR ===
    - 'cal_list_events': List today's/upcoming events. (Optional 'calendar_name')
    - 'cal_create_event': Create event. (Requires 'event_summary','start_date','end_date', optional 'calendar_name','location')
    - 'cal_delete_event': Delete event. (Requires 'event_summary')
    - 'cal_list_calendars': List available calendars.

    === FINDER / FILES ===
    - 'finder_list': List files. (Requires 'path')
    - 'finder_move': Move file. (Requires 'path','destination')
    - 'finder_copy': Copy file. (Requires 'path','destination')
    - 'finder_delete': Trash file. (Requires 'path')
    - 'finder_create_folder': Create folder. (Requires 'path')
    - 'finder_open': Open file with default app. (Requires 'path')
    - 'finder_get_info': Get file info. (Requires 'path')

    === APPLE NOTES ===
    - 'notes_list': List notes. (Optional 'folder','max_results')
    - 'notes_create': Create note. (Requires 'title','body', optional 'folder')
    - 'notes_read': Read note by title. (Requires 'title')
    - 'notes_delete': Delete note. (Requires 'title')
    - 'notes_search': Search notes. (Requires 'query')

    === APPLE REMINDERS ===
    - 'reminders_list': List reminders. (Optional 'reminder_list')
    - 'reminders_create': Create reminder. (Requires 'title', optional 'due_date','reminder_list')
    - 'reminders_complete': Mark as done. (Requires 'title')
    - 'reminders_delete': Delete reminder. (Requires 'title')

    === SYSTEM ===
    - 'system_volume': Set/get volume. (Optional 'value' 0-100, omit to get current)
    - 'system_brightness': Get brightness info.
    - 'system_screenshot': Take screenshot. (Optional 'path')
    - 'system_notify': Show notification. (Requires 'title','body')
    - 'system_open_app': Open app. (Requires 'app_name')
    - 'system_quit_app': Quit app. (Requires 'app_name')
    - 'system_list_apps': List running apps.
    - 'system_clipboard_get': Get clipboard content.
    - 'system_clipboard_set': Set clipboard content. (Requires 'value')
    """
    if platform.system() != "Darwin":
        return "Error: macOS control is only available on macOS."

    try:
        # =====================================================================
        # APPLE MAIL
        # =====================================================================
        if action == "mail_send":
            if not to or not subject or not body:
                return "Error: Missing 'to', 'subject', or 'body'"
            escaped_body = body.replace('"', '\\"').replace('\n', '\\n')
            escaped_subject = subject.replace('"', '\\"')
            script = f'''
            tell application "Mail"
                set newMessage to make new outgoing message with properties {{subject:"{escaped_subject}", content:"{escaped_body}", visible:true}}
                tell newMessage
                    make new to recipient at end of to recipients with properties {{address:"{to}"}}
                end tell
                send newMessage
            end tell
            '''
            return _run_applescript(script)

        elif action == "mail_read_inbox":
            n = max_results or 10
            account_filter = f'of account "{account}"' if account else ""
            script = f'''
            tell application "Mail"
                try
                    set msgs to messages of inbox {account_filter}
                    set output to ""
                    set msgCount to count of msgs
                    set limit to {n}
                    if msgCount < limit then set limit to msgCount
                    repeat with i from 1 to limit
                        set m to item i of msgs
                        set output to output & i & ". From: " & (sender of m) & " | Subject: " & (subject of m) & " | Date: " & (date received of m as string) & linefeed
                    end repeat
                    if output is "" then return "No recent emails."
                    return output
                on error errMsg
                    return "AppleScript Error: " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "mail_read_message":
            if message_index is None:
                return "Error: Missing 'message_index'"
            account_filter = f'of account "{account}"' if account else ""
            mailbox_target = f'mailbox "{mailbox}"' if mailbox and mailbox.upper() != "INBOX" else "inbox"
            script = f'''
            tell application "Mail"
                try
                    set m to message {message_index} of {mailbox_target} {account_filter}
                    return "From: " & (sender of m) & linefeed & "Subject: " & (subject of m) & linefeed & "Date: " & (date received of m as string) & linefeed & linefeed & (content of m)
                on error errMsg
                    return "AppleScript Error (Message may not exist): " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "mail_reply":
            if message_index is None or not body:
                return "Error: Missing 'message_index' or 'body'"
            escaped_body = body.replace('"', '\\"').replace('\n', '\\n')
            script = f'''
            tell application "Mail"
                try
                    set m to message {message_index} of inbox
                    set replyMsg to reply m with opening window
                    set content of replyMsg to "{escaped_body}" & linefeed & linefeed & (content of replyMsg)
                    send replyMsg
                    return "Reply sent successfully."
                on error errMsg
                    return "AppleScript Error: " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "mail_search":
            if not query:
                return "Error: Missing 'query'"
            return _run_shell(f'mdfind -onlyin ~/Library/Mail "kMDItemTextContent == \\"{query}\\"" | head -20')

        # =====================================================================
        # APPLE CALENDAR
        # =====================================================================
        elif action == "cal_list_events":
            cal_filter = f'calendar "{calendar_name}"' if calendar_name else "every calendar"
            script = f'''
            tell application "Calendar"
                try
                    set today to current date
                    set tomorrow to today + 1 * days
                    set output to ""
                    set allEvents to every event of {cal_filter} whose start date >= today and start date < tomorrow
                    repeat with e in allEvents
                        set output to output & (summary of e) & " | Start: " & (start date of e as string) & " | End: " & (end date of e as string) & linefeed
                    end repeat
                    if output is "" then return "No events today."
                    return output
                on error errMsg
                    return "AppleScript Error (Check Calendar name/permissions): " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "cal_create_event":
            if not event_summary or not start_date or not end_date:
                return "Error: Missing 'event_summary', 'start_date', or 'end_date'"
            cal_target = f'calendar "{calendar_name}"' if calendar_name else 'first calendar'
            loc_prop = f', location:"{location}"' if location else ""
            script = f'''
            tell application "Calendar"
                try
                    tell {cal_target}
                        make new event with properties {{summary:"{event_summary}", start date:date "{start_date}", end date:date "{end_date}"{loc_prop}}}
                    end tell
                    return "Event created successfully."
                on error errMsg
                    return "AppleScript Error: " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "cal_delete_event":
            if not event_summary:
                return "Error: Missing 'event_summary'"
            script = f'''
            tell application "Calendar"
                try
                    set deletedCount to 0
                    repeat with c in every calendar
                        set matchingEvents to (every event of c whose summary is "{event_summary}")
                        repeat with e in matchingEvents
                            delete e
                            set deletedCount to deletedCount + 1
                        end repeat
                    end repeat
                    return "Deleted " & deletedCount & " events."
                on error errMsg
                    return "AppleScript Error: " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "cal_list_calendars":
            script = '''
            tell application "Calendar"
                set output to ""
                repeat with c in every calendar
                    set output to output & (name of c) & linefeed
                end repeat
                return output
            end tell
            '''
            return _run_applescript(script)

        # =====================================================================
        # FINDER / FILES
        # =====================================================================
        elif action == "finder_list":
            if not path:
                return "Error: Missing 'path'"
            return _run_shell(f'ls -la "{path}"')

        elif action == "finder_move":
            if not path or not destination:
                return "Error: Missing 'path' or 'destination'"
            return _run_shell(f'mv "{path}" "{destination}"')

        elif action == "finder_copy":
            if not path or not destination:
                return "Error: Missing 'path' or 'destination'"
            return _run_shell(f'cp -r "{path}" "{destination}"')

        elif action == "finder_delete":
            if not path:
                return "Error: Missing 'path'"
            script = f'''
            tell application "Finder"
                try
                    move POSIX file "{path}" to trash
                    return "Moved to trash successfully."
                on error errMsg
                    return "AppleScript Error (Ensure path exists/permissions): " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "finder_create_folder":
            if not path:
                return "Error: Missing 'path'"
            return _run_shell(f'mkdir -p "{path}"')

        elif action == "finder_open":
            if not path:
                return "Error: Missing 'path'"
            return _run_shell(f'open "{path}"')

        elif action == "finder_get_info":
            if not path:
                return "Error: Missing 'path'"
            return _run_shell(f'stat -f "Name: %N%nSize: %z bytes%nModified: %Sm%nType: %HT" "{path}"')

        # =====================================================================
        # APPLE NOTES
        # =====================================================================
        elif action == "notes_list":
            n = max_results or 10
            folder_filter = f'of folder "{folder}"' if folder else ""
            script = f'''
            tell application "Notes"
                try
                    set output to ""
                    set noteList to notes {folder_filter}
                    set noteCount to count of noteList
                    set limit to {n}
                    if noteCount < limit then set limit to noteCount
                    repeat with i from 1 to limit
                        set n_item to item i of noteList
                        set output to output & i & ". " & (name of n_item) & " | Modified: " & (modification date of n_item as string) & linefeed
                    end repeat
                    if output is "" then return "No notes found."
                    return output
                on error errMsg
                    return "AppleScript Error (Check folder name/permissions): " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "notes_create":
            if not title or not body:
                return "Error: Missing 'title' or 'body'"
            escaped_body = body.replace('"', '\\"')
            folder_target = f'folder "{folder}"' if folder else 'default account'
            script = f'''
            tell application "Notes"
                tell {folder_target}
                    make new note with properties {{name:"{title}", body:"{escaped_body}"}}
                end tell
            end tell
            '''
            return _run_applescript(script)

        elif action == "notes_read":
            if not title:
                return "Error: Missing 'title'"
            script = f'''
            tell application "Notes"
                set matchingNotes to notes whose name is "{title}"
                if (count of matchingNotes) > 0 then
                    set n to item 1 of matchingNotes
                    return "Title: " & (name of n) & linefeed & "Body: " & (plaintext of n)
                else
                    return "Note not found: {title}"
                end if
            end tell
            '''
            return _run_applescript(script)

        elif action == "notes_delete":
            if not title:
                return "Error: Missing 'title'"
            script = f'''
            tell application "Notes"
                set matchingNotes to notes whose name is "{title}"
                repeat with n in matchingNotes
                    delete n
                end repeat
            end tell
            '''
            return _run_applescript(script)

        elif action == "notes_search":
            if not query:
                return "Error: Missing 'query'"
            script = f'''
            tell application "Notes"
                set output to ""
                set matchingNotes to notes whose name contains "{query}"
                repeat with n in matchingNotes
                    set output to output & (name of n) & linefeed
                end repeat
                if output is "" then return "No notes found matching '{query}'."
                return output
            end tell
            '''
            return _run_applescript(script)

        # =====================================================================
        # APPLE REMINDERS
        # =====================================================================
        elif action == "reminders_list":
            list_filter = f'list "{reminder_list}"' if reminder_list else "default list"
            script = f'''
            tell application "Reminders"
                try
                    set output to ""
                    set rList to reminders of {list_filter}
                    repeat with r in rList
                        if not (completed of r) then
                            set d to due date of r
                            if d is missing value then
                                set dueStr to "None"
                            else
                                set dueStr to (d as string)
                            end if
                            set output to output & (name of r) & " | Due: " & dueStr & linefeed
                        end if
                    end repeat
                    if output is "" then return "No active reminders."
                    return output
                on error errMsg
                    return "AppleScript Error: " & errMsg
                end try
            end tell
            '''
            return _run_applescript(script)

        elif action == "reminders_create":
            if not title:
                return "Error: Missing 'title'"
            list_target = f'list "{reminder_list}"' if reminder_list else "default list"
            due_prop = f', due date:date "{due_date}"' if due_date else ""
            script = f'''
            tell application "Reminders"
                tell {list_target}
                    make new reminder with properties {{name:"{title}"{due_prop}}}
                end tell
            end tell
            '''
            return _run_applescript(script)

        elif action == "reminders_complete":
            if not title:
                return "Error: Missing 'title'"
            script = f'''
            tell application "Reminders"
                set matchingReminders to reminders whose name is "{title}"
                repeat with r in matchingReminders
                    set completed of r to true
                end repeat
            end tell
            '''
            return _run_applescript(script)

        elif action == "reminders_delete":
            if not title:
                return "Error: Missing 'title'"
            script = f'''
            tell application "Reminders"
                set matchingReminders to reminders whose name is "{title}"
                repeat with r in matchingReminders
                    delete r
                end repeat
            end tell
            '''
            return _run_applescript(script)

        # =====================================================================
        # SYSTEM CONTROL
        # =====================================================================
        elif action == "system_volume":
            if value is not None:
                return _run_applescript(f'set volume output volume {value}')
            return _run_applescript('output volume of (get volume settings)')

        elif action == "system_brightness":
            return _run_shell("brightness -l 2>/dev/null || echo 'Brightness tool not installed. Use: brew install brightness'")

        elif action == "system_screenshot":
            target = path or "~/Desktop/screenshot.png"
            return _run_shell(f'screencapture -x "{target}"')

        elif action == "system_notify":
            if not title or not body:
                return "Error: Missing 'title' or 'body'"
            escaped_body = body.replace('"', '\\"')
            escaped_title = title.replace('"', '\\"')
            script = f'display notification "{escaped_body}" with title "{escaped_title}"'
            return _run_applescript(script)

        elif action == "system_open_app":
            if not app_name:
                return "Error: Missing 'app_name'"
            script = f'''
            tell application "{app_name}"
                activate
            end tell
            '''
            return _run_applescript(script)

        elif action == "system_quit_app":
            if not app_name:
                return "Error: Missing 'app_name'"
            script = f'''
            tell application "{app_name}"
                quit
            end tell
            '''
            return _run_applescript(script)

        elif action == "system_list_apps":
            script = '''
            tell application "System Events"
                set output to ""
                repeat with p in (every process whose background only is false)
                    set output to output & (name of p) & linefeed
                end repeat
                return output
            end tell
            '''
            return _run_applescript(script)

        elif action == "system_clipboard_get":
            return _run_shell("pbpaste")

        elif action == "system_clipboard_set":
            if not value:
                return "Error: Missing 'value'"
            escaped = value.replace("'", "'\\''")
            return _run_shell(f"echo '{escaped}' | pbcopy")

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"macOS Control Error: {str(e)}\n{traceback.format_exc()}"
