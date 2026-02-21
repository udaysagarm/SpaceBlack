"""
wallet.py — Space Black Google Wallet API Tool
Provides a single tool entry point `wallet_act` for managing Google Wallet passes.
"""

from typing import Optional
from langchain_core.tools import tool


def _get_wallet_service():
    from tools.skills.google.auth import get_google_service
    return get_google_service("walletobjects", "v1")


@tool
def wallet_act(
    action: str,
    issuer_id: Optional[str] = None,
    class_id: Optional[str] = None,
    class_suffix: Optional[str] = None,
    object_id: Optional[str] = None,
    object_suffix: Optional[str] = None,
    payload: Optional[dict] = None,
) -> str:
    """
    A unified tool for interacting with Google Wallet API (Generic Passes).

    Actions:
    - 'get_issuer': Get issuer details. (Requires 'issuer_id')
    - 'list_classes': List pass classes for an issuer. (Requires 'issuer_id')
    - 'get_class': Get a specific pass class. (Requires 'issuer_id' and 'class_suffix' OR fully qualified 'class_id')
    - 'create_class': Create a new pass class. (Requires 'payload')
    - 'get_object': Get a specific pass object. (Requires 'issuer_id' and 'object_suffix' OR fully qualified 'object_id')
    - 'create_object': Create a new pass object. (Requires 'payload')
    """
    try:
        service = _get_wallet_service()
    except Exception as e:
        return f"Wallet Auth Error: {e}"

    try:
        if action == "get_issuer":
            if not issuer_id:
                return "Error: Missing 'issuer_id'"
            result = service.issuer().get(issuerId=issuer_id).execute()
            return f"Issuer: {result}"

        elif action == "list_classes":
            if not issuer_id:
                return "Error: Missing 'issuer_id'"
            result = service.genericclass().list(issuerId=issuer_id).execute()
            return f"Classes: {result.get('resources', [])}"

        elif action == "get_class":
            cid = class_id or f"{issuer_id}.{class_suffix}"
            if not cid or cid == ".":
                return "Error: Missing 'class_id' or ('issuer_id' and 'class_suffix')"
            result = service.genericclass().get(resourceId=cid).execute()
            return f"Class Details: {result}"

        elif action == "create_class":
            if not payload:
                return "Error: Missing 'payload'"
            result = service.genericclass().insert(body=payload).execute()
            return f"Class created: {result.get('id')}"

        elif action == "get_object":
            oid = object_id or f"{issuer_id}.{object_suffix}"
            if not oid or oid == ".":
                return "Error: Missing 'object_id' or ('issuer_id' and 'object_suffix')"
            result = service.genericobject().get(resourceId=oid).execute()
            return f"Object Details: {result}"

        elif action == "create_object":
            if not payload:
                return "Error: Missing 'payload'"
            result = service.genericobject().insert(body=payload).execute()
            return f"Object created: {result.get('id')}"

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Google Wallet Error: {str(e)}\n{traceback.format_exc()}"
