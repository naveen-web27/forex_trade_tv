(function () {
  var config = window.DASHBOARD_CONFIG || {};
  var state = { rows: [], news: [], timeframe: "all" };
  var pairOrder = config.pairs || [];
  var rates = config.rates || {};
  var $ = function (selector) { return document.querySelector(selector); };
  var fmt = function (value, symbol) { if (value === "" || value == null || isNaN(Number(value))) return "--"; return Number(value).toFixed(symbol && symbol.indexOf("JPY") >= 0 ? 3 : symbol === "XAUUSD" ? 2 : 5); };
  var esc = function (value) { return String(value == null ? "" : value).replace(/[&<>\"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" })[c]; }); };
  var dateKey = function (value) { var text = String(value == null ? "" : value).trim(); var match = text.match(/(\d{4})[-/]([01]\d)[-/]([0-3]\d)/); return match ? match[1] + "-" + match[2] + "-" + match[3] : ""; };
  var dateLabel = function (value) { var key = dateKey(value); if (!key) return "--"; var parts = key.split("-"); var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])); return isNaN(date.getTime()) ? "--" : date.toLocaleDateString("en-US", { month: "short", day: "numeric" }); };
  var wideLabel = function (row, pair) { var width = Number(row.Width || 0); var price = Number(row["Current Price"] || 0); if (!width || !price) return "--"; return width / price >= (pair === "XAUUSD" ? 0.004 : 0.002) ? "Wide band" : "Normal band"; };
  var parsePair = function (pair) { if (pair.indexOf("XAU") === 0) return { base: "XAU", quote: pair.slice(3) }; return { base: pair.slice(0, 3), quote: pair.slice(3) }; };
  var trendEffect = function (trend) { if (trend === "hiking") return 1; if (trend === "cutting") return -1; return 0; };
  function macroBias(pair) {
    var parts = parsePair(pair);
    if (parts.base === "XAU") {
      var usd = rates.USD; if (!usd) return "No rate data configured for USD.";
      var usdEffect = trendEffect(usd.trend);
      if (usdEffect > 0) return "Fed is hiking, which raises real rates and typically pressures gold lower.";
      if (usdEffect < 0) return "Fed is cutting, which lowers real rates and typically supports gold higher.";
      return "Fed is holding rates; gold direction depends more on USD strength and safe-haven demand.";
    }
    var base = rates[parts.base]; var quote = rates[parts.quote];
    if (!base || !quote) return "No rate data configured for " + parts.base + "/" + parts.quote + ".";
    var effect = trendEffect(base.trend) - trendEffect(quote.trend);
    if (effect > 0) return parts.base + " central bank is hiking relative to " + parts.quote + ", which favors " + pair + " upside.";
    if (effect < 0) return parts.base + " central bank is cutting relative to " + parts.quote + ", which favors " + pair + " downside.";
    return "Both central banks are on a similar path; rate policy is roughly balanced for " + pair + ".";
  }
  function rateRow(code) {
    var info = rates[code];
    if (!info) return "";
    return "<div><b>" + esc(code) + " — " + esc(info.bank || "") + "</b><span>" + esc(info.rate || "--") + " (" + esc(info.trend || "--") + ")</span></div>";
  }
  function newsForPair(pair) {
    var parts = parsePair(pair);
    var currencies = parts.base === "XAU" ? ["USD"] : [parts.base, parts.quote];
    return state.news.filter(function (item) { return currencies.indexOf(item.Country) >= 0; })
      .sort(function (a, b) { return new Date(a.Date) - new Date(b.Date); })
      .slice(0, 4);
  }
  function newsLabel(value) { var date = new Date(value); if (isNaN(date.getTime())) return "--"; return date.toLocaleDateString("en-US", { month: "short", day: "numeric" }) + ", " + date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }); }
  function load() {
    var badge = $("#connection");
    if (!config.scriptUrl) { badge.className = "status error"; badge.innerHTML = "<i></i> Add Apps Script URL"; return; }
    badge.className = "status"; badge.innerHTML = "<i></i> Loading data";
    var base = config.scriptUrl + (config.scriptUrl.indexOf("?") >= 0 ? "&" : "?");
    Promise.all([
      fetch(base + "action=vcpr&t=" + Date.now()).then(function (response) { if (!response.ok) throw new Error("Request failed"); return response.json(); }),
      fetch(base + "action=news&t=" + Date.now()).then(function (response) { if (!response.ok) throw new Error("Request failed"); return response.json(); }).catch(function () { return { status: "ok", rows: [] }; })
    ]).then(function (results) {
      var vcprData = results[0], newsData = results[1];
      if (vcprData.status !== "ok") throw new Error(vcprData.message || "Sheet error");
      state.rows = normalizeRows((vcprData.rows || []).filter(function (row) { return String(row.Active).toLowerCase() !== "false"; }));
      state.news = newsData.rows || [];
      render();
      badge.className = "status ok"; badge.innerHTML = "<i></i> Sheets connected";
      $("#last-refresh").textContent = "Updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }).catch(function (error) { badge.className = "status error"; badge.innerHTML = "<i></i> " + esc(error.message); });
  }
  function normalizeRows(rows) {
    var latest = {};
    var daily = [];
    rows.forEach(function (row) {
      var timeframe = String(row.Timeframe || "").toLowerCase();
      if (timeframe !== "weekly" && timeframe !== "monthly") { daily.push(row); return; }
      var key = String(row.Symbol || "") + "|" + timeframe;
      var currentDate = dateKey(row["VCPR Date"]);
      var previousDate = latest[key] && dateKey(latest[key]["VCPR Date"]);
      if (!latest[key] || currentDate > previousDate) latest[key] = row;
    });
    return daily.concat(Object.keys(latest).map(function (key) { return latest[key]; }));
  }
  function rowsForPair(pair) { return state.rows.filter(function (row) { return row.Symbol === pair && (state.timeframe === "all" || String(row.Timeframe).toLowerCase() === state.timeframe); }); }
  function render() {
    var query = $("#pair-search").value.trim().toUpperCase(); var nearOnly = $("#near-only").checked;
    var pairs = pairOrder.filter(function (pair) { return !query || pair.indexOf(query) >= 0; });
    var nearCount = state.rows.filter(function (row) { return String(row.Alert).toUpperCase() === "NEAR"; }).length;
    $("#stat-pairs").textContent = new Set(state.rows.map(function (row) { return row.Symbol; })).size;
    $("#stat-bands").textContent = state.rows.length; $("#stat-near").textContent = nearCount;
    $("#stat-scan").textContent = state.rows.length ? String(state.rows[0]["Scan Time"] || "--").slice(11, 16) : "--";
    var visibleRows = [];
    pairs.forEach(function (pair) {
      var rows = rowsForPair(pair).filter(function (row) { return !nearOnly || String(row.Alert).toUpperCase() === "NEAR"; });
      rows.sort(function (a, b) { return (String(a.Alert).toUpperCase() === "NEAR" ? -1 : 1) - (String(b.Alert).toUpperCase() === "NEAR" ? -1 : 1); });
      rows.forEach(function (row) { visibleRows.push({ pair: pair, row: row }); });
    });
    var html = [];
    visibleRows.forEach(function (item, index) {
      var row = item.row, pair = item.pair, near = String(row.Alert).toUpperCase() === "NEAR", distance = Number(row["Distance Pips"] || 0);
      var parts = parsePair(pair);
      var newsItems = newsForPair(pair);
      var newsHtml = newsItems.length
        ? newsItems.map(function (n) { return '<div class="news-item"><span class="news-country">' + esc(n.Country) + '</span><span class="news-title">' + esc(n.Title) + '</span><span class="news-date">' + newsLabel(n.Date) + '</span></div>'; }).join("")
        : '<div class="news-item empty-inline">No high-impact news scheduled this week.</div>';
      html.push('<div class="market-row ' + (near ? "near" : "") + '" data-row-index="' + index + '" data-pair="' + esc(pair) + '" tabindex="0"><span class="row-pair">' + esc(pair) + '</span><span>' + esc(row.Timeframe) + '</span><span>' + dateLabel(row["VCPR Date"]) + '</span><span>' + fmt(row["Current Price"], pair) + '</span><span>' + fmt(row.BCPR, pair) + ' - ' + fmt(row.TCPR, pair) + '</span><span class="row-gap ' + (near ? "near" : "") + '">' + distance.toFixed(1) + ' pips</span><span>' + (near ? "Near" : "Watching") + '</span><span class="row-chevron">+</span></div>');
      html.push(
        '<div class="row-details" data-details-index="' + index + '" data-pair="' + esc(pair) + '">' +
        '<div class="row-details-grid">' +
        '<div><b>VCPR zone</b><span>' + fmt(row.BCPR, pair) + ' to ' + fmt(row.TCPR, pair) + '</span></div>' +
        '<div><b>Band width</b><span>' + fmt(row.Width, pair) + ' (' + wideLabel(row, pair) + ')</span></div>' +
        '<div><b>Gap to zone</b><span>' + distance.toFixed(1) + ' pips, approaching from ' + esc(row.Direction || "unknown") + '</span></div>' +
        '<div><b>Meaning</b><span>A VCPR band is a price area where a reaction may happen. The gap is the distance from the current price to the nearest band edge. A wide band covers a larger price range and needs slower confirmation.</span></div>' +
        '</div>' +
        '<div class="row-subsection"><h4>Macro / interest rates</h4><div class="rate-grid">' + rateRow(parts.base) + rateRow(parts.quote === parts.base ? "" : parts.quote) + '</div><p class="macro-note">' + esc(macroBias(pair)) + '</p></div>' +
        '<div class="row-subsection"><h4>Upcoming / recent news</h4><div class="news-list">' + newsHtml + '</div></div>' +
        '<div class="row-subsection"><h4>Chart</h4><div class="tv-widget" data-symbol="' + esc(pair) + '"></div></div>' +
        '</div>'
      );
    });
    $("#pair-grid").innerHTML = visibleRows.length ? '<div class="market-header"><span>Pair</span><span>TF</span><span>VCPR date</span><span>Live price</span><span>Band</span><span>Gap</span><span>Status</span><span></span></div>' + html.join("") : '<div class="empty">No zones match this view.</div>';
    document.querySelectorAll(".market-row").forEach(function (element) { element.addEventListener("click", toggleRow); element.addEventListener("keydown", function (event) { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); toggleRow.call(element); } }); });
  }
  function loadTradingViewWidget(container) {
    if (container.dataset.loaded) return;
    container.dataset.loaded = "1";
    var widgetDiv = document.createElement("div");
    widgetDiv.className = "tradingview-widget-container__widget";
    container.className = "tv-widget tradingview-widget-container";
    container.appendChild(widgetDiv);
    var script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js";
    script.async = true;
    script.text = JSON.stringify({
      symbol: "FX:" + container.dataset.symbol,
      width: "100%", height: 220, locale: "en", dateRange: "1M",
      colorTheme: "light", isTransparent: false, autosize: false
    });
    container.appendChild(script);
  }
  function toggleRow() {
    var index = this.dataset.rowIndex;
    var opening = !this.classList.contains("open");
    this.classList.toggle("open");
    var details = document.querySelector('[data-details-index="' + index + '"]');
    if (details) {
      details.classList.toggle("open");
      if (opening) { var widget = details.querySelector(".tv-widget"); if (widget) loadTradingViewWidget(widget); }
    }
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
