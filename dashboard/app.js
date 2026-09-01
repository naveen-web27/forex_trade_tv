(function () {
  var config = window.DASHBOARD_CONFIG || {};
  var state = { rows: [], news: [], timeframe: "all", mainTab: "gold" };
  var pairOrder = config.pairs || [];
  var rates = config.rates || {};
  var $ = function (selector) { return document.querySelector(selector); };
  var fmt = function (value, symbol) { if (value === "" || value == null || isNaN(Number(value))) return "--"; return Number(value).toFixed(symbol && symbol.indexOf("JPY") >= 0 ? 3 : symbol === "XAUUSD" ? 2 : 5); };
  var esc = function (value) { return String(value == null ? "" : value).replace(/[&<>\"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" })[c]; }); };
  var dateKey = function (value) { var text = String(value == null ? "" : value).trim(); var match = text.match(/(\d{4})[-/]([01]\d)[-/]([0-3]\d)/); return match ? match[1] + "-" + match[2] + "-" + match[3] : ""; };
  var dateLabel = function (value) { var key = dateKey(value); if (!key) return "--"; var parts = key.split("-"); var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])); return isNaN(date.getTime()) ? "--" : date.toLocaleDateString("en-US", { month: "short", day: "numeric" }); };
  var wideLabel = function (row, pair) { var width = Number(row.Width || 0); var price = Number(row["Current Price"] || 0); if (!width || !price) return "--"; return width / price >= (pair === "XAUUSD" ? 0.004 : 0.002) ? "Wide band" : "Normal band"; };
  var pipSize = function (pair) { if (pair.indexOf("JPY") >= 0) return 0.01; if (pair.indexOf("XAU") >= 0) return 0.10; return 0.0001; };
  function computeGap(row, pair) {
    var price = Number(row["Current Price"]);
    var bcpr = Number(row.BCPR); var tcpr = Number(row.TCPR);
    if (!price || isNaN(price) || isNaN(bcpr) || isNaN(tcpr)) {
      return { pips: Number(row["Distance Pips"] || 0), direction: row.Direction || "unknown", stale: true };
    }
    var pip = pipSize(pair);
    if (price < bcpr) return { pips: (bcpr - price) / pip, direction: "below", stale: false };
    if (price > tcpr) return { pips: (price - tcpr) / pip, direction: "above", stale: false };
    return { pips: 0, direction: "inside", stale: false };
  }
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
  function isNear(row, pair) { var pips = computeGap(row, pair).pips; return pips >= 5 && pips <= 20; }
  function render() {
    var query = $("#pair-search").value.trim().toUpperCase(); var nearOnly = $("#near-only").checked;
    var pairs = pairOrder.filter(function (pair) {
      var matchesSearch = !query || pair.indexOf(query) >= 0;
      var matchesTab = state.mainTab !== "pairs" || pair !== "XAUUSD";
      return matchesSearch && matchesTab;
    });
    var nearCount = state.rows.filter(function (row) { return isNear(row, row.Symbol); }).length;
    $("#stat-pairs").textContent = new Set(state.rows.map(function (row) { return row.Symbol; })).size;
    $("#stat-bands").textContent = state.rows.length; $("#stat-near").textContent = nearCount;
    $("#stat-scan").textContent = state.rows.length ? String(state.rows[0]["Scan Time"] || "--").slice(11, 16) : "--";
    var visibleRows = [];
    pairs.forEach(function (pair) {
      var rows = rowsForPair(pair).filter(function (row) { return !nearOnly || isNear(row, pair); });
      rows.sort(function (a, b) { return (isNear(a, pair) ? -1 : 1) - (isNear(b, pair) ? -1 : 1); });
      rows.forEach(function (row) { visibleRows.push({ pair: pair, row: row }); });
    });
    var html = [];
    visibleRows.forEach(function (item, index) {
      var row = item.row, pair = item.pair;
      var gap = computeGap(row, pair);
      var near = gap.pips >= 5 && gap.pips <= 20;
      var distance = gap.pips;
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
        '<div><b>Gap to zone</b><span>' + distance.toFixed(1) + ' pips, approaching from ' + esc(gap.direction || "unknown") + (gap.stale ? " (last known price)" : "") + '</span></div>' +
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
    renderGoldSection();
  }
  function impactClass(impact) { var value = String(impact || "").toLowerCase(); return value === "high" ? "impact-high" : value === "medium" ? "impact-medium" : "impact-low"; }
  function goldNews() {
    return state.news.filter(function (item) { return item.Country === "USD"; })
      .sort(function (a, b) { return new Date(a.Date) - new Date(b.Date); });
  }
  function renderGoldSection() {
    var bandsEl = $("#gold-bands"), macroEl = $("#gold-macro"), newsEl = $("#gold-news-list");
    if (!bandsEl) return;
    var goldRows = state.rows.filter(function (row) { return row.Symbol === "XAUUSD"; })
      .sort(function (a, b) { var order = { daily: 0, weekly: 1, monthly: 2 }; return (order[String(a.Timeframe).toLowerCase()] || 9) - (order[String(b.Timeframe).toLowerCase()] || 9); });
    bandsEl.innerHTML = goldRows.length ? goldRows.map(function (row) {
      var gap = computeGap(row, "XAUUSD");
      var near = gap.pips >= 5 && gap.pips <= 20;
      return '<div class="gold-band-row"><b>' + esc(row.Timeframe) + ' — ' + dateLabel(row["VCPR Date"]) + '</b><span>' + fmt(row.BCPR, "XAUUSD") + ' - ' + fmt(row.TCPR, "XAUUSD") + ' · price ' + fmt(row["Current Price"], "XAUUSD") + ' · <span class="' + (near ? "near" : "") + '">' + gap.pips.toFixed(1) + ' pips ' + esc(gap.direction || "") + '</span></span></div>';
    }).join("") : '<div class="gold-band-row"><span>No XAUUSD VCPR data loaded yet.</span></div>';
    if (macroEl) macroEl.innerHTML = rateRow("USD") + '<p class="macro-note">' + esc(macroBias("XAUUSD")) + '</p>';
    var items = goldNews();
    newsEl.innerHTML = items.length ? items.map(function (n) {
      return '<div class="news-item ' + impactClass(n.Impact) + '"><span class="news-country">' + esc(n.Country) + '</span><span class="news-title">' + esc(n.Title) + ' <span class="news-impact">' + esc(n.Impact || "") + '</span></span><span class="news-meta">' + newsLabel(n.Date) + (n.Forecast || n.Previous || n.Actual ? ' · f:' + esc(n.Forecast || "--") + ' p:' + esc(n.Previous || "--") + ' a:' + esc(n.Actual || "--") : '') + '</span></div>';
    }).join("") : '<div class="news-item empty-inline">No USD news loaded yet.</div>';
  }
  function buildAiPrompt() {
    var goldRows = state.rows.filter(function (row) { return row.Symbol === "XAUUSD"; });
    var price = latestPrice("XAUUSD");
    var bandsText = goldRows.length ? goldRows.map(function (row) {
      var gap = computeGap(row, "XAUUSD");
      return "- " + row.Timeframe + " VCPR (" + dateLabel(row["VCPR Date"]) + "): band " + fmt(row.BCPR, "XAUUSD") + " to " + fmt(row.TCPR, "XAUUSD") + ", width " + fmt(row.Width, "XAUUSD") + " (" + wideLabel(row, "XAUUSD") + "), gap " + gap.pips.toFixed(1) + " pips " + (gap.direction || "unknown") + " the band" + (gap.stale ? " (stale price)" : "") + ".";
    }).join("\n") : "- No VCPR band data loaded.";
    var newsText = goldNews().map(function (n) {
      return "- [" + (n.Impact || "?") + "] " + newsLabel(n.Date) + " " + n.Country + " — " + n.Title + " (forecast: " + (n.Forecast || "--") + ", previous: " + (n.Previous || "--") + ", actual: " + (n.Actual || "--") + ")";
    }).join("\n");
    if (!newsText) newsText = "- No scheduled/recent USD news loaded.";
    var usd = rates.USD || {};
    var prompt =
      "You are a gold (XAUUSD) trading analyst. Here is the current market context.\n\n" +
      "CURRENT PRICE\n- XAUUSD: " + (isNaN(price) ? "unknown" : fmt(price, "XAUUSD")) + "\n- Snapshot time: " + new Date().toString() + "\n\n" +
      "VCPR / CPR BAND LEVELS (daily, weekly, monthly)\n" + bandsText + "\n\n" +
      "MACRO BACKDROP (config)\n- " + (usd.bank || "Federal Reserve") + " rate: " + (usd.rate || "--") + " (" + (usd.trend || "--") + ")\n- " + macroBias("XAUUSD") + "\n\n" +
      "MANUALLY ENTERED MACRO & MICRO DATA\n" + buildMacroInputsText() + "\n\n" +
      "CALENDAR NEWS (USD, ForexFactory, chronological)\n" + newsText + "\n\n" +
      "TASK\n" +
      "1. Summarize what the macro/micro data entries above tell us about USD strength and gold demand right now. Note any conflicting signals between factors.\n" +
      "2. Cross-reference the news/data timing with the VCPR/CPR band levels and current price.\n" +
      "3. Give a clear bias (bullish/bearish/neutral) for XAUUSD for the next session with full reasoning.\n" +
      "4. Suggest a trade plan using the specific VCPR band(s) as entry/invalidation zones (entry, stop, target in both price and pips), and flag high-impact news windows to avoid.\n" +
      "5. State the one key risk that would fully invalidate this plan.";
    return prompt;
  }
  // ─── Macro input panel ──────────────────────────────────────────────────
  function miGet(key) {
    var el = document.querySelector('[data-mi="' + key + '"]');
    if (!el) return "";
    return el.type === "checkbox" ? el.checked : el.value;
  }
  function miGetAll() {
    var result = {};
    document.querySelectorAll("[data-mi]").forEach(function (el) {
      result[el.getAttribute("data-mi")] = el.type === "checkbox" ? el.checked : el.value;
    });
    return result;
  }
  function miSave() {
    try { localStorage.setItem("vcpr-macro-inputs", JSON.stringify(miGetAll())); } catch (_) {}
  }
  function miRestore() {
    try {
      var saved = JSON.parse(localStorage.getItem("vcpr-macro-inputs") || "{}");
      Object.keys(saved).forEach(function (key) {
        var el = document.querySelector('[data-mi="' + key + '"]');
        if (!el) return;
        if (el.type === "checkbox") { el.checked = !!saved[key]; el.closest(".mi-geo-tag") && el.closest(".mi-geo-tag").classList.toggle("checked", !!saved[key]); }
        else el.value = saved[key] || "";
      });
      document.querySelectorAll(".mi-actual[data-bias-id]").forEach(computeBias);
      computeFedBias();
    } catch (_) {}
  }
  function parseMiNum(raw) {
    var s = String(raw || "").trim().replace(/,/g, "");
    var m = s.match(/^-?\d+(\.\d+)?/);
    return m ? parseFloat(m[0]) : NaN;
  }
  function computeBias(actualEl) {
    var rule = actualEl.getAttribute("data-bias-rule");
    var biasId = actualEl.getAttribute("data-bias-id");
    var fcKey = actualEl.getAttribute("data-fc-key");
    var fcEl = document.querySelector('[data-mi="' + fcKey + '"]');
    var biasEl = document.getElementById("mi-bias-" + biasId);
    if (!biasEl) return;
    var act = parseMiNum(actualEl.value);
    var fc = fcEl ? parseMiNum(fcEl.value) : NaN;
    if (isNaN(act) || !actualEl.value.trim()) { biasEl.textContent = "--"; biasEl.className = "mi-bias"; return; }
    if (isNaN(fc)) { biasEl.textContent = "No forecast"; biasEl.className = "mi-bias neutral"; return; }
    if (act === fc) { biasEl.textContent = "Neutral ➡"; biasEl.className = "mi-bias neutral"; return; }
    var bullish = rule === "standard" ? act < fc : act > fc;
    biasEl.textContent = bullish ? "Bullish 📈" : "Bearish 📉";
    biasEl.className = "mi-bias " + (bullish ? "bullish" : "bearish");
  }
  function computeFedBias() {
    var el = document.getElementById("mi-fed-tone");
    var biasEl = document.getElementById("mi-bias-fed");
    if (!el || !biasEl) return;
    var map = { hawkish: ["Bearish 📉", "bearish"], dovish: ["Bullish 📈", "bullish"], neutral: ["Neutral ➡", "neutral"] };
    var entry = map[el.value];
    if (entry) { biasEl.textContent = entry[0]; biasEl.className = "mi-bias " + entry[1]; }
    else { biasEl.textContent = "--"; biasEl.className = "mi-bias"; }
  }
  function buildMacroInputsText() {
    var v = miGetAll();
    function dataRow(name, prevKey, fcKey, actKey, rule) {
      var prev = v[prevKey], fc = v[fcKey], act = v[actKey];
      var row = "- " + name + ": prev=" + (prev || "--") + " | forecast=" + (fc || "--") + " | actual=" + (act || "not released");
      if (act) {
        var aNum = parseMiNum(act), fNum = parseMiNum(fc);
        if (!isNaN(aNum) && !isNaN(fNum) && aNum !== fNum) {
          var beat = aNum > fNum;
          var goldBias = rule === "standard"
            ? (beat ? "BEAT → USD Strong → Gold bearish ↓" : "MISS → USD Weak → Gold bullish ↑")
            : (beat ? "ABOVE FC → USD Weak → Gold bullish ↑" : "BELOW FC → USD Strong → Gold bearish ↓");
          row += " → " + goldBias;
        }
      }
      return row;
    }
    var lines = [
      "HIGH IMPACT:",
      dataRow("Core PCE m/m", "pce_prev", "pce_fc", "pce_act", "standard"),
      dataRow("GDP q/q", "gdp_prev", "gdp_fc", "gdp_act", "standard"),
      dataRow("NFP", "nfp_prev", "nfp_fc", "nfp_act", "standard"),
      dataRow("Unemployment Rate", "unemp_prev", "unemp_fc", "unemp_act", "inverse"),
      dataRow("CPI m/m", "cpi_prev", "cpi_fc", "cpi_act", "standard"),
      dataRow("Payrolls Revision", "payrev_prev", "payrev_fc", "payrev_act", "inverse"),
      "\nMEDIUM IMPACT:",
      dataRow("Unemployment Claims", "claims_prev", "claims_fc", "claims_act", "inverse"),
      dataRow("Consumer Confidence", "conf_prev", "conf_fc", "conf_act", "standard"),
      "\nMARKET LEVELS:"
    ];
    if (v.dxy_val || v.dxy_dir) lines.push("- DXY: " + (v.dxy_val || "--") + " | " + (v.dxy_dir === "rising" ? "Rising ↑ → Gold bearish" : v.dxy_dir === "falling" ? "Falling ↓ → Gold bullish" : v.dxy_dir || "--"));
    if (v.us10y_val || v.us10y_dir) lines.push("- US10Y: " + (v.us10y_val || "--") + " | " + (v.us10y_dir === "rising" ? "Rising ↑ → Real rates up → Gold bearish" : v.us10y_dir === "falling" ? "Falling ↓ → Gold bullish" : v.us10y_dir || "--"));
    if (v.vix_val) { var vn = parseFloat(v.vix_val); lines.push("- VIX: " + v.vix_val + (isNaN(vn) ? "" : vn > 30 ? " → HIGH FEAR — safe haven demand supports gold" : vn > 20 ? " → Elevated caution" : " → Calm market")); }
    lines.push("\nFED CHAIR TONE:");
    if (v.fed_tone) lines.push("- Tone: " + v.fed_tone + (v.fed_tone === "hawkish" ? " → Gold bearish" : v.fed_tone === "dovish" ? " → Gold bullish" : ""));
    if (v.fed_notes) lines.push("- Speech notes: " + v.fed_notes);
    var geo = [];
    if (v.geo_me) geo.push("Middle East tension"); if (v.geo_ru) geo.push("Russia-Ukraine");
    if (v.geo_cn) geo.push("China-Taiwan"); if (v.geo_rec) geo.push("Recession fear");
    if (v.geo_bank) geo.push("Banking crisis"); if (v.geo_calm) geo.push("No active tension (calm)");
    lines.push("\nGEOPOLITICAL: " + (geo.length ? geo.join(", ") + (geo.some(function (x) { return x !== "No active tension (calm)"; }) ? " → Safe haven demand → Gold bullish override possible" : "") : "None specified"));
    return lines.join("\n");
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
  function contractSize(pair) { return pair.indexOf("XAU") >= 0 ? 100 : 100000; }
  function latestPrice(pair) { var row = state.rows.filter(function (r) { return r.Symbol === pair; })[0]; return row ? Number(row["Current Price"]) : NaN; }
  function pipValueInUsd(pair, lots) {
    var parts = parsePair(pair);
    var pipInQuote = pipSize(pair) * contractSize(pair) * lots;
    if (parts.quote === "USD") return { usd: pipInQuote, note: "" };
    var directPrice = latestPrice("USD" + parts.quote);
    if (directPrice) return { usd: pipInQuote / directPrice, note: "converted via USD" + parts.quote };
    var inversePrice = latestPrice(parts.quote + "USD");
    if (inversePrice) return { usd: pipInQuote * inversePrice, note: "converted via " + parts.quote + "USD" };
    return { usd: null, note: "no live " + parts.quote + "/USD rate available; showing pips only" };
  }
  function initCalcPairs() {
    var select = $("#calc-pair");
    if (!select || select.options.length) return;
    select.innerHTML = pairOrder.map(function (pair) { return '<option value="' + esc(pair) + '">' + esc(pair) + '</option>'; }).join("");
  }
  function runCalculator(event) {
    event.preventDefault();
    var form = new FormData(event.target);
    var pair = form.get("pair"), direction = form.get("direction");
    var entry = Number(form.get("entry")), exit = Number(form.get("exit")), lots = Number(form.get("lots")) || 1;
    var result = $("#calc-result");
    if (!pair || isNaN(entry) || isNaN(exit)) { result.className = "calc-result show"; result.innerHTML = '<p class="calc-note">Enter a valid entry and exit price.</p>'; return; }
    var pip = pipSize(pair);
    var pips = (direction === "Short" ? (entry - exit) : (exit - entry)) / pip;
    var value = pipValueInUsd(pair, lots);
    var usdPl = value.usd == null ? null : value.usd * pips;
    var pipsClass = pips >= 0 ? "profit" : "loss";
    var usdHtml = usdPl == null
      ? '<div><b>Estimated P/L</b><span>--</span></div>'
      : '<div><b>Estimated P/L</b><span class="' + (usdPl >= 0 ? "profit" : "loss") + '">' + (usdPl >= 0 ? "+" : "") + "$" + usdPl.toFixed(2) + '</span></div>';
    result.className = "calc-result show";
    result.innerHTML =
      '<div><b>Pips</b><span class="' + pipsClass + '">' + (pips >= 0 ? "+" : "") + pips.toFixed(1) + '</span></div>' +
      usdHtml +
      '<div><b>Lot size</b><span>' + lots.toFixed(2) + '</span></div>' +
      (value.note ? '<p class="calc-note">' + esc(value.note) + '</p>' : '');
  }
  $("#refresh").addEventListener("click", load); $("#pair-search").addEventListener("input", render); $("#near-only").addEventListener("change", render);
  (function () {
    var tabs = [$("#ptab-pairs"), $("#ptab-gold")];
    var panels = [$("#tab-panel-pairs"), $("#tab-panel-gold")];
    var tabKeys = ["pairs", "gold"];
    tabs.forEach(function (btn, i) {
      if (!btn) return;
      btn.addEventListener("click", function () {
        tabs.forEach(function (b, j) { if (b) { b.classList.toggle("active", j === i); b.setAttribute("aria-selected", j === i); } });
        panels.forEach(function (p, j) { if (p) p.classList.toggle("active", j === i); });
        state.mainTab = tabKeys[i];
        render();
      });
    });
  }());
  document.querySelectorAll(".tab").forEach(function (tab) { tab.addEventListener("click", function () { document.querySelectorAll(".tab").forEach(function (item) { item.classList.remove("active"); }); tab.classList.add("active"); state.timeframe = tab.dataset.timeframe; render(); }); });
  $("#trade-form").addEventListener("submit", function (event) { event.preventDefault(); var form = new FormData(event.target); var items = journal(); items.unshift(Object.fromEntries(form.entries())); saveJournal(items); event.target.reset(); });
  $("#journal-body").addEventListener("click", function (event) { if (event.target.dataset.delete) { var items = journal(); items.splice(Number(event.target.dataset.delete), 1); saveJournal(items); } });
  $("#export-journal").addEventListener("click", function () { var items = journal(); var csv = "Pair,Direction,Entry,Stop,Target,Note\n" + items.map(function (item) { return [item.pair, item.direction, item.entry, item.stop, item.target, item.note].map(function (value) { return '"' + String(value || "").replace(/"/g, '""') + '"'; }).join(","); }).join("\n"); var link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); link.download = "vcpr-trade-journal.csv"; link.click(); });
  $("#calc-form").addEventListener("submit", runCalculator);
  $("#calc-use-live").addEventListener("click", function () { var pair = $("#calc-pair").value; var price = latestPrice(pair); if (!isNaN(price)) { $("#calc-form").entry.value = price; $("#calc-form").exit.value = price; } });
  $("#gold-generate-prompt").addEventListener("click", function () {
    var wrap = $("#ai-prompt-wrap"), output = $("#ai-prompt-output");
    output.value = buildAiPrompt();
    wrap.style.display = "block";
    wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
  // mi-generate-btn is the second button in the macro input panel — same prompt
  document.addEventListener("click", function (e) {
    if (e.target.id === "mi-generate-btn") {
      var wrap = $("#ai-prompt-wrap"), output = $("#ai-prompt-output");
      output.value = buildAiPrompt();
      wrap.style.display = "block";
      wrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    if (e.target.id === "mi-clear-btn") {
      document.querySelectorAll("[data-mi]").forEach(function (el) {
        if (el.type === "checkbox") { el.checked = false; el.closest(".mi-geo-tag") && el.closest(".mi-geo-tag").classList.remove("checked"); }
        else el.value = "";
      });
      document.querySelectorAll(".mi-actual[data-bias-id]").forEach(computeBias);
      computeFedBias();
      miSave();
    }
  });
  // Bias computation on actual field change
  document.addEventListener("input", function (e) {
    var el = e.target;
    if (el.hasAttribute("data-mi")) miSave();
    if (el.classList.contains("mi-actual") && el.getAttribute("data-bias-id")) computeBias(el);
    if (el.id === "mi-fed-tone") computeFedBias();
    // VIX color hint
    if (el.getAttribute("data-mi") === "vix_val") {
      var hint = document.getElementById("mi-vix-hint"); if (!hint) return;
      var v = parseFloat(el.value);
      hint.style.color = isNaN(v) ? "" : v > 30 ? "var(--red)" : v > 20 ? "var(--amber)" : "var(--green)";
    }
  });
  document.addEventListener("change", function (e) {
    var el = e.target;
    if (el.hasAttribute("data-mi")) miSave();
    if (el.id === "mi-fed-tone") computeFedBias();
    if (el.closest && el.closest(".mi-geo-tag")) el.closest(".mi-geo-tag").classList.toggle("checked", el.checked);
  });
  // Micro checklist checkbox styling
  document.addEventListener("change", function (e) {
    if (e.target.closest && e.target.closest(".micro-check-item")) {
      e.target.closest(".micro-check-item").classList.toggle("done", e.target.checked);
    }
  });
  miRestore();
  $("#copy-ai-prompt").addEventListener("click", function () {
    var output = $("#ai-prompt-output");
    output.select();
    var button = $("#copy-ai-prompt");
    var reset = function () { button.textContent = "Copy prompt"; };
    (navigator.clipboard && navigator.clipboard.writeText
      ? navigator.clipboard.writeText(output.value)
      : Promise.resolve(document.execCommand("copy"))
    ).then(function () { button.textContent = "Copied!"; setTimeout(reset, 1500); }).catch(function () { button.textContent = "Copy failed"; setTimeout(reset, 1500); });
  });
  initCalcPairs();
  renderJournal(); load();
}());
