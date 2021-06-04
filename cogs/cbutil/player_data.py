from typing import Dict, List, Tuple

from cogs.cbutil.operation_type import OperationType
from setting import EMOJI_MAGIC, EMOJI_PHYSICS


class PlayerData():
    def __init__(self, user_id: int) -> None:
        self.user_id: int = user_id
        self.physics_attack: int = 0
        self.magic_attack: int = 0
        self.carry_over: bool = False
        self.carry_over_time: int = 0
        self.log: List[Tuple[OperationType, int, Dict]] = []

    def initialize_attack(self) -> None:
        """凸の進捗状況の初期化を実施する"""
        self.physics_attack = 0
        self.magic_attack = 0
        self.carry_over = False
        self.carry_over_time = 0

    def create_txt(self, display_name: str) -> None:
        """残凸表示時のメッセージを作成する"""
        return f"{display_name} \t {EMOJI_PHYSICS}{self.physics_attack} {EMOJI_MAGIC}{self.magic_attack}"

    def from_dict(self, dict) -> None:
        self.physics_attack = dict["physics_attack"]
        self.magic_attack = dict["magic_attack"]
        self.carry_over = dict["carry_over"]
        self.carry_over_time = dict["carry_over_time"]
