/**
 * VCPR Desk Google Apps Script backend.
 *
 * Setup:
 * 1. Open the destination Google Sheet.
 * 2. Extensions -> Apps Script -> paste this file.
 * 3. Project Settings -> Script properties -> add VCPR_API_KEY.
 * 4. Deploy as Web app: execute as you, access anyone with the URL.
 * 5. Put the deployment URL in dashboard/config.js.
 */

var SHEET_NAME = "VCPR";
var API_KEY_PROPERTY = "VCPR_API_KEY";
var HEADERS = [
  "Key", "Symbol", "Timeframe", "VCPR Date", "BCPR", "TCPR", "Width",
  "Current Price", "Distance Pips", "Direction", "Alert", "Scan Time",
  "Updated At", "Active"
];

function doGet(e) {
  var action = (e.parameter && e.parameter.action) || "";
  if (action === "vcpr") return readVcpr();
  return output({ status: "ok", message: "VCPR Desk API ready" });
}

function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents || "{}");
    if (body.action !== "syncVcpr") return output({ status: "error", message: "Unknown action" });
    return syncVcpr(body);
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
  var expected = PropertiesService.getScriptProperties().getProperty(API_KEY_PROPERTY);
  if (!expected || String(body.apiKey || "") !== expected) {
    return output({ status: "error", code: "AUTH_REQUIRED", message: "Invalid VCPR API key" });
  }

  var target = sheet();
  var incoming = Array.isArray(body.rows) ? body.rows : [];
  var now = new Date().toISOString();
  var lastRow = target.getLastRow();
  var existing = lastRow > 1 ? target.getRange(2, 1, lastRow - 1, HEADERS.length).getValues() : [];
  var rowByKey = {};

  for (var i = 0; i < existing.length; i++) {
    var existingKey = String(existing[i][0] || "").trim();
    if (existingKey) rowByKey[existingKey] = i + 2;
    target.getRange(i + 2, 14).setValue(false);
  }

  incoming.forEach(function(item) {
    var key = String(item.symbol || "") + "|" + String(item.timeframe || "") + "|" + String(item.vcprDate || "");
    var row = [[
      key, item.symbol || "", item.timeframe || "", item.vcprDate || "",
      item.bcpr || "", item.tcpr || "", item.width || "", item.price || "",
      item.distancePips || "", item.direction || "", item.alert || "",
      body.scanTime || "", now, true
    ]];

    if (rowByKey[key]) {
      target.getRange(rowByKey[key], 1, 1, HEADERS.length).setValues(row);
    } else {
      target.appendRow(row[0]);
    }
  });

  return output({ status: "ok", rows: incoming.length, updatedAt: now });
}

function output(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
