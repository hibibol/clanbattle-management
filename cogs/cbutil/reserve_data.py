from enum import Enum
from typing import Tuple

from cogs.cbutil.attack_type import AttackType
from cogs.cbutil.player_data import PlayerData
from setting import EMOJI_ANY, EMOJI_ONLY


class ReserveType(Enum):
    ONLY = EMOJI_ONLY
    ANY = EMOJI_ANY


class ReserveData():
    def __init__(
        self, player_data: PlayerData, attack_type: AttackType
    ) -> None:
        self.attack_type: AttackType = attack_type
        self.player_data: PlayerData = player_data
        # self.reserve_type: ReserveType = reserve_info[0]
        self.damage: int = -1
        self.memo: str = ""
        self.carry_over: bool = False

    def create_reserve_txt(self, display_name: str) -> str:
        """予約状況を表示するためのテキストを作成する"""

        # txt = self.reserve_type.value + self.attack_type.value
        txt = f"{self.attack_type.value} {display_name}"
        if self.damage != -1:
            txt += f" {'{:,}'.format(self.damage)}万 {self.memo} "\
                + "持ち越し" * self.carry_over
        
        return txt

    def set_reserve_info(self, reserve_info: Tuple[int, str, bool]) -> None:
        self.damage: int = reserve_info[0]
        self.memo: str = reserve_info[1]
        self.carry_over: bool = reserve_info[2]

    def __str__(self) -> str:
        txt = self.attack_type.value
        if self.damage != -1:
            txt += f" {'{:,}'.format(self.damage)}万 {self.memo} "\
                + "持ち越し" * self.carry_over
        return txt


RESERVE_TYPE_DICT = {
    EMOJI_ONLY: ReserveType.ONLY,
    EMOJI_ANY: ReserveType.ANY
}
