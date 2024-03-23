import json
import re

import disnake
from disnake import TextInputStyle
from disnake.ext import commands

from sqlalchemy import select, delete, insert, update
from sqlalchemy import and_
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core import *


async def save_embed_dict(embed: disnake.Embed, author: disnake.Member):
    async with AsyncSession(engine) as session:
        await session.execute(
            update(User_global)
            .where(User_global.user_id == author.id)
            .values(embed_json=json.dumps(embed.to_dict()))
        )
        await session.commit()


async def check_url(text_value: str):
    url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
    urls = re.findall(url_pattern, text_value)
    if text_value == "":
        return True
    if text_value.startswith("https:") or text_value.startswith("http:"):
        if "." in text_value:
            return True
    if urls is not None:
        return True
    return False


class ChannelSendModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="ID канала(ов)",
                placeholder="",
                custom_id="m_channel_id",
                style=TextInputStyle.short,
                required=True,
            ),
        ]
        super().__init__(title="Отправка созданного эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        await interaction.response.defer()
        dict_embed = interaction.message.embeds[0].to_dict()

        try:
            channel = interaction.guild.get_channel(
                int(interaction.text_values["m_channel_id"])
            )
        except AttributeError:
            await accessDeniedCustom("Вы указали несуществующий канал")
            return
                                                                    
        if channel.guild.id != interaction.author.id:
            embed = await accessDeniedCustom(
                "Вы не можете отправить эмбед в эту гильдию"
            )
            await interaction.send(embed=embed, ephemeral=True)
            return

        async with AsyncSession(engine) as session:
            text = await session.scalar(
                select(Users).where(Users.user_id == interaction.author.id)
            )

        embed = disnake.Embed().from_dict(dict_embed)

        await interaction.delete_original_response()

        await channel.send(content=text, embed=embed)
        return


class AuthorModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Автор",
                placeholder="",
                custom_id="m_author_name",
                style=TextInputStyle.paragraph,
                max_length=64,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Ссылка на автора",
                placeholder="URL",
                custom_id="m_author_url",
                style=TextInputStyle.short,
                max_length=2048,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Ссылка на иконку",
                placeholder="URL",
                custom_id="m_author_icon_url",
                style=TextInputStyle.short,
                max_length=2048,
                required=False,
            ),
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_author_name = interaction.text_values["m_author_name"]
        m_author_url = interaction.text_values["m_author_url"]
        m_author_icon_url = interaction.text_values["m_author_icon_url"]

        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        embed.set_author(
            name=m_author_name,
        )

        if await check_url(m_author_url) is False:
            embed = await accessDeniedCustom("Неверная ссылка")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        embed.set_author(
            name=m_author_name,
            url=m_author_url,
        )

        if await check_url(m_author_icon_url) is False:
            embed = await accessDeniedCustom("Неверная ссылка")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        embed.set_author(
            name=m_author_name,
            icon_url=m_author_icon_url,
        )

        await save_embed_dict(embed, interaction.author)

        await interaction.response.edit_message(
            embed=embed, view=EmbedCreator(interaction.author)
        )
        return


class FooterModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Футер",
                placeholder="",
                custom_id="m_footer",
                style=TextInputStyle.paragraph,
                max_length=64,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Ссылка на иконку",
                placeholder="URL",
                custom_id="m_footer_icon",
                style=TextInputStyle.short,
                required=False,
            ),
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_footer = interaction.text_values["m_footer"]
        m_footer_icon = interaction.text_values["m_footer_icon"]

        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        embed.set_footer(
            text=interaction.text_values["m_footer"],
        )

        if check_url(m_footer_icon) is False:
            embed = await accessDeniedCustom("Неверная ссылка")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        embed.set_footer(
            text=m_footer,
            icon_url=m_footer_icon,
        )

        await save_embed_dict(embed, interaction.author)

        await interaction.response.edit_message(
            embed=embed, view=EmbedCreator(interaction.author)
        )
        return


class ThumbnailModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Ссылка на миниатюру",
                placeholder="URL",
                custom_id="m_thumbnail",
                style=TextInputStyle.short,
                required=False,
            )
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_thumbnail = interaction.text_values["m_thumbnail"]

        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        if check_url(m_thumbnail) is False:
            embed = await accessDeniedCustom("Неверная ссылка")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        embed.set_thumbnail(url=m_thumbnail)

        await save_embed_dict(embed, interaction.author)

        await interaction.response.edit_message(
            embed=embed, view=EmbedCreator(interaction.author)
        )
        return


class ImageModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Ссылка на картинку",
                placeholder="URL",
                custom_id="m_image",
                style=TextInputStyle.short,
                required=False,
            )
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_image = interaction.text_values["m_image"]

        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        if check_url(m_image) is False:
            embed = await accessDeniedCustom("Неверная ссылка")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        embed.set_image(url=m_image)

        await save_embed_dict(embed, interaction.author)

        await interaction.response.edit_message(
            embed=embed, view=EmbedCreator(interaction.author)
        )
        return


class TitleModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Название",
                placeholder="",
                custom_id="m_title",
                style=TextInputStyle.short,
                max_length=50,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Описание",
                placeholder="",
                custom_id="m_desc",
                style=TextInputStyle.paragraph,
                max_length=256,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Цвет",
                placeholder="Без #",
                custom_id="m_color",
                style=TextInputStyle.short,
                max_length=6,
                min_length=3,
                required=True,
            ),
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        dict_embed = interaction.message.embeds[0].to_dict()

        dict_embed[f"title"] = interaction.text_values["m_title"]
        dict_embed[f"description"] = interaction.text_values["m_desc"]
        dict_embed[f"color"] = int(interaction.text_values["m_color"], 16)

        embed = disnake.Embed().from_dict(dict_embed)

        await save_embed_dict(embed, interaction.author)

        await interaction.response.edit_message(
            embed=embed, view=EmbedCreator(interaction.author)
        )
        return


class TextModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Текст",
                placeholder="",
                custom_id="m_text",
                style=TextInputStyle.paragraph,
                max_length=2000,
                required=False,
            )
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        content = interaction.text_values["m_text"]

        async with AsyncSession(engine) as session:
            await session.execute(
                update(User_global)
                .where(User_global.user_id == interaction.author.id)
                .values(embed_text=content)
            )
            await session.commit()

        await interaction.response.edit_message(content)
        return


class AddField(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Название",
                placeholder="",
                custom_id="m_name",
                style=TextInputStyle.paragraph,
                max_length=512,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Значение",
                placeholder="",
                custom_id="m_value",
                style=TextInputStyle.paragraph,
                max_length=512,
                required=True,
            ),
            disnake.ui.TextInput(
                label="В линию",
                placeholder="Да / нет",
                custom_id="m_inline",
                style=TextInputStyle.short,
                required=True,
            ),
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_name = interaction.text_values["m_name"]
        m_value = interaction.text_values["m_value"]
        m_inline = interaction.text_values["m_inline"]

        if m_inline.lower() == "да":
            m_inline = True
        else:
            m_inline = False

        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        embed.add_field(
            name=m_name,
            value=m_value,
            inline=m_inline,
        )

        await save_embed_dict(embed, interaction.author)

        await interaction.response.edit_message(
            embed=embed, view=FieldEditor(embed, interaction.author)
        )
        return


class EditEmbedSelect(disnake.ui.StringSelect):
    def __init__(self, embed: disnake.Embed, message: disnake.Message):
        self.embed = embed
        self.message = message

        num = 0
        options = []
        self.dict_embed = embed.to_dict()

        for field in self.dict_embed["fields"]:
            options.append(
                disnake.SelectOption(
                    value=f"{num}",
                    label=field["name"],
                )
            )
            num += 1

        super().__init__(
            placeholder="Выберите область для изменения",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        await interaction.response.send_modal(
            modal=EditFieldModal(self.embed, int(self.values[0]), self.message),
        )

        return


class EditFieldModal(disnake.ui.Modal):
    def __init__(self, embed: disnake.Embed, num: int, message: disnake.Message):
        self.dict_embed = embed.to_dict()
        self.num = num
        self.message = message

        components = [
            disnake.ui.TextInput(
                label="Название",
                placeholder="",
                custom_id="m_name",
                style=TextInputStyle.paragraph,
                max_length=512,
                required=True,
            ),
            disnake.ui.TextInput(
                label="Значение",
                placeholder="",
                custom_id="m_value",
                style=TextInputStyle.paragraph,
                max_length=512,
                required=True,
            ),
            disnake.ui.TextInput(
                label="В линию",
                placeholder="Да / нет",
                custom_id="m_inline",
                style=TextInputStyle.short,
                required=True,
            ),
        ]
        super().__init__(title="Изменение эмбеда", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        m_inline = interaction.text_values["m_inline"]
        m_name = interaction.text_values["m_name"]
        m_value = interaction.text_values["m_value"]

        if m_inline.lower() == "да":
            m_inline = True
        else:
            m_inline = False

        self.dict_embed["fields"][self.num] = {
            f"name": m_name,
            f"value": m_value,
            f"inline": m_inline,
        }

        embed = disnake.Embed().from_dict(self.dict_embed)

        await save_embed_dict(embed, interaction.author)

        await self.message.edit(
            embed=embed, view=FieldEditor(embed, interaction.author)
        )

        select_view = disnake.ui.View().add_item(
            EditEmbedSelect(embed, interaction.message)
        )

        await interaction.response.edit_message(view=select_view)
        return


class DeleteEmbedSelect(disnake.ui.StringSelect):
    def __init__(self, embed: disnake.Embed, message: disnake):
        self.embed = embed
        self.message = message

        num = 0
        options = []
        self.dict_embed = embed.to_dict()

        for field in self.dict_embed["fields"]:
            options.append(
                disnake.SelectOption(
                    value=f"{num}",
                    label=field["name"],
                )
            )
            num += 1

        super().__init__(
            placeholder="Выберите область для удаления",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        del self.dict_embed["fields"][int(self.values[0])]

        embed = disnake.Embed().from_dict(self.dict_embed)

        select_view = disnake.ui.View().add_item(DeleteEmbedSelect(embed, self.message))

        await save_embed_dict(embed, interaction.author)

        await self.message.edit(
            embed=embed, view=FieldEditor(embed, interaction.author)
        )

        await interaction.response.defer()

        if not embed.to_dict().get("fields"):
            await interaction.delete_original_response()
            return

        await interaction.edit_original_response(view=select_view)
        return


class FieldEditor(disnake.ui.View):
    def __init__(self, embed: disnake.Embed, buttonAuthor: disnake.Member):
        super().__init__(timeout=20)
        self.embed = embed
        self.buttonAuthor = buttonAuthor

        dict_embed = embed.to_dict()
        if not dict_embed.get("fields"):
            self.delete_field.disabled = True
            self.edit_field.disabled = True

    async def interaction_check(self, interaction: disnake.Interaction) -> bool:
        if interaction.author.id != self.buttonAuthor.id:
            embed = await accessDeniedButton(self.buttonAuthor)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Добавить", style=disnake.ButtonStyle.green, emoji="➕", row=1
    )
    async def add_field(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        dict_embed = interaction.message.embeds[0].to_dict()

        try:
            if len(dict_embed["fields"]) == 25:
                embed = await accessDeniedCustom(
                    "Вы достигли максимального кол-ва доступных областей"
                )
                await interaction.send(embed=embed, ephemeral=True, delete_after=15)
                return
        except KeyError:
            pass

        await interaction.response.send_modal(modal=AddField())

    @disnake.ui.button(
        label="Удалить", style=disnake.ButtonStyle.red, emoji="➖", row=1
    )
    async def delete_field(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        select_view = disnake.ui.View().add_item(
            DeleteEmbedSelect(embed, interaction.message)
        )

        await interaction.response.send_message(view=select_view, ephemeral=True)

    @disnake.ui.button(
        label="Изменить", style=disnake.ButtonStyle.secondary, emoji="✅", row=2
    )
    async def edit_field(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        select_view = disnake.ui.View().add_item(
            EditEmbedSelect(embed, interaction.message)
        )

        await interaction.response.send_message(view=select_view, ephemeral=True)

    @disnake.ui.button(
        label="Назад", style=disnake.ButtonStyle.blurple, emoji="⬅️", row=2
    )
    async def back(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.edit_message(view=EmbedCreator(interaction.author))


class EmbedCreator(disnake.ui.View):
    def __init__(self, buttonAuthor: disnake.Member):
        super().__init__(timeout=20)
        self.buttonAuthor = buttonAuthor

    async def interaction_check(self, interaction: disnake.Interaction) -> bool:
        if interaction.author.id != self.buttonAuthor.id:
            embed = await accessDeniedButton(self.buttonAuthor)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @disnake.ui.button(
        label="Текст", style=disnake.ButtonStyle.secondary, emoji="💬", row=1
    )
    async def text(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=TextModal())

    @disnake.ui.button(
        label="Автор", style=disnake.ButtonStyle.secondary, emoji="👤", row=1
    )
    async def change_author(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=AuthorModal())

    @disnake.ui.button(
        label="Название, описание и цвет",
        style=disnake.ButtonStyle.secondary,
        emoji="📝",
        row=1,
    )
    async def change_main(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=TitleModal())

    @disnake.ui.button(
        label="Миниатюра", style=disnake.ButtonStyle.secondary, emoji="🌆", row=1
    )
    async def change_thumbnail(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=ThumbnailModal())

    @disnake.ui.button(
        label="Картинка", style=disnake.ButtonStyle.secondary, emoji="🏞️", row=2
    )
    async def change_image(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=ImageModal())

    @disnake.ui.button(
        label="Футер", style=disnake.ButtonStyle.secondary, emoji="🧷", row=2
    )
    async def change_footer(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=FooterModal())

    @disnake.ui.button(
        label="Области", style=disnake.ButtonStyle.blurple, emoji="📂", row=2
    )
    async def manage_fields(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        dict_embed = interaction.message.embeds[0].to_dict()
        embed = disnake.Embed().from_dict(dict_embed)

        await interaction.response.edit_message(
            view=FieldEditor(embed, interaction.author)
        )

    @disnake.ui.button(
        label="Отправить", style=disnake.ButtonStyle.success, emoji="✉️", row=3
    )
    async def send(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        await interaction.response.send_modal(modal=ChannelSendModal())

    @disnake.ui.button(
        label="Очистить", style=disnake.ButtonStyle.red, emoji="❌", row=3
    )
    async def delete_embed(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        async with AsyncSession(engine) as session:
            await session.execute(
                delete(User_global).where(User_global.user_id == interaction.author.id)
            )
            await session.commit()

        db = await database(interaction.author)

        async with AsyncSession(engine) as session:
            text = await session.scalar(
                select(User_global.embed_text).where(
                    User_global.user_id == interaction.author.id
                )
            )

        if text is None or "<Record text=None>":
            text = None

        embed = disnake.Embed().from_dict(json.loads(db[2].embed_json))

        await interaction.message.edit(
            text,
            embed=embed,
        )

        await interaction.response.defer()


class EmbedCreatorMain(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.save_embed = {}

    @commands.slash_command(
        name="create-embed",
        description="Конструктор эмбедов, которые ты можешь сохранить или " "отправить",
    )
    async def create_embed(self, interaction: disnake.ApplicationCommandInteraction):
        if await defaultMemberChecker(interaction, interaction.author) is False:
            return

        db = await database(interaction.author)

        async with AsyncSession(engine) as session:
            text = await session.scalar(
                select(User_global).where(User_global.user_id == interaction.author.id)
            )

        embed = disnake.Embed().from_dict(json.loads(db[2].embed_json))

        async with AsyncSession(engine) as session:
            await session.execute(
                update(User_global)
                .where(User_global.user_id == interaction.author.id)
                .values(embed_json=str(json.dumps(embed.to_dict())))
            )
            await session.commit()

        self.save_embed = embed.to_dict()
        await interaction.send(
            content=text.embed_text,
            embed=embed,
            view=EmbedCreator(interaction.author),
        )


def setup(bot):
    bot.add_cog(EmbedCreatorMain(bot))
