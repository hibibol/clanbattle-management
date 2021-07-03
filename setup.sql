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
    summary_channel_id int,
    summary_message_1_id int,
    summary_message_2_id int,
    summary_message_3_id int,
    summary_message_4_id int,
    summary_message_5_id int,
    day date
);

create table PlayerData (
    category_id int,
    user_id int,
    physics_attack int default 0,
    magic_attack int default 0,
    task_kill boolean
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
    carry_over boolean,
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

create table FormData (
    category_id int,
    form_url varchar,
    sheet_url varchar,
    name_entry varchar,
    discord_id_entry varchar,
    created datetime
)
