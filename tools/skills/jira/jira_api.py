"""
jira_api.py — Space Black autonomous Jira API Tool
Provides a single tool entry point `jira_act` to manage issues, projects, and comments.
"""

import os
import requests
import base64
from typing import Optional
from langchain_core.tools import tool

# API Endpoint Paths
JIRA_API_BASE = "/rest/api/3"

def _get_jira_config() -> dict:
    """Returns Jira configuration including domain, email, and API token."""
    domain = None
    email = None
    token = None
    
    # Check config.json first
    try:
        import json
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config_data = json.load(f)
                jira_config = config_data.get("skills", {}).get("jira", {})
                domain = jira_config.get("domain")
                email = jira_config.get("email")
                token = jira_config.get("api_token")
    except Exception:
        pass
        
    # Fallback to .env
    if not domain:
        domain = os.environ.get("JIRA_DOMAIN")
    if not email:
        email = os.environ.get("JIRA_EMAIL")
    if not token:
        token = os.environ.get("JIRA_API_TOKEN")
        
    if not domain or not email or not token:
        raise ValueError("Missing Jira config. Please add 'domain', 'email', and 'api_token' via the TUI /skills menu or set JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN in .env")
        
    # Ensure domain doesn't end with slash
    if domain.endswith("/"):
        domain = domain[:-1]
        
    return {
        "domain": domain,
        "email": email,
        "token": token
    }

def _get_headers(email: str, token: str) -> dict:
    """Returns headers required for Jira API authentication."""
    auth_str = f"{email}:{token}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    return {
        "Authorization": f"Basic {b64_auth}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def _handle_response(resp: requests.Response) -> str:
    """Helper to consistently handle API responses."""
    if resp.status_code >= 400:
        try:
            err_data = resp.json()
            err_msgs = err_data.get("errorMessages", [])
            err_dict = err_data.get("errors", {})
            err_str = " | ".join(err_msgs) + " | " + str(err_dict)
            return f"Jira API Error: {resp.status_code} - {err_str}"
        except:
            return f"Jira API Error: {resp.status_code} - {resp.text}"
    
    if resp.status_code == 204:
        return "Success (Status 204 No Content)"
        
    try:
        return str(resp.json())
    except:
        return f"Success (No JSON returned, status {resp.status_code})"


@tool
def jira_act(
    action: str, 
    issue_key: Optional[str] = None, 
    project_key: Optional[str] = None,
    summary: Optional[str] = None, 
    description: Optional[str] = None, 
    issue_type: Optional[str] = "Task",
    jql_query: Optional[str] = None,
    comment_body: Optional[str] = None,
    transition_id: Optional[str] = None
) -> str:
    """
    A unified tool for interacting with the Jira API. 
    
    Actions:
    - 'get_issue': Get details of a specific issue. (Requires 'issue_key')
    - 'search_issues': Search issues using JQL limit 50. (Requires 'jql_query'. Format: 'project = PROJ AND status = "In Progress"')
    - 'create_issue': Create a new ticket. (Requires 'project_key', 'summary', 'description', 'issue_type')
    - 'add_comment': Add a comment to an issue. (Requires 'issue_key', 'comment_body')
    - 'get_transitions': List valid status transitions for an issue. (Requires 'issue_key')
    - 'transition_issue': Move an issue to a new status. (Requires 'issue_key', 'transition_id')
    
    To change a status, FIRST use 'get_transitions' to find the correct 'transition_id', then use 'transition_issue'.
    """
    try:
        config = _get_jira_config()
        domain = config["domain"]
        headers = _get_headers(config["email"], config["token"])
        api_base = f"{domain}{JIRA_API_BASE}"
    except Exception as e:
        return str(e)

    try:
        if action == "get_issue":
            if not issue_key: return "Error: Missing 'issue_key' (e.g., 'PROJ-123')"
            resp = requests.get(f"{api_base}/issue/{issue_key}", headers=headers)
            return _handle_response(resp)

        elif action == "search_issues":
            if not jql_query: return "Error: Missing 'jql_query'"
            payload = {
                "jql": jql_query,
                "startAt": 0,
                "maxResults": 50,
                "fields": ["summary", "status", "assignee", "created", "updated"]
            }
            resp = requests.post(f"{api_base}/search", headers=headers, json=payload)
            return _handle_response(resp)

        elif action == "create_issue":
            if not project_key or not summary or not description: 
                return "Error: Missing 'project_key', 'summary', or 'description'"
            
            # Jira v3 expects Atlassian Document Format for description
            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "text": description,
                                        "type": "text"
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {"name": issue_type}
                }
            }
            resp = requests.post(f"{api_base}/issue", headers=headers, json=payload)
            return _handle_response(resp)

        elif action == "add_comment":
            if not issue_key or not comment_body: return "Error: Missing 'issue_key' or 'comment_body'"
            
            # Jira v3 expects Atlassian Document Format for comments
            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "text": comment_body,
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                }
            }
            resp = requests.post(f"{api_base}/issue/{issue_key}/comment", headers=headers, json=payload)
            return _handle_response(resp)

        elif action == "get_transitions":
            if not issue_key: return "Error: Missing 'issue_key'"
            resp = requests.get(f"{api_base}/issue/{issue_key}/transitions", headers=headers)
            return _handle_response(resp)

        elif action == "transition_issue":
            if not issue_key or not transition_id: return "Error: Missing 'issue_key' or 'transition_id'"
            payload = {
                "transition": {
                    "id": transition_id
                }
            }
            resp = requests.post(f"{api_base}/issue/{issue_key}/transitions", headers=headers, json=payload)
            return _handle_response(resp)

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Tool execution failed: {str(e)}\n{traceback.format_exc()}"
