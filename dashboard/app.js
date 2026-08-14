(function () {
  var config = window.DASHBOARD_CONFIG || {};
  var state = { rows: [], timeframe: "all" };
  var pairOrder = config.pairs || [];
  var $ = function (selector) { return document.querySelector(selector); };
  var fmt = function (value, symbol) { if (value === "" || value == null || isNaN(Number(value))) return "--"; return Number(value).toFixed(symbol && symbol.indexOf("JPY") >= 0 ? 3 : symbol === "XAUUSD" ? 2 : 5); };
  var esc = function (value) { return String(value == null ? "" : value).replace(/[&<>\"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" })[c]; }); };
  function load() {
    var badge = $("#connection");
    if (!config.scriptUrl) { badge.className = "status error"; badge.innerHTML = "<i></i> Add Apps Script URL"; return; }
    badge.className = "status"; badge.innerHTML = "<i></i> Loading data";
    fetch(config.scriptUrl + (config.scriptUrl.indexOf("?") >= 0 ? "&" : "?") + "action=vcpr&t=" + Date.now())
      .then(function (response) { if (!response.ok) throw new Error("Request failed"); return response.json(); })
      .then(function (data) { if (data.status !== "ok") throw new Error(data.message || "Sheet error"); state.rows = (data.rows || []).filter(function (row) { return String(row.Active).toLowerCase() !== "false"; }); render(); badge.className = "status ok"; badge.innerHTML = "<i></i> Sheets connected"; $("#last-refresh").textContent = "Updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); })
      .catch(function (error) { badge.className = "status error"; badge.innerHTML = "<i></i> " + esc(error.message); });
  }
  function rowsForPair(pair) { return state.rows.filter(function (row) { return row.Symbol === pair && (state.timeframe === "all" || String(row.Timeframe).toLowerCase() === state.timeframe); }); }
  function render() {
    var query = $("#pair-search").value.trim().toUpperCase(); var nearOnly = $("#near-only").checked;
    var pairs = pairOrder.filter(function (pair) { return !query || pair.indexOf(query) >= 0; });
    var nearCount = state.rows.filter(function (row) { return String(row.Alert).toUpperCase() === "NEAR"; }).length;
    $("#stat-pairs").textContent = new Set(state.rows.map(function (row) { return row.Symbol; })).size;
    $("#stat-bands").textContent = state.rows.length; $("#stat-near").textContent = nearCount;
    $("#stat-scan").textContent = state.rows.length ? String(state.rows[0]["Scan Time"] || "--").slice(11, 16) : "--";
    var cards = [];
    pairs.forEach(function (pair) {
      var rows = rowsForPair(pair).filter(function (row) { return !nearOnly || String(row.Alert).toUpperCase() === "NEAR"; });
      if (!rows.length) return;
      rows.sort(function (a, b) { return (String(a.Alert).toUpperCase() === "NEAR" ? -1 : 1) - (String(b.Alert).toUpperCase() === "NEAR" ? -1 : 1); });
      var row = rows[0], near = String(row.Alert).toUpperCase() === "NEAR", distance = Number(row["Distance Pips"] || 0);
      cards.push('<article class="pair-card ' + (near ? "near" : "") + '"><div class="pair-head"><div class="pair-name">' + esc(pair) + '</div><div class="pair-price">' + fmt(row["Current Price"], pair) + '</div></div><div class="pair-meta"><span class="chip">' + esc(row.Timeframe) + '</span><span class="chip ' + (near ? "near" : "") + '">' + (near ? "near zone" : "active") + '</span></div><div class="band-row"><span>VCPR ' + esc(row["VCPR Date"]) + '</span><span>' + esc(row.Direction || "") + '</span></div><div class="meter"><span class="meter-band" style="left:30%;width:40%"></span><span class="meter-price" style="left:' + Math.min(96, Math.max(4, 50 - distance * 1.4)) + '%"></span></div><div class="band-row"><span>Band <strong>' + fmt(row.BCPR, pair) + ' - ' + fmt(row.TCPR, pair) + '</strong></span><span>' + fmt(row.Width, pair) + ' wide</span></div><div class="card-footer"><span>' + (near ? "Reaction watch" : "Wait for confirmation") + '</span><span class="distance ' + (near ? "near" : "") + '">' + (near ? distance.toFixed(1) + ' pips' : 'distance ' + distance.toFixed(1) + 'p') + '</span></div></article>');
    });
    $("#pair-grid").innerHTML = cards.length ? cards.join("") : '<div class="empty">No zones match this view.</div>';
  }
  function journal() { try { return JSON.parse(localStorage.getItem("vcpr-desk-journal") || "[]"); } catch (_) { return []; } }
  function saveJournal(items) { localStorage.setItem("vcpr-desk-journal", JSON.stringify(items)); renderJournal(); }
  function renderJournal() { var items = journal(); $("#journal-body").innerHTML = items.length ? items.map(function (item, index) { return '<tr><td>' + esc(item.pair) + '</td><td>' + esc(item.direction) + '</td><td>' + esc(item.entry) + '</td><td>' + esc(item.stop) + '</td><td>' + esc(item.target) + '</td><td>' + esc(item.note) + '</td><td><button class="delete" data-delete="' + index + '" title="Delete trade">x</button></td></tr>'; }).join("") : '<tr><td colspan="7" class="empty">No paper trades logged.</td></tr>'; }
  $("#refresh").addEventListener("click", load); $("#pair-search").addEventListener("input", render); $("#near-only").addEventListener("change", render);
  document.querySelectorAll(".tab").forEach(function (tab) { tab.addEventListener("click", function () { document.querySelectorAll(".tab").forEach(function (item) { item.classList.remove("active"); }); tab.classList.add("active"); state.timeframe = tab.dataset.timeframe; render(); }); });
  $("#trade-form").addEventListener("submit", function (event) { event.preventDefault(); var form = new FormData(event.target); var items = journal(); items.unshift(Object.fromEntries(form.entries())); saveJournal(items); event.target.reset(); });
  $("#journal-body").addEventListener("click", function (event) { if (event.target.dataset.delete) { var items = journal(); items.splice(Number(event.target.dataset.delete), 1); saveJournal(items); } });
  $("#export-journal").addEventListener("click", function () { var items = journal(); var csv = "Pair,Direction,Entry,Stop,Target,Note\n" + items.map(function (item) { return [item.pair, item.direction, item.entry, item.stop, item.target, item.note].map(function (value) { return '"' + String(value || "").replace(/"/g, '""') + '"'; }).join(","); }).join("\n"); var link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); link.download = "vcpr-trade-journal.csv"; link.click(); });
  renderJournal(); load();
}());
