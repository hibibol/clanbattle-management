import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials

from setting import GOOGLE_JSON_PATH


def get_creds():
    return ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_JSON_PATH,
        [
            'https://www.googleapis.com/auth/spreadsheets'
        ]
    )


agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)


async def get_sheet_values(sheeturl: str, sheet_name: str):
    """
    スプレッドシートに書いてある内容を取り出す
    """
    
    agc = await agcm.authorize()
    sh = await agc.open_by_url(sheeturl)
    worksheet = await sh.worksheet(sheet_name)
    list_of_lists = await worksheet.get_all_values()
    return list_of_lists


async def get_worksheet_list(sheeturl: str):
    """ワークシートの一覧を取得"""
    agc = await agcm.authorize()
    sh = await agc.open_by_url(sheeturl)
    worksheets = await sh.worksheets()

    return [worksheet.title for worksheet in worksheets]
