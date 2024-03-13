import disnake
from disnake import TextInputStyle, MessageInteraction
from disnake.ext import commands

from sqlalchemy import select
from sqlalchemy import and_
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core import *

import datetime


async def userinfo(member: disnake.Member) -> disnake.Embed:
    db = await database(member)
    file = await getRankCard(member.guild, member)

    def format_url(url: str, prefix: str):
        return f"[{url.replace(prefix, '')}]({url})" if url != prefix else None

    vk_url = format_url(db[2].vk_url, "https://vk.com/")
    inst_url = format_url(db[2].inst_url, "https://www.instagram.com/")
    tg_url = format_url(db[2].tg_url, "https://t.me/")
    description = db[2].description[:256]
    currency = f"{db[0].currency:,}"
    donate = f"{db[2].donate:,}"
    voice_seconds = str(datetime.timedelta(seconds=int(db[0].all_voice_time)))

    if member.avatar:
        icon_url = member.avatar
    else:
        icon_url = None

    embed = disnake.Embed(description=member.mention, color=EmbedColor.MAIN_COLOR.value)
    embed.set_author(
        name=member.name,
        icon_url=icon_url,
    )
    embed.add_field(
        name="> 💬 Статус",
        value=f"```{description}```",
        inline=False,
    )
    embed.add_field(
        name="> 🔊 Время в войсе", value=f"```{voice_seconds}```", inline=True
    )
    embed.add_field(
        name=f"> {EmbedEmoji.SILVER_COIN.value} Серебрянные монеты",
        value=f"```{currency}```",
        inline=True,
    )
    embed.add_field(
        name=f"> {EmbedEmoji.GOLD_COIN.value} Золотые монеты",
        value=f" ```{donate}```",
        inline=True,
    )
    embed.add_field(
        name=f"> {EmbedEmoji.VK_ICON.value} **VK**",
        value=vk_url or "Ссылка не установлена",
        inline=True,
    )
    embed.add_field(
        name=f"> {EmbedEmoji.INST_ICON.value} **Instagram**",
        value=inst_url or "Ссылка не установлена",
        inline=True,
    )
    embed.add_field(
        name=f"> {EmbedEmoji.TG_ICON.value} **Telegram**",
        value=tg_url or "Ссылка не установлена",
        inline=True,
    )

    embed.set_image(file=file)
    return embed


class AboutMeModal(disnake.ui.Modal):
    def __init__(self, bot):
        self.bot = bot
        components = [
            disnake.ui.TextInput(
                label='Статус"',
                placeholder="Напишите что-нибудь",
                custom_id="m_about",
                max_length=256,
                style=TextInputStyle.long,
                required=True,
            )
        ]
        super().__init__(title="Изменение профиля", components=components, timeout=3600)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_about = str(interaction.text_values["m_about"])
        if await banWords(m_about) is True:
            await interaction.response.send_message(
                f"{EmbedEmoji.ACCESS_DENIED.value} В профиле запрещено использовать мат",
                ephemeral=True,
            )
            return

        async with AsyncSession(engine) as session:
            await session.execute(
                update(User_global)
                .where(User_global.user_id == interaction.author.id)
                .values(description=m_about)
            )
            await session.commit()

        embed = await userinfo(interaction.author)
        await interaction.response.edit_message(embed=embed)
        return


class VKModal(disnake.ui.Modal):
    def __init__(self, bot):
        self.bot = bot
        components = [
            disnake.ui.TextInput(
                label="Ссылка на ВК",
                placeholder="Укажите ваш тег без @ и ссылок",
                custom_id="m_vk_url",
                max_length=32,
                style=TextInputStyle.short,
                required=True,
            )
        ]
        super().__init__(title="Изменение профиля", components=components, timeout=3600)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_vk_url = str(interaction.text_values["m_vk_url"])

        async with AsyncSession(engine) as session:
            stmt = (
                update(User_global)
                .where(User_global.user_id == interaction.author.id)
                .values(vk_url=f"https://vk.com/{m_vk_url}")
            )
            await session.execute(stmt)
            await session.commit()

        embed = await userinfo(interaction.author)
        await interaction.response.edit_message(embed=embed)
        return


class InstModal(disnake.ui.Modal):
    def __init__(self, bot):
        self.bot = bot
        components = [
            disnake.ui.TextInput(
                label="Ссылка на Instagram",
                placeholder="Укажите ваш тег без @ и ссылок",
                custom_id="m_inst_url",
                max_length=32,
                style=TextInputStyle.short,
                required=True,
            )
        ]
        super().__init__(title="Изменение профиля", components=components, timeout=3600)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_inst_url = str(interaction.text_values["m_inst_url"])

        async with AsyncSession(engine) as session:
            await session.execute(
                update(User_global)
                .where(User_global.user_id == interaction.author.id)
                .values(inst_url=f"https://www.instagram.com/{m_inst_url}")
            )
            await session.commit()

        embed = await userinfo(interaction.author)
        await interaction.response.edit_message(embed=embed)
        return


class TgModal(disnake.ui.Modal):
    def __init__(self, bot):
        self.bot = bot

        components = [
            disnake.ui.TextInput(
                label="Ссылка на Telegram",
                placeholder="Укажите ваш тег без @ и ссылок",
                custom_id="m_tg_url",
                max_length=32,
                style=TextInputStyle.short,
                required=True,
            )
        ]
        super().__init__(title="Изменение профиля", components=components, timeout=3600)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_tg_url = str(interaction.text_values["m_tg_url"])

        async with AsyncSession(engine) as session:
            await session.execute(
                update(User_global)
                .where(User_global.user_id == interaction.author.id)
                .values(tg_url=f"https://t.me/{m_tg_url}")
            )
            await session.commit()

        embed = await userinfo(interaction.author)
        await interaction.response.edit_message(embed=embed)
        return


class RankCardSelect(disnake.ui.StringSelect):
    def __init__(self, bot, user_global, message):
        self.bot = bot
        self.message = message

        options = []
        for i in user_global.cards:
            options.append(
                disnake.SelectOption(
                    value=f"{i}",
                    label=f"{ID_CARD_NAMES[i]}",
                    description=f'Выбрать карточку "{ID_CARD_NAMES[i]}"',
                )
            )

        super().__init__(
            placeholder="Выберите отображаемую карточку рейтинга",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        async with AsyncSession(engine) as session:
            await session.execute(
                update(Users)
                .where(
                    and_(
                        Users.user_id == interaction.author.id,
                        Users.guild_id == interaction.guild.id,
                    )
                )
                .values(select_card=int(self.values[0]))
            )
            await session.commit()

        await interaction.response.edit_message(
            f'Вы выбрали "{ID_CARD_NAMES[int(self.values[0])]}"', view=None
        )
        await interaction.delete_original_response(delay=10)

        org_message = self.message
        embed = await userinfo(interaction.author)
        await org_message.edit(embed=embed)


class UserChange(disnake.ui.View):
    def __init__(self, bot, buttonAuthor: disnake.Member):
        super().__init__(timeout=None)
        self.bot = bot
        self.buttonAuthor = buttonAuthor
        self.message = None

    async def interaction_check(self, interaction: MessageInteraction) -> bool:
        if self.buttonAuthor.id != interaction.author.id:
            embed = await accessDeniedButton(self.buttonAuthor)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Изменить статус", style=disnake.ButtonStyle.secondary, emoji="📃", row=1
    )
    async def change_status(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=AboutMeModal(self.bot))

    @disnake.ui.button(
        label="Изменить карточку рейтинга",
        style=disnake.ButtonStyle.secondary,
        emoji="🎆",
        row=1,
    )
    async def change_rank_card(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        user_global = await database(interaction.author)
        select_view = disnake.ui.View()
        message = interaction.message
        select_view.add_item(RankCardSelect(self.bot, user_global[2], message))

        await interaction.response.send_message(
            view=select_view, ephemeral=True, delete_after=30
        )

    @disnake.ui.button(
        label="Редактировать ссылку на VK",
        style=disnake.ButtonStyle.secondary,
        emoji=EmbedEmoji.VK_ICON.value,
        row=2,
    )
    async def change_url_vk(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=VKModal(self.bot))

    @disnake.ui.button(
        label="Редактировать ссылку на Instagram",
        style=disnake.ButtonStyle.secondary,
        emoji=EmbedEmoji.INST_ICON.value,
        row=2,
    )
    async def change_url_inst(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=InstModal(self.bot))

    @disnake.ui.button(
        label="Редактировать ссылку на Telegram",
        style=disnake.ButtonStyle.secondary,
        emoji=EmbedEmoji.TG_ICON.value,
        row=2,
    )
    async def change_url_tg(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=TgModal(self.bot))


class UserInfo(commands.Cog):
    def __init__(self, bot) -> None:
        self.message = None
        self.bot = bot
        self.member_id = int

    @commands.user_command(name="Профиль")
    async def profile_popup(
        self, interaction: disnake.ApplicationCommandInteraction, member: disnake.Member
    ):
        if await defaultMemberChecker(interaction, member) is False:
            return

        embed = await userinfo(member)
        file = await getRankCard(member.guild, member)
        await database(interaction.author)
        self.member_id = interaction.author.id
        change_user = UserChange(self.bot, interaction.author)

        if interaction.author.id is member.id:
            await interaction.send(
                embed=embed,
                view=change_user,
                ephemeral=False,
                delete_after=300,
            )
            return

        await interaction.response.send_message(
            file=file, embed=embed, ephemeral=True, delete_after=300
        )

    @commands.slash_command(
        name="profile", description="Выводит информацию о пользователе"
    )
    async def profile_no_popup(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        member: disnake.Member = commands.Param(name="пользователь", default=None),
    ):
        if await defaultMemberChecker(interaction, member) is False:
            return

        target = member
        if not target:
            target = interaction.author

        embed = await userinfo(target)
        file = await getRankCard(member.guild, member)
        await database(target)
        self.member_id = target.id
        change_user = UserChange(self.bot, target)

        if target.id is member.id:
            await interaction.send(
                embed=embed,
                view=change_user,
                ephemeral=False,
                delete_after=300,
            )
            return

        await interaction.response.send_message(
            file=file, embed=embed, ephemeral=True, delete_after=300
        )


def setup(bot):
    bot.add_cog(UserInfo(bot))
