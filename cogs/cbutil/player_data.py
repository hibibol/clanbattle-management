import copy
from datetime import datetime
from typing import List

from cogs.cbutil.attack_type import AttackType
from cogs.cbutil.clan_battle_data import ClanBattleData
from cogs.cbutil.log_data import LogData
from cogs.cbutil.util import create_limit_time_text
from setting import EMOJI_MAGIC, EMOJI_PHYSICS, EMOJI_TASK_KILL, JST


class CarryOver():
    def __init__(self, attack_type: AttackType, boss_index: int) -> None:
        self.attack_type = attack_type
        self.boss_index = boss_index
        self.carry_over_time = -1
        self.created = datetime.now(JST)

    def __str__(self) -> str:
        txt = f"{self.created.strftime('%H時%M分')}発生 {ClanBattleData().boss_names[self.boss_index]}"
        if self.carry_over_time != -1:
            txt += f" {self.carry_over_time}秒"
        return txt + "持ち越し"


class PlayerData():
    def __init__(self, user_id: int) -> None:
        self.user_id: int = user_id
        self.physics_attack: int = 0
        self.magic_attack: int = 0
        self.log: List[LogData] = []
        self.carry_over_list: List[CarryOver] = []
        self.raw_limit_time_text: str = ""
        self.task_kill: bool = False

    def initialize_attack(self) -> None:
        """凸の進捗状況の初期化を実施する"""
        self.physics_attack = 0
        self.magic_attack = 0
        self.carry_over_list = []
        self.task_kill = False
        self.raw_limit_time_text = ""
        self.log = []

    def create_txt(self, display_name: str) -> str:
        """残凸表示時のメッセージを作成する"""
        txt = f"{display_name}\t{EMOJI_PHYSICS}{self.physics_attack} {EMOJI_MAGIC}{self.magic_attack}"
        if self.task_kill:
            txt += f" {EMOJI_TASK_KILL}"
        if self.raw_limit_time_text:
            txt += " " + create_limit_time_text(self.raw_limit_time_text)
        if self.carry_over_list:
            txt += "\n　　-" + '\n　　-'.join([str(carry_over) for carry_over in self.carry_over_list])
        return txt

    def create_simple_txt(self, display_name: str) -> str:
        """進行や予約用に表示するメッセージを作成する"""
        txt = f"\n　　- {display_name} "\
            + f"({self.physics_attack+self.magic_attack}/3"\
            + f" 物{self.physics_attack}魔{self.magic_attack})" + self.task_kill * f" {EMOJI_TASK_KILL}"
        if self.raw_limit_time_text:
            txt += " " + create_limit_time_text(self.raw_limit_time_text)
        return txt

    def from_dict(self, dict) -> None:
        self.physics_attack = dict["physics_attack"]
        self.magic_attack = dict["magic_attack"]
        self.carry_over_list = dict["carry_over_list"]

    def to_dict(self) -> dict:
        return {
            "physics_attack": self.physics_attack,
            "magic_attack": self.magic_attack,
            "carry_over_list": copy.deepcopy(self.carry_over_list)
        }
