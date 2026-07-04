"""Ticket system for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select
from typing import Optional
import asyncio

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class TicketCloseView(View):
    """View for closing tickets"""

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        """Close the ticket"""
        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)
            return

        # Confirm close
        confirm_view = View(timeout=30)

        async def confirm_callback(inter: discord.Interaction):
            await self._close_ticket(inter)

        async def cancel_callback(inter: discord.Interaction):
            await inter.response.send_message("Ticket close cancelled.", ephemeral=True)

        confirm_btn = Button(label="Confirm Close", style=discord.ButtonStyle.danger, emoji="✅")
        confirm_btn.callback = confirm_callback
        cancel_btn = Button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
        cancel_btn.callback = cancel_callback

        confirm_view.add_item(confirm_btn)
        confirm_view.add_item(cancel_btn)

        await interaction.response.send_message(
            "Are you sure you want to close this ticket?",
            view=confirm_view,
            ephemeral=True
        )

    async def _close_ticket(self, interaction: discord.Interaction):
        """Actually close the ticket"""
        channel = interaction.channel
        guild = interaction.guild

        # Get transcript
        config = await self.bot.db.get_tickets(guild.id)
        transcript_channel_id = config.get('transcript_channel')

        if transcript_channel_id:
            transcript_channel = guild.get_channel(transcript_channel_id)
            if transcript_channel:
                # Generate simple transcript
                messages = []
                async for msg in channel.history(limit=500, oldest_first=True):
                    messages.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M')}] {msg.author}: {msg.content}")

                transcript = "\n".join(messages)

                embed = discord.Embed(
                    title=f"📄 Ticket Transcript - {channel.name}",
                    description=f"Closed by {interaction.user.mention}",
                    color=Config.PRIMARY_COLOR,
                    timestamp=discord.utils.utcnow()
                )

                # Send transcript
                if len(transcript) > 1900:
                    from io import BytesIO
                    file = discord.File(BytesIO(transcript.encode()), filename=f"{channel.name}_transcript.txt")
                    await transcript_channel.send(embed=embed, file=file)
                else:
                    embed.add_field(name="Transcript", value=f"```\n{transcript[:1000]}\n```", inline=False)
                    await transcript_channel.send(embed=embed)

        # Delete channel
        await interaction.response.send_message("Closing ticket...")
        await asyncio.sleep(2)
        await channel.delete(reason=f"Ticket closed by {interaction.user}")

class TicketCreateView(View):
    """View for creating tickets"""

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="create_ticket")
    async def create_button(self, interaction: discord.Interaction, button: Button):
        """Create a new ticket"""
        guild = interaction.guild
        user = interaction.user

        config = await self.bot.db.get_tickets(guild.id)

        # Check max tickets
        max_tickets = config.get('max_tickets_per_user', 3)
        user_tickets = [c for c in guild.text_channels if c.name == f'ticket-{user.id}']

        if len(user_tickets) >= max_tickets:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Ticket Limit Reached",
                    description=f"You can only have {max_tickets} open ticket(s) at a time.",
                    color=Config.ERROR_COLOR
                ),
                ephemeral=True
            )
            return

        # Create ticket modal
        modal = TicketModal(self.bot)
        await interaction.response.send_modal(modal)

class TicketModal(Modal):
    """Modal for ticket creation"""

    def __init__(self, bot: commands.Bot):
        super().__init__(title="🎫 Create Support Ticket")
        self.bot = bot

        self.reason = TextInput(
            label="Reason for ticket",
            placeholder="Describe why you need support...",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        )
        self.add_item(self.reason)

        self.category_select = TextInput(
            label="Category",
            placeholder="General, Purchase, Report, Partnership...",
            style=discord.TextStyle.short,
            max_length=50,
            required=True
        )
        self.add_item(self.category_select)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        guild = interaction.guild
        user = interaction.user

        config = await self.bot.db.get_tickets(guild.id)
        category_id = config.get('category')

        category = guild.get_channel(category_id) if category_id else None

        # Create ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        # Add support roles
        support_roles = config.get('support_roles', [])
        for role_id in support_roles:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f'ticket-{user.id}',
            category=category,
            overwrites=overwrites,
            topic=f"Ticket by {user} | Category: {self.category_select.value}"
        )

        # Send ticket info
        embed = discord.Embed(
            title=f"🎫 Ticket - {self.category_select.value}",
            description=f"**User:** {user.mention} (`{user.id}`)\n"
                       f"**Reason:** {self.reason.value}\n"
                       f"**Created:** <t:{int(discord.utils.utcnow().timestamp())}:R>",
            color=Config.INFO_COLOR,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        view = TicketCloseView(self.bot)
        msg = await channel.send(content=user.mention, embed=embed, view=view)
        await msg.pin()

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Ticket Created",
                description=f"Your ticket has been created: {channel.mention}",
                color=Config.SUCCESS_COLOR
            ),
            ephemeral=True
        )

class Tickets(commands.Cog):
    """Ticket management system"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

    @app_commands.command(name="ticket-panel", description="Send the ticket creation panel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        """Send ticket panel"""
        embed = discord.Embed(
            title="🎫 Obsidian Support",
            description="Need help? Click the button below to create a support ticket.\n\n"
                       "**Our team will assist you with:**\n"
                       "• Purchase issues\n"
                       "• Product questions\n"
                       "• Report a user\n"
                       "• Partnership inquiries\n"
                       "• General support",
            color=Config.PRIMARY_COLOR
        )
        embed.set_footer(text="Obsidian Marketplace Support")

        view = TicketCreateView(self.bot)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            embed=self.embeds.success("Panel Sent", "Ticket panel has been posted."),
            ephemeral=True
        )

    @app_commands.command(name="ticket-config", description="Configure ticket system")
    @app_commands.describe(
        category="Category for ticket channels",
        transcript_channel="Channel for ticket transcripts",
        max_per_user="Max tickets per user (default: 3)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_config(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        transcript_channel: Optional[discord.TextChannel] = None,
        max_per_user: Optional[int] = 3
    ):
        """Configure tickets"""
        config = await self.db.get_tickets(interaction.guild_id)

        config['category'] = category.id
        config['max_tickets_per_user'] = max_per_user
        if transcript_channel:
            config['transcript_channel'] = transcript_channel.id

        await self.db.set(interaction.guild_id, 'tickets', config)

        embed = self.embeds.success(
            "Ticket System Configured",
            f"Category: {category.mention}\n"
            f"Max tickets per user: `{max_per_user}`"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ticket-add-role", description="Add a support role")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_add_role(self, interaction: discord.Interaction, role: discord.Role):
        """Add support role"""
        config = await self.db.get_tickets(interaction.guild_id)
        support_roles = config.get('support_roles', [])

        if role.id in support_roles:
            await interaction.response.send_message(
                embed=self.embeds.warning("Already Added", f"{role.mention} is already a support role."),
                ephemeral=True
            )
            return

        support_roles.append(role.id)
        config['support_roles'] = support_roles
        await self.db.set(interaction.guild_id, 'tickets', config)

        await interaction.response.send_message(
            embed=self.embeds.success("Role Added", f"{role.mention} can now view tickets."),
            ephemeral=True
        )

    @app_commands.command(name="ticket-remove-role", description="Remove a support role")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_remove_role(self, interaction: discord.Interaction, role: discord.Role):
        """Remove support role"""
        config = await self.db.get_tickets(interaction.guild_id)
        support_roles = config.get('support_roles', [])

        if role.id not in support_roles:
            await interaction.response.send_message(
                embed=self.embeds.error("Not Found", f"{role.mention} is not a support role."),
                ephemeral=True
            )
            return

        support_roles.remove(role.id)
        config['support_roles'] = support_roles
        await self.db.set(interaction.guild_id, 'tickets', config)

        await interaction.response.send_message(
            embed=self.embeds.success("Role Removed", f"{role.mention} removed from support roles."),
            ephemeral=True
        )

    @app_commands.command(name="close", description="Close the current ticket")
    async def close_ticket(self, interaction: discord.Interaction):
        """Close current ticket"""
        if not interaction.channel.name.startswith('ticket-'):
            await interaction.response.send_message(
                embed=self.embeds.error("Not a Ticket", "This command only works in ticket channels."),
                ephemeral=True
            )
            return

        view = TicketCloseView(self.bot)
        await interaction.response.send_message(
            "Are you sure you want to close this ticket?",
            view=view,
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
