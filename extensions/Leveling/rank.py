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
    ):
        target = None
        if member is None or member == interaction.author:
            target = interaction.author
        elif member.id != interaction.author.id:
            target = member

        if await defaultMemberChecker(interaction, target) is False:
            return

        user = interaction.author or member
        file = await getRankCard(interaction.guild, user)
        await interaction.response.send_message(file=file)


def setup(bot):
    bot.add_cog(Rank(bot))
