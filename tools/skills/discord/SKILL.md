---
name: Discord Skill
description: Autonomous Discord server management and messaging via Bot Token.
---

# Discord Skill

This skill grants the agent the ability to interact with Discord servers through the Discord REST API (v10).

## Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create a new Application → go to **Bot** → copy the **Bot Token**.
3. Under **OAuth2 → URL Generator**, select `bot` scope and grant permissions: `Send Messages`, `Read Message History`, `Manage Channels`, `Add Reactions`, `Manage Threads`.
4. Use the generated URL to invite the bot to your server.
5. In Space Black, press `Cmd+S` → paste the Bot Token into the Discord section.

## The Single Tool: `discord_act`

All operations route through `discord_act` using the `action` parameter.

### Messaging
| Action | Description | Required params |
|--------|-------------|-----------------|
| `send_message` | Send a message to a channel | `channel_id`, `content` |
| `get_messages` | Fetch recent messages (last 25) | `channel_id` |
| `add_reaction` | React with an emoji | `channel_id`, `message_id`, `emoji` |
| `delete_message` | Delete a message | `channel_id`, `message_id` |

### Channels & Threads
| Action | Description | Required params |
|--------|-------------|-----------------|
| `list_channels` | List all channels in a server | `guild_id` |
| `create_channel` | Create a new text channel | `guild_id`, `name` |
| `create_thread` | Start a thread from a message | `channel_id`, `message_id`, `name` |

### Server Info
| Action | Description | Required params |
|--------|-------------|-----------------|
| `list_guilds` | List servers the bot is in | — |
| `get_guild` | Get server details | `guild_id` |
| `list_members` | List members in a server | `guild_id` |

### Direct Messages
| Action | Description | Required params |
|--------|-------------|-----------------|
| `send_dm` | Send a DM to a user | `user_id`, `content` |

### Example: Sending a Message

```
discord_act(action="list_guilds")  → find the guild_id
discord_act(action="list_channels", guild_id="123456")  → find the channel_id
discord_act(action="send_message", channel_id="789012", content="Hello from Space Black!")
```
