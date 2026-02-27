"""
docs.py — Space Black Google Docs API Tool
Provides a single tool entry point `docs_act` for managing Google Docs.
"""

from typing import Optional
from langchain_core.tools import tool


def _get_docs_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("docs", "v1")


def _get_drive_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("drive", "v3")


@tool
def docs_act(
    action: str,
    document_id: Optional[str] = None,
    title: Optional[str] = None,
    text: Optional[str] = None,
    index: Optional[int] = None,
    find: Optional[str] = None,
    replace: Optional[str] = None,
    max_results: Optional[int] = 20,
) -> str:
    """
    A unified tool for interacting with Google Docs.

    Actions:
    - 'create_doc': Create a new document. (Requires 'title')
    - 'read_doc': Read full text of a document. (Requires 'document_id')
    - 'append_text': Append text to end of doc. (Requires 'document_id', 'text')
    - 'insert_text': Insert text at a position. (Requires 'document_id', 'text', 'index')
    - 'replace_text': Find and replace text. (Requires 'document_id', 'find', 'replace')
    - 'list_docs': List recent documents.
    """
    try:
        docs_service = _get_docs_service()
    except Exception as e:
        return f"Docs Auth Error: {e}"

    try:
        if action == "create_doc":
            if not title:
                return "Error: Missing 'title'"
            doc = docs_service.documents().create(body={"title": title}).execute()
            return f"Document created: '{title}' (ID: {doc['documentId']})"

        elif action == "read_doc":
            if not document_id:
                return "Error: Missing 'document_id'"
            doc = docs_service.documents().get(documentId=document_id).execute()
            content = doc.get("body", {}).get("content", [])
            text_parts = []
            for element in content:
                if "paragraph" in element:
                    for elem in element["paragraph"].get("elements", []):
                        run = elem.get("textRun")
                        if run:
                            text_parts.append(run.get("content", ""))
            full_text = "".join(text_parts)
            return f"Title: {doc.get('title', 'Untitled')}\n\n{full_text}"

        elif action == "append_text":
            if not document_id or not text:
                return "Error: Missing 'document_id' or 'text'"
            # Get end index of document
            doc = docs_service.documents().get(documentId=document_id).execute()
            body_content = doc.get("body", {}).get("content", [])
            end_index = 1
            for element in body_content:
                if "endIndex" in element:
                    end_index = element["endIndex"]
            requests_body = [
                {"insertText": {"location": {"index": end_index - 1}, "text": text}}
            ]
            docs_service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests_body}
            ).execute()
            return f"Text appended to document {document_id}."

        elif action == "insert_text":
            if not document_id or not text or index is None:
                return "Error: Missing 'document_id', 'text', or 'index'"
            requests_body = [
                {"insertText": {"location": {"index": index}, "text": text}}
            ]
            docs_service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests_body}
            ).execute()
            return f"Text inserted at index {index} in document {document_id}."

        elif action == "replace_text":
            if not document_id or not find or not replace:
                return "Error: Missing 'document_id', 'find', or 'replace'"
            requests_body = [
                {
                    "replaceAllText": {
                        "containsText": {"text": find, "matchCase": True},
                        "replaceText": replace,
                    }
                }
            ]
            result = docs_service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests_body}
            ).execute()
            count = 0
            for reply in result.get("replies", []):
                count += reply.get("replaceAllText", {}).get("occurrencesChanged", 0)
            return f"Replaced {count} occurrences of '{find}' with '{replace}'."

        elif action == "list_docs":
            drive_service = _get_drive_service()
            results = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.document'",
                pageSize=max_results,
                fields="files(id, name, modifiedTime)"
            ).execute()
            files = results.get("files", [])
            if not files:
                return "No documents found."
            return "\n".join([
                f"ID: {f['id']} | {f['name']} | Modified: {f.get('modifiedTime', 'N/A')}"
                for f in files
            ])

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Docs Error: {str(e)}\n{traceback.format_exc()}"
