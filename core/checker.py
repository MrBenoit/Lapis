import json
from io import BytesIO

import asyncpg
import disnake

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import *
from core.messages import *
from core.vars import *


async def defaultMemberChecker(interaction, member) -> bool:
    if member.bot:
        return False

    if not member.guild or not interaction.author.guild:
        return False

    if not interaction.channel.permissions_for(interaction.author).send_messages:
        return False
    return True


async def database(member: disnake.Member):
    """
    return:

    [0] - Users

    [1] - Guilds

    [2] - GlobalUsers
    """

    user = await userDB(member.guild, member)
    guild = await guildDB(member.guild)
    globalUser = await globalUsersDB(member)

    return [user, guild, globalUser]


async def levelUpChannel(guild: disnake.Guild) -> int | None:
    async with AsyncSession(engine) as session:
        channel_id = await session.scalar(
            select(Guilds.level_up_channel).where(Guilds.guild_id == guild.id)
        )
        return channel_id


async def guildDB(
    guild: disnake.Guild,
):
    try:
        async with AsyncSession(engine) as session:
            queryGuild = await session.scalar(
                select(Guilds).where(Guilds.guild_id == guild.id)
            )
    except IntegrityError as e:
        print(f"Ошибка уникальности: {e}")
        pass

    if not queryGuild:
        async with AsyncSession(engine) as session:
            session.add(Guilds(guild_id=guild.id))
            await session.commit()

        async with AsyncSession(engine) as session:
            queryGuild = await session.scalar(
                select(Guilds).where(Guilds.guild_id == guild.id)
            )
    return queryGuild


async def userDB(guild: disnake.Guild, member: disnake.Member):
    try:
        async with AsyncSession(engine) as session:
            queryUser = await session.scalar(
                select(Users).where(
                    and_(Users.user_id == member.id, Users.guild_id == guild.id)
                )
            )
    except IntegrityError as e:
        print(f"Ошибка уникальности: {e}")
        pass

    if not queryUser:
        async with AsyncSession(engine) as session:
            session.add(Users(user_id=member.id, guild_id=guild.id))
            await session.commit()

        async with AsyncSession(engine) as session:
            queryUser = await session.scalar(
                select(Users).where(
                    and_(Users.user_id == member.id, Users.guild_id == guild.id)
                )
            )
    return queryUser


async def globalUsersDB(member: disnake.Member):
    embed = disnake.Embed(
        title=f"Пустой эмбед",
        description=f"Тут можно что-то написать",
        color=EmbedColor.MAIN_COLOR.value,
    )
    embed_json = json.dumps(embed.to_dict())

    try:
        async with AsyncSession(engine) as session:
            userGlobal = await session.scalar(
                select(User_global).where(
                    User_global.user_id == member.id,
                )
            )
    except IntegrityError as e:
        print(f"Ошибка уникальности: {e}")
        pass

    if not userGlobal:
        async with AsyncSession(engine) as session:
            session.add(User_global(user_id=member.id, embed_json=embed_json))
            await session.commit()

        async with AsyncSession(engine) as session:
            userGlobal = await session.scalar(
                select(User_global).where(
                    User_global.user_id == member.id,
                )
            )
    return userGlobal


async def getRankCard(guild: disnake.Guild, member: disnake.Member) -> disnake.File:
    user = await userDB(guild, member)

    fonts = {
        "nunitoLightSmallText": ImageFont.truetype(
            "../LapisBot/fonts/Nunito-Light.ttf", 25
        ),
        "nunitoLightLevelTop": ImageFont.truetype(
            "../LapisBot/fonts/Nunito-Light.ttf", 55
        ),
        "nunitoLightScore": ImageFont.truetype(
            "../LapisBot/fonts/Nunito-Light.ttf", 25
        ),
        "nunitoLightName": ImageFont.truetype("../LapisBot/fonts/Nunito-Light.ttf", 48),
    }

    card_images = [
        "../LapisBot/images/banners/rank_card.png",
    ]

    image = Image.open(card_images[user.select_card])
    color = [
        (181, 181, 181),
    ][user.select_card]

    async with AsyncSession(engine) as session:
        queryUser = await session.scalars(
            select(Users)
            .where(and_(Users.user_id == member.id, Users.guild_id == guild.id))
            .order_by(Users.level.desc())
        )

    top = [i.user_id for i in queryUser]
    my_top = top.index(user.user_id) + 1

    idraw = ImageDraw.Draw(image)

    name = member.display_name
    if len(name) > 20:
        name = member.display_name[:20]

    if member.avatar is not None:
        avatar = member.avatar.with_format("png")
        data = BytesIO(await avatar.read())

        pfp = Image.open(data).convert("RGBA")
        pfp = pfp.resize((140, 140))

        mask = Image.new("L", (140, 140), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + (140, 140), fill=255)

        avatar_rounded = Image.new("RGBA", (140, 140), (255, 255, 255, 0))
        avatar_rounded.paste(pfp, (0, 0), mask)

        image.paste(avatar_rounded, (40, 30), avatar_rounded)

    total_score = 5 * (user.level**2) + (50 * user.level) + 100

    procent = user.exp / total_score
    pos = round(procent * 620 + 210)
    if pos <= 295:
        idraw.ellipse((210, 130, 250, 169), fill=color)
    else:
        idraw.rounded_rectangle(
            (210, 130, min(pos, 830), 169), width=40, fill=color, radius=40
        )

    xp_number = f"{user.exp} / {total_score} ({round(procent * 100, 2)}%)"

    idraw.text((220, 15), name, font=fonts["nunitoLightName"])
    idraw.text((220, 96), "ур.", font=fonts["nunitoLightSmallText"])
    idraw.text(
        (250, 124), str(user.level), font=fonts["nunitoLightLevelTop"], anchor="ls"
    )

    level_text = str(my_top)
    if user.level in range(1, 9):
        idraw.text(
            (300 + (len(level_text) - 1) * 25, 96),
            "топ",
            font=fonts["nunitoLightSmallText"],
        )
        idraw.text(
            (350 + (len(level_text) - 1) * 45, 124),
            f"#{level_text}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )
    elif user.level in range(10, 99):
        idraw.text(
            (320 + (len(level_text) - 1) * 35, 96),
            "топ",
            font=fonts["nunitoLightSmallText"],
        )
        idraw.text(
            (365 + (len(level_text) - 1) * 55, 124),
            f"#{level_text}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )
    elif user.level in range(100, 1000):
        idraw.text(
            (350 + (len(level_text) - 1) * 45, 96),
            "топ",
            font=fonts["nunitoLightSmallText"],
        )
        idraw.text(
            (395 + (len(level_text) - 1) * 55, 124),
            f"#{level_text}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )

    idraw.text((489, 148), xp_number, font=fonts["nunitoLightScore"], anchor="mm")

    buffer = BytesIO()
    image.save(buffer, "png", optimize=True)
    file = disnake.File(BytesIO(buffer.getvalue()), filename=f"{member.name}.png")
    return file
