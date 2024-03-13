from disnake.abc import Connectable
from mafic import Player, Track

from .bot import LapisBot


class LapisPlayer(Player):
    def __init__(self, client: LapisBot, channel: Connectable) -> None:
        super().__init__(client, channel)
        self.queue: list[Track] = []
