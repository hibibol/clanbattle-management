from datetime import datetime
from typing import Optional, TypedDict
from urllib.parse import urlencode

from cogs.cbutil.clan_battle_data import ClanBattleData
from cogs.cbutil.util import get_from_web_api
from setting import CREATE_FORM_API, JST


class FormDataDict(TypedDict):
    form_url: str
    ss_url: str
    name_entry: str
    discord_id_entry: str


class FormData():
    def __init__(self) -> None:
        self.form_url = ""
        self.sheet_url = ""
        self.name_entry = ""
        self.discord_id_entry = ""
        self.created: Optional[datetime] = None

    def set_from_form_data_dict(self, form_data_dict: FormDataDict):
        self.form_url = form_data_dict["form_url"]
        self.sheet_url = form_data_dict["ss_url"]
        self.name_entry = form_data_dict["name_entry"]
        self.discord_id_entry = form_data_dict["discord_id_entry"]
        self.created = datetime.now(JST)

    def create_form_url(self, name: str, discord_id: int) -> str:
        d = {
            "entry."+self.name_entry: name,
            "entry."+self.discord_id_entry: discord_id
        }
        d_qs = urlencode(d)
        return self.form_url + "?" + d_qs

    def check_update(self) -> bool:
        if not self.created or self.created.month != datetime.now().month:
            return True
        return False


async def create_form_data(title: str):
    now = datetime.now(JST)
    if now < ClanBattleData.end_time:
        start_day = ClanBattleData.start_time.day
    else:
        start_day = ClanBattleData.next_start.day

    url = CREATE_FORM_API + "?" + urlencode({
        "title": title,
        "start_day": start_day
    })
    form_data: FormData = await get_from_web_api(url)
    return form_data
