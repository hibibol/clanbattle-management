import math
from datetime import datetime
from typing import List, Optional, Tuple

import aiohttp
import discord
import jaconv

from setting import JST


def get_damage(damage_message_txt: str) -> Optional[Tuple[int, str]]:
    """入力内容からダメージとコメントを抽出する

    先頭が数値でない場合は値を返さない

    Returns:
        danage: int
        memo: str
    """
    damage_message_txts = damage_message_txt.split()
    damage_txt = jaconv.z2h(damage_message_txts[0].replace("万", ""), digit=True)
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
) -> Optional[int]:
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
    try:
        reaction, _ = await bot.wait_for(
            'reaction_add', timeout=60.0,
            check=lambda reaction, reaction_user: reaction_user == user
            and str(reaction.emoji) in reaction_number and reaction_number.index(str(reaction.emoji)) < len(contents)
        )
        return reaction_number.index(str(reaction.emoji))
    except TimeoutError:
        return None


async def get_from_web_api(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.json()


def create_limit_time_text(raw_limit_time_text: str) -> str:
    spans = [tuple(map(int, span.replace("時", "").split("～"))) for span in raw_limit_time_text.split(", ")]
    fix_spans = []
    min_hour = spans[0][0]
    max_hour = spans[0][1]
    for span in spans[1:]:
        if max_hour == span[0]:
            max_hour = span[1]
        else:
            fix_spans.append((min_hour, max_hour))
            min_hour = span[0]
            max_hour = span[1]
    fix_spans.append((min_hour, max_hour))

    now_hour = datetime.now(JST).hour
    if now_hour < 5:
        now_hour += 24
    time_text_list = []

    for i, span in enumerate(fix_spans):
        if span[1] < now_hour:
            if len(fix_spans) - 1 == i:
                time_text_list.append(f"～{span[1]}時")
        if span[0] > now_hour:
            time_text_list.append(f"{span[0]}～{span[1]}時")
        if span[0] <= now_hour and now_hour < span[1]:
            time_text_list.append(f"～{span[1]}時")
    return ", ".join(time_text_list)


def calc_carry_over_time(remain_hp: int, damage: int) -> int:
    carry_over_time = math.ceil((1-remain_hp/damage) * 90 + 20)
    if carry_over_time > 90:
        carry_over_time = 90
    return carry_over_time
