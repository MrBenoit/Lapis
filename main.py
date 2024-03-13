import locale
import os
import traceback
import disnake
from disnake.ext.commands import InteractionBot
from dotenv import load_dotenv

from overwritten import LapisBot

load_dotenv()
locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")


bot = InteractionBot(
    intents=disnake.Intents.all(),
    owner_id=1004649810323845142,
    allowed_mentions=disnake.AllowedMentions(
        users=True,
        everyone=True,
        roles=True,
        replied_user=True,
    ),
)

local_path = [
    "extensions/Leveling",
    "extensions/Info",
    "extensions/Statistic",
    "extensions/PrivateChannels",
    "extensions/Utils",
    "extensions/Fun/Actions",
    "extensions/Fun/Casino",
    "extensions/Fun/Emotions",
    "extensions/Fun",
    "extensions/Setup",
    "extensions/Economy",
    "extensions/Moderation",
    "extensions/ReportSystem",
    "extensions",
]

if __name__ == "__main__":
    for current_path in local_path:
        for extension in disnake.utils.search_directory(f"{current_path}"):
            try:
                bot.load_extension(extension)
                print(f"Extension {extension} load successful")
            except Exception as error:
                print(f"Failed to load extension {extension}")
                errors = traceback.format_exception(
                    type(error), error, error.__traceback__
                )
                print(errors)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))


# @bot.slash_command(
#     description="Загрузить модуль",
#     guild_ids=[
#         1025853938207047762
#     ]
# )
# @commands.is_owner()
# async def load(
#     interaction: disnake.ApplicationCommandInteraction,
#     directory: str = commands.Param(name="папка", default=None),
#     file: str = commands.Param(name="файл", default=None),
# ):
#     path = f"extensions.{directory}.{file}"
#
#     bot.load_extension(name=path)
#
#     await interaction.send(
#         embed=disnake.Embed(
#             title=f"Загрузка модуля",
#             description=f"Модуль {path} загружен",
#             color=EmbedColor.MAIN_COLOR.value,
#         ),
#         ephemeral=True,
#     )
#     return
#
#
# @bot.slash_command(
#     description="Отключить модуль",
#     guild_ids=[
#         1025853938207047762
#     ]
# )
# @commands.is_owner()
# async def unload(
#     interaction: disnake.ApplicationCommandInteraction,
#     directory: str = commands.Param(name="папка", default=None),
#     file: str = commands.Param(name="файл", default=None),
# ):
#     path = f"extensions.{directory}.{file}"
#
#     bot.unload_extension(name=path)
#     bot.load_extension(name=path)
#
#     await interaction.send(
#         embed=disnake.Embed(
#             title=f"Отключение модуля",
#             description=f"Модуль {path} отключен",
#             color=EmbedColor.MAIN_COLOR.value,
#         ),
#         ephemeral=True,
#     )
#     return
#
#
# @bot.slash_command(
#     description="Перезагрузить модуль",
#     guild_ids=[
#         1025853938207047762
#     ]
# )
# @commands.is_owner()
# async def reload(
#     interaction: disnake.ApplicationCommandInteraction,
#     directory: str = commands.Param(name="папка", default=None),
#     file: str = commands.Param(name="файл", default=None),
# ):
#     path = f"extensions.{directory}.{file}"
#
#     bot.unload_extension(name=path)
#     bot.load_extension(name=path)
#
#     await interaction.send(
#         embed=disnake.Embed(
#             title=f"Перезагрузка модуля",
#             description=f"Модуль {path} перезагружен",
#             color=EmbedColor.MAIN_COLOR.value,
#         ),
#         ephemeral=True,
#     )
#     return
