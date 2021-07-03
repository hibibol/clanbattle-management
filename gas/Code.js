function create_form(title, start_day){
  // formを作成する
  var form = FormApp.create(title)
  form.setDescription(
    "日程調査用のアンケートフォームです。\n各日付の参戦可能時間すべてにチェックを付けてください。\n\n"
    + "'/form' コマンドを使用することでお名前とDiscord Idが自動入力された専用URLが発行されます。\n"
    + "予定を変更したい場合は、再度アンケートフォームに回答してください。最新のものが反映されます。"
  );

  const folder = DriveApp.getFolderById(folder_ID)
  const form_file = DriveApp.getFileById(form.getId())
  form_file.moveTo(folder)

  var name_item = form.addTextItem().setTitle("お名前").setRequired(true)
  var discord_id_item = form.addTextItem().setTitle("Discord Id").setRequired(true)
  
  var date = new Date();
  const day_of_week_str = [ "日", "月", "火", "水", "木", "金", "土" ];

  for (let day=1; day<6; day++){
    var checkbox_item = form.addCheckboxItem()
    date.setDate(start_day+day-1)
    item_title = day + "日目: " + date.getDate() + "日" + "（" + day_of_week_str[date.getDay()] + "）"
    checkbox_item.setTitle(item_title)
    checkbox_item.setRequired(true)
    if (day == 5){
      var max_time = 24
    }else{
      var max_time = 29
    }
    var choices = []
    for (let hour=5; hour<max_time; hour++){
      choices.push(checkbox_item.createChoice(hour + "～" + (hour+1) + "時"))
    }
    checkbox_item.setChoices(choices)
  }

  // 集計用のSpreadsheetを作成する
  const template_ss_file = DriveApp.getFileById(template_ss_id)
  var ss_file = template_ss_file.makeCopy(title, folder)
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss_file.getId())

  var ss = SpreadsheetApp.open(ss_file)
  var sheets = ss.getSheets()

  sheets.forEach(sheet => {
    if (!template_sheet_names.includes(sheet.getName())) {
      sheet.setName("フォームの回答")
    }
  });

  // 補完用のentry idを取得する
  var fieldIds = [];
  var response = form.createResponse();
  response.withItemResponse(name_item.createResponse("aaaaa"));
  response.withItemResponse(discord_id_item.createResponse("172047012"));
  var url = response.toPrefilledUrl();
  var split = url.split("entry.");
  for (var x = 1; x < split.length; x++) {
    var split2 = split[x].split("=");
    fieldIds[x - 1] = split2[0];
  }
  delete response;
  return {
    form_url: form.getPublishedUrl(),
    ss_url: ss_file.getUrl(),
    name_entry: fieldIds[0],
    discord_id_entry: fieldIds[1]
  }
}

//HTTP GETをハンドリングする
function doGet(e) {

    //リクエストパラメータ名"text"の値を取得する
    var title = e.parameter.title;
    var start_day = Number(e.parameter.start_day);
    var result;
    if (title) {
        result = create_form(title, start_day)
    } else {
      result = {
        errors: {
          message: "please set title"
        }
      }
    }
    var out = ContentService.createTextOutput();

    //Mime TypeをJSONに設定
    out.setMimeType(ContentService.MimeType.JSON);

    //JSONテキストをセットする
    out.setContent(JSON.stringify(result));

    return out;
}
