from discord.ext import commands
from discord.ext.commands import Context


class Sync(commands.Cog, name="Sync"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="sync",
        description="Sync command",
        aliases=["s"],
    )
    async def sync(self, context: Context) -> None:
        """
        /sync commands: Sync commands globally
        /sync status: Sync status globally

        :param context: The context of the message that was sent.
        """
        if context.author.id != 226674196112080896:
            await context.send("You are not allowed to use this command.")
            return

        self.bot.logger.info("Syncing commands globally...")
        await self.bot.tree.sync()


async def setup(bot):
    await bot.add_cog(Sync(bot))
