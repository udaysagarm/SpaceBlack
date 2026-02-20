"""
github.py — Space Black autonomous GitHub API Tool
Provides a single tool entry point `github_act` to manage repos, issues, and direct file commits.
"""

import os
import requests
from typing import Optional
from langchain_core.tools import tool

# Constants
GITHUB_API_BASE = "https://api.github.com"

def _get_headers() -> dict:
    """Returns headers required for GitHub API authentication."""
    token = None
    
    # Check config.json first (via TUI /skills menu)
    try:
        import json
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config_data = json.load(f)
                token = config_data.get("skills", {}).get("github", {}).get("api_key")
    except Exception:
        pass
        
    # Fallback to .env
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
        
    if not token:
        raise ValueError("Missing GitHub API Token. Please add it via the /skills menu or set GITHUB_TOKEN in .env")
        
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def _handle_response(resp: requests.Response) -> str:
    """Helper to consistently handle API responses."""
    if resp.status_code >= 400:
        return f"GitHub API Error: {resp.status_code} - {resp.text}"
    try:
        return str(resp.json())
    except:
        return "Success (No JSON returned)"


@tool
def github_act(
    action: str, 
    repo: Optional[str] = None, 
    title: Optional[str] = None, 
    body: Optional[str] = None, 
    issue_number: Optional[int] = None, 
    query: Optional[str] = None,
    branch_name: Optional[str] = None,
    file_path: Optional[str] = None,
    commit_message: Optional[str] = None,
    content: Optional[str] = None,
    head_branch: Optional[str] = None,
    base_branch: Optional[str] = None
) -> str:
    """
    A unified tool for interacting with the GitHub API. 
    
    Actions:
    - 'get_repo': Get repository details. (Requires 'repo' format "owner/name")
    - 'list_issues': List open issues and PRs. (Requires 'repo')
    - 'create_issue': Create a new issue. (Requires 'repo', 'title', 'body')
    - 'list_prs': List open pull requests. (Requires 'repo')
    - 'get_issue_comments': Read comments on an issue/PR. (Requires 'repo', 'issue_number')
    - 'create_comment': Post a comment on an issue/PR. (Requires 'repo', 'issue_number', 'body')
    - 'search_repos': Search repositories globally. (Requires 'query')
    - 'search_code': Search for code terminology within a repo. (Requires 'repo', 'query')
    - 'create_branch': Create a new branch off the default branch. (Requires 'repo', 'branch_name')
    - 'commit_file': Create/Update a file directly on a branch. (Requires 'repo', 'branch_name', 'file_path', 'commit_message', 'content')
    - 'create_pr': Open a Pull Request. (Requires 'repo', 'title', 'head_branch', 'base_branch', 'body')
    """
    try:
        headers = _get_headers()
    except Exception as e:
        return str(e)

    try:
        if action == "get_repo":
            if not repo: return "Error: Missing 'repo' (e.g., 'owner/name')"
            resp = requests.get(f"{GITHUB_API_BASE}/repos/{repo}", headers=headers)
            return _handle_response(resp)

        elif action == "list_issues":
            if not repo: return "Error: Missing 'repo'"
            resp = requests.get(f"{GITHUB_API_BASE}/repos/{repo}/issues?state=open", headers=headers)
            return _handle_response(resp)

        elif action == "create_issue":
            if not repo or not title or not body: return "Error: Missing 'repo', 'title', or 'body'"
            payload = {"title": title, "body": body}
            resp = requests.post(f"{GITHUB_API_BASE}/repos/{repo}/issues", headers=headers, json=payload)
            return _handle_response(resp)

        elif action == "list_prs":
            if not repo: return "Error: Missing 'repo'"
            resp = requests.get(f"{GITHUB_API_BASE}/repos/{repo}/pulls?state=open", headers=headers)
            return _handle_response(resp)

        elif action == "get_issue_comments":
            if not repo or not issue_number: return "Error: Missing 'repo' or 'issue_number'"
            resp = requests.get(f"{GITHUB_API_BASE}/repos/{repo}/issues/{issue_number}/comments", headers=headers)
            return _handle_response(resp)

        elif action == "create_comment":
            if not repo or not issue_number or not body: return "Error: Missing 'repo', 'issue_number', or 'body'"
            payload = {"body": body}
            resp = requests.post(f"{GITHUB_API_BASE}/repos/{repo}/issues/{issue_number}/comments", headers=headers, json=payload)
            return _handle_response(resp)

        elif action == "search_repos":
            if not query: return "Error: Missing 'query'"
            resp = requests.get(f"{GITHUB_API_BASE}/search/repositories?q={query}", headers=headers)
            return _handle_response(resp)

        elif action == "search_code":
            if not repo or not query: return "Error: Missing 'repo' or 'query'"
            resp = requests.get(f"{GITHUB_API_BASE}/search/code?q={query}+repo:{repo}", headers=headers)
            return _handle_response(resp)
            
        elif action == "create_branch":
            if not repo or not branch_name: return "Error: Missing 'repo' or 'branch_name'"
            # Get default branch sha
            repo_data = requests.get(f"{GITHUB_API_BASE}/repos/{repo}", headers=headers).json()
            default_branch = repo_data.get("default_branch", "main")
            ref_data = requests.get(f"{GITHUB_API_BASE}/repos/{repo}/git/refs/heads/{default_branch}", headers=headers).json()
            sha = ref_data.get("object", {}).get("sha")
            if not sha: return "Error: Could not find default branch SHA."
            
            # Create new branch
            payload = {"ref": f"refs/heads/{branch_name}", "sha": sha}
            resp = requests.post(f"{GITHUB_API_BASE}/repos/{repo}/git/refs", headers=headers, json=payload)
            return f"Branch creation response: {_handle_response(resp)}"
            
        elif action == "commit_file":
            if not repo or not branch_name or not file_path or not commit_message or not content:
                return "Error: Missing params for commit_file. Need repo, branch_name, file_path, commit_message, content."
            
            # Get current file SHA (if it exists) to update it, otherwise create new
            import base64
            sha = None
            file_resp = requests.get(f"{GITHUB_API_BASE}/repos/{repo}/contents/{file_path}?ref={branch_name}", headers=headers)
            if file_resp.status_code == 200:
                sha = file_resp.json().get("sha")
                
            payload = {
                "message": commit_message,
                "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
                "branch": branch_name
            }
            if sha:
                payload["sha"] = sha
                
            resp = requests.put(f"{GITHUB_API_BASE}/repos/{repo}/contents/{file_path}", headers=headers, json=payload)
            return f"Commit response: {_handle_response(resp)}"
            
        elif action == "create_pr":
            if not repo or not title or not head_branch or not base_branch or not body:
                return "Error: Missing params. Need repo, title, head_branch, base_branch, body."
            
            payload = {"title": title, "head": head_branch, "base": base_branch, "body": body}
            resp = requests.post(f"{GITHUB_API_BASE}/repos/{repo}/pulls", headers=headers, json=payload)
            return f"Pull Request creation response: {_handle_response(resp)}"

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Tool execution failed: {str(e)}\n{traceback.format_exc()}"
