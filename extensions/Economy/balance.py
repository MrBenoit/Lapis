import disnake
from disnake.ext import commands

from core import *


class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="balance", description="Проверить баланс")
    async def balance(
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

        db = await database(target)

        authorDB = db[0]
        globalAuthorDB = db[2]

        premiumTime = "Нет действующей подписки"
        if globalAuthorDB.prem_time is not None:
            premiumTime = (
                f"Закончится в {disnake.utils.format_dt(globalAuthorDB.prem_time, 'F')}, \n"
                f"{disnake.utils.format_dt(globalAuthorDB.prem_time, 'R')}"
            )

        embed = disnake.Embed(
            color=EmbedColor.MAIN_COLOR.value,
        )
        embed.set_author(name=target.name, icon_url=target.avatar.url)
        embed.add_field(
            name=f"> {EmbedEmoji.SILVER_COIN.value} Серебряные монеты",
            value=f"```{authorDB.currency:,}```",
            inline=True,
        )
        embed.add_field(
            name=f"> {EmbedEmoji.GOLD_COIN.value} Золотые монеты",
            value=f" ```{globalAuthorDB.donate:,}```",
            inline=True,
        )
        embed.add_field(
            name=f"> {EmbedEmoji.GOLD_COIN.value} Премиум подписка",
            value=premiumTime,
            inline=False,
        )
        await interaction.send(embed=embed, ephemeral=True)
        return


def setup(bot):
    bot.add_cog(Balance(bot))
