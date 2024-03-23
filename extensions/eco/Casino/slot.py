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


class Slot(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(description="Игровой автомат")
    async def slot(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        amount: int = commands.Param(name="ставка"),
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

        slot1, slot2, slot3 = (
            random.choice(SLOT),
            random.choice(SLOT),
            random.choice(SLOT),
        )

        if slot1 == "🔔" and slot2 == "🔔" and slot3 == "🔔":
            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == interaction.author.id,
                            Users.guild_id == interaction.guild.id,
                        )
                    )
                    .values(currency=(Users.currency - amount) + (amount * 4))
                )
                await session.commit()

            embed = disnake.Embed(
                title="🎉 Выигрыш есть, можно поесть! 🎉",
                description=f"<@{author.id}> выбивает {slot1}{slot2}{slot3}и выигрывает **{round(amount * 4):,}** {EmbedEmoji.SILVER_COIN.value}\n\n"
                f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
                "`Множитель:` **x4**\n"
                f"`Баланс:` **{round((authorDB[0].currency - amount) + (amount * 4)):,}** {EmbedEmoji.SILVER_COIN.value}",
                color=EmbedColor.CASINO_WIN4X.value,
            )
            embed.timestamp = datetime.datetime.utcnow()
            await interaction.send(embed=embed, ephemeral=True)
            return

        if slot1 == "🍒" and slot2 == "🍒" and slot3 == "🍒":
            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == interaction.author.id,
                            Users.guild_id == interaction.guild.id,
                        )
                    )
                    .values(currency=(Users.currency - amount) + (amount * 10))
                )
                await session.commit()

            embed = disnake.Embed(
                title="🎉 Выигрыш есть, можно поесть! 🎉",
                description=f"<@{author.id}> выбивает {slot1}{slot2}{slot3} и выигрывает **{round(amount * 10):,}** {EmbedEmoji.SILVER_COIN.value}\n\n"
                f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
                f"`Множитель:` **x10**\n"
                f"`Баланс:` **{round((authorDB[0].currency - amount) + (amount * 10)):,}** {EmbedEmoji.SILVER_COIN.value}",
                color=EmbedColor.CASINO_WIN10X.value,
            )

            embed.timestamp = datetime.datetime.utcnow()
            await interaction.send(embed=embed, ephemeral=True)
            return

        if slot1 == "🍇" and slot2 == "🍇" and slot3 == "🍇":
            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == interaction.author.id,
                            Users.guild_id == interaction.guild.id,
                        )
                    )
                    .values(currency=(Users.currency - amount) + (amount * 50))
                )
                await session.commit()

            embed = disnake.Embed(
                title="🎉 Выигрыш есть, можно поесть! 🎉",
                description=f"<@{author.id}> выбивает {slot1}{slot2}{slot3} и выигрывает **{round(amount * 50):,}** {EmbedEmoji.SILVER_COIN.value}\n\n"
                f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
                f"`Множитель:` **x50**\n"
                f"`Баланс:` **{round((authorDB[0].currency - amount) + (amount * 50)):,}** {EmbedEmoji.SILVER_COIN.value}",
                color=EmbedColor.CASINO_WIN50X.value,
            )
            embed.timestamp = datetime.datetime.utcnow()
            await interaction.send(embed=embed, ephemeral=True)
            return

        if slot1 == "💎" and slot2 == "💎" and slot3 == "💎":
            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == interaction.author.id,
                            Users.guild_id == interaction.guild.id,
                        )
                    )
                    .values(currency=(Users.currency - amount) + (amount * 100))
                )
                await session.commit()

            embed = disnake.Embed(
                title="🎉 Выигрыш есть, можно поесть! 🎉",
                description=f"<@{author.id}> выбивает {slot1}{slot2}{slot3} и выигрывает **{round(amount * 100):,}** {EmbedEmoji.SILVER_COIN.value}\n\n"
                f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
                f"`Множитель:` **x100**\n"
                f"`Баланс:` **{round((authorDB[0].currency - amount) + (amount * 100)):,}** {EmbedEmoji.SILVER_COIN.value}",
                color=EmbedColor.CASINO_WIN100X.value,
            )
            embed.timestamp = datetime.datetime.utcnow()
            await interaction.send(embed=embed, ephemeral=True)
            return

        if slot1 and slot2 and slot3 != "🔔🔔🔔" or "🍒🍒🍒" or "🍇🍇🍇" or "💎💎💎":
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
                title="Игровой автомат",
                description=f"<@{author.id}> выбивает {slot1}{slot2}{slot3} и ничего не выигрывает\n\n"
                f"`Ставка:`**{amount:,}** {EmbedEmoji.SILVER_COIN.value}\n"
                f"`Баланс:` **{round(authorDB[0].currency - amount):,}**",
                color=EmbedColor.CASINO_ORANGE.value,
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        return


def setup(bot):
    bot.add_cog(Slot(bot))
