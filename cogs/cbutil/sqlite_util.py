import sqlite3
from collections import defaultdict
from typing import DefaultDict, List, Optional

from cogs.cbutil.attack_type import ATTACK_TYPE_DICT
from cogs.cbutil.boss_status_data import AttackStatus, BossStatusData
from cogs.cbutil.clan_data import ClanData
from cogs.cbutil.player_data import CarryOver, PlayerData
from cogs.cbutil.reserve_data import RESERVE_TYPE_DICT, ReserveData
from setting import DB_NAME

REGISTER_CLANDATA_SQL = """insert into ClanData values (
    :guild_id,
    :category_id,
    :boss1_channel_id,
    :boss2_channel_id,
    :boss3_channel_id,
    :boss4_channel_id,
    :boss5_channel_id,
    :remain_attack_channel_id,
    :reserve_channel_id,
    :command_channel_id,
    :lap,
    :boss1_reserve_message_id,
    :boss2_reserve_message_id,
    :boss3_reserve_message_id,
    :boss4_reserve_message_id,
    :boss5_reserve_message_id,
    :remain_attack_message_id,
    :boss1_progress_message_id,
    :boss2_progress_message_id,
    :boss3_progress_message_id,
    :boss4_progress_message_id,
    :boss5_progress_message_id,
    :day
)"""
UPDATE_CLANDATA_SQL = """update ClanData
    set
        lap=?,
        boss1_reserve_message_id=?,
        boss2_reserve_message_id=?,
        boss3_reserve_message_id=?,
        boss4_reserve_message_id=?,
        boss5_reserve_message_id=?,
        remain_attack_message_id=?,
        boss1_progress_message_id=?,
        boss2_progress_message_id=?,
        boss3_progress_message_id=?,
        boss4_progress_message_id=?,
        boss5_progress_message_id=?,
        day=?
    where
        category_id=?"""
DELETE_CLANDATA_SQL = """delete from ClanData where category_id=?"""
REGISTER_PLAYERDATA_SQL = """insert into PlayerData values (
    :category_id,
    :user_id,
    0,
    0,
)"""
UPDATE_PLAYERDATA_SQL = """update PlayerData
    set
        physics_attack=?,
        magic_attack=?,
    where
        category_id=? and user_id=?
"""
DELETE_PLAYERDATA_SQL = """DELETE FROM PlayerData
    where
        category_id=? and user_id=?
"""
REGISTER_RESERVEDATA_SQL = """insert into ReserveData values (
    :category_id,
    :boss_index,
    :user_id,
    :attack_type,
    :damage,
    :memo,
    :carry_over
)"""
UPDATE_RESERVEDATA_SQL = """update ReserveData
    set
        damage=?,
        memo=?,
        carry_over=?
    where
        category_id=? and boss_index=? and user_id=? and attack_type=?"""
DELETE_RESERVEDATA_SQL = """delete from ReserveData
where
    category_id=? and boss_index=? and user_id=? and attack_type=? and carry_over=?"""
REGISTER_ATTACKSTATUS_SQL = """insert into AttackStatus values (
    :category_id,
    :user_id,
    :boss_index,
    :damage,
    :memo,
    :attacked,
    :attack_type,
    :carry_over,
    :created
)"""
UPDATE_ATTACKSTATUS_SQL = """update AttackStatus
    set
        damage=?,
        memo=?,
        attacked=?,
        attack_type=?
    where
        category_id=? and user_id=? and boss_index=? and attacked='FALSE'"""
REVERSE_ATTACKSTATUS_SQL = """update AttackStatus
    set
        attacked='FALSE'
    where
        category_id=? and user_id=? and boss_index=? and created=?
"""
DELETE_ATTACKSTATUS_SQL = """delete from AttackStatus
    where
        category_id=? and user_id=? and boss_index=? and attacked='FALSE'"""
REGISTER_BOSS_STATUS_DATA_SQL = """insert into BossStatusData values (
    :category_id,
    :boss_index,
    :lap,
    :beated
)"""
UPDATE_BOSS_STATUS_DATA_SQL = """update BossStatusData
    set
        lap=?,
        beated=?
    where
        category_id=? and boss_index=?
"""
DELETE_BOSS_STATUS_DATA_SQL = """delete from BossStatusData
where
    category_id=? and boss_index=?"""
REGISTER_CARRYOVER_DATA_SQL = """insert into CarryOver values (
    :category_id,
    :user_id,
    :boss_index,
    :attack_type,
    :carry_over_time,
    :created
);"""
UPDATE_CARRYOVER_DATA_SQL = """update CarryOver
    set
        carry_over_time=?
    where
        category_id=? and user_id=? and created=?"""
DELETE_CARRYOVER_DATA_SQL = """delete from CarryOver
where
    category_id=? and user_id=? and created=?"""
DELETE_ALL_CARRYOVER_DATA_SQL = """delete from CarryOver
where
    category_id=? and user_id=?"""

class SQLiteUtil():
    con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    @staticmethod
    def register_clandata(clan_data: ClanData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(REGISTER_CLANDATA_SQL, (
            clan_data.guild_id,
            clan_data.category_id,
            clan_data.boss_channel_ids[0],
            clan_data.boss_channel_ids[1],
            clan_data.boss_channel_ids[2],
            clan_data.boss_channel_ids[3],
            clan_data.boss_channel_ids[4],
            clan_data.remain_attack_channel_id,
            clan_data.reserve_channel_id,
            clan_data.command_channel_id,
            clan_data.lap,
            clan_data.reserve_message_ids[0],
            clan_data.reserve_message_ids[1],
            clan_data.reserve_message_ids[2],
            clan_data.reserve_message_ids[3],
            clan_data.reserve_message_ids[4],
            clan_data.remain_attack_message_id,
            clan_data.progress_message_ids[0],
            clan_data.progress_message_ids[1],
            clan_data.progress_message_ids[2],
            clan_data.progress_message_ids[3],
            clan_data.progress_message_ids[4],
            clan_data.date,
        ))
        con.commit()
        con.close()

    @staticmethod
    def update_clandata(clan_data: ClanData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(UPDATE_CLANDATA_SQL, (
            clan_data.lap,
            clan_data.reserve_message_ids[0],
            clan_data.reserve_message_ids[1],
            clan_data.reserve_message_ids[2],
            clan_data.reserve_message_ids[3],
            clan_data.reserve_message_ids[4],
            clan_data.remain_attack_message_id,
            clan_data.progress_message_ids[0],
            clan_data.progress_message_ids[1],
            clan_data.progress_message_ids[2],
            clan_data.progress_message_ids[3],
            clan_data.progress_message_ids[4],
            clan_data.date,
            clan_data.category_id,
        ))
        con.commit()
        con.close()

    @staticmethod
    def delete_clandata(clan_data: ClanData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(DELETE_CLANDATA_SQL, (
            clan_data.category_id,
        ))
        con.commit()
        con.close()

    @staticmethod
    def register_playerdata(clan_data: ClanData, player_data_list: List[PlayerData]):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        records = [(clan_data.category_id, player_data.user_id) for player_data in player_data_list]
        cur = con.cursor()
        cur.executemany(REGISTER_PLAYERDATA_SQL, records)
        con.commit()
        con.close()

    @staticmethod
    def update_playerdata(clan_data: ClanData, player_data: PlayerData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(UPDATE_PLAYERDATA_SQL, (
            player_data.physics_attack,
            player_data.magic_attack,
            clan_data.category_id,
            player_data.user_id,
        ))
        con.commit()
        con.close()

    @staticmethod
    def delete_playerdata(clan_data: ClanData, player_data: PlayerData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(DELETE_PLAYERDATA_SQL, (
            clan_data.category_id,
            player_data.user_id,
        ))
        con.commit()
        con.close()

    @staticmethod
    def register_reservedata(clan_data: ClanData, boss_index: int, reserve_data: ReserveData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(REGISTER_RESERVEDATA_SQL, (
            clan_data.category_id,
            boss_index,
            reserve_data.player_data.user_id,
            reserve_data.attack_type.value,
            reserve_data.damage,
            reserve_data.memo,
            reserve_data.carry_over,
        ))
        con.commit()
        con.close()

    @staticmethod
    def update_reservedata(clan_data: ClanData, boss_index: int, reserve_data: ReserveData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(UPDATE_RESERVEDATA_SQL, (
            reserve_data.damage,
            reserve_data.memo,
            clan_data.category_id,
            boss_index,
            reserve_data.player_data.user_id,
            reserve_data.attack_type.value,
            reserve_data.carry_over,
        ))
        con.commit()
        con.close()

    @staticmethod
    def delete_reservedata(clan_data: ClanData, boss_index: int, reserve_data: ReserveData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(DELETE_RESERVEDATA_SQL, (
            clan_data.category_id,
            boss_index,
            reserve_data.player_data.user_id,
            reserve_data.attack_type.value,
            reserve_data.carry_over
        ))
        con.commit()
        con.close()

    @staticmethod
    def delete_all_reservedata(clan_data: ClanData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute("delete from ReserveData where category_id=?", (clan_data.category_id,))
        con.commit()
        con.close()

    @staticmethod
    def register_attackstatus(clan_data: ClanData, boss_index: int, attack_status: AttackStatus):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(REGISTER_ATTACKSTATUS_SQL, (
            clan_data.category_id,
            attack_status.player_data.user_id,
            boss_index,
            attack_status.damage,
            attack_status.memo,
            attack_status.attacked,
            attack_status.attack_type.value,
            attack_status.carry_over,
            attack_status.created,
        ))
        con.commit()
        con.close()

    @staticmethod
    def update_attackstatus(clan_data: ClanData, boss_index: int, attack_status: AttackStatus):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(UPDATE_ATTACKSTATUS_SQL, (
            attack_status.damage,
            attack_status.memo,
            attack_status.attacked,
            attack_status.attack_type.value,
            clan_data.category_id,
            attack_status.player_data.user_id,
            boss_index,
        ))
        con.commit()
        con.close()

    @staticmethod
    def delete_attackstatus(clan_data: ClanData, boss_index: int, attack_status: AttackStatus):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(DELETE_ATTACKSTATUS_SQL, (
            clan_data.category_id,
            attack_status.player_data.user_id,
            boss_index,
        ))
        con.commit()
        con.close()

    @staticmethod
    def reverse_attackstatus(clan_data: ClanData, boss_index: int, attack_status: AttackStatus):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(REVERSE_ATTACKSTATUS_SQL, (
            clan_data.category_id,
            attack_status.player_data.user_id,
            boss_index,
            attack_status.created
        ))
        con.commit()
        con.close()

    @staticmethod
    def delete_all_attackstatus(clan_data: ClanData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute("delete from AttackStatus where category_id=?", (clan_data.category_id,))
        con.commit()

    @staticmethod
    def register_boss_status_data(clan_data: ClanData, boss_index: int, boss_status_data: BossStatusData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(REGISTER_BOSS_STATUS_DATA_SQL, (
            clan_data.category_id,
            boss_index,
            boss_status_data.lap,
            boss_status_data.beated,
        ))
        con.commit()
        con.close()

    @staticmethod
    def update_boss_status_data(clan_data: ClanData, boss_index: int, boss_status_data: BossStatusData):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(UPDATE_BOSS_STATUS_DATA_SQL, (
            boss_status_data.lap,
            boss_status_data.beated,
            clan_data.category_id,
            boss_index,
        ))
        con.commit()
        con.close()

    @staticmethod
    def delete_boss_status_data(clan_data: ClanData, boss_index: int):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(DELETE_BOSS_STATUS_DATA_SQL, (
            clan_data.category_id,
            boss_index,
        ))
        con.commit()
        con.close()

    @staticmethod
    def register_carryover_data(clan_data: ClanData, player_data: PlayerData, carryover: CarryOver):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(REGISTER_CARRYOVER_DATA_SQL, (
            clan_data.category_id,
            player_data.user_id,
            carryover.boss_index,
            carryover.attack_type.value,
            carryover.carry_over_time,
            carryover.created,
        ))
        con.commit()
        con.close()

    @staticmethod
    def update_carryover_data(clan_data: ClanData, player_data: PlayerData, carryover: CarryOver):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(UPDATE_CARRYOVER_DATA_SQL, (
            carryover.carry_over_time,
            clan_data.category_id,
            player_data.user_id,
            carryover.created,
        ))
        con.commit()
        con.close()
    
    @staticmethod
    def delete_carryover_data(clan_data: ClanData, player_data: PlayerData, carryover: CarryOver):
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(DELETE_CARRYOVER_DATA_SQL, (
            clan_data.category_id,
            player_data.user_id,
            carryover.created,
        ))
        con.commit()
        con.close()

    @staticmethod
    def reregister_carryover_data(clan_data: ClanData, player_data: PlayerData):
        """すでに登録してある持ち越しをすべて削除して登録しなおす"""
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        cur.execute(DELETE_ALL_CARRYOVER_DATA_SQL, (
            clan_data.category_id,
            player_data.user_id,
        ))
        records = [(
            clan_data.category_id,
            player_data.user_id,
            carryover.boss_index,
            carryover.attack_type.value,
            carryover.carry_over_time,
            carryover.created
        ) for carryover in player_data.carry_over_list]
        cur.executemany(REGISTER_CLANDATA_SQL, records)
        con.commit()
        con.close()

    @staticmethod
    def load_clandata_dict() -> DefaultDict[int, ClanData]:
        clan_data_dict: DefaultDict[int, Optional[ClanData]] = defaultdict(lambda: None)
        con = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = con.cursor()
        for row in cur.execute("select * from ClanData"):
            clan_data = ClanData(
                row[0],
                row[1],
                [row[2], row[3], row[4], row[5], row[6]],
                row[7],
                row[8],
                row[9]
            )
            clan_data.lap = row[10]
            clan_data.reserve_message_ids = [row[11], row[12], row[13], row[14], row[15]]
            clan_data.remain_attack_message_id = row[16]
            clan_data.progress_message_ids = [row[17], row[18], row[19], row[20], row[21]]
            clan_data.date = row[22]
            clan_data_dict[clan_data.category_id] = clan_data

        for row in cur.execute("select * from PlayerData"):
            player_data = PlayerData(row[1])
            player_data.physics_attack = row[2]
            player_data.magic_attack = row[3]
            clan_data = clan_data_dict[row[0]]
            if clan_data:
                clan_data.player_data_dict[row[1]] = player_data

        for row in cur.execute("select * from ReserveData"):
            clan_data = clan_data_dict[row[0]]
            if not clan_data:
                continue
            player_data = clan_data.player_data_dict[row[2]]
            reserve_data = ReserveData(
                player_data, ATTACK_TYPE_DICT[row[3]],
            )
            reserve_data.set_reserve_info((row[4], row[5], row[6]))
            clan_data.reserve_list[row[1]].append(reserve_data)

        for row in cur.execute("select * from BossStatusData"):
            clan_data = clan_data_dict[row[0]]
            if not clan_data:
                continue
            boss_status_data = BossStatusData(row[2], row[1])
            boss_status_data.beated = row[3]
            clan_data.boss_status_data[row[1]] = boss_status_data

        for row in cur.execute("select * from AttackStatus"):
            clan_data = clan_data_dict[row[0]]
            if not clan_data:
                continue
            player_data = clan_data.player_data_dict[row[1]]
            boss_status_data = clan_data.boss_status_data[row[2]]
            attack_status = AttackStatus(
                player_data,
                ATTACK_TYPE_DICT[row[6]],
                row[7]
            )
            attack_status.damage = row[3]
            attack_status.memo = row[4]
            attack_status.attacked = row[5]
            attack_status.created = row[8]
            boss_status_data.attack_players.append(attack_status)

        for row in cur.execute("select * from CarryOver"):
            clan_data = clan_data_dict[row[0]]
            if not clan_data:
                continue
            player_data = clan_data.player_data_dict[row[1]]
            carryover = CarryOver(ATTACK_TYPE_DICT[row[3]], row[2])
            carryover.carry_over_time = row[4]
            carryover.created = row[5]
            player_data.carry_over_list.append(carryover)
        con.close()
        return clan_data_dict
