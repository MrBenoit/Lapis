import disnake
from disnake.ext import commands

from core.checker import *
from io import BytesIO

import qrcode


class QRGenerator(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(description="Создание QR кода")
    async def qr_generator(
        self,
        inter: disnake.ApplicationCommandInteraction,
        url: str = commands.Param(name="ссылка"),
    ):
        filename = f"{url}.png"
        img = qrcode.make(url)

        buffer = BytesIO()
        img.save(buffer, "png")
        file = disnake.File(BytesIO(buffer.getvalue()), filename=filename)

        await inter.send(file=file, ephemeral=True)


def setup(bot):
    bot.add_cog(QRGenerator(bot))
