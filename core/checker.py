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


def mask_circle_transparent(pil_img, blur_radius, offset=0):
    offset = blur_radius * 2 - offset
    mask = Image.new("L", pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset), fill=255
    )
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    result = pil_img.copy()
    result.putalpha(mask)

    return result


async def getRankCard(guild: disnake.Guild, member: disnake.Member):
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
        "../LapisBot/images/banners/rank_card_prem1.png",
        "../LapisBot/images/banners/rank_card_prem2.png",
        "../LapisBot/images/banners/rank_card_prem3.png",
        "../LapisBot/images/banners/rank_card_prem4.png",
    ]

    image = Image.open(card_images[user.select_card])
    color = [
        (145, 145, 145),
        (77, 165, 168),
        (95, 62, 194),
        (196, 47, 39),
        (77, 82, 130),
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

        pfp = Image.open(data)
        pfp = pfp.resize((145, 145))
        pfp = mask_circle_transparent(pfp, 0)
        image.paste(pfp, (34, 24), pfp)

    total_score = 5 * (user.level**2) + (50 * user.level) + 100

    procent = user.exp / total_score
    pos = round(procent * 620 + 209)
    line = [209, 148, min(pos, 810), 148] if pos < 810 else [206, 148, 791, 148]
    ec1, ec2 = pos - 20, pos + 20 if pos < 810 else 790
    eclimpse = [ec1, 129, ec2, 168] if pos < 810 else [770, 129, 810, 168]

    xp_number = f"{user.exp} / {total_score} ({round(procent * 100, 2)}%)"

    idraw.text((189, 15), name, font=fonts["nunitoLightName"])
    idraw.text((215, 96), "ур.", font=fonts["nunitoLightSmallText"])
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
            (360 + (len(level_text) - 1) * 55, 124),
            f"#{level_text}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )
    elif user.level in range(100, 999):
        idraw.text(
            (350 + (len(level_text) - 1) * 45, 96),
            "топ",
            font=fonts["nunitoLightSmallText"],
        )
        idraw.text(
            (390 + (len(level_text) - 1) * 65, 124),
            f"#{level_text}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )

    idraw.ellipse((189, 129, 229, 168), fill=color)
    idraw.line(line, fill=color, width=40)
    idraw.ellipse(eclimpse, fill=color)
    idraw.text((489, 148), xp_number, font=fonts["nunitoLightScore"], anchor="mm")

    buffer = BytesIO()
    image.save(buffer, "png", optimize=True)
    file = disnake.File(BytesIO(buffer.getvalue()), filename=f"{member.name}.png")
    return file
