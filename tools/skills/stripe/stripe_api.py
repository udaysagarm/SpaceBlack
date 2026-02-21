"""
stripe_api.py — Space Black autonomous Stripe Tool
Provides `stripe_act` to manage customers, balances, and payments securely.
"""
import os
import requests
import sys
from typing import Optional
from langchain_core.tools import tool

# Constants
STRIPE_API_BASE = "https://api.stripe.com/v1"

def _get_auth() -> tuple:
    """Returns Basic Auth tuple required for Stripe API."""
    token = None
    
    # Check config.json first (via TUI /skills menu)
    try:
        import json
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config_data = json.load(f)
                token = config_data.get("skills", {}).get("stripe", {}).get("api_key")
    except Exception:
        pass
        
    # Fallback to .env
    if not token:
        token = os.environ.get("STRIPE_API_KEY") or os.environ.get("STRIPE_SECRET_KEY")
        
    if not token:
        raise ValueError("Missing Stripe API Key. Please add it via the Custom Skills menu (Cmd+S) or set STRIPE_API_KEY in .env")
        
    # Stripe uses Basic Auth with the secret key as the username, no password
    return (token, "")

def _handle_response(resp: requests.Response) -> str:
    """Helper to consistently handle Stripe JSON schemas."""
    try:
        data = resp.json()
        if resp.status_code >= 400:
            error = data.get("error", {})
            return f"Stripe API Error ({resp.status_code}): {error.get('message', 'Unknown Error')} (Code: {error.get('code')})"
        return str(data)
    except:
        return f"HTTP {resp.status_code}: {resp.text}"

@tool
def stripe_act(
    action: str, 
    email: Optional[str] = None, 
    name: Optional[str] = None, 
    amount: Optional[int] = None, 
    currency: Optional[str] = "usd", 
    customer_id: Optional[str] = None, 
    price_id: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None
) -> str:
    """
    A unified tool for interacting with the Stripe Payment API.
    
    WARNING: For any action involving 'charge' or 'payment_intent', YOU MUST explicitly 
    receive permission from the user in their preceding chat before executing the tool. 
    Never guess permission.
    
    Actions:
    - 'get_balance': Retrieve current Stripe account balance.
    - 'list_customers': Search/List existing customers (pass 'email' to filter).
    - 'create_customer': Create a new customer (requires 'email' and 'name').
    - 'create_payment_intent': Create a payment intent (requires 'amount' in cents, 'currency').
    - 'create_charge': Run a direct charge (requires 'amount' in cents, 'currency', 'customer_id').
    - 'list_products': List active Stripe products.
    - 'list_prices': List product prices.
    - 'create_checkout_session': Generate a hosted payment link (requires 'price_id', 'success_url', 'cancel_url').
    """
    try:
        auth = _get_auth()
    except Exception as e:
        return str(e)

    try:
        if action == "get_balance":
            resp = requests.get(f"{STRIPE_API_BASE}/balance", auth=auth)
            return _handle_response(resp)

        elif action == "list_customers":
            params = {}
            if email: params["email"] = email
            resp = requests.get(f"{STRIPE_API_BASE}/customers", auth=auth, params=params)
            return _handle_response(resp)

        elif action == "create_customer":
            if not email or not name: return "Error: Missing 'email' or 'name'."
            data = {"email": email, "name": name}
            resp = requests.post(f"{STRIPE_API_BASE}/customers", auth=auth, data=data)
            return _handle_response(resp)

        elif action == "create_payment_intent":
            if not amount or not currency: return "Error: Missing 'amount' (cents) or 'currency'."

            print("\n" + "="*50)
            print("🚨 CRITICAL ALERT: AI INITIATED PAYMENT INTENT 🚨")
            print(f"Action: Create Stripe Payment Intent")
            print(f"Customer ID: {customer_id or 'Guest'}")
            print(f"Amount: {amount} {currency.upper()} (in cents)")
            print("="*50)
            print("Do you authorize this transaction? Type 'yes' to proceed, or any other key to cancel: ", end="")
            sys.stdout.flush()
            user_input = sys.stdin.readline().strip().lower()

            if user_input != 'yes':
                return "Payment Intent creation cancelled by human user. Aborted."

            data = {"amount": amount, "currency": currency.lower()}
            if customer_id: data["customer"] = customer_id
            resp = requests.post(f"{STRIPE_API_BASE}/payment_intents", auth=auth, data=data)
            return _handle_response(resp)

        elif action == "create_charge":
            if not amount or not currency or not customer_id: 
                return "Error: Missing 'amount' (cents), 'currency', or 'customer_id'."

            print("\n" + "="*50)
            print("🚨 CRITICAL ALERT: AI INITIATED DIRECT STRIPE CHARGE 🚨")
            print(f"Action: Direct Stripe Charge")
            print(f"Customer ID: {customer_id}")
            print(f"Amount: {amount} {currency.upper()} (in cents)")
            print("="*50)
            print("Do you authorize this transaction? Type 'yes' to proceed, or any other key to cancel: ", end="")
            sys.stdout.flush()
            user_input = sys.stdin.readline().strip().lower()

            if user_input != 'yes':
                return "Direct Charge cancelled by human user. Aborted."

            data = {"amount": amount, "currency": currency.lower(), "customer": customer_id}
            resp = requests.post(f"{STRIPE_API_BASE}/charges", auth=auth, data=data)
            return _handle_response(resp)
            
        elif action == "list_products":
            resp = requests.get(f"{STRIPE_API_BASE}/products?active=true", auth=auth)
            return _handle_response(resp)
            
        elif action == "list_prices":
            resp = requests.get(f"{STRIPE_API_BASE}/prices?active=true", auth=auth)
            return _handle_response(resp)
            
        elif action == "create_checkout_session":
            if not price_id or not success_url or not cancel_url:
                return "Error: Missing 'price_id', 'success_url', or 'cancel_url'."
            data = {
                "success_url": success_url,
                "cancel_url": cancel_url,
                "mode": "payment",
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": 1
            }
            if customer_id: data["customer"] = customer_id
            resp = requests.post(f"{STRIPE_API_BASE}/checkout/sessions", auth=auth, data=data)
            return _handle_response(resp)

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Stripe Tool execution failed: {str(e)}\n{traceback.format_exc()}"
