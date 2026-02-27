# PayPal Skill

## Overview
Connects Space Black to the PayPal Developer API via OAuth2, enabling autonomous check of balances, sending payouts, and generating invoices.

**Security Note:** The `send_payout` action has a hardcoded strict human-in-the-loop confirmation step. The agent cannot send money without explicitly waiting for you to type `yes` in the terminal.

## Setup
1. Go to the [PayPal Developer Dashboard](https://developer.paypal.com/).
2. Create a new App (Sandbox or Live).
3. Copy the **Client ID** and **Client Secret**.
4. Open your `config.json` (or use the Space Black TUI).
5. Set `skills.paypal.enabled` to `true`.
6. Enter your `client_id` and `client_secret`.
7. Set `environment` to `"sandbox"` or `"live"`.

## Tools

### `paypal_act`
| Action | Description | Required Args | Optional Args |
|--------|-------------|---------------|---------------|
| `get_balance` | Retrieve current PayPal account balance | — | — |
| `send_payout` | Send money to an email address | `amount`, `currency`, `recipient` (email), `note` | — |
| `create_invoice` | Draft an invoice for a client | `recipient` (email), `items` | `currency`, `note`, `invoice_number` |

#### Data Structures

**`items` (for `create_invoice`)**
An array of objects representing the invoice line items:
```json
[
  {
    "name": "Web Development Services",
    "quantity": "1",
    "unit_amount": {
      "currency_code": "USD",
      "value": "500.00"
    }
  }
]
```
