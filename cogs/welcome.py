"""Welcome system for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class Welcome(commands.Cog):
    """Advanced welcome system"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member join"""
        if member.bot:
            return

        config = await self.db.get_welcome(member.guild.id)
        if not config.get('enabled', True):
            return

        # Get welcome channel
        welcome_channel_id = config.get('channel')
        if not welcome_channel_id:
            # Try to find a welcome or general channel
            welcome_channel = discord.utils.get(member.guild.text_channels, name='welcome') or                             discord.utils.get(member.guild.text_channels, name='general')
        else:
            welcome_channel = member.guild.get_channel(welcome_channel_id)

        if not welcome_channel:
            return

        # Build welcome message
        count = member.guild.member_count
        message = config.get('message', Config.WELCOME_DEFAULTS['message'])

        embed = self.embeds.welcome_card(member, member.guild, message, count)

        # Send welcome
        try:
            await welcome_channel.send(embed=embed)
        except:
            pass

        # Send DM if configured
        dm_message = config.get('dm_message')
        if dm_message:
            try:
                dm_embed = discord.Embed(
                    title=f"Welcome to {member.guild.name}!",
                    description=dm_message.format(
                        user=member.mention,
                        server=member.guild.name,
                        count=count,
                        username=member.name
                    ),
                    color=Config.PRIMARY_COLOR
                )
                await member.send(embed=dm_embed)
            except:
                pass

        # Assign auto role
        auto_role_id = config.get('auto_role')
        if auto_role_id:
            role = member.guild.get_role(auto_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leave"""
        if member.bot:
            return

        config = await self.db.get_welcome(member.guild.id)
        goodbye_channel_id = config.get('goodbye_channel') or config.get('channel')

        if not goodbye_channel_id:
            return

        channel = member.guild.get_channel(goodbye_channel_id)
        if not channel:
            return

        goodbye_msg = config.get('goodbye_message', '👋 {user} has left the server.')

        embed = discord.Embed(
            description=goodbye_msg.format(
                user=member.mention,
                username=member.name,
                server=member.guild.name
            ),
            color=Config.ERROR_COLOR,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{member.guild.name} now has {member.guild.member_count} members")

        try:
            await channel.send(embed=embed)
        except:
            pass

    @app_commands.command(name="welcome-config", description="Configure welcome settings")
    @app_commands.describe(
        channel="Welcome channel",
        message="Welcome message (use {user}, {server}, {count}, {username})",
        auto_role="Role to give on join",
        dm_message="DM message to send (optional)",
        goodbye_channel="Goodbye channel (optional)",
        goodbye_message="Goodbye message (optional)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_config(
        self, 
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: Optional[str] = None,
        auto_role: Optional[discord.Role] = None,
        dm_message: Optional[str] = None,
        goodbye_channel: Optional[discord.TextChannel] = None,
        goodbye_message: Optional[str] = None
    ):
        """Configure welcome system"""
        config = await self.db.get_welcome(interaction.guild_id)

        config['enabled'] = True
        config['channel'] = channel.id

        if message:
            config['message'] = message
        if auto_role:
            config['auto_role'] = auto_role.id
        if dm_message:
            config['dm_message'] = dm_message
        if goodbye_channel:
            config['goodbye_channel'] = goodbye_channel.id
        if goodbye_message:
            config['goodbye_message'] = goodbye_message

        await self.db.set(interaction.guild_id, 'welcome', config)

        embed = self.embeds.success(
            "Welcome Configured",
            f"Welcome channel set to {channel.mention}\n"
            f"Auto-role: {auto_role.mention if auto_role else 'None'}"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="welcome-test", description="Test welcome message")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_test(self, interaction: discord.Interaction):
        """Test welcome message"""
        config = await self.db.get_welcome(interaction.guild_id)
        message = config.get('message', Config.WELCOME_DEFAULTS['message'])
        count = interaction.guild.member_count

        embed = self.embeds.welcome_card(interaction.user, interaction.guild, message, count)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="welcome-toggle", description="Enable/disable welcome system")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_toggle(self, interaction: discord.Interaction):
        """Toggle welcome system"""
        config = await self.db.get_welcome(interaction.guild_id)
        config['enabled'] = not config.get('enabled', True)
        await self.db.set(interaction.guild_id, 'welcome', config)

        status = "enabled" if config['enabled'] else "disabled"
        await interaction.response.send_message(
            embed=self.embeds.success("Welcome System", f"Welcome system is now **{status}**."),
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
