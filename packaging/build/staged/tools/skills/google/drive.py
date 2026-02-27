"""
drive.py — Space Black Google Drive API Tool
Provides a single tool entry point `drive_act` for managing Google Drive.
"""

import os
from typing import Optional
from langchain_core.tools import tool


def _get_drive_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("drive", "v3")


@tool
def drive_act(
    action: str,
    file_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    name: Optional[str] = None,
    new_name: Optional[str] = None,
    local_path: Optional[str] = None,
    query: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = "reader",
    parent_id: Optional[str] = None,
    max_results: Optional[int] = 20,
) -> str:
    """
    A unified tool for interacting with Google Drive.

    Actions:
    - 'list_files': List files in Drive or a folder. (Optional 'folder_id', 'max_results')
    - 'search_files': Search files by name/type. (Requires 'query')
    - 'create_folder': Create a new folder. (Requires 'name', optional 'parent_id')
    - 'upload_file': Upload a local file. (Requires 'local_path', 'name', optional 'folder_id')
    - 'download_file': Download a file locally. (Requires 'file_id', 'local_path')
    - 'move_file': Move file to different folder. (Requires 'file_id', 'folder_id')
    - 'rename_file': Rename a file. (Requires 'file_id', 'new_name')
    - 'delete_file': Trash a file. (Requires 'file_id')
    - 'get_file_info': Get metadata of a file. (Requires 'file_id')
    - 'share_file': Share a file with a user. (Requires 'file_id', 'email', optional 'role')
    """
    try:
        service = _get_drive_service()
    except Exception as e:
        return f"Drive Auth Error: {e}"

    try:
        if action == "list_files":
            q = f"'{folder_id}' in parents" if folder_id else None
            results = service.files().list(
                q=q, pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, size)"
            ).execute()
            files = results.get("files", [])
            if not files:
                return "No files found."
            output = []
            for f in files:
                size = f.get("size", "N/A")
                output.append(
                    f"ID: {f['id']} | {f['name']} | Type: {f['mimeType']} | "
                    f"Modified: {f.get('modifiedTime', 'N/A')} | Size: {size}"
                )
            return "\n".join(output)

        elif action == "search_files":
            if not query:
                return "Error: Missing 'query'"
            results = service.files().list(
                q=f"name contains '{query}'", pageSize=max_results,
                fields="files(id, name, mimeType)"
            ).execute()
            files = results.get("files", [])
            if not files:
                return f"No files found matching '{query}'."
            return "\n".join([f"ID: {f['id']} | {f['name']} | {f['mimeType']}" for f in files])

        elif action == "create_folder":
            if not name:
                return "Error: Missing 'name'"
            metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder"
            }
            if parent_id:
                metadata["parents"] = [parent_id]
            folder = service.files().create(body=metadata, fields="id, name").execute()
            return f"Folder created: {folder['name']} (ID: {folder['id']})"

        elif action == "upload_file":
            if not local_path or not name:
                return "Error: Missing 'local_path' or 'name'"
            if not os.path.exists(local_path):
                return f"Error: Local file not found: {local_path}"
            from googleapiclient.http import MediaFileUpload
            metadata = {"name": name}
            if folder_id:
                metadata["parents"] = [folder_id]
            media = MediaFileUpload(local_path)
            uploaded = service.files().create(
                body=metadata, media_body=media, fields="id, name"
            ).execute()
            return f"Uploaded: {uploaded['name']} (ID: {uploaded['id']})"

        elif action == "download_file":
            if not file_id or not local_path:
                return "Error: Missing 'file_id' or 'local_path'"
            from googleapiclient.http import MediaIoBaseDownload
            import io
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(fh.getvalue())
            return f"Downloaded to: {local_path}"

        elif action == "move_file":
            if not file_id or not folder_id:
                return "Error: Missing 'file_id' or 'folder_id'"
            file_info = service.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(file_info.get("parents", []))
            service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, parents"
            ).execute()
            return f"File {file_id} moved to folder {folder_id}."

        elif action == "rename_file":
            if not file_id or not new_name:
                return "Error: Missing 'file_id' or 'new_name'"
            service.files().update(
                fileId=file_id, body={"name": new_name}, fields="id, name"
            ).execute()
            return f"File {file_id} renamed to '{new_name}'."

        elif action == "delete_file":
            if not file_id:
                return "Error: Missing 'file_id'"
            service.files().update(
                fileId=file_id, body={"trashed": True}
            ).execute()
            return f"File {file_id} moved to trash."

        elif action == "get_file_info":
            if not file_id:
                return "Error: Missing 'file_id'"
            info = service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, owners, webViewLink"
            ).execute()
            owners = ", ".join([o.get("emailAddress", "") for o in info.get("owners", [])])
            return (
                f"Name: {info['name']}\nID: {info['id']}\nType: {info['mimeType']}\n"
                f"Size: {info.get('size', 'N/A')}\nModified: {info.get('modifiedTime', 'N/A')}\n"
                f"Owners: {owners}\nLink: {info.get('webViewLink', 'N/A')}"
            )

        elif action == "share_file":
            if not file_id or not email:
                return "Error: Missing 'file_id' or 'email'"
            permission = {"type": "user", "role": role, "emailAddress": email}
            service.permissions().create(
                fileId=file_id, body=permission, sendNotificationEmail=True
            ).execute()
            return f"File {file_id} shared with {email} as {role}."

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Drive Error: {str(e)}\n{traceback.format_exc()}"
