from typing import Optional

from cogs.cbutil.operation_type import OperationType

class LogData():
    def __init__(
        self,
        operation_type: OperationType,
        boss_index: int,
        player_data: Optional[dict] = None,  # PlauerData.to_dict()で生成した辞書が入る。
        beated: Optional[bool] = None
    ) -> None:
        self.operation_type = operation_type
        self.boss_index = boss_index
        self.player_data = player_data
        self.beated = beated
