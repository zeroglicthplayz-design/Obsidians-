"""Moderation commands for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime, timedelta

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class Moderation(commands.Cog):
    """Moderation tools"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

    async def _log_action(self, guild: discord.Guild, embed: discord.Embed):
        """Log moderation action"""
        logs_channel_id = await self.db.get(guild.id, 'logs_channel')
        if logs_channel_id:
            channel = guild.get_channel(logs_channel_id)
            if channel:
                await channel.send(embed=embed)

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided"):
        """Kick a member"""
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                embed=self.embeds.error("Hierarchy", "You cannot kick this member."),
                ephemeral=True
            )
            return

        try:
            await member.kick(reason=f"{interaction.user}: {reason}")

            embed = self.embeds.success("Member Kicked", f"{member.mention} has been kicked.\n**Reason:** {reason}")
            await interaction.response.send_message(embed=embed)

            log_embed = self.embeds.info("Kick", f"**User:** {member.mention}\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}")
            await self._log_action(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=self.embeds.error("Error", "I don't have permission to kick this member."),
                ephemeral=True
            )

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="Member to ban", reason="Reason for ban", delete_days="Days of messages to delete (0-7)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason provided", delete_days: Optional[int] = 0):
        """Ban a member"""
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                embed=self.embeds.error("Hierarchy", "You cannot ban this member."),
                ephemeral=True
            )
            return

        try:
            await member.ban(reason=f"{interaction.user}: {reason}", delete_message_days=min(delete_days, 7))

            embed = self.embeds.success("Member Banned", f"{member.mention} has been banned.\n**Reason:** {reason}")
            await interaction.response.send_message(embed=embed)

            log_embed = self.embeds.info("Ban", f"**User:** {member.mention}\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}")
            await self._log_action(interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=self.embeds.error("Error", "I don't have permission to ban this member."),
                ephemeral=True
            )

    @app_commands.command(name="unban", description="Unban a user")
    @app_commands.describe(user_id="User ID to unban", reason="Reason for unban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: Optional[str] = "No reason provided"):
        """Unban a user"""
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=f"{interaction.user}: {reason}")

            embed = self.embeds.success("User Unbanned", f"{user.mention} has been unbanned.\n**Reason:** {reason}")
            await interaction.response.send_message(embed=embed)

        except (ValueError, discord.NotFound):
            await interaction.response.send_message(
                embed=self.embeds.error("Not Found", "User not found or not banned."),
                ephemeral=True
            )

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="Member to timeout", duration="Duration (e.g., 1h, 30m, 1d)", reason="Reason")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: Optional[str] = "No reason provided"):
        """Timeout a member"""
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                embed=self.embeds.error("Hierarchy", "You cannot timeout this member."),
                ephemeral=True
            )
            return

        # Parse duration
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * time_units[unit]

            if seconds > 2419200:  # Max 28 days
                seconds = 2419200

            delta = timedelta(seconds=seconds)

        except (KeyError, ValueError):
            await interaction.response.send_message(
                embed=self.embeds.error("Invalid Duration", "Use format like: `1h`, `30m`, `1d`, `1w`"),
                ephemeral=True
            )
            return

        try:
            await member.timeout(delta, reason=f"{interaction.user}: {reason}")

            embed = self.embeds.success("Member Timed Out", 
                f"{member.mention} has been timed out for `{duration}`.\n**Reason:** {reason}")
            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=self.embeds.error("Error", "I don't have permission to timeout this member."),
                ephemeral=True
            )

    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(member="Member to untimeout")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):
        """Remove timeout"""
        try:
            await member.timeout(None, reason=f"Removed by {interaction.user}")
            await interaction.response.send_message(
                embed=self.embeds.success("Timeout Removed", f"Timeout removed from {member.mention}."),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=self.embeds.error("Error", "I don't have permission."),
                ephemeral=True
            )

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        """Warn a member"""
        warn_count = await self.db.add_warn(interaction.guild_id, member.id, reason, interaction.user.id)

        embed = self.embeds.warning("Member Warned", 
            f"{member.mention} has been warned.\n"
            f"**Reason:** {reason}\n"
            f"**Total Warnings:** `{warn_count}`")
        await interaction.response.send_message(embed=embed)

        # DM the user
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ Warning from {interaction.guild.name}",
                description=f"**Reason:** {reason}\n**Total Warnings:** `{warn_count}`",
                color=Config.WARNING_COLOR
            )
            await member.send(embed=dm_embed)
        except:
            pass

    @app_commands.command(name="warnings", description="View a member's warnings")
    @app_commands.describe(member="Member to check")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        """View warnings"""
        warns = await self.db.get_warns(interaction.guild_id, member.id)

        if not warns:
            await interaction.response.send_message(
                embed=self.embeds.info("No Warnings", f"{member.mention} has no warnings."),
                ephemeral=True
            )
            return

        embed = self.embeds.info(f"Warnings for {member.name}", f"Total: `{len(warns)}`")

        for i, warn in enumerate(warns[-10:], 1):  # Show last 10
            mod = interaction.guild.get_member(warn['moderator'])
            mod_name = mod.mention if mod else "Unknown"
            embed.add_field(
                name=f"Warning #{i}",
                value=f"**Reason:** {warn['reason']}\n**By:** {mod_name}\n**Date:** {warn['timestamp'][:10]}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear-warns", description="Clear all warnings for a member")
    @app_commands.describe(member="Member to clear warnings for")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear_warns(self, interaction: discord.Interaction, member: discord.Member):
        """Clear warnings"""
        await self.db.clear_warns(interaction.guild_id, member.id)

        await interaction.response.send_message(
            embed=self.embeds.success("Warnings Cleared", f"All warnings cleared for {member.mention}."),
            ephemeral=True
        )

    @app_commands.command(name="purge", description="Delete messages in bulk")
    @app_commands.describe(amount="Number of messages to delete (1-100)", member="Only delete messages from this user (optional)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int, member: Optional[discord.Member] = None):
        """Purge messages"""
        amount = min(max(amount, 1), 100)

        await interaction.response.defer(ephemeral=True)

        if member:
            def check(msg):
                return msg.author.id == member.id
            deleted = await interaction.channel.purge(limit=amount * 2, check=check)
        else:
            deleted = await interaction.channel.purge(limit=amount)

        embed = self.embeds.success("Messages Purged", f"Deleted `{len(deleted)}` message(s).")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="slowmode", description="Set channel slowmode")
    @app_commands.describe(seconds="Slowmode in seconds (0 to disable)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        """Set slowmode"""
        seconds = max(0, min(seconds, 21600))

        try:
            await interaction.channel.edit(slowmode_delay=seconds)

            if seconds == 0:
                msg = "Slowmode disabled."
            else:
                msg = f"Slowmode set to `{seconds}` seconds."

            await interaction.response.send_message(
                embed=self.embeds.success("Slowmode Updated", msg),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=self.embeds.error("Error", "I don't have permission to edit this channel."),
                ephemeral=True
            )

    @app_commands.command(name="lock", description="Lock a channel")
    @app_commands.describe(channel="Channel to lock (default: current)", reason="Reason for locking")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, reason: Optional[str] = "No reason provided"):
        """Lock channel"""
        channel = channel or interaction.channel

        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False, reason=reason)

            embed = self.embeds.warning("Channel Locked", f"{channel.mention} has been locked.\n**Reason:** {reason}")
            await channel.send(embed=embed)

            if channel != interaction.channel:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=self.embeds.error("Error", "I don't have permission to lock this channel."),
                ephemeral=True
            )

    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(channel="Channel to unlock (default: current)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        """Unlock channel"""
        channel = channel or interaction.channel

        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=None)

            embed = self.embeds.success("Channel Unlocked", f"{channel.mention} has been unlocked.")
            await channel.send(embed=embed)

            if channel != interaction.channel:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                embed=self.embeds.error("Error", "I don't have permission to unlock this channel."),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
