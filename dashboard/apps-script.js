/**
 * VCPR Desk Google Apps Script backend.
 *
 * Setup:
 * 1. Open the destination Google Sheet.
 * 2. Extensions -> Apps Script -> paste this file.
 * 3. Deploy as Web app: execute as you, access anyone with the URL.
 * 4. Put the deployment URL in dashboard/config.js and GitHub Actions secrets.
 */

var SHEET_NAME = "VCPR";
var HEADERS = [
  "Key", "Symbol", "Timeframe", "VCPR Date", "BCPR", "TCPR", "Width",
  "Current Price", "Distance Pips", "Direction", "Alert", "Scan Time",
  "Updated At", "Active"
];

var NEWS_SHEET_NAME = "News";
var NEWS_HEADERS = [
  "Country", "Title", "Date", "Impact", "Forecast", "Previous", "Actual",
  "Scan Time", "Updated At"
];

var MACRO_SHEET_NAME = "Macro";
var MACRO_HEADERS = [
  "Month", "Inflation Previous", "Inflation Forecast", "Inflation Actual",
  "Fed Rate Previous", "Fed Rate Forecast", "Fed Rate Actual",
  "Employment Previous", "Employment Forecast", "Employment Actual",
  "Custom Fields", "Notes", "Updated At"
];

function doGet(e) {
  var action = (e.parameter && e.parameter.action) || "";
  if (action === "vcpr") return readVcpr();
  if (action === "news") return readNews();
  if (action === "macro") return readMacro();
  return output({ status: "ok", message: "VCPR Desk API ready" });
}

function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents || "{}");
    if (body.action === "syncVcpr") return syncVcpr(body);
    if (body.action === "syncNews") return syncNews(body);
    if (body.action === "syncMacro") return syncMacro(body);
    if (body.action === "deleteMacro") return deleteMacro(body);
    return output({ status: "error", message: "Unknown action" });
  } catch (error) {
    return output({ status: "error", message: error.message });
  }
}

function sheet() {
  var current = SpreadsheetApp.getActiveSpreadsheet();
  var target = current.getSheetByName(SHEET_NAME);
  if (!target) target = current.insertSheet(SHEET_NAME);
  ensureHeaders(target);
  return target;
}

function ensureHeaders(target) {
  if (target.getLastRow() === 0) {
    target.appendRow(HEADERS);
    return;
  }
  var current = target.getRange(1, 1, 1, Math.max(target.getLastColumn(), 1)).getValues()[0];
  for (var i = 0; i < HEADERS.length; i++) {
    if (!String(current[i] || "").trim()) target.getRange(1, i + 1).setValue(HEADERS[i]);
  }
}

function readVcpr() {
  var target = sheet();
  var values = target.getDataRange().getValues();
  if (values.length < 2) return output({ status: "ok", rows: [] });

  var rows = values.slice(1).map(function(row) {
    var item = {};
    HEADERS.forEach(function(header, index) { item[header] = row[index] === undefined ? "" : row[index]; });
    return item;
  }).filter(function(item) {
    return String(item.Active).toLowerCase() !== "false" && item.Symbol;
  });
  return output({ status: "ok", rows: rows });
}

function syncVcpr(body) {
  var target = sheet();
  var incoming = Array.isArray(body.rows) ? body.rows : [];
  Logger.log("[SHEETS] syncVcpr received " + incoming.length + " row(s)");
  var now = new Date().toISOString();
  var lastRow = target.getLastRow();
  if (lastRow > 1) {
    target.getRange(2, 1, lastRow - 1, HEADERS.length).clearContent();
  }

  var values = incoming.map(function(item) {
    var key = String(item.symbol || "") + "|" + String(item.timeframe || "") + "|" + String(item.vcprDate || "");
    Logger.log("[SHEETS] writing snapshot row: " + key);
    return [
      key, item.symbol || "", item.timeframe || "", item.vcprDate || "",
      item.bcpr || "", item.tcpr || "", item.width || "", item.price || "",
      item.distancePips || "", item.direction || "", item.alert || "",
      body.scanTime || "", now, true
    ];
  });

  if (values.length) {
    target.getRange(2, 1, values.length, HEADERS.length).setValues(values);
  }

  Logger.log("[SHEETS] replaced VCPR snapshot with " + incoming.length + " row(s)");
  return output({ status: "ok", rows: incoming.length, updatedAt: now });
}

function output(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function newsSheet() {
  var current = SpreadsheetApp.getActiveSpreadsheet();
  var target = current.getSheetByName(NEWS_SHEET_NAME);
  if (!target) target = current.insertSheet(NEWS_SHEET_NAME);
  if (target.getLastRow() === 0) {
    target.appendRow(NEWS_HEADERS);
  } else {
    var current2 = target.getRange(1, 1, 1, Math.max(target.getLastColumn(), 1)).getValues()[0];
    for (var i = 0; i < NEWS_HEADERS.length; i++) {
      if (!String(current2[i] || "").trim()) target.getRange(1, i + 1).setValue(NEWS_HEADERS[i]);
    }
  }
  return target;
}

function readNews() {
  var target = newsSheet();
  var values = target.getDataRange().getValues();
  if (values.length < 2) return output({ status: "ok", rows: [] });

  var rows = values.slice(1).map(function(row) {
    var item = {};
    NEWS_HEADERS.forEach(function(header, index) { item[header] = row[index] === undefined ? "" : row[index]; });
    return item;
  }).filter(function(item) { return item.Title; });
  return output({ status: "ok", rows: rows });
}

function syncNews(body) {
  var target = newsSheet();
  var incoming = Array.isArray(body.rows) ? body.rows : [];
  Logger.log("[SHEETS] syncNews received " + incoming.length + " row(s)");
  var now = new Date().toISOString();
  var lastRow = target.getLastRow();
  if (lastRow > 1) {
    target.getRange(2, 1, lastRow - 1, NEWS_HEADERS.length).clearContent();
  }

  var values = incoming.map(function(item) {
    return [
      item.country || "", item.title || "", item.date || "", item.impact || "",
      item.forecast || "", item.previous || "", item.actual || "",
      body.scanTime || "", now
    ];
  });

  if (values.length) {
    target.getRange(2, 1, values.length, NEWS_HEADERS.length).setValues(values);
  }

  Logger.log("[SHEETS] replaced News snapshot with " + incoming.length + " row(s)");
  return output({ status: "ok", rows: incoming.length, updatedAt: now });
}

function macroSheet() {
  var current = SpreadsheetApp.getActiveSpreadsheet();
  var target = current.getSheetByName(MACRO_SHEET_NAME);
  if (!target) target = current.insertSheet(MACRO_SHEET_NAME);
  if (target.getLastRow() === 0) {
    target.appendRow(MACRO_HEADERS);
  } else {
    var current2 = target.getRange(1, 1, 1, Math.max(target.getLastColumn(), 1)).getValues()[0];
    for (var i = 0; i < MACRO_HEADERS.length; i++) {
      if (!String(current2[i] || "").trim()) target.getRange(1, i + 1).setValue(MACRO_HEADERS[i]);
    }
  }
  return target;
}

function readMacro() {
  var target = macroSheet();
  var values = target.getDataRange().getValues();
  if (values.length < 2) return output({ status: "ok", rows: [] });

  var rows = values.slice(1).map(function(row) {
    var item = {};
    MACRO_HEADERS.forEach(function(header, index) { item[header] = row[index] === undefined ? "" : row[index]; });
    return item;
  }).filter(function(item) { return item.Month; });
  return output({ status: "ok", rows: rows });
}

// Month is the primary key — update the existing row for that month instead of appending a duplicate.
function syncMacro(body) {
  var target = macroSheet();
  var month = String(body.month || "").trim();
  if (!month) return output({ status: "error", message: "month is required" });

  var inflation = body.inflation || {}, fedRate = body.fedRate || {}, employment = body.employment || {};
  var now = new Date().toISOString();
  var rowValues = [
    month,
    inflation.previous || "", inflation.forecast || "", inflation.actual || "",
    fedRate.previous || "", fedRate.forecast || "", fedRate.actual || "",
    employment.previous || "", employment.forecast || "", employment.actual || "",
    JSON.stringify(body.custom || []), body.notes || "", now
  ];

  var values = target.getDataRange().getValues();
  var rowIndex = -1;
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][0]) === month) { rowIndex = i + 1; break; }
  }
  if (rowIndex > 0) {
    target.getRange(rowIndex, 1, 1, MACRO_HEADERS.length).setValues([rowValues]);
  } else {
    target.appendRow(rowValues);
  }
  Logger.log("[SHEETS] upserted Macro row for month " + month);
  return output({ status: "ok", month: month, updatedAt: now });
}

function deleteMacro(body) {
  var target = macroSheet();
  var month = String(body.month || "").trim();
  if (!month) return output({ status: "error", message: "month is required" });

  var values = target.getDataRange().getValues();
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][0]) === month) { target.deleteRow(i + 1); break; }
  }
  Logger.log("[SHEETS] deleted Macro row for month " + month);
  return output({ status: "ok" });
}
