# 🔮 Obsidian Marketplace Bot

A premium Discord bot designed for marketplace servers, inspired by the DevOutlet style but uniquely crafted for **Obsidian Marketplace**.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AutoMod** | Advanced spam, mention, caps, invite, link, and bad word filtering with progressive punishments |
| 👋 **Welcome System** | Customizable welcome/goodbye messages with auto-role assignment and DM support |
| 🎫 **Ticket System** | Full ticket management with transcripts, support roles, and category organization |
| 🛒 **Marketplace** | Create, view, edit, and rate product listings with purchase integration |
| 💳 **Payments** | Multi-method payment system (PayPal, CashApp, Venmo, Crypto, Robux, Gift Cards) |
| 🛡️ **Anti-Nuke** | Real-time protection against mass channel/role deletion, bans, kicks, and webhook abuse |
| 🔨 **Moderation** | Kick, ban, timeout, warn, purge, slowmode, lock/unlock commands |
| ⚙️ **Utility** | Server info, user info, bot info, rules panel, and more |

## 🚀 Setup

### 1. Prerequisites
- Python 3.10+
- A Discord Bot Token ([Get one here](https://discord.com/developers/applications))

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/obsidian-marketplace-bot.git
cd obsidian-marketplace-bot

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your bot token and owner IDs
```

Your `.env` file should look like:
```env
DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
OWNER_IDS=123456789012345678
```

### 4. Running the Bot

```bash
python bot.py
```

## 📋 Commands

### Moderation
- `/kick <member> [reason]` — Kick a member
- `/ban <member> [reason] [delete_days]` — Ban a member
- `/unban <user_id> [reason]` — Unban a user
- `/timeout <member> <duration> [reason]` — Timeout a member
- `/untimeout <member>` — Remove timeout
- `/warn <member> <reason>` — Warn a member
- `/warnings <member>` — View warnings
- `/clear-warns <member>` — Clear all warnings
- `/purge <amount> [member]` — Delete messages
- `/slowmode <seconds>` — Set slowmode
- `/lock [channel] [reason]` — Lock a channel
- `/unlock [channel]` — Unlock a channel

### Tickets
- `/ticket-panel` — Send ticket creation panel
- `/ticket-config <category> [transcript_channel] [max_per_user]` — Configure tickets
- `/ticket-add-role <role>` — Add support role
- `/ticket-remove-role <role>` — Remove support role
- `/close` — Close current ticket

### Marketplace
- `/listing-create <name> <price> <stock> <description> [category]` — Create a listing
- `/listing-view <listing_id>` — View a listing
- `/listing-list [category]` — List all listings
- `/listing-edit <listing_id> [name] [price] [stock] [description]` — Edit listing
- `/listing-delete <listing_id>` — Delete a listing
- `/listing-rate <listing_id> <rating> [review]` — Rate a listing

### Payments
- `/payment-add <method> <info>` — Add payment method
- `/payment-remove <method>` — Remove payment method
- `/payment-view` — View your payment methods
- `/payment-view-user <user>` — View user's payment methods
- `/payment-request <user> <amount> <reason> [method]` — Request payment
- `/payment-methods-info` — View supported methods

### AutoMod
- `/automod <setting> <value>` — Configure AutoMod
- `/badword <action> <word>` — Manage bad words
- `/automod-stats` — View AutoMod stats

### Anti-Nuke
- `/antinuke-config <setting> <value>` — Configure anti-nuke
- `/antinuke-whitelist <role>` — Toggle role whitelist
- `/antinuke-status` — View anti-nuke status

### Welcome
- `/welcome-config <channel> [message] [auto_role] [dm_message] [goodbye_channel] [goodbye_message]` — Configure welcome
- `/welcome-test` — Test welcome message
- `/welcome-toggle` — Toggle welcome system

### Utility
- `/help` — Show all commands
- `/ping` — Check bot latency
- `/server-info` — Show server info
- `/user-info [member]` — Show user info
- `/bot-info` — Show bot info
- `/rules` — Display server rules
- `/info-panel` — Send info panel
- `/set-logs <channel>` — Set logs channel
- `/avatar [member]` — Get avatar
- `/member-count` — Show member count

## 🎨 Customization

### Colors
Edit `utils/config.py` to change the Obsidian color theme:
```python
PRIMARY_COLOR = 0x2D1B4E      # Deep purple
SUCCESS_COLOR = 0x00D9A5       # Teal green
ERROR_COLOR = 0xFF4757         # Red
```

### Welcome Message
Use these placeholders in welcome messages:
- `{user}` — User mention
- `{server}` — Server name
- `{count}` — Member count
- `{username}` — Username

## 🛡️ Anti-Nuke Protection

The bot monitors these actions in real-time:
- Mass channel deletion (default: 3+ in 10s)
- Mass channel creation (default: 3+ in 10s)
- Mass role deletion (default: 3+ in 10s)
- Mass role creation (default: 3+ in 10s)
- Mass banning (default: 3+ in 10s)
- Mass kicking (default: 5+ in 10s)
- Mass webhook creation (default: 2+ in 10s)

Punishment options: `ban`, `kick`, `strip` (removes all roles + 24h timeout)

## 📁 Project Structure

```
obsidian-marketplace-bot/
├── bot.py                 # Main bot file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── cogs/
│   ├── automod.py        # AutoMod system
│   ├── welcome.py        # Welcome/Goodbye system
│   ├── tickets.py        # Ticket system
│   ├── stocks.py         # Marketplace listings
│   ├── payments.py       # Payment methods
│   ├── antinuke.py       # Anti-nuke protection
│   ├── moderation.py      # Mod commands
│   ├── utility.py         # Utility commands
│   └── owner.py           # Owner commands
├── utils/
│   ├── config.py          # Bot configuration
│   ├── database.py        # JSON database handler
│   └── embeds.py          # Embed builder
└── data/                  # Server data storage
```

## 🔒 Permissions

The bot requires these permissions:
- Manage Channels
- Manage Roles
- Manage Messages
- Manage Webhooks
- Kick Members
- Ban Members
- Moderate Members
- Read Messages/View Channels
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Use External Emojis
- Add Reactions

## 📜 License

This project is open source. Feel free to modify and distribute.

## 💜 Credits

Made for **Obsidian Marketplace**

Inspired by DevOutlet's clean marketplace design.
