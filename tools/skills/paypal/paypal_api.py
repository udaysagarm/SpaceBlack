"""
paypal_api.py — Space Black PayPal Integration
Provides a single tool `paypal_act` to fetch balances, send payouts, and generate invoices.

REQUIRES user interaction (confirmation) before sending actual money via the Payouts API.
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import uuid
import sys
from typing import Optional
from langchain_core.tools import tool

CONFIG_FILE = "config.json"

def _load_paypal_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config.get("skills", {}).get("paypal", {})
    except Exception:
        return {}


def _get_base_url():
    config = _load_paypal_config()
    if config.get("environment", "sandbox").lower() == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _get_access_token():
    config = _load_paypal_config()
    client_id = config.get("client_id", "")
    client_secret = config.get("client_secret", "")

    if not client_id or not client_secret:
        raise ValueError("PayPal Client ID or Secret missing in config.json. Use the /skills menu to set them.")

    import base64
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    url = f"{_get_base_url()}/v1/oauth2/token"
    # Basic data map for urlencoded request
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")

    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"Basic {b64_auth}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as response:
            res_val = response.read().decode("utf-8")
            return json.loads(res_val).get("access_token")
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        raise Exception(f"Failed to get PayPal Access Token: {error_msg}")


def _request(method: str, endpoint: str, payload: dict = None):
    token = _get_access_token()
    url = f"{_get_base_url()}{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = None
    if payload:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res_val = response.read().decode("utf-8")
            if res_val:
                return json.loads(res_val)
            return {"status": "success", "message": "No content returned"}
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        raise Exception(f"PayPal API Error ({e.code}): {error_msg}")


@tool
def paypal_act(
    action: str,
    amount: Optional[float] = None,
    currency: Optional[str] = "USD",
    recipient: Optional[str] = None,  # For payouts (email)
    note: Optional[str] = None,       # For payouts or invoices
    items: Optional[list] = None,     # For invoices: [{"name": "Web Dev", "quantity": "1", "unit_amount": {"currency_code": "USD", "value": "500.00"}}]
    invoice_number: Optional[str] = None # Optional custom invoice number
) -> str:
    """
    A unified tool for interacting with the PayPal Developer API.

    Actions:
    - 'get_balance': Retrieve current PayPal account balance.
    - 'send_payout': Send money (Requires 'amount', 'currency', 'recipient', 'note').
                     WARNING: This will prompt the user in the terminal for strict confirmation.
    - 'create_invoice': Draft an invoice (Requires 'recipient', 'items', optional 'note').
                        Items must be a list of dicts with 'name', 'quantity', 'unit_amount'.
    """
    try:
        if action == "get_balance":
            result = _request("GET", "/v1/reporting/balances")
            balances = result.get("balances", [])
            output = []
            for b in balances:
                curr = b.get("currency", "USD")
                avail = b.get("available_balance", {}).get("value", "0.00")
                output.append(f"{avail} {curr}")
            if not output:
                return "No balance found or non-business account."
            return f"Available PayPal Balance(s): {', '.join(output)}"

        elif action == "send_payout":
            if not amount or not recipient or not note:
                return "Error: send_payout requires 'amount', 'recipient' (email), and 'note'."

            # SECURITY CONFIRMATION
            print("\n" + "="*50)
            print("🚨 CRITICAL ALERT: AI INITIATED PAYOUT 🚨")
            print(f"Action: Send Money via PayPal")
            print(f"Recipient: {recipient}")
            print(f"Amount: {amount} {currency}")
            print(f"Note: {note}")
            print("="*50)
            print("Do you authorize this transaction? Type 'yes' to send money, or any other key to cancel: ", end="")
            sys.stdout.flush()

            # Read from standard input directly
            user_input = sys.stdin.readline().strip().lower()

            if user_input != 'yes':
                return "Transaction cancelled by human user. Payout aborted."

            print("\nProcessing payout...")

            # Construct Payout Payload
            sender_batch_id = f"Payout_{uuid.uuid4().hex[:8]}"
            payload = {
                "sender_batch_header": {
                    "sender_batch_id": sender_batch_id,
                    "email_subject": "You have a payment!",
                    "email_message": note
                },
                "items": [
                    {
                        "recipient_type": "EMAIL",
                        "amount": {
                            "value": f"{float(amount):.2f}",
                            "currency": currency
                        },
                        "note": note,
                        "sender_item_id": f"Item_{uuid.uuid4().hex[:8]}",
                        "receiver": recipient
                    }
                ]
            }

            result = _request("POST", "/v1/payments/payouts", payload)
            batch_id = result.get("batch_header", {}).get("payout_batch_id", "Unknown")
            status = result.get("batch_header", {}).get("batch_status", "Unknown")

            return f"Payout initialized successfully.\nBatch ID: {batch_id}\nStatus: {status}"

        elif action == "create_invoice":
            if not recipient or not items:
                return "Error: create_invoice requires 'recipient' (email address dict) and 'items' list."

            invoice_payload = {
                "detail": {
                    "currency_code": currency,
                    "note": note or "Invoice generated by Space Black."
                },
                "primary_recipients": [
                    {
                        "billing_info": {
                            "email_address": recipient
                        }
                    }
                ],
                "items": items
            }

            if invoice_number:
                invoice_payload["detail"]["invoice_number"] = invoice_number
            else:
                invoice_payload["detail"]["invoice_number"] = f"INV-{uuid.uuid4().hex[:6].upper()}"

            # 1. Draft the invoice
            draft_result = _request("POST", "/v2/invoicing/invoices", invoice_payload)
            invoice_href = draft_result.get("href")
            
            if not invoice_href:
                return f"Failed to parse drafted invoice response: {draft_result}"

            # Extract the ID from the href
            invoice_id = invoice_href.split("/")[-1]

            return f"Invoice drafted successfully.\nInvoice ID: {invoice_id}\nYou can send it manually or build a send action."

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"PayPal Error: {str(e)}\n{traceback.format_exc()}"
