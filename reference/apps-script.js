/**
 * ═══════════════════════════════════════════════════════════════
 *  BILLING — Google Apps Script  (multi-client edition)
 *
 *  MASTER SPREADSHEET  (where this script is deployed)
 *  ├─ Config   — client registry (Client ID | Sheet ID | Password | ...)
 *  └─ Sessions — auth tokens
 *
 *  CLIENT SPREADSHEET  (one per client, ID stored in Config sheet)
 *  ├─ Orders
 *  ├─ Menu
 *  └─ Inventory
 *
 *  CONFIG SHEET COLUMNS (A → E):
 *  A: Client ID     e.g. gops_briyani
 *  B: Sheet ID      Google Sheet ID of the client's own spreadsheet
 *  C: Password      login password for this client
 *  D: Session MS    session duration in ms  (default: 86400000 = 24 h)
 *  E: Status        active | inactive
 *
 *  ORDERS SHEET COLUMNS (A → O) — inside each CLIENT spreadsheet:
 *  A: Timestamp  B: Bill No  C: Customer  D: Items
 *  E: Subtotal   F: GST      G: Discount  H: Total
 *  I: Status     J: Customer Type         K: Phone
 *  L: Address    M: Pay Mode N: Order ID  O: Table No
 *
 *  SETUP:
 *  1. Create a master Google Sheet (this is your admin hub).
 *  2. Extensions → Apps Script → paste this file → Save.
 *  3. Deploy → New Deployment
 *       Type: Web App | Execute as: Me | Who can access: Anyone
 *  4. Copy the Web App URL → paste into every client's config.js  scriptURL.
 *  5. Open the master sheet, go to the Config tab (auto-created on first run).
 *     Add one row per client:
 *       gops_briyani | <Sheet ID of gops spreadsheet> | gops123 | 86400000 | active
 *  6. Each client's spreadsheet needs Orders / Menu / Inventory tabs
 *     (auto-created on first write if missing).
 * ═══════════════════════════════════════════════════════════════
 */

var SHEET_NAME           = "Orders";
var MENU_SHEET_NAME      = "Menu";
var INVENTORY_SHEET_NAME = "Inventory";
var SESSION_SHEET_NAME   = "Sessions";
var CONFIG_SHEET_NAME    = "Config";
var VCPR_SHEET_NAME      = "VCPR";

// Config sheet lives in the MASTER spreadsheet (where this script runs).
// Columns: Client ID | Sheet ID | Password | Session MS | Status
var CONFIG_HEADERS = ["Client ID", "Sheet ID", "Password", "Session MS", "Status"];

// Must match your exact sheet columns A→O in order
var HEADERS = [
  "Timestamp",     // A — already exists
  "Bill No",       // B — already exists
  "Customer",      // C — already exists
  "Items",         // D — already exists
  "Subtotal",      // E — already exists
  "GST",           // F — already exists
  "Discount",      // G — already exists
  "Total",         // H — already exists
  "Status",        // I — already exists
  "Customer Type", // J — new column you added
  "Phone",         // K — new column you added
  "Address",       // L — new column you added
  "Pay Mode",      // M
  "Order ID",      // N
  "Table No"       // O
];

var INVENTORY_HEADERS = [
  "Item ID",
  "Item Name",
  "Category",
  "Unit",
  "Stock Qty",
  "Min Qty",
  "Unit Cost",
  "Supplier",
  "Status",
  "Last Updated"
];

var MENU_HEADERS = [
  "Category",
  "Name",
  "Description",
  "Price",
  "Type",
  "ImageURL",
  "Badge",
  "Available"
];

var SESSION_HEADERS = [
  "Client",
  "Token Hash",
  "Created At",
  "Expires At",
  "Status"
];

var VCPR_HEADERS = [
  "Key", "Symbol", "Timeframe", "VCPR Date", "BCPR", "TCPR", "Width",
  "Current Price", "Distance Pips", "Direction", "Alert", "Scan Time",
  "Updated At", "Active"
];

/* ══════════════════════════════════════════
   GET
══════════════════════════════════════════ */
function doGet(e) {
  try {
    var action   = (e.parameter && e.parameter.action) || "";
    var clientId = (e.parameter && e.parameter.client) || "";
    var token    = (e.parameter && e.parameter.token)  || "";

    if (action === "login")           return loginClient(e);
    if (action === "validateSession") return validateSessionRequest(e);
    if (action === "logout")          return logoutClient(e);
    if (action === "vcpr")            return rowsOut(getVcprSheet(), VCPR_HEADERS);

    var auth = requireAuth(clientId, token);
    if (!auth.ok) return authError(auth.message);

    var clientSS = getClientSpreadsheet(auth.match);

    if (action === "menu")      return rowsOut(getMenuSheet(clientSS),      MENU_HEADERS);
    if (action === "orders")    return rowsOut(getSheet(clientSS),          HEADERS);
    if (action === "inventory") return rowsOut(getInventorySheet(clientSS), INVENTORY_HEADERS);

    return jsonOut({ status: "ok", message: "Billing API ready" });

  } catch(err) {
    return jsonOut({ status: "error", message: err.message });
  }
}

/* ══════════════════════════════════════════
   POST
══════════════════════════════════════════ */
function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    if (body.action === "syncVcpr") return syncVcpr(body);
    var auth = requireAuth(body.client || "", body.token || "");
    if (!auth.ok) return authError(auth.message);

    var clientSS = getClientSpreadsheet(auth.match);
    var sheet    = getSheet(clientSS);
    ensureHeaders(sheet);

    var action = body.action || "";
    if (action === "upsertOrder")          return upsertOrder(sheet, body);
    if (action === "addDish")              return addDish(getMenuSheet(clientSS), body);
    if (action === "editDish")             return editDish(getMenuSheet(clientSS), body);
    if (action === "editField")            return editDishField(getMenuSheet(clientSS), body);
    if (action === "deleteDish")           return deleteDish(getMenuSheet(clientSS), body);
    if (action === "saveInventoryItem")    return saveInventoryItem(getInventorySheet(clientSS), body);
    if (action === "deleteInventoryItem")  return deleteInventoryItem(getInventorySheet(clientSS), body);
    if (action === "adjustInventoryStock") return adjustInventoryStock(getInventorySheet(clientSS), body);

    var now = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });

    // Fallback append mode for backward compatibility
    var row = [
      now,                              // A: Timestamp
      body.billNo       || "",          // B: Bill No
      body.customer     || "Walk-in",   // C: Customer
      body.items        || "",          // D: Items
      body.subtotal     || "0",         // E: Subtotal
      body.gst          || "--",        // F: GST
      body.discount     || "--",        // G: Discount
      body.total        || "0",         // H: Total
      body.status       || "Closed",    // I: Status
      body.customerType || "Walk-in",   // J: Customer Type
      body.phone        || "--",        // K: Phone
      body.address      || "--",        // L: Address
      body.payMode      || "UPI",       // M: Pay Mode
      body.orderId      || genOrderId(), // N: Order ID
      body.tableNo      || "--"         // O: Table No
    ];

    sheet.appendRow(row);

    var lastRow = sheet.getLastRow();
    colorizeOrderRow(sheet, lastRow, body.status || "Closed", body.customerType || "Walk-in");

    return jsonOut({ status: "ok", message: "Saved", billNo: body.billNo });

  } catch(err) {
    return jsonOut({ status: "error", message: err.message });
  }
}

/* ══════════════════════════════════════════
   SHEET HELPERS
══════════════════════════════════════════ */

// Opens the client's own spreadsheet using the Sheet ID from the Config sheet.
function getClientSpreadsheet(match) {
  var sheetId = match.cfg.sheetId;
  if (!sheetId) throw new Error('No Sheet ID configured for client: ' + match.key + '. Add it to the Config sheet.');
  try {
    return SpreadsheetApp.openById(sheetId);
  } catch(e) {
    throw new Error('Cannot open spreadsheet for client ' + match.key + ' (ID: ' + sheetId + '). Check the Config sheet.');
  }
}

// ss = the client's spreadsheet (returned by getClientSpreadsheet)
function getSheet(ss) {
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(HEADERS);
    styleHeader(sheet);
  } else {
    ensureHeaders(sheet);
  }
  return sheet;
}

function getMenuSheet(ss) {
  var sheet = ss.getSheetByName(MENU_SHEET_NAME);
  if (!sheet) throw new Error('Menu sheet "' + MENU_SHEET_NAME + '" not found in client spreadsheet.');
  ensureMenuHeaders(sheet);
  return sheet;
}

function getInventorySheet(ss) {
  var sheet = ss.getSheetByName(INVENTORY_SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(INVENTORY_SHEET_NAME);
    sheet.appendRow(INVENTORY_HEADERS);
    styleInventoryHeader(sheet);
  } else {
    ensureInventoryHeaders(sheet);
  }
  return sheet;
}

function getVcprSheet() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(VCPR_SHEET_NAME);
  if (!sheet) {
    sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet(VCPR_SHEET_NAME);
    sheet.appendRow(VCPR_HEADERS);
    styleHeader(sheet);
  } else {
    ensureVcprHeaders(sheet);
  }
  return sheet;
}

function ensureVcprHeaders(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(VCPR_HEADERS);
    styleHeader(sheet);
    return;
  }
  var current = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
  for (var i = 0; i < VCPR_HEADERS.length; i++) {
    if (!String(current[i] || "").trim()) sheet.getRange(1, i + 1).setValue(VCPR_HEADERS[i]);
  }
}

function syncVcpr(body) {
  var sheet = getVcprSheet();
  var rows = Array.isArray(body.rows) ? body.rows : [];
  var now = new Date().toISOString();
  var lastRow = sheet.getLastRow();
  var existing = lastRow > 1 ? sheet.getRange(2, 1, lastRow - 1, VCPR_HEADERS.length).getValues() : [];
  var rowByKey = {};
  for (var i = 0; i < existing.length; i++) {
    var existingKey = String(existing[i][0] || "").trim();
    if (existingKey) rowByKey[existingKey] = i + 2;
    sheet.getRange(i + 2, 14).setValue(false);
  }

  rows.forEach(function(item) {
    var key = String(item.symbol || "") + "|" + String(item.timeframe || "") + "|" + String(item.vcprDate || "");
    var values = [[
      key, item.symbol || "", item.timeframe || "", item.vcprDate || "",
      item.bcpr || "", item.tcpr || "", item.width || "", item.price || "",
      item.distancePips || "", item.direction || "", item.alert || "",
      body.scanTime || "", now, true
    ]];
    if (rowByKey[key]) {
      sheet.getRange(rowByKey[key], 1, 1, VCPR_HEADERS.length).setValues(values);
    } else {
      sheet.appendRow(values[0]);
    }
  });
  return jsonOut({ status: "ok", rows: rows.length, updatedAt: now });
}

// Sessions & Config always live in the MASTER spreadsheet.
function getSessionSheet() {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SESSION_SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SESSION_SHEET_NAME);
    sheet.appendRow(SESSION_HEADERS);
    styleSessionHeader(sheet);
  } else {
    ensureSessionHeaders(sheet);
  }
  return sheet;
}

function getConfigSheet() {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG_SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG_SHEET_NAME);
    sheet.appendRow(CONFIG_HEADERS);
    styleConfigHeader(sheet);
  }
  return sheet;
}

function ensureHeaders(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    styleHeader(sheet);
    return;
  }

  var current = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
  var changed = false;

  for (var i = 0; i < HEADERS.length; i++) {
    if (!String(current[i] || "").trim()) {
      sheet.getRange(1, i + 1).setValue(HEADERS[i]);
      changed = true;
    }
  }

  if (changed) {
    styleHeader(sheet);
  }
}

function ensureInventoryHeaders(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(INVENTORY_HEADERS);
    styleInventoryHeader(sheet);
    return;
  }

  var current = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
  var changed = false;
  for (var i = 0; i < INVENTORY_HEADERS.length; i++) {
    if (!String(current[i] || "").trim()) {
      sheet.getRange(1, i + 1).setValue(INVENTORY_HEADERS[i]);
      changed = true;
    }
  }
  if (changed) styleInventoryHeader(sheet);
}

function ensureMenuHeaders(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(MENU_HEADERS);
    styleMenuHeader(sheet);
    return;
  }
  var current = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
  var changed = false;
  for (var i = 0; i < MENU_HEADERS.length; i++) {
    if (!String(current[i] || "").trim()) {
      sheet.getRange(1, i + 1).setValue(MENU_HEADERS[i]);
      changed = true;
    }
  }
  if (changed) styleMenuHeader(sheet);
}

function ensureSessionHeaders(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(SESSION_HEADERS);
    styleSessionHeader(sheet);
    return;
  }
  var current = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
  var changed = false;
  for (var i = 0; i < SESSION_HEADERS.length; i++) {
    if (!String(current[i] || "").trim()) {
      sheet.getRange(1, i + 1).setValue(SESSION_HEADERS[i]);
      changed = true;
    }
  }
  if (changed) styleSessionHeader(sheet);
}

function rowsOut(sheet, expectedHeaders) {
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return jsonOut({ status: "ok", rows: [] });
  var headers = data[0];
  var rows = data.slice(1).map(function(row, idx) {
    var obj = {};
    headers.forEach(function(h, i) { obj[String(h).trim()] = row[i] !== undefined ? row[i] : ""; });
    obj._row = idx + 2;
    return obj;
  }).filter(function(row) {
    return expectedHeaders.some(function(h) { return String(row[h] || '').trim(); });
  });
  return jsonOut({ status: "ok", rows: rows });
}

// Reads client credentials and Sheet ID from the Config sheet.
function clientConfig(client) {
  var key = canonicalClientId(client);
  if (!key) return null;

  var sheet   = getConfigSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return null;

  var data = sheet.getRange(2, 1, lastRow - 1, CONFIG_HEADERS.length).getValues();
  for (var i = 0; i < data.length; i++) {
    var rowKey    = canonicalClientId(String(data[i][0] || ''));
    var rowStatus = String(data[i][4] || 'active').toLowerCase();
    if (rowKey === key && rowStatus !== 'inactive') {
      return {
        key: rowKey,
        cfg: {
          sheetId:   String(data[i][1] || '').trim(),
          password:  String(data[i][2] || '').trim(),
          sessionMs: parseInt(data[i][3], 10) || (24 * 60 * 60 * 1000)
        }
      };
    }
  }
  return null;
}

function canonicalClientId(client) {
  return String(client || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function loginClient(e) {
  var client = (e.parameter && e.parameter.client) || '';
  var password = (e.parameter && e.parameter.password) || '';
  var match = clientConfig(client);
  if (!match) return authError('Unknown client');
  var cfg = match.cfg;
  if (!password || password !== cfg.password) return authError('Invalid password');

  cleanupExpiredSessions();
  var token = Utilities.getUuid() + Utilities.getUuid();
  var expiresAt = Date.now() + (cfg.sessionMs || (24 * 60 * 60 * 1000));
  var sheet = getSessionSheet();
  sheet.appendRow([
    match.key,
    hashToken(token),
    new Date().toISOString(),
    new Date(expiresAt).toISOString(),
    'active'
  ]);
  return jsonOut({ status: 'ok', token: token, expiresAt: expiresAt });
}

function validateSessionRequest(e) {
  var client = (e.parameter && e.parameter.client) || '';
  var token = (e.parameter && e.parameter.token) || '';
  var auth = requireAuth(client, token);
  if (!auth.ok) return authError(auth.message);
  return jsonOut({ status: 'ok', valid: true });
}

function logoutClient(e) {
  var client = (e.parameter && e.parameter.client) || '';
  var token = (e.parameter && e.parameter.token) || '';
  revokeSession(client, token);
  return jsonOut({ status: 'ok', loggedOut: true });
}

// Returns { ok, match } on success so callers can open the client spreadsheet.
function requireAuth(client, token) {
  if (!client || !token) return { ok: false, message: 'Login required' };
  var match = clientConfig(client);
  if (!match) return { ok: false, message: 'Unknown client' };
  cleanupExpiredSessions();

  var sheet   = getSessionSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return { ok: false, message: 'Session not found' };

  var tokenHash = hashToken(token);
  var clientKey = match.key;
  var data = sheet.getRange(2, 1, lastRow - 1, SESSION_HEADERS.length).getValues();
  for (var i = data.length - 1; i >= 0; i--) {
    var rowClient = String(data[i][0] || '').trim();
    var rowHash   = String(data[i][1] || '').trim();
    var expires   = new Date(String(data[i][3] || '')).getTime();
    var rowStatus = String(data[i][4] || '').trim().toLowerCase();
    if (rowClient === clientKey && rowHash === tokenHash && rowStatus === 'active' && expires > Date.now()) {
      return { ok: true, match: match };  // ← match included so caller can open client SS
    }
  }
  return { ok: false, message: 'Session expired' };
}

function revokeSession(client, token) {
  if (!client || !token) return;
  var match = clientConfig(client);
  if (!match) return;
  var sheet = getSessionSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  var tokenHash = hashToken(token);
  var data = sheet.getRange(2, 1, lastRow - 1, SESSION_HEADERS.length).getValues();
  for (var i = data.length - 1; i >= 0; i--) {
    if (String(data[i][0] || '').trim() === match.key && String(data[i][1] || '').trim() === tokenHash) {
      sheet.getRange(i + 2, 5).setValue('revoked');
      return;
    }
  }
}

function cleanupExpiredSessions() {
  var sheet = getSessionSheet();
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  var data = sheet.getRange(2, 1, lastRow - 1, SESSION_HEADERS.length).getValues();
  var now = Date.now();
  for (var i = data.length - 1; i >= 0; i--) {
    var expires = new Date(String(data[i][3] || '')).getTime();
    var status = String(data[i][4] || '').trim().toLowerCase();
    if ((expires && expires <= now) || status === 'revoked') {
      sheet.deleteRow(i + 2);
    }
  }
}

function hashToken(token) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(token || ''));
  var out = [];
  for (var i = 0; i < bytes.length; i++) {
    var v = bytes[i];
    if (v < 0) v += 256;
    out.push((v < 16 ? '0' : '') + v.toString(16));
  }
  return out.join('');
}

function authError(message) {
  return jsonOut({ status: 'error', code: 'AUTH_REQUIRED', message: message || 'Unauthorized' });
}

function inventoryNow() {
  return new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
}

function cleanNum(v, fallback) {
  var n = parseFloat(String(v || "").replace(/[^0-9.-]/g, ""));
  return isNaN(n) ? fallback : n;
}

function saveInventoryItem(sheet, body) {
  ensureInventoryHeaders(sheet);

  var itemId = String(body.itemId || "").trim() || ("ITM-" + Utilities.getUuid().slice(0, 8));
  var name = String(body.itemName || "").trim();
  if (!name) return jsonOut({ status: "error", message: "Item name is required" });

  var row = [
    itemId,
    name,
    String(body.category || "General").trim(),
    String(body.unit || "Nos").trim(),
    cleanNum(body.stockQty, 0),
    cleanNum(body.minQty, 0),
    cleanNum(body.unitCost, 0),
    String(body.supplier || "").trim(),
    String(body.status || "Active").trim(),
    inventoryNow()
  ];

  var lastRow = sheet.getLastRow();
  var targetRow = 0;
  if (lastRow > 1) {
    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = ids.length - 1; i >= 0; i--) {
      if (String(ids[i][0] || "").trim() === itemId) {
        targetRow = i + 2;
        break;
      }
    }
  }

  if (targetRow) {
    sheet.getRange(targetRow, 1, 1, INVENTORY_HEADERS.length).setValues([row]);
    return jsonOut({ status: "ok", mode: "updated", itemId: itemId });
  }

  sheet.appendRow(row);
  return jsonOut({ status: "ok", mode: "created", itemId: itemId });
}

function deleteInventoryItem(sheet, body) {
  ensureInventoryHeaders(sheet);
  var rowIndex = parseInt(body.rowIndex, 10);
  var itemId = String(body.itemId || "").trim();
  var lastRow = sheet.getLastRow();

  if (!isNaN(rowIndex) && rowIndex >= 2 && rowIndex <= lastRow) {
    sheet.deleteRow(rowIndex);
    return jsonOut({ status: "ok", message: "Deleted", rowIndex: rowIndex });
  }

  if (!itemId) return jsonOut({ status: "error", message: "rowIndex or itemId required" });

  if (lastRow > 1) {
    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = ids.length - 1; i >= 0; i--) {
      if (String(ids[i][0] || "").trim() === itemId) {
        sheet.deleteRow(i + 2);
        return jsonOut({ status: "ok", message: "Deleted", itemId: itemId });
      }
    }
  }

  return jsonOut({ status: "error", message: "Item not found" });
}

function adjustInventoryStock(sheet, body) {
  ensureInventoryHeaders(sheet);
  var itemId = String(body.itemId || "").trim();
  var delta = cleanNum(body.delta, 0);
  if (!itemId) return jsonOut({ status: "error", message: "itemId required" });

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return jsonOut({ status: "error", message: "No inventory data" });

  var data = sheet.getRange(2, 1, lastRow - 1, INVENTORY_HEADERS.length).getValues();
  for (var i = data.length - 1; i >= 0; i--) {
    if (String(data[i][0] || "").trim() === itemId) {
      var stock = cleanNum(data[i][4], 0) + delta;
      if (stock < 0) stock = 0;
      sheet.getRange(i + 2, 5).setValue(stock);
      sheet.getRange(i + 2, 10).setValue(inventoryNow());
      return jsonOut({ status: "ok", itemId: itemId, stockQty: stock });
    }
  }

  return jsonOut({ status: "error", message: "Item not found" });
}

function menuRowFromBody(body) {
  return [
    String(body.Category || body.category || '').trim(),
    String(body.Name || body.name || '').trim(),
    String(body.Description || body.description || '').trim(),
    String(body.Price || body.price || '0').trim(),
    String(body.Type || body.type || 'Veg').trim(),
    String(body.ImageURL || body.imageUrl || '').trim(),
    String(body.Badge || body.badge || '').trim(),
    String(body.Available || body.available || 'Yes').trim()
  ];
}

function addDish(sheet, body) {
  ensureMenuHeaders(sheet);
  var row = menuRowFromBody(body);
  if (!row[0] || !row[1] || !row[3]) return jsonOut({ status: 'error', message: 'Category, Name and Price are required' });
  sheet.appendRow(row);
  return jsonOut({ status: 'ok', mode: 'created' });
}

function editDish(sheet, body) {
  ensureMenuHeaders(sheet);
  var rowIndex = parseInt(body.rowIndex, 10);
  if (isNaN(rowIndex) || rowIndex < 2) return jsonOut({ status: 'error', message: 'Valid rowIndex required' });
  var row = menuRowFromBody(body);
  if (!row[0] || !row[1] || !row[3]) return jsonOut({ status: 'error', message: 'Category, Name and Price are required' });
  sheet.getRange(rowIndex, 1, 1, MENU_HEADERS.length).setValues([row]);
  return jsonOut({ status: 'ok', mode: 'updated', rowIndex: rowIndex });
}

function editDishField(sheet, body) {
  ensureMenuHeaders(sheet);
  var rowIndex = parseInt(body.rowIndex, 10);
  var field = String(body.field || '').trim();
  var colIndex = MENU_HEADERS.indexOf(field) + 1;
  if (isNaN(rowIndex) || rowIndex < 2 || !colIndex) return jsonOut({ status: 'error', message: 'Valid rowIndex and field required' });
  sheet.getRange(rowIndex, colIndex).setValue(body.value === undefined ? '' : body.value);
  return jsonOut({ status: 'ok', rowIndex: rowIndex, field: field });
}

function deleteDish(sheet, body) {
  ensureMenuHeaders(sheet);
  var rowIndex = parseInt(body.rowIndex, 10);
  if (isNaN(rowIndex) || rowIndex < 2) return jsonOut({ status: 'error', message: 'Valid rowIndex required' });
  sheet.deleteRow(rowIndex);
  return jsonOut({ status: 'ok', rowIndex: rowIndex });
}

function upsertOrder(sheet, body) {
  var now = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
  var status = (body.status || "Held").toString();

  var row = [
    now,
    body.billNo       || "",
    body.customer     || "Walk-in",
    body.items        || "",
    body.subtotal     || "0",
    body.gst          || "--",
    body.discount     || "--",
    body.total        || "0",
    status,
    body.customerType || "Walk-in",
    body.phone        || "--",
    body.address      || "--",
    body.payMode      || "UPI",
    body.orderId      || genOrderId(),
    body.tableNo      || "--"
  ];

  var idCol = HEADERS.indexOf("Order ID") + 1;
  var billCol = HEADERS.indexOf("Bill No") + 1;
  var lastRow = sheet.getLastRow();
  var targetRow = 0;

  if (lastRow > 1) {
    var idToFind = String(body.orderId || "").trim();
    var billToFind = String(body.billNo || "").trim();

    if (idToFind) {
      var ids = sheet.getRange(2, idCol, lastRow - 1, 1).getValues();
      for (var i = ids.length - 1; i >= 0; i--) {
        if (String(ids[i][0] || "").trim() === idToFind) {
          targetRow = i + 2;
          break;
        }
      }
    }

    if (!targetRow && billToFind) {
      var bills = sheet.getRange(2, billCol, lastRow - 1, 1).getValues();
      for (var j = bills.length - 1; j >= 0; j--) {
        if (String(bills[j][0] || "").trim() === billToFind) {
          targetRow = j + 2;
          break;
        }
      }
    }
  }

  if (targetRow) {
    sheet.getRange(targetRow, 1, 1, HEADERS.length).setValues([row]);
    colorizeOrderRow(sheet, targetRow, status, body.customerType || "Walk-in");
    return jsonOut({ status: "ok", mode: "updated", billNo: row[1], orderId: row[13] });
  }

  sheet.appendRow(row);
  var newRow = sheet.getLastRow();
  colorizeOrderRow(sheet, newRow, status, body.customerType || "Walk-in");
  return jsonOut({ status: "ok", mode: "created", billNo: row[1], orderId: row[13] });
}

function colorizeOrderRow(sheet, rowNum, status, customerType) {
  var st = String(status || "").toLowerCase();
  var color = "#f3f4f6";

  if (st === "closed") {
    color = "#e8f5e9";
  } else if (st === "held" || st === "open") {
    color = "#fff8e1";
  } else if (String(customerType || "") === "Online") {
    color = "#e3f2fd";
  }

  sheet.getRange(rowNum, 1, 1, HEADERS.length).setBackground(color);
}

function genOrderId() {
  return "ORD-" + Utilities.getUuid();
}

function styleHeader(sheet) {
  sheet.getRange(1, 1, 1, HEADERS.length)
    .setBackground("#180900")
    .setFontColor("#c9922a")
    .setFontWeight("bold")
    .setFontSize(10);
  sheet.setFrozenRows(1);

  // Column widths A→O
  [150, 90, 130, 300, 80, 100, 80, 90, 80, 110, 110, 180, 95, 210, 90]
    .forEach(function(w, i) { sheet.setColumnWidth(i + 1, w); });
}

function styleInventoryHeader(sheet) {
  sheet.getRange(1, 1, 1, INVENTORY_HEADERS.length)
    .setBackground("#180900")
    .setFontColor("#c9922a")
    .setFontWeight("bold")
    .setFontSize(10);
  sheet.setFrozenRows(1);

  [130, 220, 140, 90, 90, 90, 100, 180, 90, 160]
    .forEach(function(w, i) { sheet.setColumnWidth(i + 1, w); });
}

function styleMenuHeader(sheet) {
  sheet.getRange(1, 1, 1, MENU_HEADERS.length)
    .setBackground('#180900')
    .setFontColor('#c9922a')
    .setFontWeight('bold')
    .setFontSize(10);
  sheet.setFrozenRows(1);

  [140, 220, 260, 90, 90, 220, 110, 90]
    .forEach(function(w, i) { sheet.setColumnWidth(i + 1, w); });
}

function styleSessionHeader(sheet) {
  sheet.getRange(1, 1, 1, SESSION_HEADERS.length)
    .setBackground('#180900')
    .setFontColor('#c9922a')
    .setFontWeight('bold')
    .setFontSize(10);
  sheet.setFrozenRows(1);

  [140, 330, 180, 180, 100]
    .forEach(function(w, i) { sheet.setColumnWidth(i + 1, w); });
}

function styleConfigHeader(sheet) {
  sheet.getRange(1, 1, 1, CONFIG_HEADERS.length)
    .setBackground('#180900')
    .setFontColor('#c9922a')
    .setFontWeight('bold')
    .setFontSize(10);
  sheet.setFrozenRows(1);

  // Client ID | Sheet ID | Password | Session MS | Status
  [160, 380, 160, 120, 100]
    .forEach(function(w, i) { sheet.setColumnWidth(i + 1, w); });
}

function jsonOut(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

/* ══════════════════════════════════════════
   TEST — run these in Apps Script editor
══════════════════════════════════════════ */

// Run this ONCE after deploying to create the Config sheet with example rows.
function test_setupConfig() {
  var sheet = getConfigSheet();
  if (sheet.getLastRow() < 2) {
    // Client ID | Sheet ID | Password | Session MS | Status
    sheet.appendRow(['gops_briyani', 'PASTE_SHEET_ID_HERE', 'gops123',         86400000, 'active']);
    sheet.appendRow(['bakery_demo',  'PASTE_SHEET_ID_HERE', 'bakery-password',  86400000, 'active']);
    Logger.log('Config sheet populated. Replace the Sheet IDs with real values.');
  } else {
    Logger.log('Config sheet already has data:', sheet.getLastRow() - 1, 'client(s)');
  }
}

// Run this to verify clientConfig() reads the Config sheet correctly.
function test_clientConfig() {
  var match = clientConfig('gops_briyani');
  if (!match) { Logger.log('ERROR: gops_briyani not found in Config sheet.'); return; }
  Logger.log('Client key:', match.key);
  Logger.log('Sheet ID:', match.cfg.sheetId);
  Logger.log('Session MS:', match.cfg.sessionMs);
}

// Run this to verify the script can open a client's spreadsheet.
function test_openClientSheet() {
  var match = clientConfig('gops_briyani');
  if (!match) { Logger.log('ERROR: client not found'); return; }
  var ss = getClientSpreadsheet(match);
  Logger.log('Opened:', ss.getName(), '| Sheets:', ss.getSheets().map(function(s){ return s.getName(); }).join(', '));
}

// Run this to verify login works end-to-end (replace password to match Config sheet).
function test_login() {
  var result = doGet({ parameter: { action: 'login', client: 'gops_briyani', password: 'gops123' } });
  var data   = JSON.parse(result.getContent());
  Logger.log('Login result:', JSON.stringify(data));
  if (data.status === 'ok') {
    Logger.log('Token (first 16 chars):', data.token.slice(0, 16) + '...');
  }
}