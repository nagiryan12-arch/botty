# Discord Staff Tracking Bot 🏆

A Discord bot that automatically tracks staff member activity through messages and moderation actions, with automated leaderboard posting.

## Quick Start Guide

### Step 1: Enable Required Intents in Discord Developer Portal

⚠️ **IMPORTANT**: Before the bot can run, you must enable privileged intents:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Click on the **"Bot"** section in the left sidebar
4. Scroll down to **"Privileged Gateway Intents"**
5. Enable these three toggles:
   - ✅ **Presence Intent**
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent**
6. Click **"Save Changes"**

### Step 2: Invite Bot to Your Server

1. In Discord Developer Portal, go to **OAuth2 > URL Generator**
2. Select scopes: **`bot`**
3. Select bot permissions:
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ View Audit Log (required to track moderation actions)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### Step 3: Get Your Channel ID

1. Enable Developer Mode in Discord:
   - Settings → Advanced → Developer Mode (toggle ON)
2. Right-click the channel where you want leaderboards posted
3. Click **"Copy ID"**
4. Use this as your LEADERBOARD_CHANNEL_ID

### Step 4: Configure the Bot

The bot is already configured with your secrets! Just make sure you've set:
- ✅ DISCORD_TOKEN
- ✅ STAFF_ROLE_NAME
- ✅ LEADERBOARD_CHANNEL_ID
- ✅ MESSAGE_WEIGHT (points per message)
- ✅ MOD_ACTION_WEIGHT (points per mod action)
- ✅ RESET_INTERVAL_DAYS (7 for weekly, 30 for monthly)

### Step 5: Start the Bot

Once you've enabled the intents in the Developer Portal, just click the **Run** button or restart the workflow!

## Features

### Automatic Tracking
- 📝 Tracks every message sent by staff members
- ⚖️ Tracks moderation actions (kicks, bans)
- 💾 Persistent storage survives bot restarts

### Commands
- `!leaderboard` - View current staff rankings anytime

### Moderation Tracking
The bot automatically tracks kicks and bans performed by staff members through **any** moderation tool:
- ✅ Works with Dyno
- ✅ Works with MEE6
- ✅ Works with Discord's built-in moderation
- ✅ Works with any bot or manual moderation

The bot reads Discord's audit log to detect when staff members perform moderation actions.

### Automated Leaderboards
- 📊 Automatically posts leaderboards at configured intervals
- 🔄 Resets data after each period
- 🏅 Shows rankings with detailed stats

### Point System
**Total Points = (Messages × MESSAGE_WEIGHT) + (Mod Actions × MOD_ACTION_WEIGHT)**

Example with defaults (MESSAGE_WEIGHT=1, MOD_ACTION_WEIGHT=5):
- 50 messages + 3 mod actions = 50 + 15 = **65 points**

## Troubleshooting

### Bot won't start / "PrivilegedIntentsRequired" error
➡️ You need to enable the three privileged intents in the Discord Developer Portal (see Step 1 above)

### Bot is online but not tracking messages
➡️ Make sure "Message Content Intent" is enabled in the Developer Portal

### Leaderboard not posting
➡️ Verify the LEADERBOARD_CHANNEL_ID is correct and the bot has permission to send messages in that channel

### "Missing Permissions" errors
➡️ Make sure the bot role is positioned above the roles it needs to manage, and has the required permissions

## Data Storage

Staff activity data is stored in `staff_data.json` which persists between bot restarts. The file is automatically created and updated.

## Need Help?

Check the full documentation in `replit.md` for more details!
