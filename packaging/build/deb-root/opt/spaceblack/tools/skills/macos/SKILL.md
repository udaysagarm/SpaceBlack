# macOS Native Control Skill

## Overview
Allows Space Black to control macOS natively via AppleScript. Only available on macOS (Darwin).

## No Setup Required
This skill is auto-detected on macOS. Enable it via the `/skills` menu.

## Tool: `macos_act`

### Apple Mail
| Action | Description |
|--------|-------------|
| `mail_send` | Send email (`to`, `subject`, `body`) |
| `mail_read_inbox` | List inbox messages |
| `mail_read_message` | Read message by index |
| `mail_reply` | Reply to message |
| `mail_search` | Search mailbox |

### Apple Calendar
| Action | Description |
|--------|-------------|
| `cal_list_events` | Today's events |
| `cal_create_event` | Create event |
| `cal_delete_event` | Delete event |
| `cal_list_calendars` | List calendars |

### Finder / Files
| Action | Description |
|--------|-------------|
| `finder_list` | List directory |
| `finder_move` | Move file |
| `finder_copy` | Copy file |
| `finder_delete` | Trash file |
| `finder_create_folder` | New folder |
| `finder_open` | Open with default app |
| `finder_get_info` | File metadata |

### Apple Notes
| Action | Description |
|--------|-------------|
| `notes_list` | List notes |
| `notes_create` | Create note |
| `notes_read` | Read note |
| `notes_delete` | Delete note |
| `notes_search` | Search notes |

### Apple Reminders
| Action | Description |
|--------|-------------|
| `reminders_list` | List reminders |
| `reminders_create` | Create reminder |
| `reminders_complete` | Mark done |
| `reminders_delete` | Delete reminder |

### System Control
| Action | Description |
|--------|-------------|
| `system_volume` | Get/set volume |
| `system_brightness` | Get brightness |
| `system_screenshot` | Take screenshot |
| `system_notify` | Show notification |
| `system_open_app` | Launch app |
| `system_quit_app` | Quit app |
| `system_list_apps` | Running apps |
| `system_clipboard_get` | Get clipboard |
| `system_clipboard_set` | Set clipboard |
