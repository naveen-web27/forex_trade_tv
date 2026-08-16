window.DASHBOARD_CONFIG = {
  scriptUrl: "https://script.google.com/macros/s/AKfycbyyADs_KVACi-3LFilybTbN_ZcwDTJgLvqnbVxqFFl4q49BbSZxdnpMvUcrpiNyJBLNMg/exec",
  pairs: ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCHF", "EURJPY", "GBPJPY", "XAUUSD", "NZDCHF", "USDCAD", "AUDNZD", "AUDCAD"],
  proximityMaxPips: 20,
  // Reference only — update these whenever a central bank changes rates.
  // "trend" is one of: hiking, cutting, holding.
  rates: {
    USD: { bank: "Federal Reserve", rate: "4.25% - 4.50%", trend: "holding" },
    EUR: { bank: "ECB", rate: "2.25%", trend: "holding" },
    GBP: { bank: "Bank of England", rate: "4.00%", trend: "cutting" },
    JPY: { bank: "Bank of Japan", rate: "0.50%", trend: "hiking" },
    AUD: { bank: "RBA", rate: "3.85%", trend: "holding" },
    NZD: { bank: "RBNZ", rate: "3.25%", trend: "cutting" },
    CAD: { bank: "Bank of Canada", rate: "2.75%", trend: "holding" },
    CHF: { bank: "SNB", rate: "0.00%", trend: "holding" },
    XAU: { bank: "N/A (Gold)", rate: "--", trend: "--" }
  }
};
