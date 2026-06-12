var SHEET_ID = '{{SHEET_ID}}';

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('{{TITLE}}')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function sanitizeAutodeckValue(value) {
  if (value === null || value === undefined) return '';
  if (Object.prototype.toString.call(value) === '[object Date]') {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }
  if (typeof value === 'number' && !isFinite(value)) return '';
  return value;
}

function sanitizeAutodeckRows(rows) {
  return rows.map(function(row) {
    return row.map(sanitizeAutodeckValue);
  });
}

function loadAutodeckData() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheets = ss.getSheets();
  var result = {
    sheetId: SHEET_ID,
    sheetUrl: 'https://docs.google.com/spreadsheets/d/' + SHEET_ID + '/edit',
    tabs: {},
    loadedAt: new Date().toISOString()
  };

  sheets.forEach(function(sheet) {
    var name = sheet.getName();
    if (
      name.indexOf('sec_') === 0 ||
      name === 'Gate Config' ||
      name === 'Chart Registry' ||
      name === 'Feedback Log'
    ) {
      result.tabs[name] = sanitizeAutodeckRows(sheet.getDataRange().getValues());
    }
  });

  return result;
}
