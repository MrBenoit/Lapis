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


class Wheel(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(description="Колесо удачи")
    async def wheel(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        amount: int = commands.Param(name="ставка"),
    ):
        if await defaultMemberChecker(interaction, interaction.author) is False:
            return

        author = interaction.author
        choice = random.choice(WHEEL)
        authorDB = await database(author)

        if amount <= 99:
            embed = await accessDeniedCustom(
                f"Ставки меньше **100** {EmbedEmoji.SILVER_COIN.value} не принимаются"
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        if authorDB[0].currency < amount:
            embed = await accessDeniedNoMoney(amount, authorDB[0])
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
                .values(currency=(Users.currency - amount) + round(amount * choice))
            )
            await session.commit()

        embed = disnake.Embed(
            title="Колесо удачи",
            description=f"<@{author.id}> выиграл(а) **{round(amount * choice):,}** {EmbedEmoji.SILVER_COIN.value}\n\n"
            f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
            f"`Множитель:` **{choice}**\n"
            f"`Баланс:` **"
            f"{round((authorDB[0].currency - amount) + (amount * choice)):,}** {EmbedEmoji.SILVER_COIN.value}",
            color=EmbedColor.CASINO_ORANGE.value,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Wheel(bot))
