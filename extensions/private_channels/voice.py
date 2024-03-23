import disnake
from disnake import TextInputStyle
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


async def unlockRoom(interaction: disnake.MessageInteraction):
    author = interaction.author

    try:
        channel = author.voice.channel
    except AttributeError:
        embed = await accessDeniedCustom("Вы не находитесь в вашем приватном канале")
        await interaction.send(embed=embed, ephemeral=True, delete_after=15)
        return

    user_settngs = await database(author)

    if user_settngs[0].p_channel_id != channel.id:
        embed = await accessDeniedCustom("Вы не находитесь в вашем приватном канале")
        await interaction.send(embed=embed, ephemeral=True, delete_after=15)
        return

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

    embed = disnake.Embed(
        title="Управление приватной комнатой",
        description=f"{EmbedEmoji.ACCESS_ALLOWED.value}<@!{author.id}> открывает комнату <#{channel.id}>",
        color=EmbedColor.PCHANNEL_SETTINGS.value,
    )
    await interaction.send(embed=embed, ephemeral=True, delete_after=15)
    return


async def lockRoom(interaction: disnake.MessageInteraction):
    author = interaction.author

    try:
        channel = author.voice.channel
    except AttributeError:
        embed = await accessDeniedCustom("Вы не находитесь в вашем приватном канале")
        await interaction.send(embed=embed, ephemeral=True, delete_after=15)
        return

    user_settngs = await database(author)

    if user_settngs[0].p_channel_id != channel.id:
        embed = await accessDeniedCustom("Вы не находитесь в вашем приватном канале")
        await interaction.send(embed=embed, ephemeral=True, delete_after=15)
        return

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

    embed = disnake.Embed(
        title="Управление приватной комнатой",
        description=f"{EmbedEmoji.ACCESS_ALLOWED.value}<@!{author.id}> закрывает комнату <#{channel.id}>",
        color=EmbedColor.PCHANNEL_SETTINGS.value,
    )
    await interaction.send(embed=embed, ephemeral=True, delete_after=15)
    return


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

        embed = disnake.Embed(
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


class VLimitModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Лимит",
                placeholder="",
                custom_id="m_v_limit",
                max_length=2,
                style=TextInputStyle.short,
                required=True,
            )
        ]
        super().__init__(title="Приватный канал", components=components, timeout=3600)

    async def callback(self, interaction: disnake.ModalInteraction):
        try:
            m_v_limit = int(interaction.text_values["m_v_limit"])
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
        author = interaction.author
        user_settngs = await database(author)

        try:
            channel = author.voice.channel
        except AttributeError:
            await accessDeniedCustom("Вы не находитесь в вашем приватном канале")
            return

        if user_settngs[0].p_channel_id != channel.id:
            embed = await accessDeniedCustom(
                "Вы не находитесь в вашем приватном канале"
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        try:
            int(m_v_limit)
        except ValueError:
            embed = await accessDeniedCustom("Укажите число")
            await interaction.send(embed=embed, ephemeral=True)
            return

        if 0 > m_v_limit > 99:
            embed = await accessDeniedCustom("Укажите число от `0` до `99`")
            await interaction.send(embed=embed, ephemeral=True)
            return

        await channel.edit(user_limit=m_v_limit)

        async with AsyncSession(engine) as session:
            stmt = (
                update(Users)
                .where(
                    and_(
                        Users.user_id == author.id,
                        Users.guild_id == author.guild.id,
                    )
                )
                .values(p_channel_users_limit=m_v_limit)
            )
            await session.execute(stmt)
            await session.commit()

        embed = disnake.Embed(
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


class VNameModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Название",
                placeholder="",
                custom_id="m_v_name",
                max_length=32,
                style=TextInputStyle.short,
                required=True,
            )
        ]
        super().__init__(title="Приватный канал", components=components, timeout=3600)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_v_name = interaction.text_values["m_v_name"]
        author = interaction.author
        user_settngs = await database(author)

        try:
            channel = author.voice.channel
        except AttributeError:
            await accessDeniedCustom("Вы не находитесь в вашем приватном канале")
            return

        if user_settngs[0].p_channel_id != channel.id:
            embed = await accessDeniedCustom(
                "Вы не находитесь в вашем приватном канале"
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
                .values(p_channel_name=m_v_name)
            )
            await session.commit()

        await author.voice.channel.edit(name=m_v_name)

        embed = disnake.Embed(
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


class VoiceSettingsSelect(disnake.ui.StringSelect):
    def __init__(self):
        options = [
            disnake.SelectOption(value="0", label=f"Изменить название", emoji="📝"),
            disnake.SelectOption(value="1", label=f"Установить лимит", emoji="🔠"),
            disnake.SelectOption(value="2", label=f"Открыть", emoji="🔓"),
            disnake.SelectOption(value="3", label=f"Закрыть", emoji="🔒"),
            disnake.SelectOption(value="4", label=f"Выгнать", emoji="👠"),
        ]

        super().__init__(
            placeholder="Выбрать действие",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        selector = int(self.values[0])
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

        if selector == 0:
            await interaction.response.send_modal(modal=VNameModal())
            await interaction.edit_original_message()
            return

        elif selector == 1:
            await interaction.response.send_modal(modal=VLimitModal())
            await interaction.edit_original_message()
            return

        elif selector == 2:
            await unlockRoom(interaction)
            return

        elif selector == 3:
            await lockRoom(interaction)
            return

        elif selector == 4:
            channel_members = channel.members
            if interaction.author in channel_members:
                channel_members.remove(interaction.author)

            if len(channel_members) == 0:
                embed = disnake.Embed(
                    title="Управление приватной комнатой",
                    description="Из комнаты некого выгонять",
                    colour=EmbedColor.MAIN_COLOR.value,
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return

            select_view = disnake.ui.View()
            select_view.add_item(VKickSelect(channel_members))

            await interaction.response.send_message(
                view=select_view, ephemeral=True, delete_after=60
            )
            await interaction.edit_original_message()
            return


class VoiceSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Управлять своим приватным каналом")
    async def voice(self, interaction: disnake.ApplicationCommandInteraction):
        if await defaultMemberChecker(interaction, interaction.author) is False:
            return

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

        embed = disnake.Embed(
            title="Управление приватной комнатой",
            description="Взаимодействуйте с приватной комнатой через селектор",
            color=EmbedColor.MAIN_COLOR.value,
        )

        select_view = disnake.ui.View()
        select_view.add_item(VoiceSettingsSelect())

        await interaction.response.send_message(
            embed=embed, view=select_view, ephemeral=True, delete_after=300
        )


def setup(bot):
    bot.add_cog(VoiceSettings(bot))
