import disnake
from disnake.ext import commands, tasks

from sqlalchemy import select, delete, insert, update
from sqlalchemy import and_
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core.checker import *
from core.vars import *
from core.models import *


class BotSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_bot_status.start()

    @tasks.loop(minutes=5.0)
    async def change_bot_status(self):
        await self.bot.change_presence(
            status=disnake.Status.online,
            activity=disnake.Activity(
                type=disnake.ActivityType.watching,
                name=f"{len(self.bot.users):,} участников",
            ),
        )
        await self.bot.wait_until_ready()

    @change_bot_status.before_loop
    async def before_change_bot_status(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        async with AsyncSession(engine) as session:
            guilds = await session.scalars(select(Guilds.guild_id))
        guild_list = []

        for i in guilds:
            guild_list.append(i)

        for guild in self.bot.guilds:
            if guild.id not in guild_list:
                async with AsyncSession(engine) as session:
                    session.add(Guilds(guild_id=guild.id))
                    await session.commit()
                    print(f"Guild added {guild.name} | {guild.id}")

    @commands.slash_command()
    async def testaa(self, interaction: disnake.ApplicationCommandInteraction):
        channel = self.bot.get_channel(652250028781600778)
        embed = disnake.Embed(
            title="Поддержка проекта | Donate for the development of the project",
            colour=EmbedColor.MAIN_COLOR.value,
        )
        embed.set_thumbnail(
            url="https://media.discordapp.net/attachments/1179149649823662113/1179351041779699742/i8Wj65ikPQs.png?ex=65faaa3f&is=65e8353f&hm=6e199ca1d3bdc6f61ef6baad044056531441f8fd89ec6b5239a3fb75fde4f1e3&=&format=webp&quality=lossless&width=942&height=942"
        )
        embed.add_field(
            name="Сбербанк | Sberbank",
            value=f"Номер карты (Card Number): 4276 3500 1180 2897\n"
            f"На имя (Of name): А. BRESKALENKO",
            inline=False,
        )
        embed.add_field(
            name="Ю money",
            value="[ссылка / link](https://yoomoney.ru/to/4100116927715862)",
        )
        embed.add_field(
            name="Donation for EU/US players",
            value="[ссылка / link](https://clients.xlgames.pro/clanpay/pay/4o96r-2aWzTP-MslXdK-I5mthE )",
            inline=False,
        )
        embed.add_field(
            name="Игровой магазин | Online store",
            value="[ссылка / link](https://outofdeath.ru)",
            inline=False,
        )
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(BotSettings(bot))
