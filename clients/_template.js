/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║   BILLZO — NEW CLIENT TEMPLATE                               ║
 * ║                                                              ║
 * ║  STEPS TO ONBOARD A NEW CLIENT (~10–20 mins):               ║
 * ║                                                              ║
 * ║  1. Copy this file → save as clients/your_client_name.js    ║
 * ║  2. Fill in all sections below                              ║
 * ║  3. Open config.js → paste the config block into            ║
 * ║     BILLZO_CLIENTS with your chosen key name                ║
 * ║  4. Change ACTIVE_CLIENT = 'your_client_name'               ║
 * ║  5. Push to GitHub Pages — live in seconds!                 ║
 * ║                                                              ║
 * ║  CHECKLIST:                                                  ║
 * ║  □ business.name, phone, address filled in                   ║
 * ║  □ theme chosen from THEME PRESETS in config.js              ║
 * ║  □ Google Sheet created with Menu & Orders tabs              ║
 * ║  □ Sheet published to web → CSV URLs pasted in sheets.*      ║
 * ║  □ apps-script.js deployed → URL pasted in sheets.scriptURL  ║
 * ║  □ billing.staffPin and admin.pin set                        ║
 * ║  □ outlets, testimonials, heroSlides filled in               ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 *  Copy the block below (starting from "your_client_key: {")
 *  and paste it inside BILLZO_CLIENTS in config.js.
 *  Rename "your_client_key" to something like "sharma_bakery".
 */

// ─────────────────────────────────────────────────────────────
//  PASTE THIS BLOCK INTO BILLZO_CLIENTS IN config.js
// ─────────────────────────────────────────────────────────────

your_client_key: {

  /* ── 1. BUSINESS INFO ─────────────────────────────────────── */
  business: {
    name:       'Your Business Name',     // Shows on bills, website title, topbar
    tagline:    'Your catchy tagline here.',
    type:       'restaurant',             // restaurant | bakery | supermarket | stationery | general
    since:      '2024',
    phone:      '+91 XXXXX XXXXX',
    whatsapp:   '+91XXXXXXXXXX',          // digits only, no spaces — used for WhatsApp links
    email:      'hello@yourbusiness.com',
    address:    'Street Name, City – PIN',
    gstin:      '',                       // leave blank if not GST registered
    orderLink:  '',                       // Swiggy / Zomato URL, or '#' if none
    award:      '',                       // e.g. 'Best Bakery · City 2024' — or leave ''
    hoursShort: '9 AM – 9 PM Daily',
    hoursLong:  'Mon–Sat: 9 AM – 9 PM\nSunday: 10 AM – 6 PM',
  },

  /* ── 2. THEME ──────────────────────────────────────────────
     Copy a preset from config.js (search for THEME PRESETS).
     Options: PRESET_RESTAURANT | PRESET_BAKERY |
              PRESET_SUPERMARKET | PRESET_STATIONERY | PRESET_PHARMACY
     Or use any hex colors you like.                           */
  theme: {
    primary:     '#8b1a1a',   // main color — buttons, active nav, links
    primaryDark: '#6e1212',   // hover/pressed version of primary
    gold:        '#c9922a',   // accent color — prices, highlights
    goldLight:   '#e8c46a',   // lighter accent — gradient end, glow
    dark:        '#180900',   // main page background (dark mode)
    darkBg:      '#100500',   // topbar / PIN screen background
    darkPanel:   '#1e0f05',   // modals, sidebar, cards
  },

  /* ── 3. GOOGLE SHEETS ────────────────────────────────────────
     QUICK SETUP (5 minutes):

     STEP A — Create the Sheet:
       • Go to sheets.google.com → New spreadsheet
       • Rename Tab 1 to "Menu" — add these exact column headers in Row 1:
           Category | Name | Description | Price | Type | ImageURL | Badge | Available
       • Type = "Veg" or "NonVeg"
       • Badge = "Bestseller" or "New" or "Chef Special" or leave blank
       • Available = "Yes" or "No"

     STEP B — Get the Menu CSV URL:
       • File → Share → Publish to web
       • Select "Menu" tab → select "CSV" → click Publish
       • Copy the URL → paste below as menuCSV

     STEP C — Get the Orders CSV URL:
       • In "Publish to web", select "Orders" tab → CSV → Publish
       • (The "Orders" tab is created automatically by the Apps Script)
       • Copy URL → paste below as ordersCSV
       • Tip: find the gid= number in the URL — that's the tab ID

     STEP D — Deploy Apps Script:
       • Open apps-script.js → copy its contents
       • In Google Sheets → Extensions → Apps Script → paste → Save
       • Deploy → New Deployment → Web App
       • Execute as: Me | Who can access: Anyone
       • Click Deploy → copy the Web App URL → paste below as scriptURL  */
  sheets: {
    menuCSV:   '',    // https://docs.google.com/spreadsheets/d/e/YOUR_ID/pub?output=csv
    ordersCSV: '',    // https://docs.google.com/spreadsheets/d/e/YOUR_ID/pub?gid=XXXXXX&single=true&output=csv
    scriptURL: '',    // https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
  },

  /* ── 4. BILLING APP SETTINGS ─────────────────────────────── */
  billing: {
    staffPin:        '1234',   // PIN required when pinEnabled is true
    pinEnabled:      false,    // true = show PIN screen before billing.html opens
    currency:        '₹',
    gstEnabled:      true,     // show the GST toggle in billing
    gstDefault:      0,        // default GST % on a new bill (0 = no GST by default)
    discountEnabled: true,
    customerTypes:   ['Walk-in', 'Online', 'Takeaway'],   // shown in Type dropdown
    payModes:        ['Cash', 'UPI', 'Card'],              // shown in Payment dropdown
    whatsappBill:    true,
    downloadBill:    true,
    printBill:       true,
  },

  /* ── 5. ADMIN SETTINGS ───────────────────────────────────── */
  admin: {
    pin: '1234',   // Admin panel PIN (client can change it inside the panel)
  },

  /* ── 6. ABOUT SECTION (website homepage) ─────────────────── */
  about: {
    years: '1+',
    title: 'Our Story',
    p1:    'Write a short, warm intro about the business here. One or two sentences.',
    p2:    'Second paragraph — mention quality, commitment, what makes them special.',
    stats: [
      { n: '1+',  l: 'Years Old'       },
      { n: '1',   l: 'Outlet'          },
      { n: '500', l: 'Happy Customers' },
    ],
  },

  /* ── 7. WHY CHOOSE US (website) ──────────────────────────── */
  whyUs: [
    { ic: '⭐', title: 'Quality First',   desc: 'We never compromise on quality or freshness'   },
    { ic: '🚀', title: 'Quick Service',   desc: 'Fast and friendly service, always'              },
    { ic: '💰', title: 'Best Prices',     desc: 'Great value for your money, every time'        },
    { ic: '🏆', title: 'Trusted Brand',   desc: 'Hundreds of happy customers and counting'      },
  ],

  /* ── 8. EVENTS / SERVICES (website) ─────────────────────── */
  events: [
    { title: 'Special Events', desc: 'We cater for all your special occasions.', emoji: '🎉', btn: 'Contact Us', href: '#contact' },
    { title: 'Bulk Orders',    desc: 'Special pricing available on bulk orders.', emoji: '📦', btn: 'Call Now',   href: 'tel:+91XXXXXXXXXX' },
  ],

  /* ── 9. OUTLETS (website) ────────────────────────────────── */
  outlets: [
    {
      name:    'Branch Name',
      address: 'Street Name\nCity – PIN',
      phone:   '+91 XXXXX XXXXX',
      hours:   '9 AM – 9 PM',
      map:     'https://maps.google.com/',   // Google Maps link for this branch
    },
    // Add more outlets here if needed
  ],

  /* ── 10. TESTIMONIALS (website) ──────────────────────────── */
  testimonials: [
    { name: 'Customer One',   date: 'Jan 2025', stars: 5, review: 'Great product/service! Highly recommend to everyone.'  },
    { name: 'Customer Two',   date: 'Feb 2025', stars: 5, review: 'Amazing quality and excellent value for money!'        },
    { name: 'Customer Three', date: 'Mar 2025', stars: 5, review: 'Friendly staff and quick service. Will visit again!'   },
  ],

  /* ── 11. SOCIAL MEDIA LINKS (website) ───────────────────── */
  social: {
    instagram: '',    // https://instagram.com/yourhandle
    facebook:  '',    // https://facebook.com/yourpage
    whatsapp:  '',    // https://wa.me/91XXXXXXXXXX
    youtube:   '',
    swiggy:    '',
    zomato:    '',
  },

  /* ── 12. HERO SLIDES (website homepage slider) ──────────── */
  heroSlides: [
    { tag: 'Your Tagline',        h1Em: 'Business',  h1Rest: ' Name',         p: 'Short compelling description of the business.'     },
    { tag: 'What Makes You Special', h1Em: 'Key',    h1Rest: ' Feature',      p: 'Highlight the most important feature or offer.'    },
    { tag: 'Open Now',            h1Em: 'Visit',     h1Rest: ' Us Today',     p: 'Address or timing or a call-to-action message.'    },
  ],

  /* ── 13. CONTACT / RESERVATION FORM (optional) ──────────── */
  formURL: '',   // Google Apps Script URL to collect form submissions

  /* ── 14. DEMO MENU (shown when Google Sheet is not set up yet) ── */
  demoMenu: [
    { Category: 'Category 1', Name: 'Item 1', Description: 'Short description', Price: '100', Type: 'Veg',    ImageURL: '', Badge: 'Bestseller', Available: 'Yes' },
    { Category: 'Category 1', Name: 'Item 2', Description: 'Short description', Price: '150', Type: 'NonVeg', ImageURL: '', Badge: '',           Available: 'Yes' },
    { Category: 'Category 2', Name: 'Item 3', Description: 'Short description', Price: '80',  Type: 'Veg',    ImageURL: '', Badge: 'New',        Available: 'Yes' },
    { Category: 'Category 2', Name: 'Item 4', Description: 'Short description', Price: '200', Type: 'Veg',    ImageURL: '', Badge: '',           Available: 'Yes' },
  ],

},  // ← keep this comma when pasting into config.js
