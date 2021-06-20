import datetime
from typing import Dict, List, Optional

from cogs.cbutil.boss_status_data import BossStatusData
from cogs.cbutil.form_data import FormData
from cogs.cbutil.player_data import PlayerData
from cogs.cbutil.reserve_data import ReserveData
from setting import JST


class ClanData():
    def __init__(
        self,
        guild_id: int,
        category_id: int,
        boss_channel_ids: List[int],
        remain_attack_channel_id: int,
        reserve_channel_id: int,
        command_channel_id: int
    ) -> None:
        self.guild_id: int = guild_id
        self.category_id: int = category_id
        self.boss_channel_ids: List[int] = boss_channel_ids
        self.remain_attack_channel_id: int = remain_attack_channel_id
        self.reserve_channel_id: int = reserve_channel_id
        self.command_channel_id: int = command_channel_id

        self.player_data_dict: Dict[int, PlayerData] = {}
        self.lap: int = 1
        self.reserve_list: List[List[ReserveData]] = [
            [], [], [], [], []
        ]

        self.initialize_boss_status_data()
        self.reserve_message_ids: List[int] = [0, 0, 0, 0, 0]
        self.remain_attack_message_id: int = 0
        self.progress_message_ids: List[int] = [0, 0, 0, 0, 0]

        self.date: str = (datetime.datetime.now(JST) - datetime.timedelta(hours=5)).date()
        self.form_data = FormData()

    def initialize_boss_status_data(self):
        self.boss_status_data = [BossStatusData(self.lap, i) for i in range(5)]

    def get_boss_index_from_channel_id(self, channel_id: int) -> Optional[int]:
        try:
            return self.boss_channel_ids.index(channel_id)
        except ValueError:
            return None
