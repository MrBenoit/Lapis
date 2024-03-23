import asyncpg
from disnake import TextInputStyle
from disnake.ext import commands

from sqlalchemy import select
from sqlalchemy import and_
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core import *


class TransferModal(disnake.ui.Modal):
    def __init__(
        self,
        guild: disnake.Guild,
        author: disnake.Member,
        member: disnake.Member,
        authorDB,
        mentionDB,
    ):
        self.guild = guild
        self.author = author
        self.member = member
        self.authorDB = authorDB
        self.mentionDB = mentionDB

        components = [
            disnake.ui.TextInput(
                label=f"Серебрянных монет - {authorDB.currency:,}",
                placeholder="Сколько вы хотите перевести серебряных монет?",
                custom_id="m_transfer_silver_coin",
                max_length=128,
                style=TextInputStyle.short,
                required=False,
            )
        ]
        super().__init__(title="Перевод монет", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        try:
            amount = int(interaction.text_values["m_transfer_silver_coin"])
        except (TypeError, ValueError):
            embed = await accessDeniedCustom("Неверный тип данных")
            embed.add_field(
                name="Ожидаемый тип данных", value="`int` *Число*", inline=True
            )
            embed.add_field(
                name="Полученный тип данных",
                value=f"`{type(interaction.text_values['m_transfer_silver_coin'])}` *Строка*",
                inline=True,
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        if amount > self.authorDB.currency:
            embed = await accessDeniedNoMoney(amount, self.authorDB)
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)

        elif amount <= 0:
            embed = await accessDeniedCustom("Значение не должно быть меньше чем `0`")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
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
                .values(currency=Users.currency - amount)
            )
            await session.execute(
                update(Users)
                .where(
                    and_(
                        Users.user_id == self.member.id,
                        Users.guild_id == interaction.guild.id,
                    )
                )
                .values(currency=Users.currency + amount)
            )
            await session.commit()

        DM = self.member.create_dm()

        embedDM = disnake.Embed(
            title="Перевод монет",
            description=f"<@!{self.author.id}> перевел(а) вам **{amount:,}** {EmbedEmoji.SILVER_COIN.value}",
            color=EmbedColor.MAIN_COLOR.value,
        )
        embedDM.add_field(
            name="Баланс",
            value=f"**{self.authorDB.currency + amount:,}** {EmbedEmoji.SILVER_COIN.value}",
            inline=True,
        )

        try:
            await DM.send(embed=embedDM, mention_author=False)
        except TypeError:
            pass

        embed = disnake.Embed(
            title="Перевод монет",
            description=f"Вы перевели <@{self.member.id}> **{amount:,}** {EmbedEmoji.SILVER_COIN.value}",
            color=EmbedColor.MAIN_COLOR.value,
        )
        embed.add_field(
            name="Перевод монет",
            value=f"Баланс: **{self.mentionDB.currency - amount:,}** {EmbedEmoji.SILVER_COIN.value}",
            inline=True,
        )

        await interaction.send(
            embed=embed,
            ephemeral=True,
        )


class Transfer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.user_command(name="Перевод монет")
    async def transfer(
        self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member
    ):
        if await defaultMemberChecker(interaction, interaction.author) is False:
            return

        author = interaction.author

        if member.bot:
            embed = await accessDeniedCustom("Вы не можете переводить монеты боту")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        elif member.id == author.id:
            embed = await accessDeniedCustom(
                "Вы не можете переводить монеты самому себе"
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        mentionDB = await database(member)
        authorDB = await database(interaction.author)

        await interaction.response.send_modal(
            modal=TransferModal(
                interaction.guild,
                interaction.author,
                member,
                mentionDB[0],
                authorDB[0],
            )
        )


def setup(bot):
    bot.add_cog(Transfer(bot))
