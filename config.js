/**
 * ╔═══════════════════════════════════════════════════════════════════╗
 * ║             BILLZO — MASTER CONFIG FILE                           ║
 * ║   Simple billing & website system for small businesses            ║
 * ╠═══════════════════════════════════════════════════════════════════╣
 * ║  HOW TO SWITCH CLIENTS (takes 5 seconds):                         ║
 * ║    Change ACTIVE_CLIENT on the very next line.  That's it!        ║
 * ║                                                                   ║
 * ║  HOW TO ADD A NEW CLIENT:                                         ║
 * ║    1. Copy /clients/_template.js as reference                     ║
 * ║    2. Add a new key inside BILLZO_CLIENTS below                   ║
 * ║    3. Set ACTIVE_CLIENT to your new key                           ║
 * ║    4. Push to GitHub Pages                                        ║
 * ╚═══════════════════════════════════════════════════════════════════╝
 */

/* ═══════════════════════════════════════════════════════════════
   ▼▼▼  CHANGE THIS ONE LINE TO SWITCH CLIENTS  ▼▼▼
═══════════════════════════════════════════════════════════════ */
const ACTIVE_CLIENT = 'gops_briyani';
/* ═══════════════════════════════════════════════════════════════
   ▲▲▲  CHANGE THIS ONE LINE TO SWITCH CLIENTS  ▲▲▲
═══════════════════════════════════════════════════════════════ */


/* ════════════════════════════════════════════════════════════════════
   CLIENT REGISTRY
   Each key is a client. Add as many as you need.
   See /clients/_template.js for a blank starting point.
════════════════════════════════════════════════════════════════════ */
const BILLZO_CLIENTS = {


  /* ──────────────────────────────────────────────────────────────
     CLIENT: gops_briyani
     Type  : Restaurant
  ─────────────────────────────────────────────────────────────── */
  gops_briyani: {

    /* ── 1. BUSINESS INFO ─────────────────────────────────────── */
    business: {
      name:       'Gops Briyani',
      tagline:    'Authentic South Indian Biryani, cooked with love.',
      type:       'restaurant',   // restaurant | bakery | supermarket | stationery | general
      since:      '2018',
      phone:      '+91 98765 43210',
      whatsapp:   '+919876543210',      // digits only, no spaces
      email:      'gops@example.com',
      address:    'No. 1, Main Road, Erode – 638001',
      gstin:      '',
      orderLink:  'https://www.zomato.com/',
      award:      'Best Biryani · Erode 2024',
      hoursShort: '11 AM – 11 PM Daily',
      hoursLong:  'Mon–Thu: 11 AM – 10 PM\nFri–Sun: 11 AM – 11 PM',
    },

    /* ── 2. THEME ──────────────────────────────────────────────
       Copy a preset from the THEME PRESETS section at the
       bottom of this file, or use any hex colors you like.    */
    theme: {
      primary:     '#8b1a1a',   // main brand color (buttons, active states)
      primaryDark: '#6e1212',   // hover / darker version
      gold:        '#c9922a',   // accent color
      goldLight:   '#e8c46a',   // lighter accent
      dark:        '#180900',   // main dark background
      darkBg:      '#100500',   // topbar / PIN screen background
      darkPanel:   '#1e0f05',   // modals / sidebar panels
    },

    /* ── 3. GOOGLE SHEETS ────────────────────────────────────────
       SETUP GUIDE (one-time, ~5 min):
       a) Create a Google Sheet
       b) Tab 1 named "Menu"  — columns:
          Category | Name | Description | Price | Type | ImageURL | Badge | Available
       c) File → Share → Publish to web → CSV → copy URL → paste below as menuCSV
       d) Tab 2 named "Orders" (Apps Script creates this automatically)
          Share → Publish → select "Orders" tab → CSV → copy URL → paste as ordersCSV
       e) Deploy apps-script.js → copy Web App URL → paste as scriptURL             */
    sheets: {
      menuCSV:   'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5nrT4MebZBW-Az3Efq-hRzfQm-R8ehCKYGVqk6H4Zs6Z3u4RBlYcE52SV9tQ2yT0PtcUNdh7_UXfQ/pub?output=csv',
      ordersCSV: 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5nrT4MebZBW-Az3Efq-hRzfQm-R8ehCKYGVqk6H4Zs6Z3u4RBlYcE52SV9tQ2yT0PtcUNdh7_UXfQ/pub?gid=553776590&single=true&output=csv',
      scriptURL: 'https://script.google.com/macros/s/AKfycbyYP49LWQ5-sk5pHEaPIZwphe9fA2bfqeJdo4uJcLedzZ-m14pxcnxeB6inpZuBbxRxFg/exec',
    },

    /* ── 4. BILLING APP SETTINGS ─────────────────────────────── */
    billing: {
      staffPin:        '1234',
      pinEnabled:      false,    // true = require PIN to open billing.html
      currency:        '₹',
      gstEnabled:      true,
      gstDefault:      0,        // default GST % shown on bill
      discountEnabled: true,
      customerTypes:   ['Walk-in', 'Online', 'Takeaway', 'Delivery'],
      payModes:        ['Cash', 'UPI', 'Card'],
      whatsappBill:    true,
      downloadBill:    true,
      printBill:       true,
    },

    /* ── 5. ADMIN SETTINGS ───────────────────────────────────── */
    admin: {
      pin: '1234',   // default PIN (user can change inside admin panel)
    },

    /* ── 6. ABOUT SECTION (website) ──────────────────────────── */
    about: {
      years: '6+',
      title: 'Real Biryani. Real Flavour.',
      p1:    'Born from a passion for authentic South Indian flavours, Gops Briyani has been the go-to biryani spot in Erode since 2018.',
      p2:    'Every pot is slow-cooked with hand-ground spices, fresh ingredients, and generations of culinary wisdom.',
      stats: [
        { n: '6+',   l: 'Years Old'      },
        { n: '2',    l: 'Outlets'        },
        { n: '50K+', l: 'Happy Guests'   },
      ],
    },

    /* ── 7. WHY CHOOSE US (website) ──────────────────────────── */
    whyUs: [
      { ic: '🍲', title: 'Authentic Recipes',  desc: 'Traditional dum-cooked biryani with whole spices'    },
      { ic: '🌿', title: 'Fresh Ingredients',  desc: 'Sourced fresh every morning from local markets'      },
      { ic: '👨‍🍳', title: 'Expert Chefs',   desc: 'Trained in authentic South Indian cooking'            },
      { ic: '🏅', title: 'Award Winning',      desc: 'Best Biryani Restaurant, Erode Food Awards 2024'     },
    ],

    /* ── 8. EVENTS (website) ─────────────────────────────────── */
    events: [
      { title: 'Catering Services', desc: 'We bring Gops Briyani to your event — weddings, birthdays, corporates.', emoji: '🍽️', btn: 'Enquire Now', href: '#contact' },
      { title: 'Bulk Orders',       desc: 'Special pricing on orders above 50 packs. Call us to discuss.',           emoji: '📦', btn: 'Call Now',    href: 'tel:+919876543210' },
    ],

    /* ── 9. OUTLETS (website) ────────────────────────────────── */
    outlets: [
      { name: 'Main Branch – Erode',  address: 'No. 1, Main Road\nErode – 638001',  phone: '+91 98765 43210', hours: '11 AM – 11 PM', map: 'https://maps.google.com/?q=Erode' },
      { name: 'Branch 2 – Erode',     address: 'No. 2, Cross Road\nErode – 638002', phone: '+91 98765 43211', hours: '11 AM – 10 PM', map: 'https://maps.google.com/?q=Erode' },
    ],

    /* ── 10. TESTIMONIALS (website) ──────────────────────────── */
    testimonials: [
      { name: 'Priya S.',  date: 'Jan 2025', stars: 5, review: 'Best Chicken Biryani in Erode! The aroma fills the whole street. My family loves it!' },
      { name: 'Arjun M.',  date: 'Dec 2024', stars: 5, review: 'Ordered for my office party — 40 people, all happy. Delivery was on time too!' },
      { name: 'Divya R.',  date: 'Feb 2025', stars: 5, review: 'The mutton biryani is unbelievable. Worth every rupee. Will keep coming back!' },
    ],

    /* ── 11. SOCIAL MEDIA (website) ──────────────────────────── */
    social: {
      instagram: 'https://instagram.com/',
      facebook:  'https://facebook.com/',
      whatsapp:  'https://wa.me/919876543210',
      youtube:   '',
      swiggy:    '',
      zomato:    'https://www.zomato.com/',
    },

    /* ── 12. HERO SLIDES (website) ───────────────────────────── */
    heroSlides: [
      { tag: 'Since 2018 · Erode',      h1Em: 'Gops',  h1Rest: ' Briyani',       p: 'Authentic South Indian Dum Biryani, slow-cooked with love.' },
      { tag: 'Catering Available',      h1Em: 'Feed',  h1Rest: ' Your Crowd',     p: 'Bulk orders & catering for weddings, events and parties.'   },
      { tag: 'Fresh Every Day',         h1Em: 'Fresh', h1Rest: ' Every Morning',  p: 'Hand-ground spices, fresh ingredients, cooked to order.'    },
    ],

    /* ── 13. CONTACT / RESERVATION FORM URL ─────────────────── */
    formURL: '',   // Google Apps Script URL for contact form (optional)

    /* ── 14. DEMO MENU (shown when Sheet not connected) ─────── */
    demoMenu: [
      { Category: 'Biryani', Name: 'Chicken Dum Biryani', Description: 'Slow-cooked on dum with whole spices', Price: '180', Type: 'NonVeg', ImageURL: '', Badge: 'Bestseller', Available: 'Yes' },
      { Category: 'Biryani', Name: 'Mutton Biryani',      Description: 'Tender mutton in aged basmati rice',   Price: '220', Type: 'NonVeg', ImageURL: '', Badge: '',           Available: 'Yes' },
      { Category: 'Biryani', Name: 'Veg Biryani',         Description: 'Seasonal vegetables in saffron rice',  Price: '130', Type: 'Veg',    ImageURL: '', Badge: 'New',        Available: 'Yes' },
      { Category: 'Biryani', Name: 'Egg Biryani',         Description: 'Masala eggs with spiced rice',         Price: '140', Type: 'NonVeg', ImageURL: '', Badge: '',           Available: 'Yes' },
      { Category: 'Sides',   Name: 'Raita',               Description: 'Chilled yogurt with cucumber',         Price: '30',  Type: 'Veg',    ImageURL: '', Badge: '',           Available: 'Yes' },
      { Category: 'Sides',   Name: 'Salna',               Description: 'Spiced gravy side dish',               Price: '20',  Type: 'NonVeg', ImageURL: '', Badge: '',           Available: 'Yes' },
      { Category: 'Drinks',  Name: 'Mango Lassi',         Description: 'Chilled yogurt mango drink',           Price: '60',  Type: 'Veg',    ImageURL: '', Badge: 'Bestseller', Available: 'Yes' },
      { Category: 'Drinks',  Name: 'Buttermilk',          Description: 'Fresh spiced buttermilk',              Price: '25',  Type: 'Veg',    ImageURL: '', Badge: '',           Available: 'Yes' },
    ],
  },


  /* ──────────────────────────────────────────────────────────────
     CLIENT: bakery_demo
     Type  : Bakery  (uses PRESET_BAKERY theme)
  ─────────────────────────────────────────────────────────────── */
  bakery_demo: {

    business: {
      name:       'Fresh Bakes',
      tagline:    'Home-style bakes, fresh every morning.',
      type:       'bakery',
      since:      '2020',
      phone:      '+91 99999 00000',
      whatsapp:   '+919999900000',
      email:      'hello@freshbakes.in',
      address:    '10, Gandhi Street, Salem – 636001',
      gstin:      '',
      orderLink:  '#',
      award:      '',
      hoursShort: '7 AM – 9 PM Daily',
      hoursLong:  'Mon–Sat: 7 AM – 9 PM\nSunday: 8 AM – 6 PM',
    },

    theme: {
      primary:     '#7b4f2e',   // warm brown
      primaryDark: '#5c3820',
      gold:        '#d4813a',   // orange-gold
      goldLight:   '#f0b97e',
      dark:        '#1a0d05',
      darkBg:      '#120800',
      darkPanel:   '#221208',
    },

    sheets: {
      menuCSV:   '',   // paste your Google Sheet CSV URL here
      ordersCSV: '',   // paste your Orders tab CSV URL here
      scriptURL: '',   // paste your Apps Script URL here
    },

    billing: {
      staffPin:        '0000',
      pinEnabled:      false,
      currency:        '₹',
      gstEnabled:      false,
      gstDefault:      0,
      discountEnabled: true,
      customerTypes:   ['Walk-in', 'Home Delivery', 'Pre-order'],
      payModes:        ['Cash', 'UPI'],
      whatsappBill:    true,
      downloadBill:    true,
      printBill:       true,
    },

    admin: {
      pin: '0000',
    },

    about: {
      years: '4+',
      title: 'Baked Fresh, Every Morning',
      p1:    'Fresh Bakes started as a home kitchen in 2020 and has grown into Salem\'s favourite neighbourhood bakery.',
      p2:    'Every loaf, cake, and cookie is baked in-house with no preservatives and only real ingredients.',
      stats: [
        { n: '4+',  l: 'Years Old'    },
        { n: '1',   l: 'Outlet'       },
        { n: '200', l: 'Daily Orders' },
      ],
    },

    whyUs: [
      { ic: '🍞', title: 'Freshly Baked',   desc: 'Baked every morning — no day-old items ever'         },
      { ic: '🥚', title: 'Eggless Options', desc: 'Full range of eggless cakes and breads available'     },
      { ic: '🎂', title: 'Custom Cakes',    desc: 'Birthday, anniversary & wedding cakes to order'       },
      { ic: '🚚', title: 'Home Delivery',   desc: 'Free delivery within 3 km of our store'               },
    ],

    events: [
      { title: 'Custom Cakes',  desc: 'Your dream birthday, anniversary or wedding cake — made to order.', emoji: '🎂', btn: 'Order Now', href: '#contact' },
      { title: 'Bulk Orders',   desc: 'Corporate gifts, event trays and bulk cookie boxes available.',      emoji: '📦', btn: 'Enquire',   href: '#contact' },
    ],

    outlets: [
      { name: 'Fresh Bakes – Salem', address: '10, Gandhi Street\nSalem – 636001', phone: '+91 99999 00000', hours: '7 AM – 9 PM', map: 'https://maps.google.com/' },
    ],

    testimonials: [
      { name: 'Reka M.',   date: 'Mar 2025', stars: 5, review: 'The chocolate truffle cake was divine! Ordered for my daughter\'s birthday — everyone loved it.' },
      { name: 'Suresh K.', date: 'Feb 2025', stars: 5, review: 'Best croissants in Salem. I come here every Sunday morning without fail!' },
      { name: 'Anitha P.', date: 'Jan 2025', stars: 5, review: 'The eggless vanilla cake was so soft and fresh. My kids absolutely loved it!' },
    ],

    social: {
      instagram: 'https://instagram.com/',
      facebook:  'https://facebook.com/',
      whatsapp:  'https://wa.me/919999900000',
      youtube:   '',
    },

    heroSlides: [
      { tag: 'Freshly Baked Daily',     h1Em: 'Fresh',   h1Rest: ' Bakes',        p: 'Home-style bakes made fresh every morning with love.'     },
      { tag: 'Custom Orders Welcome',   h1Em: 'Your',    h1Rest: ' Dream Cake',   p: 'Custom birthday, anniversary & wedding cakes.'            },
      { tag: 'No Preservatives',        h1Em: 'Real',    h1Rest: ' Ingredients', p: 'No preservatives. No compromise. Just fresh goodness.'   },
    ],

    formURL: '',

    demoMenu: [
      { Category: 'Breads',   Name: 'White Sandwich Loaf', Description: 'Soft white bread, freshly baked',    Price: '45',  Type: 'Veg', ImageURL: '', Badge: 'Bestseller', Available: 'Yes' },
      { Category: 'Breads',   Name: 'Brown Bread',         Description: 'Whole wheat, no preservatives',      Price: '55',  Type: 'Veg', ImageURL: '', Badge: '',           Available: 'Yes' },
      { Category: 'Cakes',    Name: 'Chocolate Truffle',   Description: 'Rich dark chocolate ganache cake',   Price: '380', Type: 'Veg', ImageURL: '', Badge: 'Bestseller', Available: 'Yes' },
      { Category: 'Cakes',    Name: 'Vanilla Sponge',      Description: 'Light & fluffy vanilla cake',        Price: '320', Type: 'Veg', ImageURL: '', Badge: '',           Available: 'Yes' },
      { Category: 'Pastries', Name: 'Croissant',           Description: 'Buttery, flaky pastry',              Price: '60',  Type: 'Veg', ImageURL: '', Badge: 'New',        Available: 'Yes' },
      { Category: 'Pastries', Name: 'Puff Pastry',         Description: 'Crispy golden puff',                 Price: '35',  Type: 'Veg', ImageURL: '', Badge: '',           Available: 'Yes' },
      { Category: 'Cookies',  Name: 'Chocolate Chip',      Description: 'Classic choco chip cookies (6 pcs)', Price: '120', Type: 'Veg', ImageURL: '', Badge: 'Bestseller', Available: 'Yes' },
      { Category: 'Drinks',   Name: 'Fresh Juice',         Description: 'Seasonal fresh fruit juice',         Price: '60',  Type: 'Veg', ImageURL: '', Badge: '',           Available: 'Yes' },
    ],
  },


}; /* ← END BILLZO_CLIENTS — add new clients above this line */


/* ════════════════════════════════════════════════════════════════════
   THEME PRESETS
   Copy one of these into your client's  theme: { ... }  block above.
════════════════════════════════════════════════════════════════════

  PRESET_RESTAURANT  (dark red + gold — current default)
    primary:'#8b1a1a', primaryDark:'#6e1212',
    gold:'#c9922a',    goldLight:'#e8c46a',
    dark:'#180900',    darkBg:'#100500',   darkPanel:'#1e0f05'

  PRESET_BAKERY  (warm brown + orange-gold)
    primary:'#7b4f2e', primaryDark:'#5c3820',
    gold:'#d4813a',    goldLight:'#f0b97e',
    dark:'#1a0d05',    darkBg:'#120800',   darkPanel:'#221208'

  PRESET_SUPERMARKET  (deep green + teal)
    primary:'#1b5e20', primaryDark:'#145218',
    gold:'#00897b',    goldLight:'#4db6ac',
    dark:'#030f06',    darkBg:'#020c04',   darkPanel:'#071a0b'

  PRESET_STATIONERY  (deep blue + amber)
    primary:'#1a2b6e', primaryDark:'#111f56',
    gold:'#f59e0b',    goldLight:'#fcd34d',
    dark:'#050912',    darkBg:'#030710',   darkPanel:'#0a1022'

  PRESET_PHARMACY  (navy + cyan)
    primary:'#0d3b6e', primaryDark:'#082b54',
    gold:'#0891b2',    goldLight:'#67e8f9',
    dark:'#020a12',    darkBg:'#01070f',   darkPanel:'#051525'

════════════════════════════════════════════════════════════════════ */


/* ════════════════════════════════════════════════════════════════════
   ACTIVATE CLIENT — do not edit below this line
════════════════════════════════════════════════════════════════════ */
window.APP_CONFIG = BILLZO_CLIENTS[ACTIVE_CLIENT];
if (!window.APP_CONFIG) {
  var _fbKeys = Object.keys(BILLZO_CLIENTS);
  console.warn('[Billzo] Client "' + ACTIVE_CLIENT + '" not found. Falling back to: ' + _fbKeys[0]);
  window.APP_CONFIG = BILLZO_CLIENTS[_fbKeys[0]];
}

/* ═══ Auto-apply CSS theme variables ═══
   This runs immediately in <head> before the page renders,
   so the correct brand colors appear with zero flicker.    */
(function applyBillzoTheme() {
  var c = window.APP_CONFIG;
  if (!c || !c.theme) return;
  var t = c.theme;
  var r = document.documentElement;
  if (t.primary)     r.style.setProperty('--red',   t.primary);
  if (t.primaryDark) r.style.setProperty('--red2',  t.primaryDark);
  if (t.gold)        r.style.setProperty('--gold',  t.gold);
  if (t.goldLight)   r.style.setProperty('--gold2', t.goldLight);
  if (t.dark)        r.style.setProperty('--dark',  t.dark);
  if (t.darkBg)      r.style.setProperty('--dark2', t.darkBg);
  if (t.darkPanel)   r.style.setProperty('--panel', t.darkPanel);
})();
