from enum import Enum, auto


class OperationType(Enum):
    ATTACK_DECLAR = auto()
    ATTACK = auto()
    LAST_ATTACK = auto()
    PROGRESS_LAP = auto()


OPERATION_TYPE_DESCRIPTION_DICT = {
    OperationType.ATTACK_DECLAR: "凸宣言",
    OperationType.ATTACK: "ボスへの凸",
    OperationType.LAST_ATTACK: "ボスの討伐",
    OperationType.PROGRESS_LAP: "周の進行"
}