import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from logging import getLogger
from typing import List, Optional, Tuple

import discord
from discord import colour
from discord.channel import TextChannel
from discord.errors import Forbidden, HTTPException
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_choice, create_option

from cogs.cbutil.attack_type import ATTACK_TYPE_DICT, AttackType
from cogs.cbutil.boss_status_data import AttackStatus
from cogs.cbutil.clan_battle_data import ClanBattleData, update_clanbattledata
from cogs.cbutil.clan_data import ClanData
from cogs.cbutil.form_data import create_form_data
from cogs.cbutil.gss import get_sheet_values, get_worksheet_list
from cogs.cbutil.log_data import LogData
from cogs.cbutil.operation_type import (OPERATION_TYPE_DESCRIPTION_DICT,
                                        OperationType)
from cogs.cbutil.player_data import CarryOver, PlayerData
from cogs.cbutil.reserve_data import ReserveData
from cogs.cbutil.sqlite_util import SQLiteUtil
from cogs.cbutil.util import get_damage, select_from_list
from setting import (BOSS_COLOURS, EMOJI_ATTACK, EMOJI_CANCEL, EMOJI_CARRYOVER,
                     EMOJI_LAST_ATTACK, EMOJI_MAGIC, EMOJI_NO, EMOJI_PHYSICS,
                     EMOJI_REVERSE, EMOJI_SETTING, EMOJI_TASK_KILL, EMOJI_YES,
                     GUILD_IDS, JST)

logger = getLogger(__name__)

class ClanBattle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ready = False

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("loading ClanBattle data...")
        asyncio.create_task(update_clanbattledata())
        # bossデータの読み込みが完了するまで待つ
        while not ClanBattleData.boudaries:
            await asyncio.sleep(1)
        self.clan_data: defaultdict[int, Optional[ClanData]] = SQLiteUtil.load_clandata_dict()
        self.clan_battle_data = ClanBattleData()
        self.ready = True
        logger.info("ClanBattle Management Ready!")

    @cog_ext.cog_slash(
        description="凸管理するメンバーを追加します。オプションがない場合、コマンドを実行した人が追加されます。",
        options=[
            create_option(
                name="role",
                description="追加したいロール(ロールがついているメンバーをまとめて追加できます)",
                option_type=SlashCommandOptionType.ROLE,
                required=False
            ),
            create_option(
                name="member",
                description="追加したいメンバー",
                option_type=SlashCommandOptionType.USER,
                required=False
            )
        ],
        guild_ids=GUILD_IDS
    )
    async def add(self, ctx: SlashContext, role: Optional[discord.Role] = None, member: Optional[discord.User] = None) -> None:
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return
        player_data_list: List[PlayerData] = []
        if role is None and member is None:
            player_data = PlayerData(ctx.author_id)
            clan_data.player_data_dict[ctx.author_id] = player_data
            player_data_list.append(player_data)

        if member is not None:
            player_data = PlayerData(member.id)
            clan_data.player_data_dict[member.id] = player_data
            player_data_list.append(player_data)

        if role is not None:
            for member in role.members:
                player_data = PlayerData(member.id)
                clan_data.player_data_dict[member.id] = PlayerData(member.id)
                player_data_list.append(player_data)
        await ctx.send(f"{len(player_data_list)}名追加します。")
        await self._update_remain_attack_message(clan_data)
        if player_data_list:
            SQLiteUtil.register_playerdata(clan_data, player_data_list)

    @cog_ext.cog_slash(
        description="凸管理するメンバーを削除します。オプションがない場合、コマンドを実行した人が削除されます。",
        options=[
            create_option(
                name="member",
                description="削除したいメンバー",
                option_type=SlashCommandOptionType.USER,
                required=False
            ),
            create_option(
                name="all",
                description="全てのメンバーを削除します。",
                option_type=SlashCommandOptionType.BOOLEAN,
                required=False
            )
        ],
        guild_ids=GUILD_IDS
    )
    async def remove(self, ctx: SlashContext, member: Optional[discord.User] = None, all: Optional[bool] = None):
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return

        player_data_list: List[PlayerData] = []
        if member is None and all is None:
            if player_data := clan_data.player_data_dict.get(ctx.author.id):
                player_data_list.append(player_data)
            else:
                return await ctx.send(f"{ctx.author.display_name}さんは凸管理対象ではありません。")

        if member:
            if player_data := clan_data.player_data_dict.get(member.id):
                player_data_list.append(player_data)
            else:
                return await ctx.send(f"{member.display_name}さんは凸管理対象ではありません。")

        if all:
            player_data_list += list(clan_data.player_data_dict.values())

        await ctx.send(f"{len(player_data_list)}名のデータを削除します。")
        for player_data in player_data_list:
            for i in range(5):
                clan_data.reserve_list[i] = [
                    reserve_data for reserve_data in clan_data.reserve_list[i]
                    if reserve_data.player_data.user_id != player_data.user_id]
            SQLiteUtil.delete_playerdata(clan_data, player_data)
            del clan_data.player_data_dict[player_data.user_id]
        await self._update_remain_attack_message(clan_data)
        await ctx.channel.send("削除が完了しました。")

    @cog_ext.cog_slash(
        description="凸管理のセットアップを実施します。",
        options=[
            create_option(
                name="category_channel_name",
                description="凸管理を行うカテゴリーチャンネルの名前",
                option_type=SlashCommandOptionType.STRING,
                required=False
            )
        ],
        guild_ids=GUILD_IDS
    )
    async def setup(self, ctx: SlashContext, category_channel_name: str = ""):
        """凸管理用チャンネルを作成するセットアップを実施する"""
        await ctx.send("チャンネルのセットアップを実施します")
        if not category_channel_name:
            category_channel_name = "凸管理"
        try:
            category = await ctx.guild.create_category(category_channel_name)
            summary_channel = await category.create_text_channel("まとめ")
            boss_channels: List[TextChannel] = []
            for i in range(5):
                boss_channel = await category.create_text_channel(f"ボス{i+1}")
                boss_channels.append(boss_channel)
            remain_attack_channel = await category.create_text_channel("残凸把握板")
            reserve_channel = await category.create_text_channel("凸ルート共有板")
            command_channel = await category.create_text_channel("コマンド入力板")
        except Forbidden:
            await ctx.send("チャンネル作成の権限を付与してください。")
            return
        except HTTPException as e:
            await ctx.send(f"チャンネルの作成に失敗しました\n```\n{e.response}\n```")
            return
        clan_data = ClanData(
            ctx.guild_id,
            category.id,
            [boss_channel.id for boss_channel in boss_channels],
            remain_attack_channel.id,
            reserve_channel.id,
            command_channel.id,
            summary_channel.id
        )
        logger.info(f"New ClanData is created: guild={ctx.guild.name}")
        self.clan_data[category.id] = clan_data
        await self._initialize_progress_messages(clan_data, 1)
        await self._initialize_reserve_message(clan_data)
        await self._initialize_remain_attack_message(clan_data)
        SQLiteUtil.register_clandata(clan_data)
        await ctx.channel.send("セットアップが完了しました")

    @cog_ext.cog_slash(
        description="周回数を変更します",
        options=[
            create_option(
                name="lap",
                description="周回数",
                option_type=SlashCommandOptionType.INTEGER,
                required=True
            )
        ],
        guild_ids=GUILD_IDS
    )
    async def lap(self, ctx: SlashContext, lap: int):
        """周回数を設定する"""
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return
        await ctx.send(content=f"周回数を{lap}に設定します")
        # ボス状態に関するすべてのデータを削除する
        clan_data.initialize_progress_data()
        SQLiteUtil.delete_old_data(clan_data, 999)
        await self._initialize_progress_messages(clan_data, lap)
        await self._update_remain_attack_message(clan_data)
        SQLiteUtil.update_clandata(clan_data)

    @cog_ext.cog_slash(
        description="ボスに凸宣言した時の処理を実施します",
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name="member",
                description="処理対象のメンバー(メンションで指定)",
                option_type=SlashCommandOptionType.USER,
                required=True
            ),
            create_option(
                name="attack_type",
                description="凸方法を指定します。",
                option_type=SlashCommandOptionType.STRING,
                required=True,
                choices=[
                    create_choice(
                        name=f"{EMOJI_PHYSICS} 物理凸",
                        value=EMOJI_PHYSICS,
                    ),
                    create_choice(
                        name=f"{EMOJI_MAGIC} 魔法凸",
                        value=EMOJI_MAGIC
                    ),
                    create_choice(
                        name=f"{EMOJI_CARRYOVER} 持ち越し凸",
                        value=EMOJI_CARRYOVER
                    )
                ]
            ),
            create_option(
                name="lap",
                description="周回数 (指定がない場合は今現在のボスが指定されます)",
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            ),
            create_option(
                name="boss_number",
                description="ボス番号 (各ボスの進行用チャンネルで実行する場合は指定する必要がありません)",
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            )
        ]
    )
    async def attack_declare(self, ctx: SlashContext, member: discord.User, attack_type: str, lap: Optional[int] = None, boss_number: Optional[int] = None):
        """コマンドで凸宣言を実施した時の処理を行う"""
        checked = await self.check_command_arguments(ctx, member, lap, boss_number)
        if not checked:
            return
        clan_data, player_data, lap, boss_index = checked

        attack_type_v = ATTACK_TYPE_DICT.get(attack_type)
        if attack_type_v is AttackType.CARRYOVER and not player_data.carry_over_list:
            return ctx.send("持ち越しを所持していません。凸宣言をキャンセルします。")
        await ctx.send(content=f"{member.display_name}の凸を{attack_type_v.value}で{lap}周目{boss_index+1}ボスに宣言します")
        await self._attack_declare(clan_data, player_data, attack_type_v, lap, boss_index)

    @cog_ext.cog_slash(
        description="ボスに凸した時の処理を実施します。",
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name="member",
                description="処理対象のメンバー(メンションで指定)",
                option_type=SlashCommandOptionType.USER,
                required=True
            ),
            create_option(
                name="lap",
                description="周回数 (指定がない場合は今現在のボスが指定されます)",
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            ),
            create_option(
                name="boss_number",
                description="ボス番号 (各ボスの進行用チャンネルで実行する場合は指定する必要がありません)",
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            ),
            create_option(
                name="damage",
                description="与えたダメージ",
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            )
        ]
    )
    async def attack_fin(
        self, ctx: SlashContext,
        member: discord.User,
        lap: Optional[int] = None,
        boss_number: Optional[int] = None,
        damage: Optional[int] = None
    ):
        """ボスに凸した時の処理を実施する"""
        cheked = await self.check_command_arguments(ctx, member, lap, boss_number)
        if not cheked:
            return
        clan_data, player_data, lap, boss_index = cheked

        await ctx.send(content=f"{member.display_name}の凸を{lap}周目{boss_index+1}ボスに消化します")

        boss_status_data = clan_data.boss_status_data[lap][boss_index]
        attack_status_index = boss_status_data.get_attack_status_index(player_data, False)
        if attack_status_index is None:
            return await ctx.send("凸宣言がされていません。処理を中断します。")
        attack_status = boss_status_data.attack_players[attack_status_index]
        if damage:
            attack_status.damage = damage
        await self._attack_boss(attack_status, clan_data, lap, boss_index, ctx.channel, ctx.author)
        # return ctx.channel.send("処理が完了しました。")
    
    @cog_ext.cog_slash(
        description="ボスを討伐した時の処理を実施します。",
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name="member",
                description="処理対象のメンバー(メンションで指定)",
                option_type=SlashCommandOptionType.USER,
                required=True
            ),
            create_option(
                name="lap",
                description="周回数 (指定がない場合は今現在のボスが指定されます)",
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            ),
            create_option(
                name="boss_number",
                description="ボス番号 (各ボスの進行用チャンネルで実行する場合は指定する必要がありません)",
                option_type=SlashCommandOptionType.INTEGER,
                required=False
            )
        ]
    )
    async def defeat_boss(
        self, ctx: SlashContext,
        member: discord.User,
        lap: Optional[int] = None,
        boss_number: Optional[int] = None
    ):
        """コマンドからボスを討伐した時の処理を実施する。"""
        checked = await self.check_command_arguments(ctx, member, lap, boss_number)
        if not checked:
            return
        clan_data, player_data, lap, boss_index = checked
        await ctx.send(content=f"{member.display_name}の凸で{boss_index+1}ボスを討伐します")

        boss_status_data = clan_data.boss_status_data[lap][boss_index]
        attack_status_index = boss_status_data.get_attack_status_index(player_data, False)
        if attack_status_index is None:
            return await ctx.send("凸宣言がされていません。処理を中断します。")
        attack_status = boss_status_data.attack_players[attack_status_index]
        await self._last_attack_boss(
            attack_status=attack_status,
            clan_data=clan_data,
            lap=lap,
            boss_index=boss_index,
            channel=ctx.channel,
            user=ctx.author
        )
        # return ctx.channel.send("処理が完了しました。")

    @cog_ext.cog_slash(
        description="元に戻す処理を実施します。",
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name="member",
                description="処理対象のメンバー(メンションで指定)",
                option_type=SlashCommandOptionType.USER,
                required=True
            )
        ]
    )
    async def undo(self, ctx: SlashContext, member: discord.User):
        """コマンドでもとに戻すときの処理を実施する"""
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return
        player_data = clan_data.player_data_dict.get(member.id)
        if not player_data:
            return await ctx.send(f"{member.display_name}さんは凸管理のメンバーに指定されていません。")

        if not player_data.log:
            return await ctx.send("元に戻す内容がありませんでした")
        log_data = player_data.log[-1]

        await ctx.send(
            f"{member.display_name}の{log_data.boss_index+1}ボスに対する"
            f"`{OPERATION_TYPE_DESCRIPTION_DICT[log_data.operation_type]}`を元に戻します。")
        await self._undo(clan_data, player_data, log_data)

    @cog_ext.cog_slash(
        description="持越時間を登録します。",
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name="time",
                description="持越秒数",
                option_type=SlashCommandOptionType.INTEGER,
                required=True
            )
        ]
    )
    async def set_cot(self, ctx: SlashContext, time: int):
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return
        if player_data := clan_data.player_data_dict.get(ctx.author.id):
            if not player_data.carry_over_list:
                return await ctx.send("持ち越しを持っていません。")
            co_index = 0
            await ctx.send(f"持ち越し時間{time}秒を設定します。")
            if len(player_data.carry_over_list) > 1:
                co_index = await select_from_list(
                    self.bot, ctx.channel, ctx.author, player_data.carry_over_list,
                    f"{ctx.author.mention} 持ち越しが二つ以上発生しています。以下から持ち越し時間を登録したい持ち越しを選択してください")

            player_data.carry_over_list[co_index].carry_over_time = time
            await self._update_remain_attack_message(clan_data)
            await ctx.channel.send("持ち越し時間の設定が完了しました。")
        else:
            return await ctx.send(f"{ctx.author.display_name}さんは凸管理対象ではありません。")

    @cog_ext.cog_slash(
        description="日程調査用のアンケートフォームを表示します。",
        guild_ids=GUILD_IDS,
    )
    async def form(self, ctx: SlashContext):
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return
        
        if clan_data.form_data.check_update():
            await ctx.send(content="アンケートフォームを新規作成しています。")
            new_flag = True if len(clan_data.form_data.form_url) == 0 else False
            async with ctx.channel.typing():
                title = f"{datetime.now(JST).month}月 " + ctx.guild.name + " 日程調査"
                form_data_dict = await create_form_data(title)
                clan_data.form_data.set_from_form_data_dict(form_data_dict)
            # ctx.sendが使えなくなるので冗長だけど分ける。
            form_url = clan_data.form_data.create_form_url(ctx.author.display_name, ctx.author.id)
            await ctx.channel.send(f"{ctx.author.display_name} さん専用のURLです。\n{form_url}")
            if new_flag:
                SQLiteUtil.register_form_data(clan_data)
            else:
                SQLiteUtil.update_form_data(clan_data)
        else:
            form_url = clan_data.form_data.create_form_url(ctx.author.display_name, ctx.author.id)
            await ctx.send(f"{ctx.author.display_name} さん専用のURLです。\n{form_url}")

    @cog_ext.cog_slash(
        description="参戦時間を読み込みます。(手動更新用)",
        guild_ids=GUILD_IDS,
        options=[
            create_option(
                name="day",
                description="何日目のデータを読み込むかを指定する",
                option_type=SlashCommandOptionType.INTEGER,
                required=True
            )
        ]
    )
    async def load_time(self, ctx: SlashContext, day: int):
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return
        if not clan_data.form_data.form_url:
            return await ctx.send("日程調査用のアンケートフォームが作成されていません。")
        if day < 0 or day > 5:
            return await ctx.send(content="1から5までの数字を指定してください")
        await ctx.send(f"{day}日目の参戦時間を読み込みます")
        await self._load_gss_data(clan_data, day)
        return await ctx.channel.send("読み込みが完了しました")

    @cog_ext.cog_slash(
        description="日程調査の回答シートを出力します",
        guild_ids=GUILD_IDS
    )
    async def form_sheet(self, ctx: SlashContext):
        clan_data = self.clan_data[ctx.channel.category_id]
        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return
        if not clan_data.form_data.form_url:
            return await ctx.send("日程調査用のアンケートフォームが作成されていません。")
        return await ctx.send(clan_data.form_data.sheet_url)

    async def _undo(self, clan_data: ClanData, player_data: PlayerData, log_data: LogData):
        """元に戻す処理を実施する。"""
        boss_index = log_data.boss_index
        log_type = log_data.operation_type
        boss_status_data = clan_data.boss_status_data[log_data.lap][boss_index]
        if log_type is OperationType.ATTACK_DECLAR:
            if (attack_index := boss_status_data.get_attack_status_index(player_data, False)) is not None:
                attack_status = boss_status_data.attack_players[attack_index]
                SQLiteUtil.delete_attackstatus(
                    clan_data=clan_data, lap=log_data.lap, boss_index=boss_index, attack_status=attack_status)
                del boss_status_data.attack_players[attack_index]
                del player_data.log[-1]
                await self._update_progress_message(clan_data, log_data.lap, boss_index)
        
        if log_type is OperationType.ATTACK or log_type is OperationType.LAST_ATTACK:
            if (attack_index := boss_status_data.get_attack_status_index(player_data, True)) is not None:
                attack_status = boss_status_data.attack_players[attack_index]
                player_data.from_dict(log_data.player_data)
                attack_status.attacked = False
                SQLiteUtil.reverse_attackstatus(clan_data, log_data.lap, boss_index, attack_status)
                if log_type is OperationType.LAST_ATTACK:
                    boss_status_data.beated = log_data.beated
                    SQLiteUtil.update_boss_status_data(clan_data, boss_index, boss_status_data)
                del player_data.log[-1]
                await self._update_progress_message(clan_data, log_data.lap, boss_index)
                await self._update_remain_attack_message(clan_data)
                SQLiteUtil.update_playerdata(clan_data, player_data)
                SQLiteUtil.reregister_carryover_data(clan_data, player_data)

    async def _delete_reserve_by_attack(self, clan_data: ClanData, attack_status: AttackStatus, boss_idx: int):
        """ボス攻撃時に予約の削除を行う"""
        reserve_idx = -1
        for i, reserve_data in enumerate(clan_data.reserve_list[boss_idx]):
            if reserve_data.carry_over == attack_status.carry_over and reserve_data.attack_type == attack_status.attack_type\
               and reserve_data.player_data == attack_status.player_data:
                reserve_idx = i
        if reserve_idx != -1:
            SQLiteUtil.delete_reservedata(clan_data, boss_idx, clan_data.reserve_list[boss_idx][reserve_idx])
            del clan_data.reserve_list[boss_idx][reserve_idx]
            await self._update_reserve_message(clan_data, boss_idx)

        # 凸が完了もしくは持ち越しを吐ききったらそれらに関する予約を削除する
        player_data = attack_status.player_data
        attack_comp = player_data.magic_attack + player_data.physics_attack == 3
        co_comp = len(player_data.carry_over_list) == 0
        if attack_comp or co_comp:
            for i in range(5):
                old_reserve_set = set(clan_data.reserve_list[i])
                finished_reserve_set = {
                    reserve_data
                    for reserve_data in clan_data.reserve_list[i]
                    if (attack_comp and reserve_data.player_data.user_id == player_data.user_id and not reserve_data.carry_over) or (
                        co_comp and reserve_data.player_data.user_id == player_data.user_id and reserve_data.carry_over)
                }
                diff_set = old_reserve_set - finished_reserve_set
                if finished_reserve_set:
                    for reserve_data in finished_reserve_set:
                        SQLiteUtil.delete_reservedata(clan_data, i, reserve_data)
                    clan_data.reserve_list[i] = list(diff_set)
                    await self._update_reserve_message(clan_data, i)

    def _create_progress_message(
        self, clan_data: ClanData, lap: int, boss_index: int, guild: discord.Guild
    ) -> discord.Embed:
        """進行用のメッセージを作成する"""
        attacked_list: List[str] = []
        attack_list: List[str] = []
        boss_status_data = clan_data.boss_status_data[lap][boss_index]
        boss_status_data.attack_players.sort(key=lambda x: x.damage, reverse=True)
        total_damage: int = 0
        current_hp: int = boss_status_data.max_hp
        for attack_status in boss_status_data.attack_players:
            if attack_status.attacked:
                user = guild.get_member(attack_status.player_data.user_id)
                if user is None:
                    continue
                attacked_list.append(f"(凸済み) {'{:,}'.format(attack_status.damage)}万 {user.display_name}")
                current_hp -= attack_status.damage
        for attack_status in boss_status_data.attack_players:
            if not attack_status.attacked:
                user = guild.get_member(attack_status.player_data.user_id)
                if user is None:
                    continue
                attack_list.append(attack_status.create_attack_status_txt(user.display_name, current_hp))
                total_damage += attack_status.damage
        progress_title = f"[{lap}周目] {ClanBattleData.boss_names[boss_index]}"
        if boss_status_data.beated:
            progress_title += " **討伐済み**"
        else:
            progress_title += f" {'{:,}'.format(current_hp)}万/{'{:,}'.format(boss_status_data.max_hp)}万"\
                f" 合計 {'{:,}'.format(total_damage)}万"

        progress_description = "\n".join(attacked_list) + "\n" + "\n".join(attack_list)
        pr_embed = discord.Embed(
            title=progress_title,
            description=progress_description,
            colour=BOSS_COLOURS[boss_index]
        )
        pr_embed.set_thumbnail(url=ClanBattleData.icon[boss_index])
        return pr_embed

    async def _initialize_progress_messages(
        self, clan_data: ClanData, lap: int
    ) -> None:
        clan_data.progress_message_ids[lap] = [0, 0, 0, 0, 0]
        clan_data.initialize_boss_status_data(lap)
        SQLiteUtil.register_progress_message_id(clan_data, lap)
        SQLiteUtil.register_all_boss_status_data(clan_data, lap)
        for i in range(5):
            await self._send_new_progress_message(clan_data, lap, i)

    async def _send_new_progress_message(
        self, clan_data: ClanData, lap: int, boss_index: int
    ) -> None:
        """新しい進行メッセージを送信する"""
        guild = self.bot.get_guild(clan_data.guild_id)

        channel = self.bot.get_channel(clan_data.boss_channel_ids[boss_index])
        progress_embed = self._create_progress_message(clan_data, lap, boss_index, guild)
        progress_message: discord.Message = await channel.send(embed=progress_embed)
        clan_data.progress_message_ids[lap][boss_index] = progress_message.id
        await progress_message.add_reaction(EMOJI_PHYSICS)
        await progress_message.add_reaction(EMOJI_MAGIC)
        await progress_message.add_reaction(EMOJI_CARRYOVER)
        await progress_message.add_reaction(EMOJI_ATTACK)
        await progress_message.add_reaction(EMOJI_LAST_ATTACK)
        await progress_message.add_reaction(EMOJI_REVERSE)
        SQLiteUtil.update_progress_message_id(clan_data, lap)

        # まとめ用のメッセージがなければ新しく送信する
        if lap not in clan_data.summary_message_ids:
            clan_data.summary_message_ids[lap] = [0, 0, 0, 0, 0]
            for i in range(5):
                progress_embed = self._create_progress_message(clan_data, lap, i, guild)
                summary_channel = self.bot.get_channel(clan_data.summary_channel_id)
                sum_progress_message = await summary_channel.send(embed=progress_embed)
                clan_data.summary_message_ids[lap][i] = sum_progress_message.id
            SQLiteUtil.register_summary_message_id(clan_data, lap)

    async def _update_progress_message(self, clan_data: ClanData, lap: int, boss_idx: int) -> None:
        """進行用のメッセージを更新する"""
        channel = self.bot.get_channel(clan_data.boss_channel_ids[boss_idx])
        progress_message = await channel.fetch_message(clan_data.progress_message_ids[lap][boss_idx])
        progress_embed = self._create_progress_message(clan_data, lap, boss_idx, channel.guild)
        await progress_message.edit(embed=progress_embed)

        # まとめチャンネルの進行用メッセージを更新する
        channel = self.bot.get_channel(clan_data.summary_channel_id)
        progress_message = await channel.fetch_message(clan_data.summary_message_ids[lap][boss_idx])
        await progress_message.edit(embed=progress_embed)

    async def _delete_carry_over_by_attack(
        self,
        clan_data: ClanData,
        attack_status: AttackStatus,
        channel: discord.TextChannel,
        user: discord.User
    ) -> bool:
        """持ち越しでの凸時に凸宣言を持ち越しを削除する。
        
        Returns
        ---------
        bool
            正常に削除できたかどうか
        """
        carry_over_index = 0
        if not attack_status.player_data.carry_over_list:
            del attack_status.player_data.log[-1]
            await channel.send(f"{user.mention} 持ち越しを所持していません。キャンセルします。")
            return False
        if len(attack_status.player_data.carry_over_list) > 1:
            try:
                carry_over_index = await select_from_list(
                    self.bot,
                    channel,
                    user,
                    attack_status.player_data.carry_over_list,
                    f"{user.mention} 持ち越しが二つ以上発生しています。以下から使用した持ち越しを選択してください"
                )
            except TimeoutError:
                del attack_status.player_data.log[-1]
                return False
        # たまにエラーが出る。再現性不明
        if carry_over_index < len(attack_status.player_data.carry_over_list):
            SQLiteUtil.delete_carryover_data(
                clan_data, attack_status.player_data, attack_status.player_data.carry_over_list[carry_over_index])
            del attack_status.player_data.carry_over_list[carry_over_index]
        else:
            logger.error(f"Index Error: carry_over_index={carry_over_index}"
                         f", length={len(attack_status.player_data.carry_over_list)}")
            await channel.send("エラーが発生しました")
            return False
        return True

    async def _attack_boss(
        self,
        attack_status: AttackStatus,
        clan_data: ClanData,
        lap: int,
        boss_index: int,
        channel: discord.TextChannel,
        user: discord.User
    ) -> None:
        """ボスに凸したときに実行する"""

        # ログデータの取得
        attack_status.player_data.log.append(
            LogData(
                OperationType.ATTACK, lap, boss_index, attack_status.player_data.to_dict()
            )
        )

        if attack_status.attack_type is AttackType.CARRYOVER:
            if not await self._delete_carry_over_by_attack(
                clan_data=clan_data,
                attack_status=attack_status,
                channel=channel,
                user=user
            ):
                return
        else:
            attack_status.update_attack_log()

        attack_status.attacked = True

        SQLiteUtil.update_attackstatus(clan_data, lap, boss_index, attack_status)
        SQLiteUtil.update_playerdata(clan_data, attack_status.player_data)
        await self._update_progress_message(clan_data, lap, boss_index)
        await self._update_remain_attack_message(clan_data)
        await self._delete_reserve_by_attack(clan_data, attack_status, boss_index)

    async def _attack_declare(
        self, clan_data: ClanData, player_data: PlayerData, attack_type: AttackType, lap: int, boss_index: int
    ) -> None:
        attack_status = AttackStatus(
            player_data, attack_type, attack_type is AttackType.CARRYOVER
        )
        clan_data.boss_status_data[lap][boss_index].attack_players.append(attack_status)
        await self._update_progress_message(clan_data, lap, boss_index)
        SQLiteUtil.register_attackstatus(clan_data, lap, boss_index, attack_status)
        player_data.log.append(LogData(
            operation_type=OperationType.ATTACK_DECLAR, lap=lap, boss_index=boss_index
        ))

    async def _last_attack_boss(
        self,
        attack_status: AttackStatus,
        clan_data: ClanData,
        lap: int,
        boss_index: int,
        channel: discord.TextChannel,
        user: discord.User
    ) -> None:
        """ボスを討伐した際に実行する"""
        boss_status_data = clan_data.boss_status_data[lap][boss_index]
        if boss_status_data.beated:
            return await channel.send("既に討伐済みのボスです")

        # ログデータの取得
        attack_status.player_data.log.append(LogData(
            OperationType.LAST_ATTACK,
            lap,
            boss_index,
            attack_status.player_data.to_dict(),
            boss_status_data.beated)
        )

        attack_status.attacked = True
        if attack_status.attack_type is AttackType.CARRYOVER:
            if not await self._delete_carry_over_by_attack(
                clan_data=clan_data,
                attack_status=attack_status,
                channel=channel,
                user=user
            ):
                return
        else:
            attack_status.update_attack_log()
            SQLiteUtil.update_playerdata(clan_data, attack_status.player_data)
            carry_over = CarryOver(attack_status.attack_type, boss_index)
            if len(attack_status.player_data.carry_over_list) < 3:
                attack_status.player_data.carry_over_list.append(carry_over)
                SQLiteUtil.register_carryover_data(clan_data, attack_status.player_data, carry_over)
        boss_status_data.beated = True
        await self._update_progress_message(clan_data, lap, boss_index)
        SQLiteUtil.update_attackstatus(clan_data, lap, boss_index, attack_status)
        SQLiteUtil.update_boss_status_data(clan_data, boss_index, boss_status_data)
        next_lap = lap + 1

        # 進行用メッセージを保持するリストがなければ新しく作成する
        if next_lap not in clan_data.progress_message_ids:
            clan_data.progress_message_ids[next_lap] = [0, 0, 0, 0, 0]
            clan_data.initialize_boss_status_data(next_lap)
            SQLiteUtil.register_progress_message_id(clan_data, next_lap)
            SQLiteUtil.register_all_boss_status_data(clan_data, next_lap)
        
        # 進行用のメッセージが送信されていなければ新しく送信する
        if clan_data.progress_message_ids[next_lap][boss_index] == 0:
            await self._send_new_progress_message(clan_data, next_lap, boss_index)
        await self._update_remain_attack_message(clan_data)
        await self._delete_reserve_by_attack(clan_data, attack_status, boss_index)

    def _create_reserve_message(self, clan_data: ClanData, boss_index: int, guild: discord.Guild) -> discord.Embed:
        """予約状況を表示するためのメッセージを作成する"""
        resreve_message_title = f"**{ClanBattleData.boss_names[boss_index]}** の 予約状況"
        reserve_message_list = []
        clan_data.reserve_list[boss_index].sort(key=lambda x: x.damage, reverse=True)
        for reserve_data in clan_data.reserve_list[boss_index]:
            user = guild.get_member(reserve_data.player_data.user_id)
            if user is None:
                continue
            reserve_message_list.append(reserve_data.create_reserve_txt(user.display_name))

        rs_embed = discord.Embed(
            title=resreve_message_title,
            description="\n".join(reserve_message_list),
            colour=BOSS_COLOURS[boss_index]
        )
        rs_embed.set_thumbnail(url=ClanBattleData.icon[boss_index])
        return rs_embed

    async def _initialize_reserve_message(self, clan_data: ClanData) -> None:
        """新しい予約メッセージを送信する"""
        guild = self.bot.get_guild(clan_data.guild_id)
        reserve_channel = self.bot.get_channel(clan_data.reserve_channel_id)
        async for old_message in reserve_channel.history(limit=100):
            try:
                await old_message.delete()
            except Exception:
                pass
        for i in range(5):
            reserve_message_embed = self._create_reserve_message(clan_data, i, guild)
            reserve_message = await reserve_channel.send(embed=reserve_message_embed)
            clan_data.reserve_message_ids[i] = reserve_message.id
            await reserve_message.add_reaction(EMOJI_PHYSICS)
            await reserve_message.add_reaction(EMOJI_MAGIC)
            await reserve_message.add_reaction(EMOJI_SETTING)
            await reserve_message.add_reaction(EMOJI_CANCEL)

    async def _update_reserve_message(self, clan_data: ClanData, boss_idx: int) -> None:
        """予約状況を表示するメッセージを更新する"""
        channel = self.bot.get_channel(clan_data.reserve_channel_id)
        reserve_message = await channel.fetch_message(clan_data.reserve_message_ids[boss_idx])
        reserve_embed = self._create_reserve_message(clan_data, boss_idx, channel.guild)
        await reserve_message.edit(embed=reserve_embed)

    def _create_remain_attaack_message(self, clan_data: ClanData) -> discord.Embed:
        """"残凸状況を表示するメッセージを作成する"""
        remain_attack_message_list = [
            [], [], [], []
        ]
        remain_attack_co = [
            [], [], [], []
        ]
        today = (datetime.now(JST) - timedelta(hours=5)).strftime('%m月%d日')
        embed = discord.Embed(
            title=f"{today} の残凸状況",
            colour=colour.Colour.orange()
        )
        sum_remain_attack = 0
        guild = self.bot.get_guild(clan_data.guild_id)
        for player_data in clan_data.player_data_dict.values():
            user = guild.get_member(player_data.user_id)
            if user is None:
                continue
            txt = "- " + player_data.create_txt(user.display_name)
            sum_attack = player_data.magic_attack + player_data.physics_attack
            sum_remain_attack += 3 - sum_attack
            if player_data.carry_over_list:
                remain_attack_co[sum_attack].append(txt)
            else:
                remain_attack_message_list[sum_attack].append(txt)
        for i in range(4):
            content = "\n".join(remain_attack_message_list[i])
            if content:
                embed.add_field(
                    name=f"残{3-i}凸",
                    value=f"```md\n{content.replace('_', '＿')}\n```",
                    inline=False
                )
            content_co = "\n".join(remain_attack_co[i])
            if content_co:
                if len(content_co) < 1014:
                    embed.add_field(
                        name=f"残{3-i}凸（持ち越し）",
                        value=f"```md\n{content_co.replace('_', '＿')}\n```",
                        inline=False
                    )
                else:
                    center = len(remain_attack_co[i]) // 2 + len(remain_attack_co[i]) % 2
                    content_co_list = [
                        "\n".join(remain_attack_co[:center]),
                        "\n".join(remain_attack_co[center:])
                    ]
                    suffix = ["A", "B"]
                    for i in range(2):
                        embed.add_field(
                            name=f"残{3-i}凸（持ち越し{suffix[i]}）",
                            value=f"```md\n{content_co_list[i]}\n```",
                            inline=False
                        )

        embed.set_footer(
            text=f"{clan_data.get_latest_lap()}周目 {sum_remain_attack}/{len(clan_data.player_data_dict)*3}"
        )
        return embed

    async def _update_remain_attack_message(self, clan_data: ClanData) -> None:
        """残凸状況を表示するメッセージを更新する"""
        remain_attack_channel = self.bot.get_channel(clan_data.remain_attack_channel_id)
        remain_attack_message = await remain_attack_channel.fetch_message(clan_data.remain_attack_message_id)
        remain_attack_embed = self._create_remain_attaack_message(clan_data)
        await remain_attack_message.edit(embed=remain_attack_embed)

    async def _initialize_remain_attack_message(self, clan_data: ClanData) -> None:
        """残凸状況を表示するメッセージの初期化を行う"""
        remain_attack_embed = self._create_remain_attaack_message(clan_data)
        remain_attack_channel = self.bot.get_channel(clan_data.remain_attack_channel_id)
        remain_attack_message = await remain_attack_channel.send(embed=remain_attack_embed)
        clan_data.remain_attack_message_id = remain_attack_message.id
        await remain_attack_message.add_reaction(EMOJI_TASK_KILL)

    async def initialize_clandata(self, clan_data: ClanData) -> None:
        """クランの凸状況を初期化する"""
        for player_data in clan_data.player_data_dict.values():
            player_data.initialize_attack()
            SQLiteUtil.update_playerdata(clan_data, player_data)
            SQLiteUtil.delete_all_carryover_data(clan_data, player_data)
        clan_data.reserve_list = [
            [], [], [], [], []
        ]
        SQLiteUtil.delete_all_reservedata(clan_data)

        # 2周以上の古い周を削除する
        # TODO 周回数管理がちゃんとできるようになったらここら辺を直す
        # latest_lap = max(clan_data.boss_status_data.keys())
        # old_laps = list(lap for lap in clan_data.boss_status_data.keys() if latest_lap - 1 > lap)

        # for old_lap in old_laps:
        #     del clan_data.boss_status_data[old_lap]
        #     del clan_data.progress_message_ids[old_lap]
        #     del clan_data.summary_message_ids[old_lap]

        # SQLiteUtil.delete_old_data(clan_data, latest_lap-1)

        if clan_data.form_data.form_url:
            now = datetime.now(JST)
            if ClanBattleData.start_time <= now <= ClanBattleData.end_time:
                diff = now - ClanBattleData.start_time
                day = diff.days + 1
                await self._load_gss_data(clan_data, day)

    async def _get_reserve_info(
        self, clan_data: ClanData, player_data: PlayerData, user: discord.User
    ) -> Optional[Tuple[int, str, bool]]:
        """ユーザーから予約に関する情報を取得する"""
        setting_content_damage = f"{user.mention} 想定ダメージを送信してください\nスペース後にコメントを付けられます (例: `600 60s討伐`)"
        setting_content_co = f"{user.mention} 持ち越しの予約ですか？"
        setting_message_cancel = f"{user.mention} タイムアウトのため予約設定をキャンセルしました"
        setting_content_fin = "予約設定を受け付けました"
        command_channnel = self.bot.get_channel(clan_data.command_channel_id)
        await command_channnel.send(content=setting_content_damage)

        try:
            damage_message: discord.Message = await self.bot.wait_for(
                'message', timeout=60.0,
                check=lambda m: m.author == user and get_damage(m.content)
            )
        except asyncio.TimeoutError:
            await command_channnel.send(setting_message_cancel)
            return None

        damage, memo = get_damage(damage_message.content)

        if player_data.carry_over_list:
            setting_co_message = await command_channnel.send(content=setting_content_co)
            await setting_co_message.add_reaction(EMOJI_YES)
            await setting_co_message.add_reaction(EMOJI_NO)

            try:
                reaction_co, user = await self.bot.wait_for(
                    'reaction_add', timeout=60.0, check=lambda reaction, reaction_user: reaction_user == user
                )
            except asyncio.TimeoutError:
                await command_channnel.send(setting_message_cancel)
                return None
            
            if str(reaction_co.emoji) == EMOJI_YES:
                carry_over = True
            else:
                carry_over = False
        else:
            carry_over = False
        await command_channnel.send(content=setting_content_fin)
        return damage, memo, carry_over

    async def _check_date_update(self, clan_data: ClanData):
        """日付が更新されているかどうかをチェックする"""
        today = (datetime.now(JST) - timedelta(hours=5)).date()
        if clan_data.date != today:
            clan_data.date = today

            await self.initialize_clandata(clan_data)
            await self._initialize_reserve_message(clan_data)
            await self._initialize_remain_attack_message(clan_data)
            SQLiteUtil.update_clandata(clan_data)

    async def _load_gss_data(self, clan_data: ClanData, day: int):
        """参戦時間を管理するスプレッドシートを読み込む"""
        if not clan_data.form_data.sheet_url:
            return

        ws_titles = await get_worksheet_list(clan_data.form_data.sheet_url)
        candidate_words = ["フォームの回答 1", "第 1 张表单回复", "フォームの回答"]
        for candidate_word in candidate_words:
            if candidate_word in ws_titles:
                sheet_data = await get_sheet_values(
                    clan_data.form_data.sheet_url,
                    candidate_word
                )
                for row in sheet_data[1:]:
                    player_data = clan_data.player_data_dict.get(int(row[2]))
                    if player_data:
                        player_data.raw_limit_time_text = row[2+day]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """凸のダメージを登録する"""
        if not self.ready:
            return
        if message.author.id == self.bot.user.id:
            return

        if message.channel.category is None:
            return
        category_channel_id = message.channel.category.id
        clan_data = self.clan_data[category_channel_id]

        if clan_data is None:
            return

        if message.channel.id not in clan_data.boss_channel_ids:
            return

        player_data = clan_data.player_data_dict.get(message.author.id)
        if not player_data:
            return

        boss_index = clan_data.boss_channel_ids.index(message.channel.id)
        lap = clan_data.get_latest_lap(boss_index)
        attack_players = clan_data.boss_status_data[lap][boss_index].attack_players

        damage_data = get_damage(message.content)
        if damage_data is None:
            return

        if (attack_status_index := clan_data.boss_status_data[lap][boss_index].get_attack_status_index(
                player_data, False)) is not None:
            attack_status = attack_players[attack_status_index]
            attack_status.damage = damage_data[0]
            attack_status.memo = damage_data[1]
            await self._update_progress_message(clan_data, lap, boss_index)
            SQLiteUtil.update_attackstatus(clan_data, lap, boss_index, attack_status)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not self.ready:
            return
        if payload.user_id == self.bot.user.id:
            return
        
        channel = self.bot.get_channel(payload.channel_id)

        if channel.category is None:
            return

        category_channel_id = channel.category.id
        clan_data = self.clan_data[category_channel_id]

        if clan_data is None:
            return

        if clan_data.reserve_channel_id == payload.channel_id:
            boss_index = clan_data.get_reserve_boss_index(payload.message_id)
            if boss_index is None:
                return
            lap = 0
            reserve_flag = True
        else:
            boss_index = clan_data.get_boss_index_from_channel_id(payload.channel_id)
            if boss_index is None:
                return
            lap = clan_data.get_lap_from_message_id(payload.message_id, boss_index)
            if lap is None:
                return
            reserve_flag = False

        player_data = clan_data.player_data_dict.get(payload.user_id)

        if player_data is None:
            return

        async def remove_reaction():
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, user)

        user = self.bot.get_user(payload.user_id)
        attack_type = ATTACK_TYPE_DICT.get(str(payload.emoji))
        if attack_type:
            await self._check_date_update(clan_data)
            if reserve_flag:
                reserve_data = ReserveData(
                    player_data, attack_type
                )
                clan_data.reserve_list[boss_index].append(reserve_data)
                await self._update_reserve_message(clan_data, boss_index)
                SQLiteUtil.register_reservedata(clan_data, boss_index, reserve_data)
            else:
                if not any(
                    attack_status.player_data.user_id == payload.user_id and not attack_status.attacked  # 既に凸宣言済みだったら実行しない
                    for attack_status in clan_data.boss_status_data[lap][boss_index].attack_players
                ) and (
                    attack_type in {AttackType.MAGIC, AttackType.PHYSICS} or (
                        attack_type is AttackType.CARRYOVER and player_data.carry_over_list  # 持ち越し未所持で持ち越しでの凸は反応しない
                    )
                ):
                    await self._attack_declare(clan_data, player_data, attack_type, lap, boss_index)
            return await remove_reaction()

        elif str(payload.emoji) == EMOJI_ATTACK:
            for attack_status in clan_data.boss_status_data[lap][boss_index].attack_players:
                if attack_status.player_data.user_id == payload.user_id and not attack_status.attacked:
                    await self._attack_boss(attack_status, clan_data, lap, boss_index, channel, user)
                    break
            return await remove_reaction()

        elif str(payload.emoji) == EMOJI_LAST_ATTACK:
            for attack_status in clan_data.boss_status_data[lap][boss_index].attack_players:
                if attack_status.player_data.user_id == payload.user_id and not attack_status.attacked:
                    await self._last_attack_boss(attack_status, clan_data, lap, boss_index, channel, user)
                    break
            return await remove_reaction()
        # 押した人が一番最後に登録した予約を削除する
        elif str(payload.emoji) == EMOJI_CANCEL and reserve_flag:
            user_reserve_data_list = [
                (i, reserve_data) for i, reserve_data in enumerate(clan_data.reserve_list[boss_index])
                if reserve_data.player_data.user_id == payload.user_id
            ]
            if user_reserve_data_list:
                rd_list_index = 0
                if len(user_reserve_data_list) > 1:
                    command_channel = self.bot.get_channel(clan_data.command_channel_id)
                    user_selected_index = await select_from_list(
                        self.bot, command_channel, user, [rd[1] for rd in user_reserve_data_list],
                        f"{user.mention} 予約が複数あります。以下から削除をしたい予約を選んでください。"
                    )
                    if user_selected_index is None:
                        return await remove_reaction()
                    else:
                        rd_list_index = user_selected_index
                reserve_index = user_reserve_data_list[rd_list_index][0]
                SQLiteUtil.delete_reservedata(clan_data, boss_index, clan_data.reserve_list[boss_index][reserve_index])
                del clan_data.reserve_list[boss_index][reserve_index]
                await self._update_reserve_message(clan_data, boss_index)
            await remove_reaction()
                
        elif str(payload.emoji) == EMOJI_SETTING and reserve_flag:
            user_reserve_data_list = [
                reserve_data for reserve_data in clan_data.reserve_list[boss_index]
                if reserve_data.player_data.user_id == payload.user_id]
            if user_reserve_data_list:
                reserve_index = 0
                if len(user_reserve_data_list) > 1:
                    command_channel = self.bot.get_channel(clan_data.command_channel_id)
                    user_selected_index = await select_from_list(
                        self.bot, command_channel, user, user_reserve_data_list,
                        f"{user.mention} 予約が複数あります。以下から予約設定をしたい予約を選んでください。"
                    )
                    if user_selected_index is None:
                        return await remove_reaction()
                    else:
                        reserve_index = user_selected_index
                reserve_info = await self._get_reserve_info(clan_data, player_data, user)
                if reserve_info:
                    reserve_data = user_reserve_data_list[reserve_index]
                    reserve_data.set_reserve_info(reserve_info)
                    await self._update_reserve_message(clan_data, boss_index)
                    SQLiteUtil.update_reservedata(clan_data, boss_index, reserve_data)
            return await remove_reaction()

        elif str(payload.emoji) == EMOJI_REVERSE:
            if not player_data.log:
                return await remove_reaction()
            log_data = player_data.log[-1]
            log_index = log_data.boss_index
            log_lap = log_data.lap
            if log_index != boss_index or log_lap != lap:
                txt = f"<@{payload.user_id}> すでに{log_lap}周目{log_index+1}ボスに凸しています。"\
                    f"先に<#{clan_data.boss_channel_ids[log_index]}>で{EMOJI_REVERSE}を押してください"
                channel = self.bot.get_channel(payload.channel_id)
                await channel.send(txt, delete_after=30)
                return await remove_reaction()
            await self._undo(clan_data, player_data, log_data)
            return await remove_reaction()

    @commands.Cog.listener("on_raw_reaction_add")
    async def set_task_kill(self, payload: discord.RawReactionActionEvent):
        """タスキルをした場合の設定を行う"""
        if not self.ready:
            return
        if payload.user_id == self.bot.user.id:
            return
        
        if str(payload.emoji) != EMOJI_TASK_KILL:
            return

        channel = self.bot.get_channel(payload.channel_id)

        if channel.category is None:
            return

        category_channel_id = channel.category.id
        clan_data = self.clan_data[category_channel_id]

        if clan_data is None:
            return

        if payload.message_id != clan_data.remain_attack_message_id:
            return

        if player_data := clan_data.player_data_dict.get(payload.user_id):
            player_data.task_kill = True
            await self._update_remain_attack_message(clan_data)
            SQLiteUtil.update_playerdata(clan_data, player_data)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def unset_task_kill(self, payload: discord.RawReactionActionEvent):
        """タスキルをした場合の設定を行う"""
        if not self.ready:
            return
        if payload.user_id == self.bot.user.id:
            return
        
        if str(payload.emoji) != EMOJI_TASK_KILL:
            return

        channel = self.bot.get_channel(payload.channel_id)

        if channel.category is None:
            return

        category_channel_id = channel.category.id
        clan_data = self.clan_data[category_channel_id]

        if clan_data is None:
            return

        if payload.message_id != clan_data.remain_attack_message_id:
            return

        if player_data := clan_data.player_data_dict.get(payload.user_id):
            player_data.task_kill = False
            await self._update_remain_attack_message(clan_data)
            SQLiteUtil.update_playerdata(clan_data, player_data)

    async def check_command_arguments(
        self, ctx: SlashContext,
        member: discord.User,
        lap: Optional[int] = None,
        boss_number: Optional[int] = None
    ) -> Optional[Tuple[ClanData, PlayerData, int, int]]:
        """凸宣言などでコマンドを使用する際の引数をチェックする"""
        clan_data = self.clan_data[ctx.channel.category_id]

        if clan_data is None:
            await ctx.send(content="凸管理を行うカテゴリーチャンネル内で実行してください")
            return

        if not boss_number:
            boss_index = clan_data.get_boss_index_from_channel_id(ctx.channel_id)
            if boss_index is None:
                await ctx.send("ボス番号を指定してください")
                return
        elif not (0 < boss_number < 6):
            await ctx.send("ボス番号が不適です。1から5までの整数を指定してください。")
            return
        else:
            boss_index = boss_number - 1

        latest_lap = clan_data.get_latest_lap(boss_index)
        if lap is None:
            lap = latest_lap
        elif latest_lap < lap:
            await ctx.send("不正な周回数です")
            return

        player_data = clan_data.player_data_dict.get(member.id)
        if not player_data:
            await ctx.send(f"{member.display_name}は凸管理対象ではありません。")
            return
        return clan_data, player_data, lap, boss_index

def setup(bot):
    bot.add_cog(ClanBattle(bot))  # TestCogにBotを渡してインスタンス化し、Botにコグとして登録する。
