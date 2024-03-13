import asyncpg
import disnake

from core.vars import *


async def maxLevel():
    embed = disnake.Embed(
        title="Вы достигли максимального уровня", color=EmbedColor.MAIN_COLOR.value
    )
    return embed


async def banWords(message: str):
    mats_files = ["core/russian_mats.txt", "core/english_mats.txt"]
    for file_path in mats_files:
        with open(file_path, "r", encoding="utf-8") as f:
            if any(word.strip().lower() in message.lower() for word in f):
                return True


async def accessDeniedCustom(description: str):
    embed = disnake.Embed(
        title=f"{EmbedEmoji.ACCESS_DENIED.value} Отказано в доступе",
        description=description,
        color=EmbedColor.ACCESS_DENIED.value,
    )
    return embed


async def accessDeniedNoMoney(amount: int, authorQueryDBUsers: asyncpg.Record):
    embed = await accessDeniedCustom("У вас недостаточно серебряных монет.")
    embed.add_field(
        name="Баланс",
        value=f"{authorQueryDBUsers.currency:,}{EmbedEmoji.SILVER_COIN.value}",
        inline=True,
    )
    embed.add_field(
        name="Не хватает",
        value=f"{amount - authorQueryDBUsers.currency:,}{EmbedEmoji.SILVER_COIN.value}",
        inline=True,
    )
    return embed


async def accessDeniedButton(buttonAuthor: disnake.Member):
    embed = disnake.Embed(
        title=f"{EmbedEmoji.ACCESS_DENIED.value} Отказано в доступе",
        description="Вы не можете использовать эту кнопку",
        color=EmbedColor.ACCESS_DENIED.value,
    )
    embed.add_field(
        name="> Владелец кнопки", value=f"<@{buttonAuthor.id}>", inline=True
    )
    return embed


async def accessDeniedNotOwner(guildOwner: disnake.Member):
    embed = disnake.Embed(
        title=f"{EmbedEmoji.ACCESS_DENIED.value} Отказано в доступе",
        description="Вы не являетесь владельцем этой гильдии",
        color=EmbedColor.ACCESS_DENIED.value,
    )
    embed.add_field(name="> Владелец гильдии", value=f"<@{guildOwner.id}>", inline=True)
    return embed
