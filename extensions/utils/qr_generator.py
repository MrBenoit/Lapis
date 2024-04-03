import disnake
from disnake.ext import commands
import qrcode
from core import *
from io import BytesIO


class QRGenerator(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(description="Создание QR кода")
    async def qr_generator(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        url: str = commands.Param(name="ссылка"),
    ):
        filename = f"{url}.png"
        img = qrcode.make(url)

        buffer = BytesIO()
        img.save(buffer, "png")
        file = disnake.File(BytesIO(buffer.getvalue()), filename=filename)

        await interaction.send(file=file, ephemeral=True)


def setup(bot):
    bot.add_cog(QRGenerator(bot))
