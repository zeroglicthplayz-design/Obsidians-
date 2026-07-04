"""
╔═══════════════════════════════════════════════════════════════════════╗
║                    OBSIDIAN MARKETPLACE BOT                           ║
║              A premium Discord marketplace management bot               ║
║                                                                       ║
║  Features: AutoMod | Welcome | Tickets | Stocks | Payments | AntiNuke ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from utils.database import Database
from utils.embeds import ObsidianEmbeds
from utils.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ObsidianBot')

class ObsidianBot(commands.Bot):
    """Main bot class for Obsidian Marketplace"""

    def __init__(self):
        intents = discord.Intents.all()
        intents.members = True
        intents.message_content = True
        intents.presences = True

        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            owner_ids=set(Config.OWNER_IDS)
        )

        self.db = Database()
        self.embeds = ObsidianEmbeds()
        self.start_time = datetime.utcnow()
        self.anti_nuke_cache = {}  # Anti-nuke tracking

    async def setup_hook(self):
        """Load all cogs on startup"""
        cogs = [
            'cogs.automod',
            'cogs.welcome',
            'cogs.tickets',
            'cogs.stocks',
            'cogs.payments',
            'cogs.antinuke',
            'cogs.moderation',
            'cogs.utility',
            'cogs.owner'
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f'✅ Loaded {cog}')
            except Exception as e:
                logger.error(f'❌ Failed to load {cog}: {e}')

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f'🔄 Synced {len(synced)} slash commands')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')

        # Start background tasks
        self.status_rotation.start()

    @tasks.loop(minutes=5)
    async def status_rotation(self):
        """Rotate bot status"""
        statuses = [
            discord.Activity(type=discord.ActivityType.watching, name="over Obsidian Marketplace"),
            discord.Activity(type=discord.ActivityType.listening, name="/help for commands"),
            discord.Activity(type=discord.ActivityType.playing, name="securing your server"),
            discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"),
            discord.Activity(type=discord.ActivityType.competing, name="marketplace deals")
        ]
        import random
        await self.change_presence(activity=random.choice(statuses))

    @status_rotation.before_loop
    async def before_status(self):
        await self.wait_until_ready()

    async def on_ready(self):
        """Called when bot is ready"""
        logger.info('=' * 60)
        logger.info('🔮 OBSIDIAN MARKETPLACE BOT ONLINE')
        logger.info(f'👤 Bot: {self.user} ({self.user.id})')
        logger.info(f'🏠 Guilds: {len(self.guilds)}')
        logger.info(f'📊 Users: {sum(g.member_count for g in self.guilds)}')
        logger.info('=' * 60)

    async def on_guild_join(self, guild: discord.Guild):
        """Handle guild join"""
        logger.info(f'➕ Joined guild: {guild.name} ({guild.id})')
        # Initialize guild in database
        await self.db.init_guild(guild.id)

    async def on_guild_remove(self, guild: discord.Guild):
        """Handle guild leave"""
        logger.info(f'➖ Left guild: {guild.name} ({guild.id})')

    async def on_command_error(self, ctx: commands.Context, error):
        """Global command error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            embed = self.embeds.error("Missing Permissions", "You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            embed = self.embeds.error("Bot Missing Permissions", f"I need: {', '.join(error.missing_permissions)}")
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = self.embeds.error("Missing Argument", f"Usage: `{ctx.command.usage or ctx.command.signature}`")
        elif isinstance(error, commands.CheckFailure):
            embed = self.embeds.error("Access Denied", "You cannot use this command.")
        else:
            embed = self.embeds.error("Error", f"```py\n{str(error)}\n```")
            logger.error(f'Command error in {ctx.command}: {error}')

        await ctx.send(embed=embed, delete_after=10)

# Run the bot
if __name__ == '__main__':
    bot = ObsidianBot()
    bot.run(Config.TOKEN)
