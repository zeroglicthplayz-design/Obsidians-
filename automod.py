"""AutoMod system for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
import re
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class AutoMod(commands.Cog):
    """Advanced AutoMod system"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

        # Message tracking for spam detection
        self.message_cache: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10))
        self.mention_cache: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10))
        self.violation_cache: Dict[int, int] = defaultdict(int)

        # Regex patterns
        self.invite_pattern = re.compile(r'discord\.(gg|com/invite)/[a-zA-Z0-9-]+')
        self.link_pattern = re.compile(r'https?://[^\s]+')
        self.zalgo_pattern = re.compile(r'[\u0300-\u036F\u0483-\u0489\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED\u0711\u0730-\u074A\u07A6-\u07B0\u07EB-\u07F3\u07FD\u0816-\u0819\u081B-\u0823\u0825-\u0827\u0829-\u082D\u0859-\u085B\u08D3-\u08E1\u08E3-\u0903\u093A-\u093C\u093E-\u094F\u0951-\u0957\u0962\u0963\u0981-\u0983\u09BC\u09BE-\u09C4\u09C7\u09C8\u09CB-\u09CD\u09D7\u09E2\u09E3\u09FE\u0A01-\u0A03\u0A3C\u0A3E-\u0A42\u0A47\u0A48\u0A4B-\u0A4D\u0A51\u0A70\u0A71\u0A75\u0A81-\u0A83\u0ABC\u0ABE-\u0AC5\u0AC7-\u0AC9\u0ACB-\u0ACD\u0AE2\u0AE3\u0AFA-\u0AFF\u0B01-\u0B03\u0B3C\u0B3E-\u0B44\u0B47\u0B48\u0B4B-\u0B4D\u0B56\u0B57\u0B62\u0B63\u0B82\u0BBE-\u0BC2\u0BC6-\u0BC8\u0BCA-\u0BCD\u0BD7\u0C00-\u0C03\u0C3E-\u0C44\u0C46-\u0C48\u0C4A-\u0C4D\u0C55\u0C56\u0C62\u0C63\u0C81-\u0C83\u0CBC\u0CBE-\u0CC4\u0CC6-\u0CC8\u0CCA-\u0CCD\u0CD5\u0CD6\u0CE2\u0CE3\u0D00-\u0D03\u0D3B\u0D3C\u0D3E-\u0D44\u0D46-\u0D48\u0D4A-\u0D4D\u0D57\u0D62\u0D63\u0D81-\u0D83\u0DCA\u0DCF-\u0DD4\u0DD6\u0DD8-\u0DDF\u0DF2\u0DF3\u0E31\u0E34-\u0E3A\u0E47-\u0E4E\u0EB1\u0EB4-\u0EB9\u0EBB\u0EBC\u0EC8-\u0ECD\u0F18\u0F19\u0F35\u0F37\u0F39\u0F3E\u0F3F\u0F71-\u0F84\u0F86\u0F87\u0F8D-\u0F97\u0F99-\u0FBC\u0FC6\u102B-\u103E\u1056-\u1059\u105E-\u1060\u1062-\u1064\u1067-\u106D\u1071-\u1074\u1082-\u108D\u108F\u109A-\u109D\u135D-\u135F\u1712-\u1714\u1732-\u1734\u1752\u1753\u1772\u1773\u17B4-\u17D3\u17DD\u180B-\u180D\u1885\u1886\u18A9\u1920-\u192B\u1930-\u193B\u1A17-\u1A1B\u1A55-\u1A5E\u1A60-\u1A7C\u1A7F\u1AB0-\u1ABD\u1ABF\u1AC0\u1B00-\u1B04\u1B34-\u1B44\u1B6B-\u1B73\u1B80-\u1B82\u1BA1-\u1BAD\u1BE6-\u1BF3\u1C24-\u1C37\u1CD0-\u1CD2\u1CD4-\u1CE8\u1CED\u1CF2-\u1CF4\u1CF8\u1CF9\u1DC0-\u1DF9\u1DFB-\u1DFF\u20D0-\u20F0\u2CEF-\u2CF1\u2D7F\u2DE0-\u2DFF\u302A-\u302F\u3099\u309A\uA66F-\uA672\uA674-\uA67D\uA69E\uA69F\uA6F0\uA6F1\uA802\uA806\uA80B\uA823-\uA827\uA880\uA881\uA8B4-\uA8C5\uA8E0-\uA8F1\uA926-\uA92D\uA947-\uA953\uA980-\uA983\uA9B3-\uA9C0\uA9E5\uAA29-\uAA36\uAA43\uAA4C\uAA4D\uAA7B-\uAA7D\uAAB0\uAAB2-\uAAB4\uAAB7\uAAB8\uAABE\uAABF\uAAC1\uAAEB-\uAAEF\uAAF5\uAAF6\uABE3-\uABEA\uABEC\uABED\uFB1E\uFE00-\uFE0F\uFE20-\uFE2F]+')

    async def log_action(self, guild: discord.Guild, embed: discord.Embed):
        """Log AutoMod action"""
        logs_channel_id = await self.db.get(guild.id, 'logs_channel')
        if logs_channel_id:
            channel = guild.get_channel(logs_channel_id)
            if channel:
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Process messages for AutoMod"""
        if message.author.bot or not message.guild:
            return

        # Check if user is immune
        if message.author.guild_permissions.administrator:
            return

        config = await self.db.get_automod(message.guild.id)
        if not config.get('enabled', True):
            return

        violations = []

        # Check spam
        if await self._check_spam(message, config):
            violations.append("Excessive messaging (spam)")

        # Check mentions
        if await self._check_mentions(message, config):
            violations.append("Mass mentioning")

        # Check caps
        if await self._check_caps(message, config):
            violations.append("Excessive caps")

        # Check bad words
        if await self._check_bad_words(message, config):
            violations.append("Inappropriate language")

        # Check invites
        if config.get('invite_filter', True):
            if await self._check_invites(message):
                violations.append("Unauthorized invite link")

        # Check links
        if config.get('link_filter', False):
            if await self._check_links(message):
                violations.append("Unauthorized link")

        # Check zalgo
        if await self._check_zalgo(message):
            violations.append("Zalgo text / text abuse")

        # Handle violations
        if violations:
            await self._handle_violations(message, violations)

    async def _check_spam(self, message: discord.Message, config: dict) -> bool:
        """Check for message spam"""
        user_id = message.author.id
        now = datetime.utcnow()

        self.message_cache[user_id].append({
            'content': message.content,
            'time': now,
            'channel': message.channel.id
        })

        threshold = config.get('spam_threshold', 5)
        interval = config.get('spam_interval', 5)

        recent = [m for m in self.message_cache[user_id] 
                  if (now - m['time']).total_seconds() <= interval]

        # Check duplicate messages
        if len(recent) >= threshold:
            contents = [m['content'] for m in recent]
            if len(set(contents)) <= 2:  # Mostly same content
                return True

        return False

    async def _check_mentions(self, message: discord.Message, config: dict) -> bool:
        """Check for mass mentions"""
        max_mentions = config.get('max_mentions', 5)

        total_mentions = len(message.mentions) + len(message.role_mentions)
        if total_mentions > max_mentions:
            return True
        return False

    async def _check_caps(self, message: discord.Message, config: dict) -> bool:
        """Check for excessive caps"""
        max_caps = config.get('max_caps_percent', 70)

        content = message.content
        if len(content) < 10:
            return False

        caps_count = sum(1 for c in content if c.isupper())
        caps_percent = (caps_count / len(content)) * 100

        return caps_percent > max_caps

    async def _check_bad_words(self, message: discord.Message, config: dict) -> bool:
        """Check for bad words"""
        bad_words = config.get('bad_words', [])
        content_lower = message.content.lower()

        for word in bad_words:
            if word in content_lower:
                return True
        return False

    async def _check_invites(self, message: discord.Message) -> bool:
        """Check for Discord invites"""
        return bool(self.invite_pattern.search(message.content))

    async def _check_links(self, message: discord.Message) -> bool:
        """Check for links"""
        return bool(self.link_pattern.search(message.content))

    async def _check_zalgo(self, message: discord.Message) -> bool:
        """Check for zalgo text"""
        return bool(self.zalgo_pattern.search(message.content))

    async def _handle_violations(self, message: discord.Message, violations: List[str]):
        """Handle detected violations"""
        user_id = message.author.id
        guild = message.guild

        # Increment violation count
        self.violation_cache[user_id] += 1
        count = self.violation_cache[user_id]

        # Delete the message
        try:
            await message.delete()
        except:
            pass

        # Send warning
        embed = self.embeds.automod(
            "AutoMod Alert",
            f"{message.author.mention}, your message was removed.\n\n**Violations:**\n" + 
            "\n".join(f"• {v}" for v in violations) + 
            f"\n\n**Strike:** `{count}/5`"
        )

        warning_msg = await message.channel.send(embed=embed, delete_after=10)

        # Log action
        log_embed = self.embeds.automod(
            "AutoMod Action",
            f"**User:** {message.author} (`{message.author.id}`)\n" +
            f"**Channel:** {message.channel.mention}\n" +
            f"**Violations:**\n" + "\n".join(f"• {v}" for v in violations) +
            f"\n**Strike Count:** {count}"
        )
        await self.log_action(guild, log_embed)

        # Progressive punishment
        if count >= 5:
            # Ban after 5 violations
            try:
                await message.author.ban(reason="AutoMod: Excessive violations (5+ strikes)")
                embed = self.embeds.automod(
                    "User Banned",
                    f"{message.author.mention} was banned for excessive AutoMod violations."
                )
                await message.channel.send(embed=embed)
            except:
                pass
        elif count >= 3:
            # Mute after 3 violations
            try:
                timeout_duration = timedelta(minutes=30)
                await message.author.timeout(timeout_duration, reason="AutoMod: 3+ violations")
            except:
                pass

    @app_commands.command(name="automod", description="Configure AutoMod settings")
    @app_commands.describe(
        setting="Setting to configure",
        value="Value to set"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_config(self, interaction: discord.Interaction, setting: str, value: str):
        """Configure AutoMod"""
        valid_settings = ['enabled', 'max_mentions', 'max_emojis', 'max_caps_percent', 
                         'spam_threshold', 'spam_interval', 'invite_filter', 'link_filter']

        if setting not in valid_settings:
            await interaction.response.send_message(
                embed=self.embeds.error("Invalid Setting", f"Valid settings: {', '.join(valid_settings)}"),
                ephemeral=True
            )
            return

        # Convert value
        if setting in ['enabled', 'invite_filter', 'link_filter']:
            value = value.lower() in ['true', 'yes', '1', 'on']
        else:
            try:
                value = int(value)
            except:
                await interaction.response.send_message(
                    embed=self.embeds.error("Invalid Value", "This setting requires a number."),
                    ephemeral=True
                )
                return

        config = await self.db.get_automod(interaction.guild_id)
        config[setting] = value
        await self.db.set(interaction.guild_id, 'automod', config)

        await interaction.response.send_message(
            embed=self.embeds.success("AutoMod Updated", f"`{setting}` set to `{value}`"),
            ephemeral=True
        )

    @app_commands.command(name="badword", description="Manage bad words filter")
    @app_commands.describe(action="Add or remove a word", word="The word to manage")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def badword(self, interaction: discord.Interaction, action: str, word: str):
        """Manage bad words"""
        config = await self.db.get_automod(interaction.guild_id)
        bad_words = config.get('bad_words', [])

        if action.lower() == 'add':
            if word.lower() not in bad_words:
                bad_words.append(word.lower())
                await interaction.response.send_message(
                    embed=self.embeds.success("Word Added", f"Added `{word}` to filter."),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=self.embeds.warning("Already Exists", f"`{word}` is already filtered."),
                    ephemeral=True
                )
        elif action.lower() == 'remove':
            if word.lower() in bad_words:
                bad_words.remove(word.lower())
                await interaction.response.send_message(
                    embed=self.embeds.success("Word Removed", f"Removed `{word}` from filter."),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=self.embeds.error("Not Found", f"`{word}` is not in the filter."),
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                embed=self.embeds.error("Invalid Action", "Use `add` or `remove`."),
                ephemeral=True
            )
            return

        config['bad_words'] = bad_words
        await self.db.set(interaction.guild_id, 'automod', config)

    @app_commands.command(name="automod-stats", description="View AutoMod statistics")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod_stats(self, interaction: discord.Interaction):
        """View AutoMod stats"""
        config = await self.db.get_automod(interaction.guild_id)

        embed = self.embeds.info("AutoMod Configuration", "Current settings:")
        embed.add_field(name="Enabled", value=str(config.get('enabled', True)), inline=True)
        embed.add_field(name="Max Mentions", value=str(config.get('max_mentions', 5)), inline=True)
        embed.add_field(name="Max Caps %", value=str(config.get('max_caps_percent', 70)), inline=True)
        embed.add_field(name="Spam Threshold", value=str(config.get('spam_threshold', 5)), inline=True)
        embed.add_field(name="Spam Interval", value=f"{config.get('spam_interval', 5)}s", inline=True)
        embed.add_field(name="Invite Filter", value=str(config.get('invite_filter', True)), inline=True)
        embed.add_field(name="Link Filter", value=str(config.get('link_filter', False)), inline=True)
        embed.add_field(name="Bad Words", value=str(len(config.get('bad_words', []))), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))
