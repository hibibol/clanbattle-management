from enum import Enum

from setting import EMOJI_MAGIC, EMOJI_PHYSICS, EMOJI_CARRYOVER


class AttackType(Enum):
    MAGIC = EMOJI_MAGIC
    PHYSICS = EMOJI_PHYSICS
    CARRYOVER = EMOJI_CARRYOVER


ATTACK_TYPE_DICT = {
    EMOJI_PHYSICS: AttackType.PHYSICS,
    EMOJI_MAGIC: AttackType.MAGIC,
    EMOJI_CARRYOVER: AttackType.CARRYOVER
}
