"""
gmail.py — Space Black Gmail API Tool
Provides a single tool entry point `gmail_act` for managing Gmail.
"""

import base64
from email.mime.text import MIMEText
from typing import Optional
from langchain_core.tools import tool


def _get_gmail_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("gmail", "v1")


@tool
def gmail_act(
    action: str,
    to: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    message_id: Optional[str] = None,
    query: Optional[str] = None,
    max_results: Optional[int] = 10,
    label: Optional[str] = None,
) -> str:
    """
    A unified tool for interacting with Gmail.

    Actions:
    - 'send_email': Send an email. (Requires 'to', 'subject', 'body')
    - 'read_inbox': List recent inbox messages. (Optional 'max_results')
    - 'read_email': Read full email by ID. (Requires 'message_id')
    - 'reply_email': Reply to a thread. (Requires 'message_id', 'body')
    - 'search_emails': Search with Gmail query syntax. (Requires 'query', optional 'max_results')
    - 'list_labels': List all Gmail labels.
    - 'delete_email': Trash an email. (Requires 'message_id')
    - 'mark_read': Mark email as read. (Requires 'message_id')
    - 'mark_unread': Mark email as unread. (Requires 'message_id')
    """
    try:
        service = _get_gmail_service()
    except Exception as e:
        return f"Gmail Auth Error: {e}"

    try:
        if action == "send_email":
            if not to or not subject or not body:
                return "Error: Missing 'to', 'subject', or 'body'"
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            result = service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            return f"Email sent successfully. Message ID: {result.get('id')}"

        elif action == "read_inbox":
            results = service.users().messages().list(
                userId="me", labelIds=["INBOX"], maxResults=max_results
            ).execute()
            messages = results.get("messages", [])
            if not messages:
                return "No messages in inbox."
            output = []
            for msg in messages:
                detail = service.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()
                headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
                output.append(
                    f"ID: {msg['id']} | From: {headers.get('From', 'N/A')} | "
                    f"Subject: {headers.get('Subject', 'N/A')} | Date: {headers.get('Date', 'N/A')}"
                )
            return "\n".join(output)

        elif action == "read_email":
            if not message_id:
                return "Error: Missing 'message_id'"
            msg = service.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            # Extract body
            body_text = ""
            payload = msg.get("payload", {})
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                        break
            elif "body" in payload and payload["body"].get("data"):
                body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

            return (
                f"From: {headers.get('From', 'N/A')}\n"
                f"To: {headers.get('To', 'N/A')}\n"
                f"Subject: {headers.get('Subject', 'N/A')}\n"
                f"Date: {headers.get('Date', 'N/A')}\n\n"
                f"{body_text}"
            )

        elif action == "reply_email":
            if not message_id or not body:
                return "Error: Missing 'message_id' or 'body'"
            original = service.users().messages().get(
                userId="me", id=message_id, format="metadata",
                metadataHeaders=["From", "Subject", "Message-ID"]
            ).execute()
            headers = {h["name"]: h["value"] for h in original.get("payload", {}).get("headers", [])}
            reply = MIMEText(body)
            reply["to"] = headers.get("From", "")
            reply["subject"] = "Re: " + headers.get("Subject", "")
            reply["In-Reply-To"] = headers.get("Message-ID", "")
            reply["References"] = headers.get("Message-ID", "")
            raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
            result = service.users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": original.get("threadId")}
            ).execute()
            return f"Reply sent successfully. Message ID: {result.get('id')}"

        elif action == "search_emails":
            if not query:
                return "Error: Missing 'query'"
            results = service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()
            messages = results.get("messages", [])
            if not messages:
                return f"No messages found for query: {query}"
            output = []
            for msg in messages:
                detail = service.users().messages().get(
                    userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()
                headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
                output.append(
                    f"ID: {msg['id']} | From: {headers.get('From', 'N/A')} | "
                    f"Subject: {headers.get('Subject', 'N/A')}"
                )
            return "\n".join(output)

        elif action == "list_labels":
            results = service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])
            return "\n".join([f"{l['id']}: {l['name']}" for l in labels])

        elif action == "delete_email":
            if not message_id:
                return "Error: Missing 'message_id'"
            service.users().messages().trash(userId="me", id=message_id).execute()
            return f"Email {message_id} moved to trash."

        elif action == "mark_read":
            if not message_id:
                return "Error: Missing 'message_id'"
            service.users().messages().modify(
                userId="me", id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            return f"Email {message_id} marked as read."

        elif action == "mark_unread":
            if not message_id:
                return "Error: Missing 'message_id'"
            service.users().messages().modify(
                userId="me", id=message_id,
                body={"addLabelIds": ["UNREAD"]}
            ).execute()
            return f"Email {message_id} marked as unread."

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Gmail Error: {str(e)}\n{traceback.format_exc()}"
