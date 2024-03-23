import datetime
import random

import disnake
from disnake.ext import commands

from sqlalchemy import select
from sqlalchemy import and_
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core import *


class Coin(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(description="Орёл и решка")
    async def coin(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        amount: int = commands.Param(name="ставка", ge=0),
        coin: str = commands.Param(name="монетка", choices=COIN),
    ):
        if await defaultMemberChecker(interaction, interaction.author) is False:
            return

        author = interaction.author
        authorDB = await database(author)

        if amount <= 99:
            embed = disnake.Embed(
                title=f"{EmbedEmoji.ACCESS_DENIED.value} Действие невозможно",
                description="Значение не должно быть меньше **100**",
                color=EmbedColor.ACCESS_DENIED.value,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        if authorDB[0].currency < amount:
            embed = disnake.Embed(
                title=f"{EmbedEmoji.ACCESS_DENIED.value} Действие невозможно",
                description=f"У вас недостаточно серебренных монет \n Пополните счет на **{amount - authorDB[0].currency:,} {EmbedEmoji.SILVER_COIN.value}**",
                color=EmbedColor.ACCESS_DENIED.value,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        r_coin = random.choice(COIN)

        if coin != r_coin:
            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == interaction.author.id,
                            Users.guild_id == interaction.guild.id,
                        )
                    )
                    .values(currency=Users.currency - amount)
                )
                await session.commit()

            embed = disnake.Embed(
                title=f"Орёл и решка",
                description=f"<@!{author.id}> выбил **{r_coin}** и ничего не выиграл\n\n"
                f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
                f"`Ваша монетка:` **{coin}**\n"
                f"`Выпавшая монетка:` **{r_coin}**\n"
                f"`Баланс:` **{authorDB[0].currency - amount:,}** {EmbedEmoji.SILVER_COIN.value}",
                color=EmbedColor.CASINO_ORANGE.value,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        async with AsyncSession(engine) as session:
            await session.execute(
                update(Users)
                .where(
                    and_(
                        Users.user_id == interaction.author.id,
                        Users.guild_id == interaction.guild.id,
                    )
                )
                .values(currency=(Users.currency - amount) + (amount * 2))
            )
            await session.commit()

        embed = disnake.Embed(
            title=f"Орёл и решка",
            description=f"<@!{author.id}> выбил **{r_coin}** и получает **{amount * 2:,}** {EmbedEmoji.SILVER_COIN.value}\n\n"
            f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
            f"`Множитель:` **x2**\n"
            f"`Баланс:` **{(authorDB[0].currency - amount) + (amount * 2):,}** {EmbedEmoji.SILVER_COIN.value}",
            color=EmbedColor.CASINO_ORANGE.value,
        )
        await interaction.send(embed=embed, ephemeral=True)
        return


def setup(bot):
    bot.add_cog(Coin(bot))
