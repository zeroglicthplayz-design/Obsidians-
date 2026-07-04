"""Owner-only commands for Obsidian Marketplace"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from utils.config import Config
from utils.embeds import ObsidianEmbeds

class Owner(commands.Cog):
    """Owner commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.embeds = bot.embeds

    async def cog_check(self, ctx):
        """Only owners can use these commands"""
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cog(self, ctx: commands.Context, cog: str):
        """Reload a cog"""
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await ctx.send(embed=self.embeds.success("Cog Reloaded", f"`cogs.{cog}` has been reloaded."))
        except Exception as e:
            await ctx.send(embed=self.embeds.error("Error", f"```py\n{e}\n```"))

    @commands.command(name="load")
    @commands.is_owner()
    async def load_cog(self, ctx: commands.Context, cog: str):
        """Load a cog"""
        try:
            await self.bot.load_extension(f"cogs.{cog}")
            await ctx.send(embed=self.embeds.success("Cog Loaded", f"`cogs.{cog}` has been loaded."))
        except Exception as e:
            await ctx.send(embed=self.embeds.error("Error", f"```py\n{e}\n```"))

    @commands.command(name="unload")
    @commands.is_owner()
    async def unload_cog(self, ctx: commands.Context, cog: str):
        """Unload a cog"""
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
            await ctx.send(embed=self.embeds.success("Cog Unloaded", f"`cogs.{cog}` has been unloaded."))
        except Exception as e:
            await ctx.send(embed=self.embeds.error("Error", f"```py\n{e}\n```"))

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context, guild_id: str = None):
        """Sync slash commands"""
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            synced = await self.bot.tree.sync(guild=guild)
            await ctx.send(embed=self.embeds.success("Synced", f"Synced `{len(synced)}` commands to guild `{guild_id}`."))
        else:
            synced = await self.bot.tree.sync()
            await ctx.send(embed=self.embeds.success("Synced", f"Synced `{len(synced)}` global commands."))

    @commands.command(name="eval")
    @commands.is_owner()
    async def eval_code(self, ctx: commands.Context, *, code: str):
        """Evaluate Python code"""
        import io
        import textwrap
        import traceback

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            'message': ctx.message,
            'discord': discord,
            'db': self.db
        }

        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(code, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                await ctx.send(f"```py\n{value}{ret}\n```")

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        """Shutdown the bot"""
        await ctx.send(embed=self.embeds.warning("Shutting Down", "Goodbye! 👋"))
        await self.bot.close()

    @commands.command(name="status")
    @commands.is_owner()
    async def set_status(self, ctx: commands.Context, *, status: str):
        """Set bot status"""
        await self.bot.change_presence(activity=discord.Game(name=status))
        await ctx.send(embed=self.embeds.success("Status Updated", f"Status set to: `{status}`"))

from contextlib import redirect_stdout

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))
