import disnake
from disnake.ext import commands
import datetime

from sqlalchemy import select, delete, insert, update
from sqlalchemy import and_
from sqlalchemy import insert, text
from sqlalchemy import update, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ARRAY

from core import *


class TicketButtons(disnake.ui.View):
    def __init__(self, buttonAuthor: disnake.Member):
        super().__init__(timeout=60)
        self.buttonAuthor = buttonAuthor

    @disnake.ui.button(
        label="Забрать тикет",
        custom_id="report_button_take_ticket",
        style=disnake.ButtonStyle.green,
        row=1,
    )
    async def TakeTickerButton(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        db_guild = await insertDatabase(interaction.author, interaction.guild)

        if not list(
            set(db_guild[1].admin_roles_ids).intersection(
                set([ids.id for ids in interaction.author.roles])
            )
        ):
            embed = await accessDeniedCustom("У вас нет ни одной админ-роли")
            embed.add_field(
                name="> Способы решения",
                value=f"```- Получить админ-роль \n"
                f"- Указать админ-роли на [сайте]{'https://discord.gg'} в раздела 'Администрирование', "
                f"если вы администратор/владелец этой гильдии```",
                inline=False,
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        await interaction.channel.edit(
            name=f"🔴│{interaction.author.name}",
        )
        await interaction.channel.set_permissions(
            interaction.guild.default_role, view_channel=False
        )
        await interaction.channel.set_permissions(
            self.buttonAuthor,
            read_messages=True,
            send_messages=True,
            attach_files=True,
        )
        await interaction.channel.set_permissions(
            interaction.author,
            read_messages=True,
            send_messages=True,
            attach_files=True,
        )

        embed_admin_take_ticket = disnake.Embed(
            title="Администратор забрал тикет",
            description=f"Администратор - <@{interaction.author.id}> (`{interaction.author.id}`) \n"
            f"Время: {disnake.utils.format_dt(datetime.datetime.now())}",
            colour=EmbedColor.MAIN_COLOR.value,
        )

        await interaction.response.send_message(embed=embed_admin_take_ticket)
        await interaction.message.edit()
        await interaction.response.defer()

    @disnake.ui.button(
        label="Закрыть тикет",
        custom_id="report_button_take_ticket",
        style=disnake.ButtonStyle.green,
        row=1,
    )
    async def CloseTicketButton(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        db_guild = await insertDatabase(interaction.author, interaction.guild)

        if not list(
            set(db_guild[1].admin_roles_ids).intersection(
                set([ids.id for ids in interaction.author.roles])
            )
        ):
            embed = await accessDeniedCustom("У вас нет ни одной админ-роли")
            embed.add_field(
                name="> Способы решения",
                value=f"```- Получить админ-роль \n"
                f"- Указать админ-роли на [сайте]{'https://discord.gg'} в раздела 'Администрирование', "
                f"если вы администратор/владелец этой гильдии```",
                inline=False,
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        channel = interaction.guild.get_channel(interaction.channel.id)
        await channel.delete()


class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_button_click")
    async def ReportButtonsTrigger(self, interaction: disnake.MessageInteraction):
        if interaction.component.custom_id == "report_button_text":
            async with AsyncSession(engine) as session:
                channel = await session.scalar(
                    select(Guilds.report_channel_id).where(
                        Guilds.guild_id == interaction.guild.id
                    )
                )

            channel = interaction.guild.get_channel(channel)
            channel = await channel.category.create_text_channel(
                f"🟢│{interaction.author.name}"
            )
            embed_create_ticket = disnake.Embed(
                title="Вы создали тикет",
                description=channel.jump_url,
                colour=EmbedColor.ACCESS_ALLOWED.value,
            )
            await interaction.response.send_message(
                embed=embed_create_ticket, ephemeral=True
            )

            embed_in_ticket = disnake.Embed(
                title="Тикет открыт1",
                description="Опишите подробно вашу проблему",
                color=EmbedColor.MAIN_COLOR.value,
            )
            await channel.send(
                embed=embed_in_ticket, view=TicketButtons(interaction.author)
            )


def setup(bot):
    bot.add_cog(ReportSystem(bot))
