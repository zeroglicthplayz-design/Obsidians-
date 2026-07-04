"""Utility commands for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import time

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class Utility(commands.Cog):
    """General utility commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

    @app_commands.command(name="help", description="Show all available commands")
    async def help_command(self, interaction: discord.Interaction):
        """Show help embed"""
        embed = discord.Embed(
            title="🔮 Obsidian Marketplace Bot",
            description="A premium marketplace management bot for your server.",
            color=Config.PRIMARY_COLOR
        )

        embed.add_field(
            name="🛡️ Moderation",
            value="`/kick` `/ban` `/unban` `/timeout` `/untimeout` `/warn` `/warnings` `/clear-warns` `/purge` `/slowmode` `/lock` `/unlock`",
            inline=False
        )

        embed.add_field(
            name="🎫 Tickets",
            value="`/ticket-panel` `/ticket-config` `/ticket-add-role` `/ticket-remove-role` `/close`",
            inline=False
        )

        embed.add_field(
            name="🛒 Marketplace",
            value="`/listing-create` `/listing-view` `/listing-list` `/listing-edit` `/listing-delete` `/listing-rate`",
            inline=False
        )

        embed.add_field(
            name="💳 Payments",
            value="`/payment-add` `/payment-remove` `/payment-view` `/payment-view-user` `/payment-request` `/payment-methods-info`",
            inline=False
        )

        embed.add_field(
            name="🤖 AutoMod",
            value="`/automod` `/badword` `/automod-stats`",
            inline=False
        )

        embed.add_field(
            name="🛡️ Anti-Nuke",
            value="`/antinuke-config` `/antinuke-whitelist` `/antinuke-status`",
            inline=False
        )

        embed.add_field(
            name="👋 Welcome",
            value="`/welcome-config` `/welcome-test` `/welcome-toggle`",
            inline=False
        )

        embed.add_field(
            name="⚙️ Utility",
            value="`/help` `/ping` `/server-info` `/user-info` `/bot-info` `/rules` `/info-panel`",
            inline=False
        )

        embed.set_footer(text="Obsidian Marketplace • Use / before each command")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        """Check ping"""
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Latency:** `{latency}ms`",
            color=Config.SUCCESS_COLOR if latency < 200 else Config.WARNING_COLOR if latency < 500 else Config.ERROR_COLOR
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="server-info", description="Show server information")
    async def server_info(self, interaction: discord.Interaction):
        """Show server info"""
        guild = interaction.guild

        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=Config.PRIMARY_COLOR
        )

        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        embed.add_field(name="👤 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)

        embed.add_field(name="👥 Members", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="🤖 Bots", value=len([m for m in guild.members if m.bot]), inline=True)
        embed.add_field(name="👤 Humans", value=len([m for m in guild.members if not m.bot]), inline=True)

        embed.add_field(name="💬 Channels", value=f"Text: {len(guild.text_channels)} | Voice: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="🏷️ Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="😀 Emojis", value=str(len(guild.emojis)), inline=True)

        embed.add_field(name="🚀 Boosts", value=f"Level {guild.premium_tier} | {guild.premium_subscription_count} boosts", inline=True)
        embed.add_field(name="🔒 Verification", value=str(guild.verification_level).replace('_', ' ').title(), inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="user-info", description="Show user information")
    @app_commands.describe(member="Member to check (default: you)")
    async def user_info(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Show user info"""
        member = member or interaction.user

        embed = discord.Embed(
            title=f"👤 {member}",
            color=member.color if member.color != discord.Color.default() else Config.PRIMARY_COLOR
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="📅 Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="📆 Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)

        roles = [r.mention for r in member.roles[1:]]  # Exclude @everyone
        embed.add_field(name=f"🏷️ Roles [{len(roles)}]", value=" ".join(roles[:20]) or "None", inline=False)

        embed.add_field(name="🎨 Color", value=str(member.color), inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="🏆 Top Role", value=member.top_role.mention, inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bot-info", description="Show bot information")
    async def bot_info(self, interaction: discord.Interaction):
        """Show bot info"""
        uptime = datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        embed = discord.Embed(
            title="🔮 Obsidian Marketplace Bot",
            description="A premium Discord marketplace management bot.",
            color=Config.PRIMARY_COLOR
        )

        embed.add_field(name="👤 Bot", value=f"{self.bot.user.mention}", inline=True)
        embed.add_field(name="🆔 ID", value=f"`{self.bot.user.id}`", inline=True)
        embed.add_field(name="📅 Uptime", value=f"{days}d {hours}h {minutes}m", inline=True)

        embed.add_field(name="🏠 Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Users", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="📊 Commands", value=str(len(self.bot.tree.get_commands())), inline=True)

        embed.add_field(name="📦 Library", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="⚡ Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🔧 Prefix", value=f"`{Config.PREFIX}`", inline=True)

        embed.set_footer(text="Obsidian Marketplace • Made with 💜")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rules", description="Display server rules")
    async def rules(self, interaction: discord.Interaction):
        """Show rules"""
        embed = self.embeds.rules_embed()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="info-panel", description="Send the server info panel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def info_panel(self, interaction: discord.Interaction):
        """Send info panel"""
        embed = self.embeds.info_embed(interaction.guild)

        # Add official links section
        embed.add_field(
            name="🌐 Official Links",
            value="**Discord Server:** discord.gg/obsidian\n"
                  "**Website:** obsidianmarket.place\n"
                  "**Support:** Click the Support button in #support",
            inline=False
        )

        embed.add_field(
            name="🎖️ How to Earn Roles",
            value="**@Member** — link your account to verify\n"
                  "**@Seller / @Buyer** — list or buy a product\n"
                  "**@Top Seller / @Top Buyer** — top sellers & buyers each period\n"
                  "**@Supreme Seller [10+] / @Supreme Buyer [10+]** — supreme tier (highest volume)\n"
                  "**@Partner** — partnered studios/communities\n"
                  "**@Server Booster** — boost the server",
            inline=False
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            embed=self.embeds.success("Panel Sent", "Info panel has been posted."),
            ephemeral=True
        )

    @app_commands.command(name="set-logs", description="Set the logs channel")
    @app_commands.describe(channel="Channel for bot logs")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set logs channel"""
        await self.db.set(interaction.guild_id, 'logs_channel', channel.id)

        await interaction.response.send_message(
            embed=self.embeds.success("Logs Channel Set", f"Logs will be sent to {channel.mention}."),
            ephemeral=True
        )

    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(member="Member to get avatar of (default: you)")
    async def avatar(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        """Get avatar"""
        member = member or interaction.user

        embed = discord.Embed(
            title=f"🖼️ {member.name}'s Avatar",
            color=Config.PRIMARY_COLOR
        )
        embed.set_image(url=member.display_avatar.url)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Open in Browser", url=member.display_avatar.url, style=discord.ButtonStyle.link))

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="member-count", description="Show server member count")
    async def member_count(self, interaction: discord.Interaction):
        """Show member count"""
        guild = interaction.guild

        embed = discord.Embed(
            title=f"👥 {guild.name} Members",
            description=f"**Total:** `{guild.member_count}`\n"
                       f"**Humans:** `{len([m for m in guild.members if not m.bot])}`\n"
                       f"**Bots:** `{len([m for m in guild.members if m.bot])}`",
            color=Config.PRIMARY_COLOR
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
