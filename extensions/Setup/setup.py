import disnake
from disnake.ext import commands
import datetime

from sqlalchemy import select, delete, insert, update
from sqlalchemy import and_
from sqlalchemy import insert, text
from sqlalchemy import update, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ARRAY

from core.checker import *
from core.vars import *
from core.models import *


class GuildStatsChannelType(disnake.ui.View):
    def __init__(self, bot, buttonAuthor: disnake.Member):
        super().__init__(timeout=60)
        self.bot = bot
        self.buttonAuthor = buttonAuthor

    async def interaction_check(self, interaction: disnake.Interaction):
        if interaction.author.id != self.buttonAuthor.id:
            embed = await accessDeniedButton(self.buttonAuthor)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Текстовые каналы", style=disnake.ButtonStyle.secondary, row=1
    )
    async def StatsChannelsTypeText(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        return

    @disnake.ui.button(
        label="Голосовые каналы", style=disnake.ButtonStyle.secondary, row=1
    )
    async def StatsChannelsTypeVoice(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        everyone = interaction.guild.default_role
        members = len(interaction.guild.members)
        boosts = interaction.guild.premium_subscription_count
        date = datetime.datetime.now().strftime("%d-ое %B, %A")

        voice_members = 0
        for x in interaction.guild.voice_channels + interaction.guild.stage_channels:
            voice_members += len(x.members)

        category = await interaction.guild.create_category("📊 | Статистика")

        members_channel = await interaction.guild.create_voice_channel(
            f"👥│{members:,}", category=category, position=0
        )
        boosts_channel = await interaction.guild.create_voice_channel(
            f"🚀│{boosts}", category=category
        )
        voice_members_channel = await interaction.guild.create_voice_channel(
            f"🎤│{voice_members}", category=category
        )
        date_channel = await interaction.guild.create_voice_channel(
            f"📅│{date}", category=category
        )

        async with AsyncSession(engine) as session:
            await session.execute(
                update(Guilds)
                .where(Guilds.guild_id == interaction.guild.id)
                .values(
                    member_stats_channel_id=members_channel.id,
                    boosts_stats_channel_id=boosts_channel.id,
                    voice_members_channel_id=voice_members_channel.id,
                    date_channel_id=date_channel.id,
                )
            )
            await session.commit()

        await members_channel.set_permissions(everyone, speak=False, connect=False)
        await boosts_channel.set_permissions(everyone, speak=False, connect=False)
        await voice_members_channel.set_permissions(
            everyone, speak=False, connect=False
        )
        await date_channel.set_permissions(everyone, speak=False, connect=False)

        embed = disnake.Embed(
            title="Вы создали категорию каналов статистики",
            description="",
            color=0xA1A1A1,
        )
        embed.add_field(
            name="Созданные каналы",
            value=f"{members_channel.jump_url} \n"
            f"{boosts_channel.jump_url} \n"
            f"{voice_members_channel.jump_url} \n"
            f"{date_channel.jump_url}",
            inline=True,
        )
        await interaction.edit_original_response(embed=embed)

    @disnake.ui.button(label="Трибуны", style=disnake.ButtonStyle.secondary, row=1)
    async def StatsChannelsTypeStage(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        return

    @disnake.ui.button(
        label="Назад", style=disnake.ButtonStyle.blurple, emoji="⬅️", row=2
    )
    async def SetupBack(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        embed = disnake.Embed(
            title="Включить дополнительные функции",
            description="",
            colour=EmbedColor.MAIN_COLOR.value,
        )

        await interaction.response.edit_message(
            embed=embed, view=VoiceStatsSetupButtons(self.bot, self.buttonAuthor)
        )


class VoiceStatsSetupButtons(disnake.ui.View):
    def __init__(self, bot, buttonAuthor: disnake.Member):
        super().__init__(timeout=60)
        self.bot = bot
        self.buttonAuthor = buttonAuthor

    async def interaction_check(self, interaction: disnake.Interaction):
        if interaction.author.id != self.buttonAuthor.id:
            embed = await accessDeniedButton(self.buttonAuthor)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Выбрать тип каналов",
        style=disnake.ButtonStyle.secondary,
        emoji="🔊",
        row=1,
    )
    async def selectChannelsType(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        embed = disnake.Embed(
            title="Управление функцией **Статистика гильдии через каналы**",
            description="После нажатия на выбранную кнопку создадутся каналы выбранного вами типа",
            colour=EmbedColor.MAIN_COLOR.value,
        )
        embed.add_field(
            name="Заметка:",
            value="При нажатии на любую из кнопок ниже, кроме кнопки **Назад**,"
            "будет создана категория с каналами выбранного вами типа \n\n"
            "Но прошлые каналы, если они были, будут удалены.",
            inline=False,
        )
        await interaction.response.defer()
        await interaction.message.edit(
            embed=embed, view=GuildStatsChannelType(self.bot, self.buttonAuthor)
        )

    @disnake.ui.button(
        label="Добавить другие каналы со статистикой",
        style=disnake.ButtonStyle.secondary,
        emoji="📊",
        row=1,
    )
    async def MoreStatsChannels(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        return

    @disnake.ui.button(
        label="Назад", style=disnake.ButtonStyle.blurple, emoji="⬅️", row=2
    )
    async def SetupBack_2(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        embed = disnake.Embed(
            title="Включить дополнительные функции",
            description="",
            colour=EmbedColor.MAIN_COLOR.value,
        )

        await interaction.response.edit_message(
            embed=embed, view=SettingsButtons(self.bot, self.buttonAuthor)
        )


class SettingsButtons(disnake.ui.View):
    def __init__(self, bot, buttonAuthor: disnake.Member):
        super().__init__(timeout=60)
        self.bot = bot
        self.buttonAuthor = buttonAuthor

    async def interaction_check(self, interaction: disnake.Interaction):
        if interaction.author.id != self.buttonAuthor.id:
            embed = await accessDeniedButton(self.buttonAuthor)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Добавить приватные каналы",
        style=disnake.ButtonStyle.secondary,
        emoji="🔊",
        row=1,
    )
    async def privateChannelsSetup(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        category = await interaction.guild.create_category(
            "Приватные каналы", position=0
        )
        main_channel = await interaction.guild.create_voice_channel(
            "[➕] Создать", category=category
        )
        settings_channel = await interaction.guild.create_text_channel(
            "⚙│настройка-комнаты", category=category
        )
        everyone = interaction.guild.default_role

        await main_channel.set_permissions(
            everyone,
            speak=False,
        )
        await settings_channel.set_permissions(
            everyone,
            read_messages=True,
            use_slash_commands=True,
            create_private_threads=False,
            create_public_threads=False,
            read_message_history=True,
        )

        await database(interaction.author)

        async with AsyncSession(engine) as session:
            channel_db = await session.scalar(
                select(Guilds.p_channel_ids).where(
                    Guilds.guild_id == interaction.guild.id
                )
            )

        channel_db.append(main_channel.id)

        async with AsyncSession(engine) as session:
            await session.execute(
                update(Guilds)
                .where(Guilds.guild_id == interaction.guild.id)
                .values(
                    p_channel_ids=text(
                        f"array_append({Guilds.p_channel_ids}, :channel\:\:bigint)"
                    )
                ),
                {"channel": main_channel.id},
            )
            await session.commit()

        embed = disnake.Embed(
            title="Вы создали категорию приватных каналов",
            color=EmbedColor.MAIN_COLOR.value,
        )
        embed.add_field(
            name="> Созданные каналы:",
            value=f"{main_channel.jump_url} \n" f"{settings_channel.jump_url}",
            inline=True,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @disnake.ui.button(
        label="Управление каналами статистики",
        style=disnake.ButtonStyle.secondary,
        emoji="📊",
        row=1,
    )
    async def voiceStatsSetup(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.defer()
        embed = disnake.Embed(
            title="Управление функцией **Статистика гильдии через каналы**",
            description="",
            colour=EmbedColor.MAIN_COLOR.value,
        )
        await interaction.message.edit(
            embed=embed, view=VoiceStatsSetupButtons(self.bot, self.buttonAuthor)
        )

    @disnake.ui.button(
        label="Включить систему репортов",
        style=disnake.ButtonStyle.secondary,
        emoji="⭕",
        row=2,
    )
    async def reportSystemSetup(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        category = await interaction.guild.create_category("⭕│Report System")
        channel = await category.create_text_channel("⛔️│report")
        async with AsyncSession(engine) as session:
            db_guilds = await session.scalar(
                select(Guilds).where(Guilds.guild_id == interaction.guild.id)
            )

        if db_guilds.report_channel_id is not None:
            return

        async with AsyncSession(engine) as session:
            await session.execute(
                update(Guilds)
                .where(Guilds.guild_id == interaction.guild.id)
                .values(report_channel_id=channel.id)
            )
            await session.commit()

        embed = disnake.Embed(
            title="Отправить репорт", color=EmbedColor.MAIN_COLOR.value
        )
        embed.add_field(
            name="Как это работает?",
            value="После нажатия на кнопку, будет создан канал в котором вы можете рассказать о вашей проблеме.",
            inline=False,
        )
        embed.add_field(
            name="Как закрыть жалобу?",
            value="Жалобу можно закрыть нажав на кнопку подсвеченную красным цветом.",
        )
        message = await channel.send(
            embed=embed,
            components=[
                disnake.ui.Button(
                    label="Текстовый тикет",
                    custom_id="report_button_text",
                    emoji="💬",
                    row=1,
                    style=disnake.ButtonStyle.secondary,
                ),
                disnake.ui.Button(
                    label="Голосовой тикет",
                    custom_id="report_button_voice",
                    emoji="🔊",
                    row=1,
                    style=disnake.ButtonStyle.secondary,
                ),
            ],
        )
        async with AsyncSession(engine) as session:
            await session.execute(
                update(Guilds)
                .where(Guilds.guild_id == interaction.guild.id)
                .values(report_message_id=message.id)
            )
            await session.commit()


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Управление доп. функциями")
    async def settings(self, interaction: disnake.ApplicationCommandInteraction):
        if await defaultMemberChecker(interaction, interaction.author) is False:
            return

        if interaction.author.id != interaction.guild.owner.id:
            err_embed = await accessDeniedNotOwner(interaction.guild.owner)
            await interaction.response.send_message(embed=err_embed, ephemeral=True)
            return

        embed = disnake.Embed(
            title="Включить дополнительные функции",
            description="",
            colour=EmbedColor.MAIN_COLOR.value,
        )

        await interaction.send(
            embed=embed, view=SettingsButtons(self.bot, interaction.author)
        )


def setup(bot):
    bot.add_cog(Settings(bot))
