from enum import Enum

from setting import EMOJI_CARRYOVER, EMOJI_MAGIC, EMOJI_PHYSICS


class AttackType(Enum):
    MAGIC = EMOJI_MAGIC
    PHYSICS = EMOJI_PHYSICS
    CARRYOVER = EMOJI_CARRYOVER


ATTACK_TYPE_DICT = {
    EMOJI_PHYSICS: AttackType.PHYSICS,
    EMOJI_MAGIC: AttackType.MAGIC,
    EMOJI_CARRYOVER: AttackType.CARRYOVER
}

ATTACK_TYPE_DICT_FOR_COMMAND = {
    EMOJI_PHYSICS: AttackType.PHYSICS,
    EMOJI_MAGIC: AttackType.MAGIC,
    EMOJI_CARRYOVER: AttackType.CARRYOVER,
    "p": AttackType.PHYSICS,
    "b": AttackType.PHYSICS,
    "P": AttackType.PHYSICS,
    "B": AttackType.PHYSICS,
    "物": AttackType.PHYSICS,
    "物理": AttackType.PHYSICS,
    "m": AttackType.MAGIC,
    "M": AttackType.MAGIC,
    "魔": AttackType.MAGIC,
    "魔法": AttackType.MAGIC,
    "co": AttackType.CARRYOVER,
    "c": AttackType.CARRYOVER,
    "持ち": AttackType.CARRYOVER,
    "持ち越し": AttackType.CARRYOVER,
    "持": AttackType.CARRYOVER,
    "持越": AttackType.CARRYOVER
}
