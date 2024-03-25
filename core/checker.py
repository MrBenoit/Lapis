import json
from io import BytesIO

import asyncpg
import disnake
import datetime

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
    user = await database(member)

    font = {
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

    color = [
        (181, 181, 181),
    ][user[0].select_card]
    total_score = 5 * (user[0].level ** 2) + (50 * user[0].level) + 100

    file = await drawing(user[0], member, font, color, total_score, card_images)
    return file


async def drawing(
    user, member: disnake.Member, font, color, total_score: int, card_images
):
    image = Image.open(card_images[user.select_card])
    IDraw = ImageDraw.Draw(image)

    user_rank = await get_user_rank(user, member)
    await draw_name(IDraw, font, member)
    if member.avatar is not None:
        await draw_avatar(image, member)
    await draw_micro(user, IDraw, font, image)
    percent = await draw_score_bar(user, total_score, color, IDraw)
    await draw_text_level(user, IDraw, font, user_rank)
    await draw_xp_score(user, IDraw, font, percent[1], total_score)

    buffer = BytesIO()
    image.save(buffer, "png", optimize=True)
    return disnake.File(BytesIO(buffer.getvalue()), filename=f"{member.name}.png")


async def get_user_rank(user, member: disnake.Member) -> int:
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(Users)
            .where(Users.guild_id == member.guild.id)
            .order_by(Users.level.desc(), Users.exp.desc())
        )
        queryUser = result.scalars().all()

    top = [i.user_id for i in queryUser]
    return top.index(user.user_id) + 1


async def draw_name(IDraw, font, member: disnake.Member):
    name = member.display_name
    if len(name) > 20:
        name = member.display_name[:20]
    return IDraw.text((220, 15), name, font=font["nunitoLightName"])


async def draw_avatar(image, member: disnake.Member):
    avatar = member.avatar.with_format("png")
    data = BytesIO(await avatar.read())

    pfp = Image.open(data).convert("RGBA")
    pfp = pfp.resize((140, 140))

    mask = Image.new("L", (140, 140), 0)
    draw = ImageDraw.Draw(mask)
    corner_radius = 40
    draw.rounded_rectangle((0, 0, 140, 140), fill=255, radius=corner_radius)

    avatar_rounded = Image.new("RGBA", (140, 140), (255, 255, 255, 0))
    avatar_rounded.paste(pfp, (0, 0), mask)

    return image.paste(avatar_rounded, (40, 30), avatar_rounded)


async def draw_micro(user, IDraw, fonts, image):
    micro = Image.open("../LapisBot/images/icons/micro.png").convert("RGBA")
    micro = micro.resize((20, 18))
    mask = micro.split()[3]
    hours = user.all_voice_time // 3600
    minutes = (user.all_voice_time % 3600) // 60
    seconds = (user.all_voice_time % 3600) % 60

    if user.all_voice_time == 0:
        image.paste(micro, (715, 102), mask=mask)
        IDraw.text(
            (740, 120),
            f"0:00:00",
            font=fonts["nunitoLightSmallText"],
            anchor="ls",
        )
        return
    if 1 <= user.all_voice_time <= 35999:
        image.paste(micro, (715, 102), mask=mask)
        IDraw.text(
            (740, 120),
            f"{hours}:{minutes}:{seconds}",
            font=fonts["nunitoLightSmallText"],
            anchor="ls",
        )
        return
    if 359999 >= user.all_voice_time >= 36000:
        image.paste(micro, (700, 102), mask=mask)
        IDraw.text(
            (725, 120),
            f"{hours}:{minutes}:{seconds}",
            font=fonts["nunitoLightSmallText"],
            anchor="ls",
        )
        return
    if 3599999 >= user.all_voice_time >= 360000:
        image.paste(micro, (685, 102), mask=mask)
        IDraw.text(
            (705, 120),
            f"{hours}:{minutes}:{seconds}",
            font=fonts["nunitoLightSmallText"],
            anchor="ls",
        )
        return
    if 35999999 >= user.all_voice_time >= 3600000:
        image.paste(micro, (670, 102), mask=mask)
        IDraw.text(
            (770, 120),
            f"{hours}:{minutes}:{seconds}",
            font=fonts["nunitoLightSmallText"],
            anchor="ls",
        )
        return


async def draw_score_bar(user, total_score: int, color, IDraw):
    percent = user.exp / total_score
    pos = round(percent * 620 + 210)
    if pos <= 295:
        return [IDraw.ellipse((210, 130, 250, 169), fill=color), percent]
    else:
        return [
            IDraw.rounded_rectangle(
                (210, 130, min(pos, 830), 169), width=40, fill=color, radius=40
            ),
            percent,
        ]


async def draw_xp_score(user, IDraw, fonts, percent, total_score):
    xp_number = f"{user.exp} / {total_score}"
    # ({round(percent * 100, 2)}%)
    return IDraw.text(
        (520, 150),
        xp_number,
        font=fonts["nunitoLightScore"],
        anchor="mm",
    )


async def draw_text_level(user, IDraw, fonts, my_top):
    top = str(my_top)

    IDraw.text(
        (260, 124), str(user.level), font=fonts["nunitoLightLevelTop"], anchor="ls"
    )

    IDraw.text((220, 96), "ур.", font=fonts["nunitoLightSmallText"])

    if user.level in range(1, 9):
        IDraw.text(
            (320, 96),
            "топ",
            font=fonts["nunitoLightSmallText"],
        )
        IDraw.text(
            (370, 124),
            f"#{top}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )
        return
    elif user.level in range(10, 99):
        IDraw.text(
            (340, 96),
            "топ",
            font=fonts["nunitoLightSmallText"],
        )
        IDraw.text(
            (390, 124),
            f"#{top}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )
        return
    elif user.level in range(100, 1000):
        IDraw.text(
            (370, 96),
            "топ",
            font=fonts["nunitoLightSmallText"],
        )
        IDraw.text(
            (420, 124),
            f"#{top}",
            font=fonts["nunitoLightLevelTop"],
            anchor="ls",
        )
        return
