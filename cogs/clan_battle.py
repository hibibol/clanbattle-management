import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from logging import getLogger
from typing import List, Optional, Tuple

import discord
from discord.channel import TextChannel
from discord.errors import Forbidden, HTTPException
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.model import SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option

from cogs.cbutil.attack_type import ATTACK_TYPE_DICT
from cogs.cbutil.boss_status_data import AttackStatus
from cogs.cbutil.clan_battle_data import ClanBattleData
from cogs.cbutil.clan_data import ClanData
from cogs.cbutil.operation_type import OperationType
from cogs.cbutil.player_data import PlayerData
from cogs.cbutil.reserve_data import (RESERVE_TYPE_DICT, ReserveData,
                                      ReserveType)
from cogs.cbutil.sqlite_util import SQLiteUtil
from cogs.cbutil.util import get_damage
from setting import (BOSS_COLOURS, EMOJI_ATTACK, EMOJI_CANCEL,
                     EMOJI_LAST_ATTACK, EMOJI_MAGIC, EMOJI_NO,
                     EMOJI_PHYSICS, EMOJI_REVERSE, EMOJI_SETTING, EMOJI_YES, GUILD_IDS, JST)

logger = getLogger(__name__)

class ClanBattle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.clan_data: defaultdict[int, Optional[ClanData]] = SQLiteUtil.load_clandata_dict()
        self.clan_battle_data = ClanBattleData()

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

        await self._update_remain_attack_message(clan_data)
        if player_data_list:
            SQLiteUtil.register_playerdata(clan_data, player_data_list)

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
            command_channel.id
        )
        self.clan_data[category.id] = clan_data
        await self._initialize_progress_messages(clan_data)
        await self._intizlize_reserve_message(clan_data)

        remain_attack_embed = self._create_remain_attaack_message(clan_data)
        remain_attack_channel = self.bot.get_channel(clan_data.remain_attack_channel_id)
        remain_attack_message = await remain_attack_channel.send(embed=remain_attack_embed)
        clan_data.remain_attack_message_id = remain_attack_message.id
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

        clan_data.lap = lap
        await self._initialize_progress_messages(clan_data)
        await self._update_remain_attack_message(clan_data)
        SQLiteUtil.update_clandata(clan_data)

    def _create_progress_message(self, clan_data: ClanData, boss_index: int, guild: discord.Guild) -> discord.Embed:
        """進行用のメッセージを作成する"""
        attacked_list: List[str] = []
        attack_list: List[str] = []
        clan_data.boss_status_data[boss_index].attack_players.sort(key=lambda x: x.damage)
        total_damage: int = 0
        current_hp: int = clan_data.boss_status_data[boss_index].max_hp
        for attack_status in clan_data.boss_status_data[boss_index].attack_players:
            user = guild.get_member(attack_status.player_data.user_id)
            if attack_status.attacked:
                attacked_list.append(f"(凸済み) {user.display_name} {'{:,}'.format(attack_status.damage)}万")
                current_hp -= attack_status.damage
            else:
                attack_list.append(attack_status.create_attack_status_txt(user.display_name))
                total_damage += attack_status.damage
        progress_title = f"[{clan_data.lap}週目] {ClanBattleData.boss_names[boss_index]}"
        if clan_data.boss_status_data[boss_index].beated:
            progress_title += " **討伐済み**"
        else:
            progress_title += f" {'{:,}'.format(current_hp)}万/{'{:,}'.format(clan_data.boss_status_data[boss_index].max_hp)}万 合計 {'{:,}'.format(total_damage)}万"

        progress_description = "\n".join(attacked_list) + "\n" + "\n".join(attack_list)
        pr_embed = discord.Embed(
            title=progress_title,
            description=progress_description,
            colour=BOSS_COLOURS[boss_index]
        )
        pr_embed.set_thumbnail(url=ClanBattleData.icon[boss_index])
        return pr_embed

    async def _initialize_progress_messages(self, clan_data: ClanData) -> None:
        """各ボスに対する凸状況を初期化して新しく進行メッセージを送信する"""
        guild = self.bot.get_guild(clan_data.guild_id)
        clan_data.initialize_boss_status_data()
        SQLiteUtil.delete_all_attackstatus(clan_data)

        for i, channel_id in enumerate(clan_data.boss_channel_ids):
            channel = self.bot.get_channel(channel_id)
            progress_embed = self._create_progress_message(clan_data, i, guild)
            progress_message: discord.Message = await channel.send(embed=progress_embed)
            clan_data.progress_message_ids[i] = progress_message.id

            await progress_message.add_reaction(EMOJI_PHYSICS)
            await progress_message.add_reaction(EMOJI_MAGIC)
            await progress_message.add_reaction(EMOJI_ATTACK)
            await progress_message.add_reaction(EMOJI_LAST_ATTACK)
            await progress_message.add_reaction(EMOJI_REVERSE)
            SQLiteUtil.update_boss_status_data(clan_data, i, clan_data.boss_status_data[i])

    async def _update_progress_message(self, clan_data: ClanData, boss_idx: int) -> None:
        """進行用のメッセージを更新する"""
        channel = self.bot.get_channel(clan_data.boss_channel_ids[boss_idx])
        progress_message = await channel.fetch_message(clan_data.progress_message_ids[boss_idx])
        progress_embed = self._create_progress_message(clan_data, boss_idx, channel.guild)
        await progress_message.edit(embed=progress_embed)

    async def _attack_boss(self, attack_status: AttackStatus, clan_data: ClanData, boss_index: int) -> None:
        """ボスに凸したときに実行する"""
        attack_status.attacked = True
        attack_status.player_data.carry_over = False
        attack_status.update_attack_log()
        SQLiteUtil.update_attackstatus(clan_data, boss_index, attack_status)
        await self._update_progress_message(clan_data, boss_index)
        await self._update_remain_attack_message(clan_data)
    
    async def _last_attack_boss(self, attack_status: AttackStatus, clan_data: ClanData, boss_index: int) -> None:
        """ボスを討伐した際に実行する"""
        attack_status.attacked = True
        if attack_status.player_data.carry_over:
            attack_status.player_data.carry_over = False
            attack_status.update_attack_log()
        else:
            attack_status.player_data.carry_over = True
        clan_data.boss_status_data[boss_index].beated = True
        SQLiteUtil.update_attackstatus(clan_data, boss_index, attack_status)
        SQLiteUtil.update_boss_status_data(clan_data, boss_index, clan_data.boss_status_data[boss_index])
        await self._update_progress_message(clan_data, boss_index)

        # この周のボスがすべて倒された場合は次週に進む
        if all(clan_data.boss_status_data[i].beated for i in range(5)):
            clan_data.lap += 1
            await self._initialize_progress_messages(clan_data)
        SQLiteUtil.update_clandata(clan_data)
        await self._update_remain_attack_message(clan_data)

    def _create_reserve_message(self, clan_data: ClanData, boss_index: int, guild: discord.Guild) -> discord.Embed:
        """予約状況を表示するためのメッセージを作成する"""
        resreve_message_title = f"**{ClanBattleData.boss_names[boss_index]}** の 予約状況"
        reserve_message_list = []
        for reserve_data in clan_data.reserve_dict[boss_index]:
            user = guild.get_member(reserve_data.player_data.user_id)
            reserve_message_list.append(reserve_data.create_reserve_txt(user.display_name))

        rs_embed = discord.Embed(
            title=resreve_message_title,
            description="\n".join(reserve_message_list),
            colour=BOSS_COLOURS[boss_index]
        )
        rs_embed.set_thumbnail(url=ClanBattleData.icon[boss_index])
        return rs_embed

    async def _intizlize_reserve_message(self, clan_data: ClanData) -> None:
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
        remain_attack_co = []
        today = (datetime.now(JST) - timedelta(hours=5)).strftime('%m月%d日')
        embed = discord.Embed(
            title=f"{today} の残凸状況")
        sum_remain_attack = 0
        guild = self.bot.get_guild(clan_data.guild_id)
        for player_data in clan_data.player_data_dict.values():
            user = guild.get_member(player_data.user_id)
            txt = player_data.create_txt(user.display_name)
            sum_attack = player_data.magic_attack + player_data.physics_attack
            sum_remain_attack += 3 - sum_attack
            if player_data.carry_over:
                remain_attack_co.append(txt)
            else:
                remain_attack_message_list[sum_attack].append(txt)
        for i in range(4):
            content = "\n".join(remain_attack_message_list[i])
            if content:
                embed.add_field(
                    name=f"残{3-i}凸",
                    value=content
                )
        content = "\n".join(remain_attack_co)
        if content:
            embed.add_field(
                name="持ち越し",
                value=content
            )
        embed.set_footer(
            text=f"{clan_data.lap}週目 {sum_remain_attack}/{len(clan_data.player_data_dict)*3}"
        )
        return embed

    async def _update_remain_attack_message(self, clan_data: ClanData) -> None:
        """残凸状況を表示するメッセージを更新する"""
        await self._check_date_update(clan_data)
        remain_attack_channel = self.bot.get_channel(clan_data.remain_attack_channel_id)
        remain_attack_message = await remain_attack_channel.fetch_message(clan_data.remain_attack_message_id)
        remain_attack_embed = self._create_remain_attaack_message(clan_data)
        await remain_attack_message.edit(embed=remain_attack_embed)

    async def _get_reserve_info(
        self, clan_data: ClanData, player_data: PlayerData, user: discord.User, reserve_target: str
    ) -> Optional[Tuple[ReserveType, int, str, bool]]:
        """予約用のリアクションが押されたときに予約に必要な情報を取得する"""
        setting_content_reserve_type = f"{user.mention} {reserve_target}の予約が申し込まれました\n"\
            + f"このボスしか行けない場合 → {EMOJI_ONLY} \n"\
            + f"他のボスも行ける場合 → {EMOJI_ANY}\n"\
            + f"予約をキャンセルする場合 → {EMOJI_CANCEL}\n"\
            + "を押してください"
        setting_content_damage = f"{user.mention} 想定ダメージを送信してください\nスペース後にコメントを付けられます (例: `600 60s討伐`)"
        setting_content_co = f"{user.mention} 持ち越しの予約ですか？"
        setting_message_cancel = f"{user.mention} 予約をキャンセルしました"
        setting_content_fin = "予約を受け付けました"
        command_channnel = await self.bot.get_channel(clan_data.command_channel_id)

        setting_reserve_type_message = await command_channnel.send(content=setting_content_reserve_type)
        await setting_reserve_type_message.add_reaction(EMOJI_ONLY)
        await setting_reserve_type_message.add_reaction(EMOJI_ANY)
        await setting_reserve_type_message.add_reaction(EMOJI_CANCEL)

        try:
            reaction_reserve_type, user = await self.bot.wait_for(
                'reaction_add', timeout=60.0, check=lambda _, reaction_user: reaction_user == user)
        except asyncio.TimeoutError:
            await command_channnel.send(setting_message_cancel)
            return None

        reserve_type = RESERVE_TYPE_DICT.get(str(reaction_reserve_type.emoji))
        if reserve_type is None:
            await command_channnel.send(setting_message_cancel)
            return None

        await command_channnel.send(content=setting_content_damage)

        try:
            damage_message: discord.Message = await self.bot.wait_for(
                'message', timeout=60.0,
                check=lambda m: m.author == user and m.content.split()[0].isdecimal()
            )
        except asyncio.TimeoutError:
            await command_channnel.send(setting_message_cancel)
            return None

        damage, memo = get_damage(damage_message.content)

        if player_data.carry_over:
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
        return reserve_type, damage, memo, carry_over

    # async def _initialize_clanbattle_management(self, clan_data: ClanData):
    #     """クラバトの凸管理の初期化を実施する"""
    #     # 残凸管理の初期化
    #     for player_data in clan_data.player_data_dict.values():
    #         player_data.initialize_attack()
    #         SQLiteUtil.update_playerdata(clan_data, player_data)
    #     await self._initialize_progress_messages(clan_data)
    #     await self._intizlize_reserve_message(clan_data)

    #     remain_attack_embed = self._create_remain_attaack_message(clan_data)
    #     remain_attack_channel = self.bot.get_channel(clan_data.remain_attack_channel_id)
    #     remain_attack_message = await remain_attack_channel.send(embed=remain_attack_embed)
    #     clan_data.remain_attack_message_id = remain_attack_message.id

    async def _check_date_update(self, clan_data: ClanData):
        """日付が更新されているかどうかをチェックする"""
        today = (datetime.now(JST) - timedelta(hours=5)).date()
        if clan_data.date != today:
            clan_data.date = today

            for player_data in clan_data.player_data_dict.values():
                player_data.initialize_attack()
                SQLiteUtil.update_playerdata(clan_data, player_data)

            remain_attack_embed = self._create_remain_attaack_message(clan_data)
            remain_attack_channel = self.bot.get_channel(clan_data.remain_attack_channel_id)
            remain_attack_message = await remain_attack_channel.send(embed=remain_attack_embed)
            clan_data.remain_attack_message_id = remain_attack_message.id
            SQLiteUtil.update_clandata(clan_data)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """凸のダメージを登録する"""
        if message.author.id == self.bot.user.id:
            return
    
        category_channel_id = message.channel.category.id
        clan_data = self.clan_data[category_channel_id]

        if clan_data is None:
            return
        if message.channel.id not in clan_data.boss_channel_ids:
            return
        boss_index = clan_data.boss_channel_ids.index(message.channel.id)
        attack_players = clan_data.boss_status_data[boss_index].attack_players

        damage_data = get_damage(message.content)
        if damage_data is None:
            return
        for attack_status in attack_players:
            if attack_status.player_data.user_id == message.author.id and not attack_status.attacked:
                attack_status.damage = damage_data[0]
                attack_status.memo = damage_data[1]
                SQLiteUtil.update_attackstatus(clan_data, boss_index, attack_status)
        await self._update_progress_message(clan_data, boss_index)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        
        channel = self.bot.get_channel(payload.channel_id)
        category_channel_id = channel.category.id
        clan_data = self.clan_data[category_channel_id]

        if clan_data is None:
            return

        if clan_data.reserve_channel_id == payload.channel_id:
            try:
                boss_index = clan_data.reserve_message_ids.index(payload.message_id)
            except ValueError:
                return
            reserve_flag = True
        else:
            try:
                boss_index = clan_data.progress_message_ids.index(payload.message_id)
            except ValueError:
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
                reserve_target = f"{boss_index+1}ボス{attack_type.value}"
                reserve_info = await self._get_reserve_info(clan_data, player_data, user, reserve_target)
                if reserve_info:
                    reserve_data = ReserveData(
                        player_data, attack_type, reserve_info
                    )
                    clan_data.reserve_dict[boss_index].append(reserve_data)
                    await self._update_reserve_message(clan_data, boss_index)
                    SQLiteUtil.register_reservedata(clan_data, boss_index, reserve_data)
            else:
                # 既に凸宣言済みだったら実行しない
                declaring_flag = False
                for attack_status in clan_data.boss_status_data[boss_index].attack_players:
                    if attack_status.player_data.user_id == payload.user_id and not attack_status.attacked:
                        declaring_flag = True
                if not declaring_flag:
                    attack_status = AttackStatus(
                        player_data, attack_type
                    )
                    clan_data.boss_status_data[boss_index].attack_players.append(attack_status)
                    await self._update_progress_message(clan_data, boss_index)
                    SQLiteUtil.register_attackstatus(clan_data, boss_index, attack_status)
                    player_data.log.append((OperationType.ATTACK_DECLAR, boss_index, {}))
            return await remove_reaction()

        elif str(payload.emoji) == EMOJI_ATTACK:
            for attack_status in clan_data.boss_status_data[boss_index].attack_players:
                if attack_status.player_data.user_id == payload.user_id and not attack_status.attacked:
                    player_data.log.append((OperationType.ATTACK, boss_index, player_data.__dict__))
                    await self._attack_boss(attack_status, clan_data, boss_index)
                    SQLiteUtil.update_attackstatus(clan_data, boss_index, attack_status)
            return await remove_reaction()

        elif str(payload.emoji) == EMOJI_LAST_ATTACK:
            for attack_status in clan_data.boss_status_data[boss_index].attack_players:
                if attack_status.player_data.user_id == payload.user_id and not attack_status.attacked:
                    player_data.log.append((OperationType.LAST_ATTACK, boss_index, player_data.__dict__))
                    await self._last_attack_boss(attack_status, clan_data, boss_index)
                    SQLiteUtil.update_attackstatus(clan_data, boss_index, attack_status)
            return await remove_reaction()
        # 押した人が一番最後に登録した予約を削除する
        elif str(payload.emoji) == EMOJI_CANCEL and reserve_flag:
            reserve_index = -1
            for i, reserve_data in enumerate(clan_data.reserve_dict[boss_index][::-1]):
                if reserve_data.player_data.user_id == payload.user_id:
                    reserve_index = len(clan_data.reserve_dict[boss_index]) - i - 1
                    break
            if reserve_index != -1:
                del clan_data.reserve_dict[boss_index][reserve_index]
                await self._update_reserve_message(clan_data, boss_index)
            return await remove_reaction()

        elif str(payload.emoji) == EMOJI_REVERSE:
            if not player_data.log:
                return await remove_reaction()
            log_type, log_index, log_data = player_data.log[-1]

            if log_index != boss_index:
                txt = f"<@{payload.user_id}> すでに{log_index+1}ボスに凸しています。先に<#{clan_data.boss_channel_ids[log_index]}>で{EMOJI_REVERSE}を押してください"
                channel = self.bot.get_channel(payload.channel_id)
                await channel.send(txt, delete_after=30)
                return await remove_reaction()

            if log_type is OperationType.ATTACK_DECLAR:
                attack_index = -1
                for i, attack_status in enumerate(clan_data.boss_status_data[boss_index].attack_players):
                    if attack_status.player_data == player_data and not attack_status.attacked:
                        attack_index = i
                        break
                if attack_index != -1:
                    attack_status = clan_data.boss_status_data[boss_index].attack_players[attack_index]
                    SQLiteUtil.delete_attackstatus(clan_data, boss_index, attack_status)
                    del clan_data.boss_status_data[boss_index].attack_players[attack_index]
                    del player_data.log[-1]
                    await self._update_progress_message(clan_data, boss_index)
            
            if log_type is OperationType.ATTACK or log_type is OperationType.LAST_ATTACK:
                attack_index = -1
                for i, attack_status in enumerate(clan_data.boss_status_data[boss_index].attack_players[::-1]):
                    if attack_status.player_data == player_data and attack_status.attacked:
                        attack_index = len(clan_data.boss_status_data[boss_index].attack_players) - 1 - i
                        break

                if attack_index != -1:
                    attack_status = clan_data.boss_status_data[boss_index].attack_players[attack_index]
                    player_data.from_dict(log_data)
                    attack_status.attacked = False
                    SQLiteUtil.reverse_attackstatus(clan_data, boss_index, attack_status)
                    del player_data.log[-1]

                    if OperationType.LAST_ATTACK:
                        clan_data.boss_status_data[boss_index].beated = False
                        SQLiteUtil.update_boss_status_data(clan_data, boss_index, clan_data.boss_status_data[boss_index])
                    await self._update_progress_message(clan_data, boss_index)
                    await self._update_remain_attack_message(clan_data)
                    SQLiteUtil.update_playerdata(clan_data, player_data)
            return await remove_reaction()

def setup(bot):
    bot.add_cog(ClanBattle(bot))  # TestCogにBotを渡してインスタンス化し、Botにコグとして登録する。
