from setting import ICONS
from typing import List, Tuple


class ClanBattleData():
    boss_names: Tuple[str, str, str, str, str] = (
        "ゴブリングレート",
        "ランドスロース",
        "オークチーフ",
        "スピリットホーン",
        "ツインピッグス"
    )
    hp: List[List[int]] = [
        [600, 700, 1000, 1200, 1500],
        [600, 700, 1000, 1200, 1500],
        [700, 900, 1300, 1500, 2000],
        [1700, 1700, 2000, 2100, 2300],
        [8500, 9000, 9500, 10000, 11000]
    ]
    icon: Tuple[str, str, str, str, str] = ICONS

    def get_hp(lap: int, boss_index: int) -> int:
        level_boundaries = [4, 10, 35, 45]
        for i, level_boundary in enumerate(level_boundaries):
            if lap < level_boundary:
                return ClanBattleData.hp[i][boss_index]
        return ClanBattleData.hp[-1][boss_index]
