import disnake
from disnake import TextInputStyle, Embed, SelectOption, MessageInteraction, ModalInteraction
from disnake.ui import StringSelect, TextInput
from disnake.ext import commands

from sqlalchemy import select, delete, func
from sqlalchemy import and_
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import array

import datetime

from core.checker import *
from core.vars import *
from core.models import *


class VKickSelect(disnake.ui.StringSelect):
    def __init__(self, members):
        self.members = members
        options = []

        for member in self.members:
            options.append(
                disnake.SelectOption(
                    value=f"{member.id}",
                    label=f"{member.name}",
                )
            )

        super().__init__(
            placeholder="Выберите участника(ов)",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        for m_v_kick in [self.values[0]]:
            members = "".join(m_v_kick)

            author = interaction.author
            user_settngs = await database(author)

            try:
                m_v_kick = int(m_v_kick)
            except ValueError:
                embed = await accessDeniedCustom("Укажите ID пользователя")
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            member = interaction.guild.get_member(m_v_kick)

            if author == member:
                embed = await accessDeniedCustom("Вы не можете выгнать себя")
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            try:
                channel = author.voice.channel
            except AttributeError:
                embed = await accessDeniedCustom(
                    "Вы не находитесь в вашем приватном канале"
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            if user_settngs[0].p_channel_id != channel.id:
                embed = await accessDeniedCustom(
                    "Вы не находитесь в вашем приватном канале"
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            if member not in channel.members:
                embed = await accessDeniedCustom("Пользователь не в канале")
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            await channel.set_permissions(member, connect=False)
            await member.move_to(None)

        embed = Embed(
            title="Управление приватной комнатой",
            description=f"<@!{members}> изгоняет пользователя из <#{channel.id}>",
            color=EmbedColor.PCHANNEL_SETTINGS.value,
        )
        embed.add_field(
            name=f"{EmbedEmoji.ACCESS_ALLOWED.value} Пользователь успешно выгнан",
            value=f"**<@!{members}>** изгнан",
            inline=False,
        )
        await interaction.send(embed=embed, ephemeral=True, delete_after=15)
        return


class VoiceSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_dropdown")
    async def voice_dropdown_logic(self, interaction: MessageInteraction) -> None:
        value = interaction.values[0]
        author = interaction.author
        user_settngs = await database(author)

        try:
            channel = author.voice.channel
        except AttributeError:
            error = await accessDeniedCustom(
                "Вы не находитесь в вашем приватном канале"
            )
            await interaction.send(embed=error, ephemeral=True, delete_after=15)
            return

        if user_settngs[0].p_channel_id != channel.id:
            embed = await accessDeniedCustom(
                "Вы не находитесь в вашем приватном канале"
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        if value == 'v_change_name':
            await interaction.response.send_modal(
                title="Приватный канал",
                custom_id="v_change_name_modal",
                components=[
                    TextInput(
                        label="Название",
                        placeholder="",
                        custom_id="m_v_name",
                        max_length=32,
                        style=TextInputStyle.short,
                        required=True,
                    )
               ]
            )
            return

        elif value == 'v_set_users_limit':
            await interaction.response.send_modal(
                title="Приватный канал",
                custom_id="v_change_limit_modal",
                components=[
                    TextInput(
                        label="Лимит",
                        placeholder="",
                        custom_id="m_v_limit",
                        max_length=2,
                        style=TextInputStyle.short,
                        required=True,
                    )
               ]
            )
            return

        elif value == 'v_open':
            everyone = interaction.guild.default_role
            connect = channel.permissions_for(everyone).connect

            if connect is True:
                embed = disnake.Embed(
                    title="Комната уже открыта",
                    color=EmbedColor.PCHANNEL_SETTINGS.value,
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == author.id,
                            Users.guild_id == author.guild.id,
                            )
                    )
                    .values(p_channel_lock=True)
                )
                await session.commit()

            await author.voice.channel.set_permissions(everyone, connect=True)

            embed = Embed(
                title="Управление приватной комнатой",
                description=f"{EmbedEmoji.ACCESS_ALLOWED.value}<@!{author.id}> открывает комнату <#{channel.id}>",
                color=EmbedColor.PCHANNEL_SETTINGS.value,
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        elif value == 'v_close':
            everyone = interaction.guild.default_role
            connect = channel.permissions_for(everyone).connect

            if connect is False:
                embed = disnake.Embed(
                    title="Комната уже открыта",
                    color=EmbedColor.PCHANNEL_SETTINGS.value,
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == author.id,
                            Users.guild_id == author.guild.id,
                            )
                    )
                    .values(p_channel_lock=False)
                )
                await session.commit()

            await channel.set_permissions(everyone, connect=False)

            embed = Embed(
                title="Управление приватной комнатой",
                description=f"{EmbedEmoji.ACCESS_ALLOWED.value}<@!{author.id}> закрывает комнату <#{channel.id}>",
                color=EmbedColor.PCHANNEL_SETTINGS.value,
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        elif value == 'v_kick':
            channel_members = channel.members
            select_view = disnake.ui.View()
            select_view.add_item(VKickSelect(channel_members))

            await interaction.response.send_message(
                view=select_view, ephemeral=True, delete_after=60
            )

    @commands.Cog.listener("on_modal_submit")
    async def voice_modals_logic(self, interaction: ModalInteraction) -> None:
        author = interaction.author
        user_settngs = await database(author)

        try:
            channel = author.voice.channel
        except AttributeError:
            embed = await accessDeniedCustom("Вы не находитесь в голосовом канале")
            await interaction.channel.send(embed=embed, ephemeral=True, delete_after=15)
            return

        if user_settngs[0].p_channel_id != channel.id:
            embed = await accessDeniedCustom(
                "Вы не находитесь в вашем приватном канале"
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        if interaction.custom_id == "v_change_name_modal":
            m_v_name = interaction.text_values["m_v_name"]

            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == author.id,
                            Users.guild_id == author.guild.id,
                            )
                    )
                    .values(p_channel_name=m_v_name)
                )
                await session.commit()

            await author.voice.channel.edit(name=m_v_name)

            embed = Embed(
                title="Управление приватной комнатой",
                description=f"<@!{author.id}> меняет настройки комнаты <#{channel.id}> ",
                color=EmbedColor.PCHANNEL_SETTINGS.value,
            )
            embed.add_field(
                name=f"{EmbedEmoji.ACCESS_ALLOWED.value} Название успешно изменено",
                value=f"Название:\n```{m_v_name}```",
                inline=False,
            )
            embed.timestamp = datetime.datetime.utcnow()
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        if interaction.custom_id == "v_change_limit_modal":
            try:
                m_v_limit = int(interaction.text_values["m_v_limit"])
            except (TypeError, ValueError):
                embed = await accessDeniedCustom("Неверный тип данных")
                embed.add_field(
                    name="Ожидаемый тип данных", value="`int` *Число*", inline=True
                )
                embed.add_field(
                    name="Полученный тип данных",
                    value=f"`{type(interaction.text_values['m_transfer_silver_coin'])}`",
                    inline=True,
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            if 0 > m_v_limit > 99:
                embed = await accessDeniedCustom("Укажите число от `0` до `99`")
                await interaction.send(embed=embed, ephemeral=True)
                return

            await channel.edit(user_limit=m_v_limit)

            async with AsyncSession(engine) as session:
                await session.execute(
                    update(Users)
                    .where(
                        and_(
                            Users.user_id == author.id,
                            Users.guild_id == author.guild.id,
                            )
                    )
                    .values(p_channel_users_limit=m_v_limit)
                )
                await session.commit()

            embed = Embed(
                title="Управление приватной комнатой",
                description=f"<@!{author.id}> меняет настройки комнаты <#{channel.id}>",
                color=EmbedColor.PCHANNEL_SETTINGS.value,
            )
            embed.add_field(
                name=f"{EmbedEmoji.ACCESS_ALLOWED.value}Лимит успешно изменен",
                value=f"Лимит комнаты изменен на `{m_v_limit}`",
                inline=False,
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

    @commands.slash_command(description="Управлять своим приватным каналом")
    async def voice(self, interaction: disnake.UserCommandInteraction):
        author = interaction.author
        if interaction.author.bot or not interaction.guild:
            return

        user_settngs = await database(author)

        try:
            channel = author.voice.channel
        except AttributeError:
            error = await accessDeniedCustom(
                "Вы не находитесь в вашем приватном канале"
            )
            await interaction.send(embed=error, ephemeral=True, delete_after=15)
            return

        if user_settngs[0].p_channel_id != channel.id:
            embed = await accessDeniedCustom(
                "Вы не находитесь в вашем приватном канале"
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        embed = Embed(
            title="Управление приватной комнатой",
            description="Взаимодействуйте с приватной комнатой через селектор",
            color=EmbedColor.MAIN_COLOR.value,
        )

        await interaction.response.send_message(
            embed=embed,
            components=StringSelect(
                options=[
                    SelectOption(value="v_change_name", label=f"Изменить название", emoji="📝"),
                    SelectOption(value="v_set_users_limit", label=f"Установить лимит", emoji="🔠"),
                    SelectOption(value="v_open", label=f"Открыть", emoji="🔓"),
                    SelectOption(value="v_close", label=f"Закрыть", emoji="🔒"),
                    SelectOption(value="v_kick", label=f"Выгнать", emoji="👠"),
                ]
            ),
            ephemeral=True,
            delete_after=300
        )


def setup(bot):
    bot.add_cog(VoiceSettings(bot))
