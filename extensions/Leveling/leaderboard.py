import disnake
from disnake.ext import commands

from sqlalchemy import select, delete, func
from sqlalchemy import and_, desc
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import aggregate_order_by

from core.vars import *
from core.models import *
from core.checker import *
from core.vars import EmbedEmoji
from core.vars import EmbedColor

CARD_NAME = {
    0: "Стандартная карточка рейтинга",
    1: "Зеленый космос",
    2: "Фиолетовая материя",
    3: "Крепкая любовь",
}

SELECT = ["по уровню", "по монетам"]


async def CurrencyLeaderboard(user, users_top_list):
    top = [i.user_id for i in users_top_list]
    my_rank = top.index(user.user_id) + 1
    top_rank = {1: "🥇", 2: "🥈", 3: "🥉"}
    my_top = f"{top_rank.get(my_rank, '#')}{my_rank}"

    embed = disnake.Embed(
        title="Таблица лидеров по серебреных монетам",
        description=(
            f"Ты: **{my_top}** - <@{user.user_id}> \n"
            f"Баланс: **{user.currency:,} {EmbedEmoji.SILVER_COIN.value}** \n"
            "-----------------------------------------"
        ),
        color=EmbedColor.MAIN_COLOR.value,
    )

    for rank, any_user in enumerate(users_top_list[:10], start=1):
        user_top = f"{top_rank.get(rank, '#')}{rank}"
        currency = f"{any_user.currency:,}"

        embed.add_field(
            name="_ _",
            value=(
                f"**{user_top}** - <@{any_user.user_id}>"
                f"\nБаланс: **{currency} {EmbedEmoji.SILVER_COIN.value}**"
            ),
            inline=False,
        )
    return embed


async def LevelLeaderboard(user, users_top_list):
    top = [i.user_id for i in users_top_list]
    my_rank = top.index(user.user_id) + 1
    top_rank = {1: "🥇", 2: "🥈", 3: "🥉"}
    my_top = f"{top_rank.get(my_rank, '#')}{my_rank}"

    embed = disnake.Embed(
        title="Таблица лидеров по уровню",
        description=(
            f"Ты: **{my_top}** - <@{user.user_id}> \n"
            f"Уровень: **{user.level}** \n"
            f"Опыт: **{user.exp}** / **{5 * (user.level ** 2) + (50 * user.level) + 100}** \n"
            "-----------------------------------------"
        ),
        color=EmbedColor.MAIN_COLOR.value,
    )

    for rank, any_user in enumerate(users_top_list[:10], start=1):
        user_top = f"{top_rank.get(rank, '#')}{rank}"

        embed.add_field(
            name="_ _",
            value=(
                f"**{user_top}** - <@{any_user.user_id}>"
                f"\nУровень: **{any_user.level}**"
                f"\nОпыт: **{any_user.exp}** / **{5 * (any_user.level ** 2) + (50 * any_user.level) + 100}**"
            ),
            inline=False,
        )
    return embed


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Ваша карточка рейтинга")
    async def lb(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        lbType: str = commands.Param(name="таблица", choices=SELECT),
    ):
        if await defaultMemberChecker(interaction, interaction.author) is False:
            return

        db = await database(interaction.author)
        if lbType == "по уровню":
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(Users)
                    .where(Users.guild_id == interaction.guild.id)
                    .order_by(Users.level.desc(), Users.exp.desc())
                )
                users_top_list = result.scalars().all()

            embed = await LevelLeaderboard(db[0], users_top_list)
            await interaction.response.send_message(embed=embed)
            return

        if lbType == "по монетам":
            async with AsyncSession(engine) as session2:
                result2 = await session2.execute(
                    select(Users)
                    .where(Users.guild_id == interaction.guild.id)
                    .order_by(Users.currency.desc())
                )
                users_top_list = result2.scalars().all()

            embed = await CurrencyLeaderboard(db[0], users_top_list)
            await interaction.response.send_message(embed=embed)
            return


def setup(bot):
    bot.add_cog(Leaderboard(bot))
