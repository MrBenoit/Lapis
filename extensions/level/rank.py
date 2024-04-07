import disnake
from disnake.ext import commands

from core.checker import *


class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Ваша карточка рейтинга")
    async def rank(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member = commands.Param(name="пользователь", default=None),
    ) -> None:
        target = member
        if member is None:
            target = interaction.author

        if await defaultMemberChecker(interaction=interaction, member=target) is False:
            return

        file = await getRankCard(member=target)
        await interaction.response.send_message(file=file)


def setup(bot):
    bot.add_cog(Rank(bot))
