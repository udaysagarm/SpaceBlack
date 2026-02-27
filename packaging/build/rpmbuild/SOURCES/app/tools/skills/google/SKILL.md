# Google Workspace Skill

## Overview
Connects Space Black to Google Workspace via OAuth2, enabling autonomous management of Gmail, Google Drive, Docs, Sheets, and Calendar.

## Setup
1. Create OAuth2 credentials at [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Enable Gmail, Drive, Docs, Sheets, and Calendar APIs
3. Enter your **Client ID** and **Client Secret** in the `/skills` menu
4. Click **Authorize** to complete the one-time browser consent flow

## Tools

### `gmail_act`
| Action | Description | Required Args |
|--------|-------------|---------------|
| `send_email` | Send an email | `to`, `subject`, `body` |
| `read_inbox` | List recent inbox messages | `max_results` |
| `read_email` | Read full email | `message_id` |
| `reply_email` | Reply to a thread | `message_id`, `body` |
| `search_emails` | Search via Gmail query | `query` |
| `list_labels` | List labels | — |
| `delete_email` | Trash email | `message_id` |
| `mark_read` / `mark_unread` | Toggle read state | `message_id` |

### `drive_act`
| Action | Description | Required Args |
|--------|-------------|---------------|
| `list_files` | List Drive files | `folder_id` |
| `search_files` | Search by name | `query` |
| `create_folder` | Create folder | `name` |
| `upload_file` | Upload local file | `local_path`, `name` |
| `download_file` | Download file | `file_id`, `local_path` |
| `move_file` | Move file | `file_id`, `folder_id` |
| `rename_file` | Rename file | `file_id`, `new_name` |
| `delete_file` | Trash file | `file_id` |
| `get_file_info` | File metadata | `file_id` |
| `share_file` | Share with user | `file_id`, `email` |

### `docs_act`
| Action | Description | Required Args |
|--------|-------------|---------------|
| `create_doc` | Create document | `title` |
| `read_doc` | Read full text | `document_id` |
| `append_text` | Append to doc | `document_id`, `text` |
| `insert_text` | Insert at index | `document_id`, `text`, `index` |
| `replace_text` | Find & replace | `document_id`, `find`, `replace` |
| `list_docs` | List documents | — |

### `sheets_act`
| Action | Description | Required Args |
|--------|-------------|---------------|
| `create_sheet` | Create spreadsheet | `title` |
| `read_range` | Read cells | `spreadsheet_id`, `range` |
| `write_range` | Write values | `spreadsheet_id`, `range`, `values` |
| `append_row` | Append row | `spreadsheet_id`, `range`, `values` |
| `list_sheets` | List sheet tabs | `spreadsheet_id` |
| `clear_range` | Clear cells | `spreadsheet_id`, `range` |

### `calendar_act`
| Action | Description | Required Args |
|--------|-------------|---------------|
| `list_events` | Upcoming events | `max_results` |
| `create_event` | Create event | `summary`, `start`, `end` |
| `delete_event` | Delete event | `event_id` |
| `update_event` | Update event | `event_id` + fields |
| `find_conflicts` | Check conflicts | `start`, `end` |
| `invite_participant` | Add attendee | `event_id`, `email` |
| `list_calendars` | List calendars | — |
| `get_event` | Event details | `event_id` |

### `wallet_act`
| Action | Description | Required Args |
|--------|-------------|---------------|
| `get_issuer` | Get issuer details | `issuer_id` |
| `list_classes` | List pass classes | `issuer_id` |
| `get_class` | Get class details | `issuer_id`, `class_suffix` (or `class_id`) |
| `create_class` | Create new pass class | `payload` |
| `get_object` | Get object details | `issuer_id`, `object_suffix` (or `object_id`) |
| `create_object` | Create new pass object | `payload` |
