from datetime import timedelta, timezone

from discord import Colour

DEBUG = False

TOKEN = ""

EMOJI_PHYSICS = "âī¸"
EMOJI_MAGIC = "đ§"
EMOJI_CARRYOVER = "â"
EMOJI_ONLY = "đĢ"
EMOJI_ANY = "â ī¸"
EMOJI_TASK_KILL = "đ"
EMOJI_SETTING = "đ"
EMOJI_CANCEL = "â"
EMOJI_REVERSE = "âŠī¸"
EMOJI_ATTACK = "âī¸"
EMOJI_LAST_ATTACK = "đ"

EMOJI_YES = "đ"
EMOJI_NO = "đ"

JST = timezone(timedelta(hours=+9), 'JST')

BOSS_COLOURS = [Colour.red(), Colour.gold(), Colour.green(), Colour.blue(), Colour.purple()]

if DEBUG:
    GUILD_IDS = None
else:
    GUILD_IDS = []

DB_NAME = ""
BASE_URL = ""
CREATE_FORM_API = ""
GOOGLE_JSON_PATH = ""
TREASURE_CHEST = "https://cdn.discordapp.com/attachments/845661889161068559/876325765434712144/unknown.png"
