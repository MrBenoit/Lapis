import disnake
from disnake.ext import commands
import datetime

from sqlalchemy import select, delete, insert, update
from sqlalchemy import and_
from sqlalchemy import insert, text
from sqlalchemy import update, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import array

from core import *


class CloseTicketButtons(disnake.ui.View):
    def __init__(self, buttonAuthor: disnake.Member):
        super().__init__(timeout=60)
        self.buttonAuthor = buttonAuthor

    @disnake.ui.button(
        label="Закрыть тикет",
        custom_id="report_button_close_ticket",
        style=disnake.ButtonStyle.red,
        emoji="❌",
        row=1,
    )
    async def TakeTickerButton(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        async with AsyncSession(engine) as session:
            await session.execute(
                update(Users)
                .where(
                    and_(
                        Users.user_id == interaction.author.id,
                        Users.guild_id == interaction.guild.id,
                    )
                )
                .values(report_ticket_channel_id=None)
            )
            await session.commit()

        await interaction.channel.delete()


class TicketButtons(disnake.ui.View):
    def __init__(self, buttonAuthor: disnake.Member):
        super().__init__(timeout=60)
        self.buttonAuthor = buttonAuthor

    @disnake.ui.button(
        label="Забрать тикет",
        custom_id="report_button_take_ticket",
        style=disnake.ButtonStyle.green,
        emoji="🟢",
        row=1,
    )
    async def TakeTickerButton(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        db_guild = await database(interaction.author)

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

        embed_edited_ticket = disnake.Embed(
            title="Тикет активен", color=EmbedColor.MAIN_COLOR.value
        )

        await interaction.response.send_message(embed=embed_admin_take_ticket)
        await interaction.message.edit(
            embed=embed_edited_ticket, view=CloseTicketButtons(self.buttonAuthor)
        )


class ReportSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_button_click")
    async def ReportButtonsTrigger(self, interaction: disnake.MessageInteraction):
        if interaction.component.custom_id == "report_button_text":
            db = await database(interaction.author)

            if db[0].report_ticket_channel_id is not None:
                channel_id = interaction.guild.get_channel(
                    db[0].report_ticket_channel_id
                )
                if channel_id is None:
                    async with AsyncSession(engine) as session:
                        await session.execute(
                            update(Users)
                            .where(
                                and_(
                                    Users.user_id == interaction.author.id,
                                    Users.guild_id == interaction.guild.id,
                                )
                            )
                            .values(report_ticket_channel_id=None)
                        )
                        await session.commit()
                else:
                    embed_err = disnake.Embed(
                        title="Вы уже создали тикет", color=EmbedColor.MAIN_COLOR.value
                    )
                    await interaction.response.send_message(
                        embed=embed_err, ephemeral=True, delete_after=15
                    )
                    return

            async with AsyncSession(engine) as session:
                guild_db = await session.scalar(
                    select(Guilds).where(Guilds.guild_id == interaction.guild.id)
                )

            channel = interaction.guild.get_channel(guild_db.report_channel_id)
            channel = await channel.category.create_text_channel(
                f"🟢│{interaction.author.name}"
            )

            await channel.set_permissions(
                interaction.guild.default_role,
                read_messages=False,
            )

            for role_id in guild_db.admin_roles_ids:
                await channel.set_permissions(
                    interaction.guild.get_role(role_id),
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
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
                title="Тикет открыт!",
                description="Опишите подробно вашу проблему",
                color=EmbedColor.MAIN_COLOR.value,
            )

            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == interaction.author.id,
                            Users.guild_id == interaction.guild.id,
                        )
                    )
                    .values(report_ticket_channel_id=channel.id)
                )
                await session.commit()

            await channel.send(
                embed=embed_in_ticket, view=TicketButtons(interaction.author)  # type: ignore
            )
            return

        if interaction.component.custom_id == "report_button_voice":
            try:
                interaction.author.voice.channel.id
            except AttributeError:
                embed = disnake.Embed(
                    title="Вы не находитесь в голосовом канале",
                    description="Что бы отправить такую жалобу, Вы должны находиться в голосовом канале",
                    color=EmbedColor.MAIN_COLOR.value,
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            async with AsyncSession(engine) as session:
                channel = await session.scalar(
                    select(Guilds.report_notif_channel_id).where(
                        Guilds.guild_id == interaction.guild.id
                    )
                )

            channel = interaction.guild.get_channel(channel)
            if channel is None:
                return

            embed = disnake.Embed(
                title="Голосовая жалоба",
                description=f"Поступила из канала <#{interaction.author.voice.channel.id}>",
                color=EmbedColor.MAIN_COLOR.value,
            )
            await channel.send(embed=embed)

            embed_channel = disnake.Embed(
                title="Жалоба отправлена", color=EmbedColor.MAIN_COLOR.value
            )
            await interaction.channel.send(
                embed=embed_channel, ephemeral=True, delete_after=15
            )


def setup(bot):
    bot.add_cog(ReportSystem(bot))
