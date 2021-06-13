import asyncio
from datetime import datetime
from cogs.cbutil.util import get_from_web_api
from setting import BASE_URL, JST
from typing import List, Tuple


class ClanBattleData():
    boss_names: List[str] = []
    hp: List[List[int]] = []
    boudaries: List[Tuple[int]] = []
    icon: List[str] = []

    @staticmethod
    def get_hp(lap: int, boss_index: int) -> int:
        for i, (lap_from, lap_to) in enumerate(ClanBattleData.boudaries):
            if lap_from <= lap <= lap_to or (lap_from <= lap and lap_to == -1):
                return ClanBattleData.hp[i][boss_index]
        return ClanBattleData.hp[-1][boss_index]


async def get_clan_battle_data() -> Tuple[List[str], List[List[int]], List[Tuple[int]], List[str]]:
    clan_battle_abstract = await get_from_web_api(BASE_URL + "clanbattles/latest")
    boss_names = clan_battle_abstract["maps"][0]["boss_names"]
    hp_list = []
    boundaries = []
    icons = []
    for i, map in enumerate(clan_battle_abstract["maps"]):
        hp_list_in_level = []
        for id in map["boss_ids"]:
            boss_data = await get_from_web_api(BASE_URL + f"enemies/{id}")
            hp_list_in_level.append(int(boss_data["parameter"]["hp"] // 10000))
            if i == 0:
                icons.append(boss_data["unit"]["icon"])
        hp_list.append(hp_list_in_level)
        boundaries.append((map['lap_from'], map['lap_to']))
    return boss_names, hp_list, boundaries, icons


async def update_clanbattledata():
    while True:
        if datetime.now(JST).strftime('%H:%M') == "04:59" or not ClanBattleData.boss_names:
            clan_battle_data = await get_clan_battle_data()
            ClanBattleData.boss_names = clan_battle_data[0]
            ClanBattleData.hp = clan_battle_data[1]
            ClanBattleData.boudaries = clan_battle_data[2]
            ClanBattleData.icon = clan_battle_data[3]
        await asyncio.sleep(60)
