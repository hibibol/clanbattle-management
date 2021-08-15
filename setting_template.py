from datetime import timedelta, timezone

from discord import Colour

DEBUG = False

TOKEN = ""

EMOJI_PHYSICS = "⚔️"
EMOJI_MAGIC = "🧙"
EMOJI_CARRYOVER = "☕"
EMOJI_ONLY = "🚫"
EMOJI_ANY = "⚠️"
EMOJI_TASK_KILL = "💀"
EMOJI_SETTING = "📝"
EMOJI_CANCEL = "❌"
EMOJI_REVERSE = "↩️"
EMOJI_ATTACK = "☑️"
EMOJI_LAST_ATTACK = "🏁"

EMOJI_YES = "🙆"
EMOJI_NO = "🙅"

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
