"""Anti-Nuke system for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict
import asyncio

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class ActionTracker:
    """Tracks user actions for anti-nuke"""

    def __init__(self):
        self.actions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

    def add_action(self, user_id: int, action_type: str):
        """Record an action"""
        key = f"{user_id}:{action_type}"
        self.actions[key].append({
            'time': datetime.utcnow(),
            'type': action_type
        })

    def get_recent_count(self, user_id: int, action_type: str, seconds: int) -> int:
        """Get count of recent actions"""
        key = f"{user_id}:{action_type}"
        now = datetime.utcnow()
        return sum(1 for a in self.actions[key] if (now - a['time']).total_seconds() <= seconds)

    def clear_user(self, user_id: int):
        """Clear user's action history"""
        keys_to_remove = [k for k in self.actions.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self.actions[key]

class AntiNuke(commands.Cog):
    """Advanced anti-nuke protection"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds
        self.tracker = ActionTracker()
        self.punished_users: Dict[int, datetime] = {}  # user_id -> punishment time

    async def _is_immune(self, member: discord.Member) -> bool:
        """Check if member is immune to anti-nuke"""
        if member.id == self.bot.user.id:
            return True
        if member.id in self.bot.owner_ids:
            return True
        if member.guild_permissions.administrator:
            # Check if they have anti-nuke bypass role
            config = await self.db.get_antinuke(member.guild.id)
            bypass_roles = config.get('bypass_roles', [])
            for role_id in bypass_roles:
                role = member.guild.get_role(role_id)
                if role and role in member.roles:
                    return True
        return False

    async def _punish(self, member: discord.Member, reason: str, config: dict):
        """Punish a user for nuke attempt"""
        punishment = config.get('punishment', 'ban')
        guild = member.guild

        # Prevent double punishment
        if member.id in self.punished_users:
            if (datetime.utcnow() - self.punished_users[member.id]).total_seconds() < 60:
                return

        self.punished_users[member.id] = datetime.utcnow()

        # Log the action
        log_embed = self.embeds.antinuke_alert(
            punishment.upper(),
            f"{member.mention} (`{member.id}`)",
            reason
        )

        logs_channel_id = await self.db.get(guild.id, 'logs_channel')
        if logs_channel_id:
            logs_channel = guild.get_channel(logs_channel_id)
            if logs_channel:
                await logs_channel.send(embed=log_embed)

        # Execute punishment
        try:
            if punishment == 'ban':
                await member.ban(reason=f"[Anti-Nuke] {reason}")
            elif punishment == 'kick':
                await member.kick(reason=f"[Anti-Nuke] {reason}")
            elif punishment == 'strip':
                # Remove all roles except @everyone
                roles_to_remove = [r for r in member.roles if r != guild.default_role]
                await member.remove_roles(*roles_to_remove, reason=f"[Anti-Nuke] {reason}")

                # Timeout for 24 hours
                await member.timeout(timedelta(hours=24), reason=f"[Anti-Nuke] {reason}")

            # Send alert to system channel
            system_channel = guild.system_channel
            if system_channel:
                alert_embed = self.embeds.antinuke_alert(
                    "THREAT NEUTRALIZED",
                    member.mention,
                    f"{reason}\n\n**Action Taken:** {punishment.upper()}"
                )
                await system_channel.send(embed=alert_embed)

        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Anti-nuke punishment error: {e}")

    async def _check_threshold(self, member: discord.Member, action_type: str, config_key: str, config: dict) -> bool:
        """Check if user exceeded action threshold"""
        time_window = config.get('time_window', 10)
        limit = config.get(config_key, 3)

        count = self.tracker.get_recent_count(member.id, action_type, time_window)
        return count >= limit

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Detect mass channel deletion"""
        if not channel.guild:
            return

        # Get audit log
        await asyncio.sleep(0.5)  # Small delay for audit log

        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    if await self._is_immune(entry.user):
                        return

                    self.tracker.add_action(entry.user.id, 'channel_delete')

                    config = await self.db.get_antinuke(channel.guild.id)
                    if not config.get('enabled', True):
                        return

                    if await self._check_threshold(entry.user, 'channel_delete', 'channel_delete_limit', config):
                        await self._punish(entry.user, f"Mass channel deletion ({config.get('channel_delete_limit', 3)}+ channels)", config)
                    break
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        """Detect mass channel creation"""
        if not channel.guild:
            return

        await asyncio.sleep(0.5)

        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    if await self._is_immune(entry.user):
                        return

                    self.tracker.add_action(entry.user.id, 'channel_create')

                    config = await self.db.get_antinuke(channel.guild.id)
                    if not config.get('enabled', True):
                        return

                    if await self._check_threshold(entry.user, 'channel_create', 'channel_create_limit', config):
                        await self._punish(entry.user, f"Mass channel creation ({config.get('channel_create_limit', 3)}+ channels)", config)
                    break
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Detect mass role deletion"""
        await asyncio.sleep(0.5)

        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    if await self._is_immune(entry.user):
                        return

                    self.tracker.add_action(entry.user.id, 'role_delete')

                    config = await self.db.get_antinuke(role.guild.id)
                    if not config.get('enabled', True):
                        return

                    if await self._check_threshold(entry.user, 'role_delete', 'role_delete_limit', config):
                        await self._punish(entry.user, f"Mass role deletion ({config.get('role_delete_limit', 3)}+ roles)", config)
                    break
        except:
            pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """Detect mass role creation"""
        await asyncio.sleep(0.5)

        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    if await self._is_immune(entry.user):
                        return

                    self.tracker.add_action(entry.user.id, 'role_create')

                    config = await self.db.get_antinuke(role.guild.id)
                    if not config.get('enabled', True):
                        return

                    if await self._check_threshold(entry.user, 'role_create', 'role_create_limit', config):
                        await self._punish(entry.user, f"Mass role creation ({config.get('role_create_limit', 3)}+ roles)", config)
                    break
        except:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Detect mass bans"""
        await asyncio.sleep(0.5)

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    if await self._is_immune(entry.user):
                        return

                    self.tracker.add_action(entry.user.id, 'ban')

                    config = await self.db.get_antinuke(guild.id)
                    if not config.get('enabled', True):
                        return

                    if await self._check_threshold(entry.user, 'ban', 'ban_limit', config):
                        await self._punish(entry.user, f"Mass banning ({config.get('ban_limit', 3)}+ users)", config)
                    break
        except:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Detect mass kicks"""
        await asyncio.sleep(0.5)

        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    if await self._is_immune(entry.user):
                        return

                    self.tracker.add_action(entry.user.id, 'kick')

                    config = await self.db.get_antinuke(member.guild.id)
                    if not config.get('enabled', True):
                        return

                    if await self._check_threshold(entry.user, 'kick', 'kick_limit', config):
                        await self._punish(entry.user, f"Mass kicking ({config.get('kick_limit', 5)}+ users)", config)
                    break
        except:
            pass

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        """Detect webhook abuse"""
        await asyncio.sleep(0.5)

        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
                if await self._is_immune(entry.user):
                    return

                self.tracker.add_action(entry.user.id, 'webhook_create')

                config = await self.db.get_antinuke(channel.guild.id)
                if not config.get('enabled', True):
                    return

                if await self._check_threshold(entry.user, 'webhook_create', 'webhook_limit', config):
                    await self._punish(entry.user, f"Mass webhook creation ({config.get('webhook_limit', 2)}+ webhooks)", config)
                break
        except:
            pass

    @app_commands.command(name="antinuke-config", description="Configure anti-nuke settings")
    @app_commands.describe(
        setting="Setting to configure",
        value="Value to set"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def antinuke_config(self, interaction: discord.Interaction, setting: str, value: str):
        """Configure anti-nuke"""
        valid_settings = [
            'enabled', 'channel_delete_limit', 'channel_create_limit',
            'role_delete_limit', 'role_create_limit', 'ban_limit',
            'kick_limit', 'webhook_limit', 'time_window', 'punishment'
        ]

        if setting not in valid_settings:
            await interaction.response.send_message(
                embed=self.embeds.error("Invalid Setting", f"Valid: {', '.join(valid_settings)}"),
                ephemeral=True
            )
            return

        if setting == 'enabled':
            value = value.lower() in ['true', 'yes', '1', 'on']
        elif setting == 'punishment':
            if value.lower() not in ['ban', 'kick', 'strip']:
                await interaction.response.send_message(
                    embed=self.embeds.error("Invalid", "Punishment must be: ban, kick, or strip"),
                    ephemeral=True
                )
                return
        else:
            try:
                value = int(value)
            except:
                await interaction.response.send_message(
                    embed=self.embeds.error("Invalid", "This setting requires a number."),
                    ephemeral=True
                )
                return

        config = await self.db.get_antinuke(interaction.guild_id)
        config[setting] = value
        await self.db.set(interaction.guild_id, 'antinuke', config)

        await interaction.response.send_message(
            embed=self.embeds.shield("Anti-Nuke Updated", f"`{setting}` set to `{value}`"),
            ephemeral=True
        )

    @app_commands.command(name="antinuke-whitelist", description="Whitelist a role from anti-nuke")
    @app_commands.checks.has_permissions(administrator=True)
    async def antinuke_whitelist(self, interaction: discord.Interaction, role: discord.Role):
        """Whitelist a role"""
        config = await self.db.get_antinuke(interaction.guild_id)
        bypass_roles = config.get('bypass_roles', [])

        if role.id in bypass_roles:
            bypass_roles.remove(role.id)
            action = "removed from"
        else:
            bypass_roles.append(role.id)
            action = "added to"

        config['bypass_roles'] = bypass_roles
        await self.db.set(interaction.guild_id, 'antinuke', config)

        await interaction.response.send_message(
            embed=self.embeds.shield("Whitelist Updated", f"{role.mention} {action} anti-nuke whitelist."),
            ephemeral=True
        )

    @app_commands.command(name="antinuke-status", description="View anti-nuke status")
    @app_commands.checks.has_permissions(administrator=True)
    async def antinuke_status(self, interaction: discord.Interaction):
        """View anti-nuke status"""
        config = await self.db.get_antinuke(interaction.guild_id)

        embed = self.embeds.shield("Anti-Nuke Status", "Current protection settings:")

        embed.add_field(name="Enabled", value=str(config.get('enabled', True)), inline=True)
        embed.add_field(name="Punishment", value=config.get('punishment', 'ban'), inline=True)
        embed.add_field(name="Time Window", value=f"{config.get('time_window', 10)}s", inline=True)
        embed.add_field(name="Channel Delete", value=str(config.get('channel_delete_limit', 3)), inline=True)
        embed.add_field(name="Channel Create", value=str(config.get('channel_create_limit', 3)), inline=True)
        embed.add_field(name="Role Delete", value=str(config.get('role_delete_limit', 3)), inline=True)
        embed.add_field(name="Role Create", value=str(config.get('role_create_limit', 3)), inline=True)
        embed.add_field(name="Ban Limit", value=str(config.get('ban_limit', 3)), inline=True)
        embed.add_field(name="Kick Limit", value=str(config.get('kick_limit', 5)), inline=True)
        embed.add_field(name="Webhook Limit", value=str(config.get('webhook_limit', 2)), inline=True)

        bypass_roles = config.get('bypass_roles', [])
        if bypass_roles:
            roles_text = " ".join(f"<@&{r}>" for r in bypass_roles)
            embed.add_field(name="Whitelisted Roles", value=roles_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiNuke(bot))
