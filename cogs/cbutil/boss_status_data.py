from datetime import datetime
from typing import List

from cogs.cbutil.attack_type import AttackType
from cogs.cbutil.clan_battle_data import ClanBattleData
from cogs.cbutil.player_data import PlayerData
from setting import EMOJI_MAGIC, EMOJI_PHYSICS, JST


class BossStatusData():
    def __init__(self, lap: int, boss_index: int) -> None:
        self.lap: int = lap
        self.max_hp: int = ClanBattleData.get_hp(lap, boss_index)
        self.attack_players: List[AttackStatus] = []
        self.beated = False


class AttackStatus():
    def __init__(self, player_data: PlayerData, attack_type: AttackType, carry_over: bool) -> None:
        self.player_data: PlayerData = player_data
        self.damage: int = 0
        self.memo: str = ""
        self.attacked: bool = False
        self.attack_type: AttackType = attack_type
        self.carry_over = carry_over
        self.created: datetime = datetime.now(JST)
    
    def create_attack_status_txt(self, display_name: str) -> str:
        """凸状況を表示するためのテキストを作成する
        
        discordの表示名はここでは取れないのでやらない
        """

        txt = self.attack_type.value
        txt += f"{'{:,}'.format(self.damage)}万 {self.memo} {display_name}  "\
            + f"({self.player_data.physics_attack+self.player_data.magic_attack}/3"\
            + f" 物{self.player_data.physics_attack}魔{self.player_data.magic_attack})"\
            + "持ち越し" * self.carry_over
        return txt

    def update_attack_log(self) -> None:
        """残凸数を更新する"""
        if self.player_data.physics_attack + self.player_data.magic_attack < 3:
            if self.attack_type == AttackType.MAGIC:
                self.player_data.magic_attack += 1
            else:
                self.player_data.physics_attack += 1
