from forex_python.converter import CurrencyRates, RatesNotAvailableError
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from io import BytesIO
import disnake
from disnake.ext import commands
from core import *


class CurrencyConvert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Конвертация валют")
    async def convert(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        amount: float = commands.Param(name="количество"),
        value_from: str = commands.Param(
            name="из", choices=CURRENCIES, description="Валюта"
        ),
        value_to: str = commands.Param(
            name="в", choices=CURRENCIES, description="Валюта"
        ),
        date_start: str = commands.Param(
            name="с", default=None, description="Формат даты: дд.мм.гггг"
        ),
        date_end: str = commands.Param(
            name="по", default=None, description="Формат даты: дд.мм.гггг"
        ),
    ):
        await interaction.response.defer()
        user = await database(interaction.author)
        amount = round(amount)

        if amount <= 0:
            embed = await accessDeniedCustom("Укажите число больше 0")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        CR = CurrencyRates()
        result = CR.convert(value_from, value_to, amount)
        now = CR.get_rate(value_from, value_to)

        # async def create_embed()
        embed = disnake.Embed(
            title="Конвертер валют",
            description=f"**{round(amount)} {value_from}** = **{round(result, 2)} {value_to}**",
            color=EmbedColor.MAIN_COLOR.value,
        )
        if amount != 1:
            embed.add_field(
                name="Текущий курс",
                value=f"**1 {value_from}** = **{round(now, 2)} {value_to}**",
                inline=False,
            )

        if not date_start:
            return

        date_start_dt = datetime.strptime(date_start, "%d.%m.%Y")

        if not date_end:
            date_end_dt = datetime.now()
        else:
            date_end_dt = datetime.strptime(date_end, "%d.%m.%Y")

        if date_start_dt > date_end_dt:
            embed = await accessDeniedCustom("Укажите правильную дату")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        date_generated = [
            date_start_dt + timedelta(days=x)
            for x in range((date_end_dt - date_start_dt).days + 1)
        ]
        if len(date_generated) > 30 and not user[2].prem_time or not user[1].prem_time:
            embed = await accessDeniedCustom(
                "Только пользователи/серверы с подпиской могут смотреть график больше чем за месяц"
            )
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return
        try:
            exchange_rates = [
                CR.get_rate(value_from, value_to, date) for date in date_generated
            ]
        except RatesNotAvailableError:
            embed = await accessDeniedCustom("Возникла ошибка при получении данных")
            await interaction.send(embed=embed, ephemeral=True, delete_after=15)
            return

        plt.figure(
            figsize=(10, 6),
            facecolor="#383E54",
        )
        ax = plt.gca()
        ax.set_facecolor("#383E54")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
        plt.plot(
            date_generated,
            exchange_rates,
            label=f"{value_from} к {value_to}",
            color="#A1A1A1",
            marker=".",
        )
        plt.title(
            f"Обменный курс от {value_from} к {value_to}",
            color="#A1A1A1",
            fontsize=15,
        )
        legend = plt.legend(fontsize=12, facecolor="#383E54")
        for text in legend.get_texts():
            text.set_color("#a1a1a1")

        plt.xticks(rotation=20, color="#A1A1A1", fontsize=15)
        plt.yticks(rotation=20, color="#A1A1A1", fontsize=15)
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close()

        file = disnake.File(buffer, filename="exchange_rate.png")

        embed.set_image(file=file or None)

        await interaction.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(CurrencyConvert(bot))
