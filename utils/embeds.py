"""Custom embed builder for Obsidian Marketplace"""
import discord
from datetime import datetime
from utils.config import Config

class ObsidianEmbeds:
    """Create styled embeds matching Obsidian theme"""

    def __init__(self):
        self.footer = "🔮 Obsidian Marketplace"
        self.icon_url = None  # Set your bot avatar URL here

    def _base(self, title: str = None, description: str = None, color: int = Config.PRIMARY_COLOR) -> discord.Embed:
        """Base embed with Obsidian styling"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=self.footer, icon_url=self.icon_url)
        return embed

    def success(self, title: str, description: str = None) -> discord.Embed:
        """Success embed"""
        return self._base(
            f"{Config.EMOJI_CHECK} {title}",
            description,
            Config.SUCCESS_COLOR
        )

    def error(self, title: str, description: str = None) -> discord.Embed:
        """Error embed"""
        return self._base(
            f"{Config.EMOJI_X} {title}",
            description,
            Config.ERROR_COLOR
        )

    def warning(self, title: str, description: str = None) -> discord.Embed:
        """Warning embed"""
        return self._base(
            f"{Config.EMOJI_WARNING} {title}",
            description,
            Config.WARNING_COLOR
        )

    def info(self, title: str, description: str = None) -> discord.Embed:
        """Info embed"""
        return self._base(
            f"{Config.EMOJI_INFO} {title}",
            description,
            Config.INFO_COLOR
        )

    def shield(self, title: str, description: str = None) -> discord.Embed:
        """Security/Anti-nuke embed"""
        return self._base(
            f"{Config.EMOJI_SHIELD} {title}",
            description,
            Config.PRIMARY_COLOR
        )

    def marketplace(self, title: str, description: str = None) -> discord.Embed:
        """Marketplace listing embed"""
        embed = self._base(title, description, Config.GOLD_COLOR)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/placeholder/obsidian.png")
        return embed

    def ticket(self, title: str, description: str = None) -> discord.Embed:
        """Ticket embed"""
        return self._base(
            f"{Config.EMOJI_TICKET} {title}",
            description,
            Config.INFO_COLOR
        )

    def payment(self, title: str, description: str = None) -> discord.Embed:
        """Payment method embed"""
        return self._base(
            f"{Config.EMOJI_MONEY} {title}",
            description,
            Config.SUCCESS_COLOR
        )

    def automod(self, title: str, description: str = None) -> discord.Embed:
        """AutoMod action embed"""
        return self._base(
            f"{Config.EMOJI_HAMMER} {title}",
            description,
            Config.WARNING_COLOR
        )

    def welcome_card(self, member: discord.Member, guild: discord.Guild, message: str, count: int) -> discord.Embed:
        """Welcome card embed"""
        embed = discord.Embed(
            title=f"Welcome to {guild.name}",
            description=message.format(
                user=member.mention,
                server=guild.name,
                count=count,
                username=member.name
            ),
            color=Config.PRIMARY_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url="https://cdn.discordapp.com/attachments/placeholder/welcome_banner.png")
        embed.set_footer(text=f"Member #{count} | {self.footer}", icon_url=self.icon_url)
        return embed

    def stock_listing(self, name: str, price: float, description: str, seller: str, stock: int) -> discord.Embed:
        """Product/stock listing embed"""
        embed = discord.Embed(
            title=f"{Config.EMOJI_CART} {name}",
            description=description,
            color=Config.GOLD_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💰 Price", value=f"`${price:.2f}`", inline=True)
        embed.add_field(name="📦 Stock", value=f"`{stock}` available", inline=True)
        embed.add_field(name="👤 Seller", value=seller, inline=True)
        embed.set_footer(text=self.footer, icon_url=self.icon_url)
        return embed

    def antinuke_alert(self, action: str, target: str, reason: str) -> discord.Embed:
        """Anti-nuke alert embed"""
        embed = discord.Embed(
            title=f"{Config.EMOJI_SHIELD} ANTI-NUKE TRIGGERED",
            description=f"**Action:** {action}\n**Target:** {target}\n**Reason:** {reason}",
            color=Config.ERROR_COLOR,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Obsidian Security System", icon_url=self.icon_url)
        return embed

    def rules_embed(self) -> discord.Embed:
        """Server rules embed (inspired by DevOutlet)"""
        embed = discord.Embed(
            title="📜 Obsidian Marketplace Rules",
            description="Read carefully — using Obsidian Marketplace means you accept all of the following.",
            color=Config.PRIMARY_COLOR
        )

        rules = [
            ("1. Account Verification", "Your account must be verified. Alternate accounts are not permitted."),
            ("2. Ownership of Listings", "You must hold 100% rights to anything you list. Selling leaked or stolen assets is forbidden."),
            ("3. Accurate Listings", "Your title, price, and visuals must honestly represent the product."),
            ("4. No Malicious Code", "Backdoors, viruses, loggers, or obfuscated malicious code result in an immediate ban."),
            ("5. Categories & Spam", "Pick the correct category. Reposting the same product across categories is spam."),
            ("6. Serious Buyers Only", "Only click 'Purchase' if you have the funds and intend to complete the deal."),
            ("7. Keep Deals In-Server", "All transactions must happen within this server."),
            ("8. No Star Manipulation", "Inflating a listing's rating with alts or vote-buying will result in removal."),
            ("9. Professional Conduct", "Be respectful. Harassment, slurs, threats, or doxxing will not be tolerated."),
            ("10. Platform Only", "Obsidian provides a platform to connect buyers and sellers. We are not a party to any transaction."),
            ("11. No Liability", "All payments are handled manually between users. You transact at your own risk."),
            ("12. Products As-Is", "We may briefly check files, but we do not fully audit every product.")
        ]

        for title, desc in rules:
            embed.add_field(name=title, value=desc, inline=False)

        embed.set_footer(text=self.footer, icon_url=self.icon_url)
        return embed

    def info_embed(self, guild: discord.Guild) -> discord.Embed:
        """Server info embed"""
        embed = discord.Embed(
            title=f"🚀 How to Use Obsidian Marketplace",
            color=Config.PRIMARY_COLOR
        )

        embed.add_field(
            name="1. Verify",
            value="Link your account to automatically receive your access role.",
            inline=False
        )
        embed.add_field(
            name="2. Post a Product",
            value="Go to #support and click **Post** to start on the website, or list directly at our store.",
            inline=False
        )
        embed.add_field(
            name="3. Buy a Product",
            value="Click the **Purchase** button on any active listing. This opens a private space to coordinate payment.",
            inline=False
        )

        embed.add_field(
            name="🤝 Partnerships",
            value="Check out our verified network of trusted development studios and communities.",
            inline=False
        )

        embed.set_footer(text=f"{guild.name} • obsidianmarket.place", icon_url=self.icon_url)
        return embed
