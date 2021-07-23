from datetime import datetime
from typing import List, Optional

from cogs.cbutil.attack_type import AttackType
from cogs.cbutil.clan_battle_data import ClanBattleData
from cogs.cbutil.player_data import PlayerData
from cogs.cbutil.util import calc_carry_over_time
from setting import JST


class AttackStatus():
    def __init__(self, player_data: PlayerData, attack_type: AttackType, carry_over: bool) -> None:
        self.player_data: PlayerData = player_data
        self.damage: int = 0
        self.memo: str = ""
        self.attacked: bool = False
        self.attack_type: AttackType = attack_type
        self.carry_over = carry_over
        self.created: datetime = datetime.now(JST)
    
    def create_attack_status_txt(self, display_name: str, current_hp: int) -> str:
        """凸状況を表示するためのテキストを作成する
        
        discordの表示名はここでは取れないのでやらない
        """

        txt = self.attack_type.value
        txt += f"{'{:,}'.format(self.damage)}万 {self.memo} " + "持ち越し" * self.carry_over
        if 0 < current_hp < self.damage:
            txt += f" 持ち越し発生: {calc_carry_over_time(current_hp, self.damage)}秒"
        txt += self.player_data.create_simple_txt(display_name)
        return txt

    def update_attack_log(self) -> None:
        """残凸数を更新する"""
        if self.player_data.physics_attack + self.player_data.magic_attack < 3:
            if self.attack_type == AttackType.MAGIC:
                self.player_data.magic_attack += 1
            else:
                self.player_data.physics_attack += 1


class BossStatusData():
    def __init__(self, lap: int, boss_index: int) -> None:
        self.lap: int = lap
        self.max_hp: int = ClanBattleData.get_hp(lap, boss_index)
        self.attack_players: List[AttackStatus] = []
        self.beated: bool = False

    def get_attack_status_index(self, player_data: PlayerData, attacked: bool) -> Optional[int]:
        """後ろから探してplayer_dataが同じ値を持ってるattack_statusのindexを返す"""
        for i, attack_status in enumerate(self.attack_players[::-1]):
            if attack_status.player_data == player_data and attack_status.attacked == attacked:
                return len(self.attack_players) - 1 - i
        return None
