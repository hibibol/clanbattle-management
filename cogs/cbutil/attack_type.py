from enum import Enum

from setting import EMOJI_MAGIC, EMOJI_PHYSICS


class AttackType(Enum):
    MAGIC = EMOJI_MAGIC
    PHYSICS = EMOJI_PHYSICS


ATTACK_TYPE_DICT = {
    EMOJI_PHYSICS: AttackType.PHYSICS,
    EMOJI_MAGIC: AttackType.MAGIC
}
