---
name: GitHub Skill
description: Autonomous GitHub interaction handling repositories, issues, code search, and direct file commits over the API.
---

# GitHub Skill

This skill provides the agent structural access to the GitHub API, allowing you to interface completely with repositories, issues, PRs, and the Git Database without needing to physically `git clone` projects to the local system.

## The Single Tool: `github_act`

All operations route through the `github_act` tool using the `action` parameter. 

> **Important**: All API queries require the `GITHUB_TOKEN` environment variable to be loaded in the `.env` file. You will get an authentication error if it is missing.

### Basic Actions (Issues & Repos)

| Action | Description | Required params |
|--------|-------------|-----------------|
| `get_repo` | Get repository details | `repo` ("owner/name") |
| `list_issues` | List open issues and PRs | `repo` |
| `create_issue` | Create an issue | `repo`, `title`, `body` |
| `list_prs` | List open PRs | `repo` |
| `get_issue_comments` | Read issue/PR comments | `repo`, `issue_number` |
| `create_comment` | Post a comment | `repo`, `issue_number`, `body` |
| `search_repos` | Find repositories | `query` ("react in:name") |
| `search_code` | Find code inside a repo | `repo`, `query` |

### Git Database Actions (Commits without Cloning)

The API allows us to write directly to repositories and submit PRs autonomously.

| Action | Description | Required params |
|--------|-------------|-----------------|
| `create_branch` | Create a new branch off default branch | `repo`, `branch_name` |
| `commit_file` | Create/edit a file and commit directly | `repo`, `branch_name`, `file_path`, `commit_message`, `content` |
| `create_pr` | Open a Pull Request from a branch | `repo`, `title`, `head_branch`, `base_branch`, `body` |

### Example Workflow: Fixing a bug

1. Search for the issue: `github_act(action="list_issues", repo="john/cool-app")`
2. Search code for context: `github_act(action="search_code", repo="john/cool-app", query="IndexOutOfBounds")`
3. Create a branch: `github_act(action="create_branch", repo="john/cool-app", branch_name="fix-bounds-bug")`
4. Commit the fix: `github_act(action="commit_file", repo="john/cool-app", branch_name="fix-bounds-bug", file_path="src/main.py", commit_message="Fix index out of bounds", content="<new file content>")`
5. Open PR: `github_act(action="create_pr", repo="john/cool-app", title="Fix bounds bug", head_branch="fix-bounds-bug", base_branch="main", body="Resolves #24")`
