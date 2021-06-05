from enum import Enum, auto


class OperationType(Enum):
    ATTACK_DECLAR = auto()
    ATTACK = auto()
    LAST_ATTACK = auto()
    PROGRESS_LAP = auto()
