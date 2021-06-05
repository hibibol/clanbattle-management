from typing import List, Optional, Tuple

import discord


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


async def select_from_list(
    bot: discord.ext.commands.Bot,
    channel: discord.TextChannel,
    user: discord.User,
    contents: List,  # 文字列化可能object
    default_message: str
):
    """リストの中からユーザーに選んでもらう
    返り値:
        selected_listのindex
    """
    reaction_number = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    select_message_content = f"{default_message}\n"

    for i, content in enumerate(contents):
        select_message_content += f"{reaction_number[i]}: {str(content)}\n"

    # select_message_content += ""

    select_message = await channel.send(select_message_content, delete_after=60)
    for i in range(len(contents)):
        await select_message.add_reaction(reaction_number[i])
    reaction, _ = await bot.wait_for(
        'reaction_add', timeout=60.0,
        check=lambda reaction, reaction_user: reaction_user == user
        and str(reaction.emoji) in reaction_number and reaction_number.index(str(reaction.emoji)) < len(contents)
    )
    return reaction_number.index(str(reaction.emoji))
