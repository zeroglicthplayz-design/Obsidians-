"""Payment system for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class PaymentMethod:
    """Represents a user's payment method"""
    def __init__(self, data: dict):
        self.user_id = data.get('user_id')
        self.methods = data.get('methods', {})

class Payments(commands.Cog):
    """Payment method management"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

    async def _get_user_payments(self, guild_id: int, user_id: int) -> dict:
        """Get user's payment methods"""
        payments = await self.db.get(guild_id, 'payments', {})
        return payments.get(str(user_id), {})

    async def _set_user_payment(self, guild_id: int, user_id: int, method: str, info: str):
        """Set user's payment method"""
        payments = await self.db.get(guild_id, 'payments', {})

        if str(user_id) not in payments:
            payments[str(user_id)] = {}

        payments[str(user_id)][method] = info
        await self.db.set(guild_id, 'payments', payments)

    async def _remove_user_payment(self, guild_id: int, user_id: int, method: str):
        """Remove user's payment method"""
        payments = await self.db.get(guild_id, 'payments', {})

        if str(user_id) in payments:
            payments[str(user_id)].pop(method, None)
            await self.db.set(guild_id, 'payments', payments)

    @app_commands.command(name="payment-add", description="Add a payment method")
    @app_commands.describe(
        method="Payment method type",
        info="Your payment info (username, email, wallet address, etc.)"
    )
    @app_commands.choices(method=[
        app_commands.Choice(name="💳 PayPal", value="paypal"),
        app_commands.Choice(name="💵 CashApp", value="cashapp"),
        app_commands.Choice(name="💸 Venmo", value="venmo"),
        app_commands.Choice(name="₿ Cryptocurrency", value="crypto"),
        app_commands.Choice(name="🎮 Robux", value="robux"),
        app_commands.Choice(name="🎁 Gift Card", value="giftcard"),
        app_commands.Choice(name="🏦 Bank Transfer", value="bank"),
        app_commands.Choice(name="💎 Other", value="other")
    ])
    async def payment_add(
        self,
        interaction: discord.Interaction,
        method: app_commands.Choice[str],
        info: str
    ):
        """Add a payment method"""
        await self._set_user_payment(interaction.guild_id, interaction.user.id, method.value, info)

        embed = self.embeds.payment(
            "Payment Method Added",
            f"**Method:** {method.name}\n"
            f"**Info:** `{info}`\n\n"
            f"Buyers can now see this when purchasing your listings."
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="payment-remove", description="Remove a payment method")
    @app_commands.choices(method=[
        app_commands.Choice(name="💳 PayPal", value="paypal"),
        app_commands.Choice(name="💵 CashApp", value="cashapp"),
        app_commands.Choice(name="💸 Venmo", value="venmo"),
        app_commands.Choice(name="₿ Cryptocurrency", value="crypto"),
        app_commands.Choice(name="🎮 Robux", value="robux"),
        app_commands.Choice(name="🎁 Gift Card", value="giftcard"),
        app_commands.Choice(name="🏦 Bank Transfer", value="bank"),
        app_commands.Choice(name="💎 Other", value="other")
    ])
    async def payment_remove(self, interaction: discord.Interaction, method: app_commands.Choice[str]):
        """Remove a payment method"""
        await self._remove_user_payment(interaction.guild_id, interaction.user.id, method.value)

        await interaction.response.send_message(
            embed=self.embeds.success("Removed", f"{method.name} has been removed from your payment methods."),
            ephemeral=True
        )

    @app_commands.command(name="payment-view", description="View your payment methods")
    async def payment_view(self, interaction: discord.Interaction):
        """View your payment methods"""
        methods = await self._get_user_payments(interaction.guild_id, interaction.user.id)

        if not methods:
            await interaction.response.send_message(
                embed=self.embeds.info("No Methods", "You haven't added any payment methods yet. Use `/payment-add` to add one."),
                ephemeral=True
            )
            return

        embed = self.embeds.payment("Your Payment Methods", "These are visible to buyers when they purchase your listings.")

        method_names = {
            'paypal': '💳 PayPal',
            'cashapp': '💵 CashApp',
            'venmo': '💸 Venmo',
            'crypto': '₿ Cryptocurrency',
            'robux': '🎮 Robux',
            'giftcard': '🎁 Gift Card',
            'bank': '🏦 Bank Transfer',
            'other': '💎 Other'
        }

        for method, info in methods.items():
            name = method_names.get(method, method)
            embed.add_field(name=name, value=f"`{info}`", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="payment-view-user", description="View a user's payment methods (for transactions)")
    @app_commands.describe(user="The user to view payment methods for")
    async def payment_view_user(self, interaction: discord.Interaction, user: discord.Member):
        """View another user's payment methods"""
        methods = await self._get_user_payments(interaction.guild_id, user.id)

        if not methods:
            await interaction.response.send_message(
                embed=self.embeds.error("No Methods", f"{user.mention} has no payment methods set up."),
                ephemeral=True
            )
            return

        embed = self.embeds.payment(
            f"{user.name}'s Payment Methods",
            f"Use these to complete your transaction with {user.mention}."
        )

        method_names = {
            'paypal': '💳 PayPal',
            'cashapp': '💵 CashApp',
            'venmo': '💸 Venmo',
            'crypto': '₿ Cryptocurrency',
            'robux': '🎮 Robux',
            'giftcard': '🎁 Gift Card',
            'bank': '🏦 Bank Transfer',
            'other': '💎 Other'
        }

        for method, info in methods.items():
            name = method_names.get(method, method)
            embed.add_field(name=name, value=f"`{info}`", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="payment-request", description="Request payment from a user")
    @app_commands.describe(
        user="User to request payment from",
        amount="Amount to request",
        reason="Reason for payment",
        method="Preferred payment method"
    )
    async def payment_request(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: float,
        reason: str,
        method: Optional[str] = None
    ):
        """Request payment from a user"""
        embed = discord.Embed(
            title=f"💰 Payment Request",
            description=f"**From:** {interaction.user.mention}\n"
                       f"**To:** {user.mention}\n"
                       f"**Amount:** `${amount:.2f}`\n"
                       f"**Reason:** {reason}",
            color=Config.GOLD_COLOR
        )

        if method:
            embed.add_field(name="Preferred Method", value=method, inline=False)

        embed.set_footer(text="Click the button below to confirm payment")

        view = discord.ui.View(timeout=86400)  # 24 hours

        async def confirm_callback(inter: discord.Interaction):
            if inter.user.id != user.id:
                await inter.response.send_message("Only the requested user can confirm!", ephemeral=True)
                return

            confirm_embed = discord.Embed(
                title="✅ Payment Confirmed",
                description=f"{user.mention} has confirmed payment of `${amount:.2f}` to {interaction.user.mention}.",
                color=Config.SUCCESS_COLOR
            )
            await inter.response.send_message(embed=confirm_embed)

        async def decline_callback(inter: discord.Interaction):
            if inter.user.id != user.id:
                await inter.response.send_message("Only the requested user can decline!", ephemeral=True)
                return

            decline_embed = discord.Embed(
                title="❌ Payment Declined",
                description=f"{user.mention} has declined the payment request.",
                color=Config.ERROR_COLOR
            )
            await inter.response.send_message(embed=decline_embed)

        confirm_btn = discord.ui.Button(label="Confirm Payment", style=discord.ButtonStyle.success, emoji="✅")
        confirm_btn.callback = confirm_callback
        decline_btn = discord.ui.Button(label="Decline", style=discord.ButtonStyle.danger, emoji="❌")
        decline_btn.callback = decline_callback

        view.add_item(confirm_btn)
        view.add_item(decline_btn)

        await interaction.response.send_message(content=user.mention, embed=embed, view=view)

    @app_commands.command(name="payment-methods-info", description="View supported payment methods")
    async def payment_methods_info(self, interaction: discord.Interaction):
        """Show supported payment methods"""
        embed = discord.Embed(
            title="💳 Supported Payment Methods",
            description="Obsidian Marketplace supports the following payment methods:",
            color=Config.PRIMARY_COLOR
        )

        methods = [
            ("💳 PayPal", "Send money via PayPal. Most common for online transactions."),
            ("💵 CashApp", "Quick and easy peer-to-peer payments."),
            ("💸 Venmo", "Popular for US-based transactions."),
            ("₿ Cryptocurrency", "Bitcoin, Ethereum, and other crypto payments."),
            ("🎮 Robux", "Roblox in-game currency for Roblox-related deals."),
            ("🎁 Gift Cards", "Amazon, Steam, Roblox, and other gift cards."),
            ("🏦 Bank Transfer", "Direct bank transfers (use with trusted users only)."),
            ("💎 Other", "Any other agreed-upon method between buyer and seller.")
        ]

        for name, desc in methods:
            embed.add_field(name=name, value=desc, inline=False)

        embed.add_field(
            name="⚠️ Important",
            value="All payments are handled manually between users. Obsidian is not liable for scams or fraud. Transact at your own risk.",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Payments(bot))
