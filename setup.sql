create table ClanData (
    guild_id int,
    category_id int,
    boss1_channel_id int,
    boss2_channel_id int,
    boss3_channel_id int,
    boss4_channel_id int,
    boss5_channel_id int,
    remain_attack_channel_id int,
    reserve_channel_id int,
    command_channel_id int,
    lap int,
    boss1_reserve_message_id int,
    boss2_reserve_message_id int,
    boss3_reserve_message_id int,
    boss4_reserve_message_id int,
    boss5_reserve_message_id int,
    remain_attack_message_id int,
    boss1_progress_message_id int,
    boss2_progress_message_id int,
    boss3_progress_message_id int,
    boss4_progress_message_id int,
    boss5_progress_message_id int,
    day date
);

create table PlayerData (
    category_id int,
    user_id int,
    physics_attack int default 0,
    magic_attack int default 0,
);

create table ReserveData (
    category_id int,
    boss_index int,
    user_id int,
    attack_type varchar,
    damage int,
    memo varchar,
    carry_over boolean
);

create table AttackStatus (
    category_id int,
    user_id int,
    boss_index int,
    damage int,
    memo varchar,
    attacked boolean,
    attack_type varchar,
    created datetime
);

create table BossStatusData (
    category_id int,
    boss_index int,
    lap int,
    beated boolean
);

create table CarryOver (
    category_id int,
    user_id int,
    boss_index int,
    attack_type varchar,
    carry_over_time int,
    created datetime
);

-- insert into BossStatusData values (
--     :category_id,
--     :boss_index,
--     :lap,
--     :beated
-- )
-- update BossStatusData
--     set
--         lap=?
--         beated=?
--     where
--         category_id=? and boss_index=?

-- delete from BossStatusData
-- where
--     category_id=? and boss_index=?

-- update AttackStatus
--     set
--         damage=?,
--         memo=?,
--         attacked=?,
--         attack_type=?
--     where
--         category_id=? and user_id=? and boss_index=? and attacked='FALSE'

-- insert into ReserveData (
--     category_id,
--     boss_index,
--     user_id,
--     reserve_type,
--     damage,
--     memo,
--     carry_over
-- )
-- update ReserveData
--     set
--         reserve_type=?
--         damage=?
--         memo=?
--     where
--         category_id=? and boss_index=? and user_id=? and attack_type=? and carry_over=_?
-- insert into AttackStatus values (
--     :category_id,
--     :user_id,
--     :boss_index,
--     :damage,
--     :memo,
--     :attacked,
--     :attack_type
-- )

-- update ReserveData
--     set
--         reserve_type=?
--         damage=?
--         memo=?
--         carry_over=?
--     where
--         category_id=? and boss_index=? and user_id=?

-- insert into PlayerData (
--     category_id,
--     user_id,
-- )

-- update PlayerData 
--     set
--         physics_attack=?,
--         magic_attack=?,
--         carry_over=?,
--         carry_over_time=?
--     where
--         category_id=? and user_id=?

-- update ClanData
--     set
--         boss1_channel_id=?,
--         boss2_channel_id=?,
--         boss3_channel_id=?,
--         boss4_channel_id=?,
--         boss5_channel_id=?,
--         remain_attack_channel_id=?,
--         reserve_channel_id=?,
--         command_channel_id=?,
--         lap=?,
--         boss1_reserve_message_id=?,
--         boss2_reserve_message_id=?,
--         boss3_reserve_message_id=?,
--         boss4_reserve_message_id=?,
--         boss5_reserve_message_id=?,
--         remain_attack_message_id=?,
--         boss1_progress_message_id=?,
--         boss2_progress_message_id=?,
--         boss3_progress_message_id=?,
--         boss4_progress_message_id=?,
--         boss5_progress_message_id=?,
--         day=?
--     where
--         category_id=?

-- update AttackStatus
--     set
--         attacked='FALSE'
--     where
--         category_id=? and user_id=? and boss_index=? and attack_type=? and damage=? and memo=?