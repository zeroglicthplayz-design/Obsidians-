"""Stock/Product system for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from datetime import datetime

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class StockListing:
    """Represents a marketplace listing"""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data.get('name')
        self.description = data.get('description')
        self.price = data.get('price', 0.0)
        self.stock = data.get('stock', 0)
        self.seller_id = data.get('seller_id')
        self.category = data.get('category', 'General')
        self.image = data.get('image')
        self.created_at = data.get('created_at')
        self.sold = data.get('sold', 0)
        self.rating = data.get('rating', [])

class Stocks(commands.Cog):
    """Marketplace stock/listing management"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

    async def _get_next_id(self, guild_id: int) -> int:
        """Get next listing ID"""
        listings = await self.db.get(guild_id, 'listings', [])
        if not listings:
            return 1
        return max(l['id'] for l in listings) + 1

    async def _get_listing(self, guild_id: int, listing_id: int) -> Optional[StockListing]:
        """Get a specific listing"""
        listings = await self.db.get(guild_id, 'listings', [])
        for l in listings:
            if l['id'] == listing_id:
                return StockListing(l)
        return None

    async def _save_listing(self, guild_id: int, listing: dict):
        """Save or update a listing"""
        listings = await self.db.get(guild_id, 'listings', [])

        # Update existing or add new
        for i, l in enumerate(listings):
            if l['id'] == listing['id']:
                listings[i] = listing
                break
        else:
            listings.append(listing)

        await self.db.set(guild_id, 'listings', listings)

    @app_commands.command(name="listing-create", description="Create a new marketplace listing")
    @app_commands.describe(
        name="Product name",
        price="Product price in USD",
        stock="Amount in stock",
        description="Product description",
        category="Product category"
    )
    async def listing_create(
        self,
        interaction: discord.Interaction,
        name: str,
        price: float,
        stock: int,
        description: str,
        category: Optional[str] = "General"
    ):
        """Create a marketplace listing"""
        listing_id = await self._get_next_id(interaction.guild_id)

        listing = {
            'id': listing_id,
            'name': name,
            'description': description,
            'price': price,
            'stock': stock,
            'seller_id': interaction.user.id,
            'category': category,
            'created_at': str(datetime.utcnow()),
            'sold': 0,
            'rating': []
        }

        await self._save_listing(interaction.guild_id, listing)

        embed = self.embeds.stock_listing(
            name, price, description, 
            interaction.user.mention, stock
        )
        embed.add_field(name="📋 Listing ID", value=f"`#{listing_id}`", inline=True)
        embed.add_field(name="🏷️ Category", value=category, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(datetime.utcnow().timestamp())}:R>", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="listing-view", description="View a marketplace listing")
    @app_commands.describe(listing_id="The ID of the listing to view")
    async def listing_view(self, interaction: discord.Interaction, listing_id: int):
        """View a listing"""
        listing = await self._get_listing(interaction.guild_id, listing_id)

        if not listing:
            await interaction.response.send_message(
                embed=self.embeds.error("Not Found", f"Listing `#{listing_id}` does not exist."),
                ephemeral=True
            )
            return

        seller = interaction.guild.get_member(listing.seller_id)
        seller_name = seller.mention if seller else "Unknown"

        embed = self.embeds.stock_listing(
            listing.name, listing.price, listing.description,
            seller_name, listing.stock
        )
        embed.add_field(name="📋 ID", value=f"`#{listing.id}`", inline=True)
        embed.add_field(name="🏷️ Category", value=listing.category, inline=True)
        embed.add_field(name="📊 Sold", value=str(listing.sold), inline=True)

        if listing.rating:
            avg_rating = sum(listing.rating) / len(listing.rating)
            embed.add_field(name="⭐ Rating", value=f"{avg_rating:.1f}/5 ({len(listing.rating)} reviews)", inline=True)

        # Add purchase button
        view = discord.ui.View(timeout=None)
        purchase_btn = discord.ui.Button(
            label="Purchase",
            style=discord.ButtonStyle.success,
            emoji="🛒",
            custom_id=f"purchase_{listing_id}"
        )

        async def purchase_callback(inter: discord.Interaction):
            if listing.stock <= 0:
                await inter.response.send_message(
                    embed=self.embeds.error("Out of Stock", "This item is currently unavailable."),
                    ephemeral=True
                )
                return

            # Create purchase thread/DM
            seller = inter.guild.get_member(listing.seller_id)

            embed = discord.Embed(
                title=f"🛒 Purchase Request - {listing.name}",
                description=f"**Buyer:** {inter.user.mention}\n"
                           f"**Seller:** {seller.mention if seller else 'Unknown'}\n"
                           f"**Price:** `${listing.price:.2f}`\n\n"
                           f"A private channel has been created for this transaction.",
                color=Config.SUCCESS_COLOR
            )

            await inter.response.send_message(embed=embed, ephemeral=True)

            # Create private thread
            if hasattr(inter.channel, 'create_thread'):
                thread = await inter.channel.create_thread(
                    name=f"deal-{listing_id}-{inter.user.id}",
                    type=discord.ChannelType.private_thread
                )
                await thread.add_user(inter.user)
                if seller:
                    await thread.add_user(seller)

                await thread.send(
                    f"🛒 **Purchase initiated!**\n"
                    f"Buyer: {inter.user.mention}\n"
                    f"Seller: {seller.mention if seller else 'Unknown'}\n"
                    f"Listing: `#{listing_id}` - {listing.name}\n"
                    f"Price: `${listing.price:.2f}`\n\n"
                    f"Please coordinate payment and delivery here."
                )

        purchase_btn.callback = purchase_callback
        view.add_item(purchase_btn)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="listing-list", description="List all marketplace listings")
    @app_commands.describe(category="Filter by category")
    async def listing_list(self, interaction: discord.Interaction, category: Optional[str] = None):
        """List all listings"""
        listings = await self.db.get(interaction.guild_id, 'listings', [])

        if category:
            listings = [l for l in listings if l['category'].lower() == category.lower()]

        if not listings:
            await interaction.response.send_message(
                embed=self.embeds.info("No Listings", "No listings found." if not category else f"No listings in category `{category}`."),
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🛒 Obsidian Marketplace Listings",
            description=f"Total: {len(listings)} listings" + (f" in `{category}`" if category else ""),
            color=Config.GOLD_COLOR
        )

        for listing in listings[:25]:  # Max 25 fields
            seller = interaction.guild.get_member(listing['seller_id'])
            seller_name = seller.name if seller else "Unknown"

            value = f"💰 `${listing['price']:.2f}` | 📦 `{listing['stock']}` left | 👤 {seller_name}"
            embed.add_field(
                name=f"#{listing['id']} - {listing['name']}",
                value=value,
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="listing-edit", description="Edit your listing")
    @app_commands.describe(
        listing_id="ID of listing to edit",
        name="New name (optional)",
        price="New price (optional)",
        stock="New stock (optional)",
        description="New description (optional)"
    )
    async def listing_edit(
        self,
        interaction: discord.Interaction,
        listing_id: int,
        name: Optional[str] = None,
        price: Optional[float] = None,
        stock: Optional[int] = None,
        description: Optional[str] = None
    ):
        """Edit a listing"""
        listing = await self._get_listing(interaction.guild_id, listing_id)

        if not listing:
            await interaction.response.send_message(
                embed=self.embeds.error("Not Found", f"Listing `#{listing_id}` does not exist."),
                ephemeral=True
            )
            return

        if listing.seller_id != interaction.user.id:
            await interaction.response.send_message(
                embed=self.embeds.error("Permission Denied", "You can only edit your own listings."),
                ephemeral=True
            )
            return

        listing_data = {
            'id': listing.id,
            'name': name or listing.name,
            'description': description or listing.description,
            'price': price if price is not None else listing.price,
            'stock': stock if stock is not None else listing.stock,
            'seller_id': listing.seller_id,
            'category': listing.category,
            'created_at': listing.created_at,
            'sold': listing.sold,
            'rating': listing.rating
        }

        await self._save_listing(interaction.guild_id, listing_data)

        await interaction.response.send_message(
            embed=self.embeds.success("Listing Updated", f"Listing `#{listing_id}` has been updated."),
            ephemeral=True
        )

    @app_commands.command(name="listing-delete", description="Delete your listing")
    @app_commands.describe(listing_id="ID of listing to delete")
    async def listing_delete(self, interaction: discord.Interaction, listing_id: int):
        """Delete a listing"""
        listing = await self._get_listing(interaction.guild_id, listing_id)

        if not listing:
            await interaction.response.send_message(
                embed=self.embeds.error("Not Found", f"Listing `#{listing_id}` does not exist."),
                ephemeral=True
            )
            return

        if listing.seller_id != interaction.user.id:
            await interaction.response.send_message(
                embed=self.embeds.error("Permission Denied", "You can only delete your own listings."),
                ephemeral=True
            )
            return

        listings = await self.db.get(interaction.guild_id, 'listings', [])
        listings = [l for l in listings if l['id'] != listing_id]
        await self.db.set(interaction.guild_id, 'listings', listings)

        await interaction.response.send_message(
            embed=self.embeds.success("Listing Deleted", f"Listing `#{listing_id}` has been removed."),
            ephemeral=True
        )

    @app_commands.command(name="listing-rate", description="Rate a listing")
    @app_commands.describe(listing_id="ID of listing", rating="Rating 1-5", review="Optional review text")
    @app_commands.choices(rating=[
        app_commands.Choice(name="⭐", value=1),
        app_commands.Choice(name="⭐⭐", value=2),
        app_commands.Choice(name="⭐⭐⭐", value=3),
        app_commands.Choice(name="⭐⭐⭐⭐", value=4),
        app_commands.Choice(name="⭐⭐⭐⭐⭐", value=5)
    ])
    async def listing_rate(
        self,
        interaction: discord.Interaction,
        listing_id: int,
        rating: app_commands.Choice[int],
        review: Optional[str] = None
    ):
        """Rate a listing"""
        listing = await self._get_listing(interaction.guild_id, listing_id)

        if not listing:
            await interaction.response.send_message(
                embed=self.embeds.error("Not Found", f"Listing `#{listing_id}` does not exist."),
                ephemeral=True
            )
            return

        if listing.seller_id == interaction.user.id:
            await interaction.response.send_message(
                embed=self.embeds.error("Invalid", "You cannot rate your own listing."),
                ephemeral=True
            )
            return

        listing_data = {
            'id': listing.id,
            'name': listing.name,
            'description': listing.description,
            'price': listing.price,
            'stock': listing.stock,
            'seller_id': listing.seller_id,
            'category': listing.category,
            'created_at': listing.created_at,
            'sold': listing.sold,
            'rating': listing.rating + [rating.value]
        }

        await self._save_listing(interaction.guild_id, listing_data)

        stars = "⭐" * rating.value
        await interaction.response.send_message(
            embed=self.embeds.success("Rating Submitted", f"You rated `{listing.name}` {stars}"),
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))
