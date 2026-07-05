"""
╔═══════════════════════════════════════════════════════════════════════╗
║                    OBSIDIAN MARKETPLACE BOT                             ║
║              A premium Discord marketplace management bot               ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import asyncio
import json
import os
import logging
import re
import socket
from datetime import datetime, timedelta
from typing import Optional, List
from threading import Thread
from collections import defaultdict, deque

# ===== KEEP ALIVE FOR RENDER =====
def run_keep_alive():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", 10000))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nObsidian Bot Online")
            conn.close()
    except:
        pass

Thread(target=run_keep_alive, daemon=True).start()
# ===== END KEEP ALIVE =====

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ObsidianBot")

# ===== CONFIG =====
import os as _os
from dotenv import load_dotenv
load_dotenv()

class Config:
    TOKEN = _os.getenv("DISCORD_TOKEN")
    PREFIX = "o!"
    OWNER_IDS = [int(x) for x in _os.getenv("OWNER_IDS", "0").split(",") if x]
    PRIMARY_COLOR = 0x2D1B4E
    SUCCESS_COLOR = 0x00D9A5
    ERROR_COLOR = 0xFF4757
    WARNING_COLOR = 0xFFA502
    INFO_COLOR = 0x70A1FF
    GOLD_COLOR = 0xFFD700

# ===== DATABASE =====
import aiofiles

class Database:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        _os.makedirs(data_dir, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_path(self, guild_id, name):
        guild_dir = _os.path.join(self.data_dir, str(guild_id))
        _os.makedirs(guild_dir, exist_ok=True)
        return _os.path.join(guild_dir, f"{name}.json")

    async def _read(self, path):
        if not _os.path.exists(path):
            return {}
        try:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except:
            return {}

    async def _write(self, path, data):
        async with self._lock:
            async with aiofiles.open(path, "w") as f:
                await f.write(json.dumps(data, indent=2))

    async def get(self, guild_id, key, default=None):
        path = self._get_path(guild_id, "config")
        data = await self._read(path)
        return data.get(key, default)

    async def set(self, guild_id, key, value):
        path = self._get_path(guild_id, "config")
        data = await self._read(path)
        data[key] = value
        await self._write(path, data)

    async def get_automod(self, guild_id):
        return await self.get(guild_id, "automod", {})

    async def get_antinuke(self, guild_id):
        return await self.get(guild_id, "antinuke", {})

    async def get_welcome(self, guild_id):
        return await self.get(guild_id, "welcome", {})

    async def get_tickets(self, guild_id):
        return await self.get(guild_id, "tickets", {})

    async def get_payments(self, guild_id):
        return await self.get(guild_id, "payments", {})

    async def init_guild(self, guild_id):
        path = self._get_path(guild_id, "config")
        if not _os.path.exists(path):
            default = {
                "automod": {
                    "enabled": True, "max_mentions": 5, "max_caps_percent": 70,
                    "spam_threshold": 5, "spam_interval": 5,
                    "invite_filter": True, "link_filter": False,
                    "bad_words": ["nigger", "nigga", "faggot", "retard", "kys", "kill yourself"]
                },
                "antinuke": {
                    "enabled": True, "channel_delete_limit": 3, "channel_create_limit": 3,
                    "role_delete_limit": 3, "role_create_limit": 3, "ban_limit": 3,
                    "kick_limit": 5, "webhook_limit": 2, "time_window": 10, "punishment": "ban"
                },
                "welcome": {"enabled": True, "message": "Welcome {user} to **{server}**! You are member **#{count}**.", "dm_message": "Thanks for joining {server}! Read the rules.", "auto_role": None},
                "tickets": {"category": None, "transcript_channel": None, "support_roles": [], "max_tickets_per_user": 3},
                "payments": {}, "logs_channel": None, "mod_role": None, "admin_role": None
            }
            await self._write(path, default)

    async def add_warn(self, guild_id, user_id, reason, moderator_id):
        path = self._get_path(guild_id, "warnings")
        data = await self._read(path)
        user_warns = data.get(str(user_id), [])
        user_warns.append({"reason": reason, "moderator": moderator_id, "timestamp": str(datetime.utcnow())})
        data[str(user_id)] = user_warns
        await self._write(path, data)
        return len(user_warns)

    async def get_warns(self, guild_id, user_id):
        path = self._get_path(guild_id, "warnings")
        data = await self._read(path)
        return data.get(str(user_id), [])

    async def clear_warns(self, guild_id, user_id):
        path = self._get_path(guild_id, "warnings")
        data = await self._read(path)
        data.pop(str(user_id), None)
        await self._write(path, data)

# ===== EMBEDS =====
class ObsidianEmbeds:
    def __init__(self):
        self.footer = "Obsidian Marketplace"
        self.icon_url = None

    def _base(self, title=None, description=None, color=Config.PRIMARY_COLOR):
        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
        embed.set_footer(text=self.footer, icon_url=self.icon_url)
        return embed

    def success(self, title, description=None):
        return self._base(f"OK {title}", description, Config.SUCCESS_COLOR)
    def error(self, title, description=None):
        return self._base(f"ERROR {title}", description, Config.ERROR_COLOR)
    def warning(self, title, description=None):
        return self._base(f"WARN {title}", description, Config.WARNING_COLOR)
    def info(self, title, description=None):
        return self._base(f"INFO {title}", description, Config.INFO_COLOR)
    def shield(self, title, description=None):
        return self._base(f"SHIELD {title}", description, Config.PRIMARY_COLOR)
    def ticket(self, title, description=None):
        return self._base(f"TICKET {title}", description, Config.INFO_COLOR)
    def payment(self, title, description=None):
        return self._base(f"PAYMENT {title}", description, Config.SUCCESS_COLOR)
    def automod(self, title, description=None):
        return self._base(f"AUTOMOD {title}", description, Config.WARNING_COLOR)

    def welcome_card(self, member, guild, message, count):
        embed = discord.Embed(
            title=f"Welcome to {guild.name}",
            description=message.format(user=member.mention, server=guild.name, count=count, username=member.name),
            color=Config.PRIMARY_COLOR, timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{count} | {self.footer}", icon_url=self.icon_url)
        return embed

    def stock_listing(self, name, price, description, seller, stock):
        embed = discord.Embed(title=f"LISTING {name}", description=description, color=Config.GOLD_COLOR, timestamp=datetime.utcnow())
        embed.add_field(name="Price", value=f"${price:.2f}", inline=True)
        embed.add_field(name="Stock", value=f"{stock} available", inline=True)
        embed.add_field(name="Seller", value=seller, inline=True)
        embed.set_footer(text=self.footer, icon_url=self.icon_url)
        return embed

    def antinuke_alert(self, action, target, reason):
        embed = discord.Embed(
            title="ANTI-NUKE TRIGGERED",
            description=f"**Action:** {action}\n**Target:** {target}\n**Reason:** {reason}",
            color=Config.ERROR_COLOR, timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Obsidian Security System", icon_url=self.icon_url)
        return embed

# ===== MAIN BOT =====
class ObsidianBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.members = True
        intents.message_content = True
        intents.presences = True
        super().__init__(command_prefix=Config.PREFIX, intents=intents, help_command=None, case_insensitive=True, owner_ids=set(Config.OWNER_IDS))
        self.db = Database()
        self.embeds = ObsidianEmbeds()
        self.start_time = datetime.utcnow()

    async def setup_hook(self):
        for cog_name, cog_class in [
            ("AutoMod", AutoMod), ("Welcome", Welcome), ("Tickets", Tickets),
            ("Stocks", Stocks), ("Payments", Payments), ("AntiNuke", AntiNuke),
            ("Moderation", Moderation), ("Utility", Utility), ("Owner", Owner)
        ]:
            try:
                await self.add_cog(cog_class(self))
                logger.info(f"Loaded {cog_name}")
            except Exception as e:
                logger.error(f"Failed {cog_name}: {e}")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
        self.status_rotation.start()

    @tasks.loop(minutes=5)
    async def status_rotation(self):
        import random
        statuses = [
            discord.Activity(type=discord.ActivityType.watching, name="over Obsidian Marketplace"),
            discord.Activity(type=discord.ActivityType.listening, name="/help for commands"),
            discord.Activity(type=discord.ActivityType.playing, name="securing your server"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"),
            discord.Activity(type=discord.ActivityType.competing, name="marketplace deals")
        ]
        await self.change_presence(activity=random.choice(statuses))

    @status_rotation.before_loop
    async def before_status(self):
        await self.wait_until_ready()

    async def on_ready(self):
        logger.info("=" * 60)
        logger.info("OBSIDIAN MARKETPLACE BOT ONLINE")
        logger.info(f"Bot: {self.user} ({self.user.id})")
        logger.info(f"Guilds: {len(self.guilds)}")
        logger.info(f"Users: {sum(g.member_count for g in self.guilds)}")
        logger.info("=" * 60)

    async def on_guild_join(self, guild):
        logger.info(f"Joined: {guild.name}")
        await self.db.init_guild(guild.id)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            embed = self.embeds.error("Missing Permissions", "You don't have permission.")
        elif isinstance(error, commands.BotMissingPermissions):
            embed = self.embeds.error("Bot Missing Permissions", f"I need: {', '.join(error.missing_permissions)}")
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = self.embeds.error("Missing Argument", f"Usage: `{ctx.command.signature}`")
        elif isinstance(error, commands.CheckFailure):
            embed = self.embeds.error("Access Denied", "You cannot use this command.")
        else:
            embed = self.embeds.error("Error", f"```{str(error)}```")
        await ctx.send(embed=embed, delete_after=10)

# ===== AUTOMOD COG =====
class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds
        self.message_cache = defaultdict(lambda: deque(maxlen=10))
        self.violation_cache = defaultdict(int)
        self.invite_pattern = re.compile(r"discord\.(gg|com/invite)/[a-zA-Z0-9-]+")

    async def log_action(self, guild, embed):
        logs_id = await self.db.get(guild.id, "logs_channel")
        if logs_id:
            ch = guild.get_channel(logs_id)
            if ch: await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        if message.author.guild_permissions.administrator: return
        config = await self.db.get_automod(message.guild.id)
        if not config.get("enabled", True): return
        violations = []
        if await self._check_spam(message, config): violations.append("Spam")
        if await self._check_mentions(message, config): violations.append("Mass mentions")
        if await self._check_caps(message, config): violations.append("Excessive caps")
        if await self._check_bad_words(message, config): violations.append("Bad words")
        if config.get("invite_filter", True) and self.invite_pattern.search(message.content): violations.append("Invite link")
        if violations: await self._handle_violations(message, violations)

    async def _check_spam(self, message, config):
        self.message_cache[message.author.id].append({"content": message.content, "time": datetime.utcnow()})
        recent = [m for m in self.message_cache[message.author.id] if (datetime.utcnow() - m["time"]).total_seconds() <= config.get("spam_interval", 5)]
        return len(recent) >= config.get("spam_threshold", 5) and len(set(m["content"] for m in recent)) <= 2

    async def _check_mentions(self, message, config):
        return (len(message.mentions) + len(message.role_mentions)) > config.get("max_mentions", 5)

    async def _check_caps(self, message, config):
        if len(message.content) < 10: return False
        return (sum(1 for c in message.content if c.isupper()) / len(message.content)) * 100 > config.get("max_caps_percent", 70)

    async def _check_bad_words(self, message, config):
        return any(word in message.content.lower() for word in config.get("bad_words", []))

    async def _handle_violations(self, message, violations):
        self.violation_cache[message.author.id] += 1
        count = self.violation_cache[message.author.id]
        try: await message.delete()
        except: pass
        embed = self.embeds.automod("AutoMod Alert", f"{message.author.mention}, message removed.\n**Violations:**\n" + "\n".join(f"- {v}" for v in violations) + f"\n**Strike:** `{count}/5`")
        await message.channel.send(embed=embed, delete_after=10)
        if count >= 5:
            try: await message.author.ban(reason="AutoMod: 5+ violations")
            except: pass
        elif count >= 3:
            try: await message.author.timeout(timedelta(minutes=30), reason="AutoMod: 3+ violations")
            except: pass

    @app_commands.command(name="automod", description="Configure AutoMod")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_config(self, interaction: discord.Interaction, setting: str, value: str):
        valid = ["enabled", "max_mentions", "max_caps_percent", "spam_threshold", "spam_interval", "invite_filter", "link_filter"]
        if setting not in valid: return await interaction.response.send_message(embed=self.embeds.error("Invalid", f"Valid: {', '.join(valid)}"), ephemeral=True)
        config = await self.db.get_automod(interaction.guild_id)
        config[setting] = value.lower() in ["true", "yes", "1", "on"] if setting in ["enabled", "invite_filter", "link_filter"] else int(value)
        await self.db.set(interaction.guild_id, "automod", config)
        await interaction.response.send_message(embed=self.embeds.success("Updated", f"`{setting}` = `{config[setting]}`"), ephemeral=True)

    @app_commands.command(name="badword", description="Manage bad words")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def badword(self, interaction: discord.Interaction, action: str, word: str):
        config = await self.db.get_automod(interaction.guild_id)
        words = config.get("bad_words", [])
        if action.lower() == "add" and word.lower() not in words: words.append(word.lower())
        elif action.lower() == "remove" and word.lower() in words: words.remove(word.lower())
        config["bad_words"] = words
        await self.db.set(interaction.guild_id, "automod", config)
        await interaction.response.send_message(embed=self.embeds.success("Done", f"`{word}` {action}ed"), ephemeral=True)

    @app_commands.command(name="automod-stats", description="View AutoMod stats")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_stats(self, interaction: discord.Interaction):
        config = await self.db.get_automod(interaction.guild_id)
        embed = self.embeds.info("AutoMod Configuration", "Current settings:")
        for k, v in config.items():
            embed.add_field(name=k, value=str(v), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== WELCOME COG =====
class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot: return
        config = await self.db.get_welcome(member.guild.id)
        if not config.get("enabled", True): return
        ch_id = config.get("channel")
        ch = member.guild.get_channel(ch_id) if ch_id else (discord.utils.get(member.guild.text_channels, name="welcome") or discord.utils.get(member.guild.text_channels, name="general"))
        if not ch: return
        embed = self.embeds.welcome_card(member, member.guild, config.get("message", "Welcome {user} to **{server}**! You are member **#{count}**."), member.guild.member_count)
        try: await ch.send(embed=embed)
        except: pass
        dm = config.get("dm_message")
        if dm:
            try: await member.send(embed=discord.Embed(title=f"Welcome to {member.guild.name}!", description=dm.format(user=member.mention, server=member.guild.name, count=member.guild.member_count, username=member.name), color=Config.PRIMARY_COLOR))
            except: pass
        role_id = config.get("auto_role")
        if role_id:
            try: await member.add_roles(member.guild.get_role(role_id), reason="Auto-role")
            except: pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot: return
        config = await self.db.get_welcome(member.guild.id)
        ch_id = config.get("goodbye_channel") or config.get("channel")
        if not ch_id: return
        ch = member.guild.get_channel(ch_id)
        if ch:
            try: await ch.send(embed=discord.Embed(description=config.get("goodbye_message", "Goodbye {user}.").format(user=member.mention, username=member.name, server=member.guild.name), color=Config.ERROR_COLOR))
            except: pass

    @app_commands.command(name="welcome-config", description="Configure welcome")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_config(self, interaction: discord.Interaction, channel: discord.TextChannel, message: Optional[str] = None, auto_role: Optional[discord.Role] = None, dm_message: Optional[str] = None):
        config = await self.db.get_welcome(interaction.guild_id)
        config.update({"enabled": True, "channel": channel.id})
        if message: config["message"] = message
        if auto_role: config["auto_role"] = auto_role.id
        if dm_message: config["dm_message"] = dm_message
        await self.db.set(interaction.guild_id, "welcome", config)
        await interaction.response.send_message(embed=self.embeds.success("Welcome Configured", f"Channel: {channel.mention}"), ephemeral=True)

    @app_commands.command(name="welcome-test", description="Test welcome")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_test(self, interaction: discord.Interaction):
        config = await self.db.get_welcome(interaction.guild_id)
        embed = self.embeds.welcome_card(interaction.user, interaction.guild, config.get("message", "Welcome {user}!"), interaction.guild.member_count)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="welcome-toggle", description="Toggle welcome")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_toggle(self, interaction: discord.Interaction):
        config = await self.db.get_welcome(interaction.guild_id)
        config["enabled"] = not config.get("enabled", True)
        await self.db.set(interaction.guild_id, "welcome", config)
        await interaction.response.send_message(embed=self.embeds.success("Welcome", f"Now **{'enabled' if config['enabled'] else 'disabled'}**"), ephemeral=True)

# ===== TICKETS COG =====
class TicketCloseView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="❌", custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message("Not a ticket!", ephemeral=True)
        await interaction.response.send_message("Closing...")
        await asyncio.sleep(2)
        await interaction.channel.delete(reason=f"Closed by {interaction.user}")

class TicketModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Create Support Ticket")
        self.bot = bot
        self.reason = TextInput(label="Reason", placeholder="Why do you need support?", style=discord.TextStyle.paragraph, max_length=500, required=True)
        self.category = TextInput(label="Category", placeholder="General, Purchase, Report...", max_length=50, required=True)
        self.add_item(self.reason)
        self.add_item(self.category)

    async def on_submit(self, interaction: discord.Interaction):
        config = await self.bot.db.get_tickets(interaction.guild_id)
        category = interaction.guild.get_channel(config.get("category")) if config.get("category") else None
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        for role_id in config.get("support_roles", []):
            role = interaction.guild.get_role(role_id)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.id}", category=category, overwrites=overwrites)
        embed = discord.Embed(title=f"TICKET {self.category.value}", description=f"**User:** {interaction.user.mention}\n**Reason:** {self.reason.value}", color=Config.INFO_COLOR, timestamp=datetime.utcnow())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        msg = await channel.send(content=interaction.user.mention, embed=embed, view=TicketCloseView(self.bot))
        await msg.pin()
        await interaction.response.send_message(embed=discord.Embed(title="Ticket Created", description=f"Your ticket: {channel.mention}", color=Config.SUCCESS_COLOR), ephemeral=True)

class TicketCreateView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="✅", custom_id="create_ticket")
    async def create_button(self, interaction: discord.Interaction, button: Button):
        config = await self.bot.db.get_tickets(interaction.guild_id)
        max_tickets = config.get("max_tickets_per_user", 3)
        user_tickets = [c for c in interaction.guild.text_channels if c.name == f"ticket-{interaction.user.id}"]
        if len(user_tickets) >= max_tickets:
            return await interaction.response.send_message(embed=discord.Embed(title="Limit Reached", description=f"Max {max_tickets} tickets", color=Config.ERROR_COLOR), ephemeral=True)
        await interaction.response.send_modal(TicketModal(self.bot))

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds

    @app_commands.command(name="ticket-panel", description="Send ticket panel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Obsidian Support", description="Need help? Click below to create a ticket.\n- Purchase issues\n- Product questions\n- Report a user\n- Partnership inquiries\n- General support", color=Config.PRIMARY_COLOR)
        await interaction.channel.send(embed=embed, view=TicketCreateView(self.bot))
        await interaction.response.send_message(embed=self.embeds.success("Panel Sent", "Ticket panel posted."), ephemeral=True)

    @app_commands.command(name="ticket-config", description="Configure tickets")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_config(self, interaction: discord.Interaction, category: discord.CategoryChannel, transcript_channel: Optional[discord.TextChannel] = None, max_per_user: Optional[int] = 3):
        config = await self.db.get_tickets(interaction.guild_id)
        config.update({"category": category.id, "max_tickets_per_user": max_per_user})
        if transcript_channel: config["transcript_channel"] = transcript_channel.id
        await self.db.set(interaction.guild_id, "tickets", config)
        await interaction.response.send_message(embed=self.embeds.success("Configured", f"Category: {category.mention}\nMax tickets: {max_per_user}"), ephemeral=True)

    @app_commands.command(name="close", description="Close ticket")
    async def close_ticket(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message(embed=self.embeds.error("Not a ticket", "Use this in a ticket channel."), ephemeral=True)
        await interaction.response.send_message("Closing ticket...")
        await asyncio.sleep(2)
        await interaction.channel.delete()

# ===== STOCKS COG =====
class Stocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds

    async def _next_id(self, guild_id):
        listings = await self.db.get(guild_id, "listings", [])
        return max((l["id"] for l in listings), default=0) + 1

    async def _save_listing(self, guild_id, listing):
        listings = await self.db.get(guild_id, "listings", [])
        for i, l in enumerate(listings):
            if l["id"] == listing["id"]:
                listings[i] = listing; break
        else:
            listings.append(listing)
        await self.db.set(guild_id, "listings", listings)

    @app_commands.command(name="listing-create", description="Create a listing")
    async def listing_create(self, interaction: discord.Interaction, name: str, price: float, stock: int, description: str, category: Optional[str] = "General"):
        listing = {"id": await self._next_id(interaction.guild_id), "name": name, "description": description, "price": price, "stock": stock, "seller_id": interaction.user.id, "category": category, "created_at": str(datetime.utcnow()), "sold": 0, "rating": []}
        await self._save_listing(interaction.guild_id, listing)
        embed = self.embeds.stock_listing(name, price, description, interaction.user.mention, stock)
        embed.add_field(name="ID", value=f"#{listing['id']}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="listing-view", description="View a listing")
    async def listing_view(self, interaction: discord.Interaction, listing_id: int):
        listings = await self.db.get(interaction.guild_id, "listings", [])
        listing = next((l for l in listings if l["id"] == listing_id), None)
        if not listing:
            return await interaction.response.send_message(embed=self.embeds.error("Not Found", f"Listing #{listing_id} doesn't exist."), ephemeral=True)
        seller = interaction.guild.get_member(listing["seller_id"])
        embed = self.embeds.stock_listing(listing["name"], listing["price"], listing["description"], seller.mention if seller else "Unknown", listing["stock"])
        embed.add_field(name="Sold", value=str(listing["sold"]), inline=True)
        if listing["rating"]:
            avg = sum(listing["rating"]) / len(listing["rating"])
            embed.add_field(name="Rating", value=f"{avg:.1f}/5", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="listing-list", description="List all listings")
    async def listing_list(self, interaction: discord.Interaction, category: Optional[str] = None):
        listings = await self.db.get(interaction.guild_id, "listings", [])
        if category: listings = [l for l in listings if l["category"].lower() == category.lower()]
        if not listings:
            return await interaction.response.send_message(embed=self.embeds.info("No Listings", "No listings found."), ephemeral=True)
        embed = discord.Embed(title="Marketplace Listings", description=f"Total: {len(listings)}", color=Config.GOLD_COLOR)
        for l in listings[:25]:
            seller = interaction.guild.get_member(l["seller_id"])
            embed.add_field(name=f"#{l['id']} - {l['name']}", value=f"${l['price']:.2f} | Stock: {l['stock']} | Seller: {seller.name if seller else 'Unknown'}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="listing-delete", description="Delete your listing")
    async def listing_delete(self, interaction: discord.Interaction, listing_id: int):
        listings = await self.db.get(interaction.guild_id, "listings", [])
        listing = next((l for l in listings if l["id"] == listing_id), None)
        if not listing or listing["seller_id"] != interaction.user.id:
            return await interaction.response.send_message(embed=self.embeds.error("Denied", "Not your listing or doesn't exist."), ephemeral=True)
        await self.db.set(interaction.guild_id, "listings", [l for l in listings if l["id"] != listing_id])
        await interaction.response.send_message(embed=self.embeds.success("Deleted", f"Listing #{listing_id} removed."), ephemeral=True)

# ===== PAYMENTS COG =====
class Payments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds

    async def _get_methods(self, guild_id, user_id):
        payments = await self.db.get(guild_id, "payments", {})
        return payments.get(str(user_id), {})

    @app_commands.command(name="payment-add", description="Add payment method")
    async def payment_add(self, interaction: discord.Interaction, method: str, info: str):
        payments = await self.db.get(interaction.guild_id, "payments", {})
        if str(interaction.user.id) not in payments:
            payments[str(interaction.user.id)] = {}
        payments[str(interaction.user.id)][method] = info
        await self.db.set(interaction.guild_id, "payments", payments)
        await interaction.response.send_message(embed=self.embeds.payment("Added", f"**{method}:** `{info}`"), ephemeral=True)

    @app_commands.command(name="payment-view", description="View your methods")
    async def payment_view(self, interaction: discord.Interaction):
        methods = await self._get_methods(interaction.guild_id, interaction.user.id)
        if not methods:
            return await interaction.response.send_message(embed=self.embeds.info("No Methods", "Use /payment-add to add one."), ephemeral=True)
        embed = self.embeds.payment("Your Methods", "Visible to buyers:")
        for m, i in methods.items():
            embed.add_field(name=m, value=f"`{i}`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="payment-view-user", description="View user's payment methods")
    async def payment_view_user(self, interaction: discord.Interaction, user: discord.Member):
        methods = await self._get_methods(interaction.guild_id, user.id)
        if not methods:
            return await interaction.response.send_message(embed=self.embeds.error("No Methods", f"{user.mention} has none set up."), ephemeral=True)
        embed = self.embeds.payment(f"{user.name}'s Methods", "Use these to pay:")
        for m, i in methods.items():
            embed.add_field(name=m, value=f"`{i}`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== ANTINUKE COG =====
class ActionTracker:
    def __init__(self):
        self.actions = defaultdict(lambda: deque(maxlen=50))
    def add(self, user_id, action_type):
        self.actions[f"{user_id}:{action_type}"].append({"time": datetime.utcnow()})
    def count(self, user_id, action_type, seconds):
        key = f"{user_id}:{action_type}"
        now = datetime.utcnow()
        return sum(1 for a in self.actions[key] if (now - a["time"]).total_seconds() <= seconds)
    def clear(self, user_id):
        for k in list(self.actions.keys()):
            if k.startswith(f"{user_id}:"): del self.actions[k]

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds; self.tracker = ActionTracker(); self.punished = {}

    async def _immune(self, member):
        if member.id == self.bot.user.id or member.id in self.bot.owner_ids: return True
        if member.guild_permissions.administrator:
            config = await self.db.get_antinuke(member.guild.id)
            for role_id in config.get("bypass_roles", []):
                if member.guild.get_role(role_id) in member.roles: return True
        return False

    async def _punish(self, member, reason, config):
        if member.id in self.punished and (datetime.utcnow() - self.punished[member.id]).total_seconds() < 60: return
        self.punished[member.id] = datetime.utcnow()
        punishment = config.get("punishment", "ban")
        try:
            if punishment == "ban":
                await member.ban(reason=f"[Anti-Nuke] {reason}")
            elif punishment == "kick":
                await member.kick(reason=f"[Anti-Nuke] {reason}")
            elif punishment == "strip":
                roles = [r for r in member.roles if r != member.guild.default_role]
                await member.remove_roles(*roles, reason=f"[Anti-Nuke] {reason}")
                await member.timeout(timedelta(hours=24), reason=f"[Anti-Nuke] {reason}")
        except: pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await asyncio.sleep(0.5)
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id and not await self._immune(entry.user):
                    self.tracker.add(entry.user.id, "channel_delete")
                    config = await self.db.get_antinuke(channel.guild.id)
                    if config.get("enabled", True) and self.tracker.count(entry.user.id, "channel_delete", config.get("time_window", 10)) >= config.get("channel_delete_limit", 3):
                        await self._punish(entry.user, f"Mass channel deletion ({config.get('channel_delete_limit', 3)}+)", config)
                    break
        except: pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await asyncio.sleep(0.5)
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id and not await self._immune(entry.user):
                    self.tracker.add(entry.user.id, "channel_create")
                    config = await self.db.get_antinuke(channel.guild.id)
                    if config.get("enabled", True) and self.tracker.count(entry.user.id, "channel_create", config.get("time_window", 10)) >= config.get("channel_create_limit", 3):
                        await self._punish(entry.user, f"Mass channel creation ({config.get('channel_create_limit', 3)}+)", config)
                    break
        except: pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await asyncio.sleep(0.5)
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id and not await self._immune(entry.user):
                    self.tracker.add(entry.user.id, "ban")
                    config = await self.db.get_antinuke(guild.id)
                    if config.get("enabled", True) and self.tracker.count(entry.user.id, "ban", config.get("time_window", 10)) >= config.get("ban_limit", 3):
                        await self._punish(entry.user, f"Mass banning ({config.get('ban_limit', 3)}+)", config)
                    break
        except: pass

    @app_commands.command(name="antinuke-config", description="Configure anti-nuke")
    @app_commands.checks.has_permissions(administrator=True)
    async def antinuke_config(self, interaction: discord.Interaction, setting: str, value: str):
        valid = ["enabled", "channel_delete_limit", "channel_create_limit", "role_delete_limit", "role_create_limit", "ban_limit", "kick_limit", "webhook_limit", "time_window", "punishment"]
        if setting not in valid: return await interaction.response.send_message(embed=self.embeds.error("Invalid", f"Valid: {','.join(valid)}"), ephemeral=True)
        config = await self.db.get_antinuke(interaction.guild_id)
        config[setting] = value.lower() in ["true", "yes", "1", "on"] if setting == "enabled" else (value.lower() if setting == "punishment" else int(value))
        await self.db.set(interaction.guild_id, "antinuke", config)
        await interaction.response.send_message(embed=self.embeds.shield("Updated", f"`{setting}` = `{config[setting]}`"), ephemeral=True)

    @app_commands.command(name="antinuke-status", description="View anti-nuke status")
    @app_commands.checks.has_permissions(administrator=True)
    async def antinuke_status(self, interaction: discord.Interaction):
        config = await self.db.get_antinuke(interaction.guild_id)
        embed = self.embeds.shield("Anti-Nuke Status", "Settings:")
        for k, v in config.items():
            embed.add_field(name=k, value=str(v), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== MODERATION COG =====
class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds

    async def _log(self, guild, embed):
        ch_id = await self.db.get(guild.id, "logs_channel")
        if ch_id:
            ch = guild.get_channel(ch_id)
            if ch: await ch.send(embed=embed)

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(embed=self.embeds.error("Hierarchy", "Can't kick this member."), ephemeral=True)
        await member.kick(reason=f"{interaction.user}: {reason}")
        await interaction.response.send_message(embed=self.embeds.success("Kicked", f"{member.mention} kicked.\n**Reason:** {reason}"))
        await self._log(interaction.guild, self.embeds.info("Kick", f"**User:** {member.mention}\n**By:** {interaction.user.mention}\n**Reason:** {reason}"))

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason", delete_days: Optional[int] = 0):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(embed=self.embeds.error("Hierarchy", "Can't ban this member."), ephemeral=True)
        await member.ban(reason=f"{interaction.user}: {reason}", delete_message_days=min(delete_days, 7))
        await interaction.response.send_message(embed=self.embeds.success("Banned", f"{member.mention} banned.\n**Reason:** {reason}"))

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: Optional[str] = "No reason"):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(embed=self.embeds.error("Hierarchy", "Can't timeout this member."), ephemeral=True)
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        try:
            seconds = int(duration[:-1]) * units[duration[-1].lower()]
            seconds = min(seconds, 2419200)
        except:
            return await interaction.response.send_message(embed=self.embeds.error("Invalid", "Use: 30m, 1h, 1d, 1w"), ephemeral=True)
        await member.timeout(timedelta(seconds=seconds), reason=f"{interaction.user}: {reason}")
        await interaction.response.send_message(embed=self.embeds.success("Timed Out", f"{member.mention} for {duration}.\n**Reason:** {reason}"))

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        count = await self.db.add_warn(interaction.guild_id, member.id, reason, interaction.user.id)
        await interaction.response.send_message(embed=self.embeds.warning("Warned", f"{member.mention} warned.\n**Reason:** {reason}\n**Total:** {count}"))
        try: await member.send(embed=discord.Embed(title=f"Warning from {interaction.guild.name}", description=f"**Reason:** {reason}\n**Total:** {count}", color=Config.WARNING_COLOR))
        except: pass

    @app_commands.command(name="warnings", description="View warnings")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        warns = await self.db.get_warns(interaction.guild_id, member.id)
        if not warns:
            return await interaction.response.send_message(embed=self.embeds.info("Clean", f"{member.mention} has no warnings."), ephemeral=True)
        embed = self.embeds.info(f"Warnings for {member.name}", f"**Total:** {len(warns)}")
        for i, w in enumerate(warns[-10:], 1):
            mod = interaction.guild.get_member(w["moderator"])
            embed.add_field(name=f"Warning #{i}", value=f"**Reason:** {w['reason']}\n**By:** {mod.mention if mod else 'Unknown'}\n**Date:** {w['timestamp'][:10]}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear-warns", description="Clear all warnings")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_warns(self, interaction: discord.Interaction, member: discord.Member):
        await self.db.clear_warns(interaction.guild_id, member.id)
        await interaction.response.send_message(embed=self.embeds.success("Cleared", f"All warnings cleared for {member.mention}."), ephemeral=True)

    @app_commands.command(name="purge", description="Delete messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int, member: Optional[discord.Member] = None):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount * 2 if member else amount, check=(lambda m: m.author.id == member.id) if member else None)
        await interaction.followup.send(embed=self.embeds.success("Purged", f"Deleted {len(deleted)} messages."), ephemeral=True)

    @app_commands.command(name="slowmode", description="Set slowmode")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        await interaction.channel.edit(slowmode_delay=max(0, min(seconds, 21600)))
        await interaction.response.send_message(embed=self.embeds.success("Slowmode", f"Set to {seconds} seconds." if seconds else "Disabled."), ephemeral=True)

    @app_commands.command(name="lock", description="Lock channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, reason: Optional[str] = "No reason"):
        ch = channel or interaction.channel
        await ch.set_permissions(interaction.guild.default_role, send_messages=False, reason=reason)
        await ch.send(embed=self.embeds.warning("Locked", f"{ch.mention} locked.\n**Reason:** {reason}"))
        if ch != interaction.channel:
            await interaction.response.send_message(embed=self.embeds.success("Locked", f"{ch.mention} locked."), ephemeral=True)

    @app_commands.command(name="unlock", description="Unlock channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        ch = channel or interaction.channel
        await ch.set_permissions(interaction.guild.default_role, send_messages=None)
        await ch.send(embed=self.embeds.success("Unlocked", f"{ch.mention} unlocked."))
        if ch != interaction.channel:
            await interaction.response.send_message(embed=self.embeds.success("Unlocked", f"{ch.mention} unlocked."), ephemeral=True)

# ===== UTILITY COG =====
class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds

    @app_commands.command(name="help", description="Show all commands")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Obsidian Marketplace Bot", description="Premium marketplace management bot.", color=Config.PRIMARY_COLOR)
        embed.add_field(name="Moderation", value="/kick /ban /timeout /warn /warnings /clear-warns /purge /slowmode /lock /unlock", inline=False)
        embed.add_field(name="Tickets", value="/ticket-panel /ticket-config /close", inline=False)
        embed.add_field(name="Marketplace", value="/listing-create /listing-view /listing-list /listing-delete", inline=False)
        embed.add_field(name="Payments", value="/payment-add /payment-view /payment-view-user", inline=False)
        embed.add_field(name="AutoMod", value="/automod /badword /automod-stats", inline=False)
        embed.add_field(name="Anti-Nuke", value="/antinuke-config /antinuke-status", inline=False)
        embed.add_field(name="Welcome", value="/welcome-config /welcome-test /welcome-toggle", inline=False)
        embed.add_field(name="Utility", value="/help /ping /server-info /user-info /bot-info /set-logs", inline=False)
        embed.set_footer(text="Use / before each command")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="Check latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        color = Config.SUCCESS_COLOR if latency < 200 else Config.WARNING_COLOR if latency < 500 else Config.ERROR_COLOR
        await interaction.response.send_message(embed=discord.Embed(title="Pong!", description=f"**Latency:** {latency}ms", color=color), ephemeral=True)

    @app_commands.command(name="server-info", description="Server information")
    async def server_info(self, interaction: discord.Interaction):
        g = interaction.guild
        embed = discord.Embed(title=f"Server: {g.name}", color=Config.PRIMARY_COLOR)
        embed.set_thumbnail(url=g.icon.url if g.icon else None)
        embed.add_field(name="Owner", value=g.owner.mention if g.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=str(g.member_count), inline=True)
        embed.add_field(name="Channels", value=f"Text: {len(g.text_channels)} | Voice: {len(g.voice_channels)}", inline=True)
        embed.add_field(name="Roles", value=str(len(g.roles)), inline=True)
        embed.add_field(name="Boosts", value=f"Level {g.premium_tier} | {g.premium_subscription_count} boosts", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="user-info", description="User information")
    async def user_info(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        m = member or interaction.user
        embed = discord.Embed(title=f"User: {m}", color=m.color if m.color != discord.Color.default() else Config.PRIMARY_COLOR)
        embed.set_thumbnail(url=m.display_avatar.url)
        embed.add_field(name="ID", value=f"{m.id}", inline=True)
        embed.add_field(name="Joined", value=f"<t:{int(m.joined_at.timestamp())}:R>" if m.joined_at else "Unknown", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(m.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Roles", value=f"{len(m.roles)} roles", inline=True)
        embed.add_field(name="Color", value=str(m.color), inline=True)
        embed.add_field(name="Bot", value="Yes" if m.bot else "No", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="about", description="Bot information")
    async def about_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Obsidian Marketplace Bot", color=Config.PRIMARY_COLOR)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="Uptime", value=f"<t:{int(self.bot.start_time.timestamp())}:R>", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set-logs", description="Set logs channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.db.set(interaction.guild_id, "logs_channel", channel.id)
        await interaction.response.send_message(embed=self.embeds.success("Logs Set", f"Mod actions will log to {channel.mention}."), ephemeral=True)

# ===== OWNER COG =====
class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot; self.db = bot.db; self.embeds = bot.embeds

    @commands.command(name="reload", hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        try:
            await self.bot.reload_extension(cog)
            await ctx.send(embed=self.embeds.success("Reloaded", f"{cog} reloaded."))
        except Exception as e:
            await ctx.send(embed=self.embeds.error("Error", f"{str(e)}"))

    @commands.command(name="sync", hidden=True)
    @commands.is_owner()
    async def sync(self, ctx, guild_id: Optional[int] = None):
        if guild_id:
            guild = discord.Object(id=guild_id)
            synced = await self.bot.tree.sync(guild=guild)
            await ctx.send(embed=self.embeds.success("Synced", f"Synced {len(synced)} commands to guild {guild_id}."))
        else:
            synced = await self.bot.tree.sync()
            await ctx.send(embed=self.embeds.success("Synced", f"Synced {len(synced)} commands globally."))

    @commands.command(name="shutdown", hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send(embed=self.embeds.info("Shutting down...", "Goodbye!"))
        await self.bot.close()

    @commands.command(name="status", hidden=True)
    @commands.is_owner()
    async def status(self, ctx, *, text: str):
        await self.bot.change_presence(activity=discord.Game(name=text))
        await ctx.send(embed=self.embeds.success("Status Updated", f"Now playing: {text}"))

# ===== RUN =====
if __name__ == "__main__":
    bot = ObsidianBot()
    bot.run(Config.TOKEN)
