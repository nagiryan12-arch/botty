# Discord Staff Tracking Bot

## Overview
A Discord bot that tracks staff member activity through messages and moderation actions, automatically posting leaderboards at configurable intervals (weekly/monthly).

## Features
- **Activity Tracking**: Automatically tracks staff messages and moderation actions
- **Point System**: Configurable weights for messages and mod actions
- **Automated Leaderboards**: Posts leaderboards to a designated channel at set intervals
- **Manual Leaderboard**: Use `!leaderboard` command to view current standings
- **Staff Commands**: `!kick` and `!ban` commands that track moderation actions
- **Persistent Storage**: JSON-based data storage that survives bot restarts

## Setup Instructions

### ⚠️ CRITICAL: Enable Privileged Intents First

Before running the bot, you MUST enable privileged intents in the Discord Developer Portal:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (if you haven't already)
3. Go to the "Bot" section
4. Scroll down to **"Privileged Gateway Intents"**
5. Enable ALL three toggles:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
6. Click **"Save Changes"**
7. Copy your bot token (you'll need this for configuration)

**Without these intents enabled, the bot will fail to start with a PrivilegedIntentsRequired error.**

### 2. Invite Bot to Your Server
1. In Discord Developer Portal, go to OAuth2 > URL Generator
2. Select scopes: `bot`
3. Select bot permissions:
   - Read Messages/View Channels
   - Send Messages
   - View Audit Log
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### 3. Configure Settings
The following environment variables have been configured in Secrets:
- `STAFF_ROLE_NAME`: The name of your staff role (default: "Staff")
- `LEADERBOARD_CHANNEL_ID`: Channel ID where leaderboards will be posted
- `MESSAGE_WEIGHT`: Points per message (default: 1)
- `MOD_ACTION_WEIGHT`: Points per moderation action (default: 5)
- `RESET_INTERVAL_DAYS`: Days between leaderboard resets (7 for weekly, 30 for monthly)

To get a channel ID:
1. Enable Developer Mode in Discord (Settings > Advanced > Developer Mode)
2. Right-click the channel and select "Copy ID"

## Commands
- `!leaderboard` - View current staff standings

## Moderation Tracking
The bot automatically tracks kicks and bans from Discord's audit log, so it works with any moderation tool (Dyno, MEE6, built-in Discord moderation, etc.)

## Point Calculation
Total Points = (Messages × MESSAGE_WEIGHT) + (Mod Actions × MOD_ACTION_WEIGHT)

## Troubleshooting

### Bot won't start - "PrivilegedIntentsRequired" error
This means you haven't enabled the required intents in the Discord Developer Portal. Follow the setup instructions above carefully, especially the "Enable Privileged Intents" step.

### Bot is online but not tracking messages
Make sure "Message Content Intent" is enabled in the Developer Portal.

### Leaderboard not posting
Verify the LEADERBOARD_CHANNEL_ID is correct and the bot has permission to send messages in that channel.

## Recent Changes
- 2025-11-06: Initial setup with improved configuration management
- Added manual leaderboard command
- Environment variable-based configuration
- Enhanced error handling and troubleshooting documentation

## Architecture
- `main.py`: Main bot logic and event handlers
- `staff_data.json`: Persistent storage for activity data
- `requirements.txt`: Python dependencies
