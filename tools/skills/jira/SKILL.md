---
name: "Jira Sandbox & Core Integration"
description: "Native integrations with Jira to fetch, create, and transition issues."
---

# 🚀 Jira Skill Module

The Jira module allows Space Black to autonomously manage tickets, answer questions by looking up Jira issues, and interact with epics/tasks directly from the LLM.

## Features
- Search and list issues
- Fetch full ticket details (description, comments, status)
- Add comments to tickets
- Create new tickets
- Transition tickets (e.g., To Do -> In Progress)

## ⚙️ Configuration
The module automatically expects configuration in `config.json` (or via TUI Settings):

```json
"skills": {
    "jira": {
        "enabled": true,
        "domain": "https://your-domain.atlassian.net",
        "email": "your-email@example.com",
        "api_token": "YOUR_JIRA_API_TOKEN"
    }
}
```

Fallback environment variables:
- `JIRA_DOMAIN`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`

## 🛠 Active Tools
- `jira_act`: Single unified tool for all Jira interactions.

## 🧑‍💻 Usage Examples
- *"What's the status of PROJ-123?"*
- *"Create a bug ticket in the APP project with the title 'Login page crash'."*
- *"Find all open issues assigned to me."*
- *"Please add a comment to PROJ-45 saying the DB is fixed."*
