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
        command_channel_id: int,
        summary_channel_id: int
    ) -> None:
        self.guild_id: int = guild_id
        self.category_id: int = category_id
        self.boss_channel_ids: List[int] = boss_channel_ids
        self.remain_attack_channel_id: int = remain_attack_channel_id
        self.reserve_channel_id: int = reserve_channel_id
        self.command_channel_id: int = command_channel_id

        self.player_data_dict: Dict[int, PlayerData] = {}
        self.reserve_list: List[List[ReserveData]] = [
            [], [], [], [], []
        ]
        self.boss_status_data: Dict[int, List[BossStatusData]] = {}

        self.reserve_message_ids: List[int] = [0, 0, 0, 0, 0]
        self.remain_attack_message_id: int = 0
        self.progress_message_ids: Dict[int, List[int]] = {}

        self.date: str = (datetime.datetime.now(JST) - datetime.timedelta(hours=5)).date()
        self.form_data = FormData()

        self.summary_channel_id: int = summary_channel_id
        self.summary_message_ids: Dict[int, List[int]] = {}

    def initialize_boss_status_data(self, lap: int):
        self.boss_status_data[lap] = [
            BossStatusData(lap, i) for i in range(5)
        ]

    def get_reserve_boss_index(self, message_id: int) -> Optional[int]:
        try:
            return self.reserve_message_ids.index(message_id)
        except ValueError:
            return None

    def get_boss_index_from_channel_id(self, channel_id: int) -> Optional[int]:
        try:
            return self.boss_channel_ids.index(channel_id)
        except ValueError:
            return None

    def get_lap_from_message_id(
        self, message_id: int, boss_index: int
    ) -> Optional[int]:
        """reaction時のmessage_idから周回数を取り出す

        Arguments:
        --------
        message_id: int
            reaction時のメッセージID
        boss_index: int
            ボスに対応したインデックス

        Returns
        -------
        lap: int
            周回数
        """
        for key in self.progress_message_ids.keys():
            if message_id == self.progress_message_ids[key][boss_index]:
                return key
        return None

    def get_latest_lap(self, boss_index: Optional[int] = None) -> int:
        """最新の周回数を取得する"""
        lap = max(self.progress_message_ids.keys())
        if boss_index is None:
            return lap
        while self.progress_message_ids[lap][boss_index] == 0:
            lap -= 1
        return lap
    
    def initialize_progress_data(self) -> None:
        """ボスの進行関連のデータを全て初期化する"""
        self.progress_message_ids = {}
        self.boss_status_data = {}
        self.summary_message_ids = {}
