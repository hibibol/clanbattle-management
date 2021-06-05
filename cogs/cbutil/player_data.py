from datetime import datetime
from cogs.cbutil.attack_type import AttackType
from typing import List

from setting import EMOJI_MAGIC, EMOJI_PHYSICS, JST


class CarryOver():
    def __init__(self, attack_type: AttackType, boss_index: int) -> None:
        self.attack_type = attack_type
        self.boss_index = boss_index
        self.carry_over_time = -1
        self.created = datetime.now(JST)


class PlayerData():
    def __init__(self, user_id: int) -> None:
        self.user_id: int = user_id
        self.physics_attack: int = 0
        self.magic_attack: int = 0
        # self.log: List[Tuple[OperationType, int, Dict]] = []
        self.carry_over_list: List[CarryOver] = []

    def initialize_attack(self) -> None:
        """凸の進捗状況の初期化を実施する"""
        self.physics_attack = 0
        self.magic_attack = 0

    def create_txt(self, display_name: str) -> None:
        """残凸表示時のメッセージを作成する"""
        return f"{display_name} \t {EMOJI_PHYSICS}{self.physics_attack} {EMOJI_MAGIC}{self.magic_attack}"

    def from_dict(self, dict) -> None:
        self.physics_attack = dict["physics_attack"]
        self.magic_attack = dict["magic_attack"]
        self.carry_over_list = dict["carry_over_list"]
