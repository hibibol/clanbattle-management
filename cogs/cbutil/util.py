from typing import Optional, Tuple


def get_damage(damage_message_txt: str) -> Optional[Tuple[int, str]]:
    """入力内容からダメージとコメントを抽出する

    先頭が数値でない場合は値を返さない

    Returns:
        danage: int
        memo: str
    """
    damage_message_txts = damage_message_txt.split()
    damage_txt = damage_message_txts[0].replace("万", "")
    if damage_txt.isdecimal():
        if len(damage_txt) > 5:
            damage_txt = damage_txt[:-4]
        damage = int(damage_txt)
        memo = " ".join(damage_message_txts[1:])
        return damage, memo
