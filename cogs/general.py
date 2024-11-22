import discord
from discord.ext import commands
from discord.ext.commands import Context


class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="Display a list of commands.",
    )
    async def help(self, context: Context) -> None:
        """
        Display a list of commands.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title="Help",
            description="Available commands:",
            color=0x9C84EF,
        )
        for command in self.bot.commands:
            embed.add_field(
                name=f"/{command.name}",
                value=command.description,
                inline=False,
            )
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="Check the bot's ping value.",
    )
    async def ping(self, context: Context) -> None:
        """
        Check the bot's ping value.

        :param context: The hybrid command context.
        """
        await context.send(f"Pong! {round(self.bot.latency * 1000)}ms")


async def setup(bot):
    await bot.add_cog(General(bot))
