/**
 * ═══════════════════════════════════════════════════════════════
 *  NEW CLIENT CONFIG — copy this file to each new client's repo
 *  Filename: config.js
 *
 *  Steps to set up a new client:
 *    1. Create a new GitHub repo (e.g. "roys-kitchen")
 *    2. Copy this file as config.js  — fill in client details below
 *    3. Copy index.html from the template repo              (10 lines)
 *    4. Add images/ folder with logo.png + hero1/2/3.jpg
 *    5. Enable GitHub Pages on the repo → done!
 *
 *  No CSS, no JS needed — everything loads from biryani-core.
 * ═══════════════════════════════════════════════════════════════
 */

window.APP_CONFIG = {

  /* ── 0. CLIENT ID ───────────────────────────────────────────── */
  clientId: 'meal_time',   // ← must match Config sheet column A exactly (lowercase + underscores)

  /* ── 1. BUSINESS INFO ───────────────────────────────────────── */
  business: {
    name:       'Roys Kitchen',                 // ← restaurant name
    tagline:    'Home-style food, made with love.',
    since:      '2015',                         // ← founding year
    phone:      '+91 98765 43210',
    whatsapp:   '+919876543210',
    email:      'hello@royskitchen.in',
    orderLink:  'https://www.zomato.com/',      // ← Zomato/Swiggy link
    award:      'Best Food · City 2024',
    hoursShort: '10 AM – 10 PM Daily',
    hoursLong:  'Mon–Sat: 10 AM – 10 PM\nSunday: 11 AM – 9 PM',
  },

  /* ── 2. THEME COLORS ────────────────────────────────────────── */
  theme: {
    /* Copy a preset from below, or use any hex colors */
    primary:     '#8b1a1a',   // buttons, active states
    primaryDark: '#6e1212',   // hover state
    gold:        '#c9922a',   // accent
    goldLight:   '#e8c46a',   // light accent
    dark:        '#180900',   // dark backgrounds
    darkBg:      '#100500',   // topbar / deepest bg
  },

  /* ── 3. GOOGLE SHEETS ───────────────────────────────────────── */
  sheets: {
    /* File → Share → Publish to web → CSV → copy each sheet's URL */
    menuCSV:      '',  // Sheet 1 (Menu) → pub?output=csv
    ordersCSV:    '',  // Orders sheet  → pub?gid=SHEET_ID&single=true&output=csv
    inventoryCSV: '',  // Inventory sheet → pub?gid=SHEET_ID&single=true&output=csv
    scriptURL:    '',  // Apps Script web app URL (for writes / auth)
  },

  /* ── 4. ABOUT SECTION ───────────────────────────────────────── */
  about: {
    years: '9+',
    title: 'Real Food. Real Flavour.',
    p1:    'Roy\'s Kitchen has been the neighbourhood\'s favourite since 2015.',
    p2:    'Every dish is cooked with fresh ingredients and years of experience.',
    stats: [
      { n: '9+',  l: 'Years Old'    },
      { n: '1',   l: 'Outlet'       },
      { n: '25K+',l: 'Happy Guests' },
    ],
  },

  /* ── 5. WHY CHOOSE US ───────────────────────────────────────── */
  whyUs: [
    { ic: '🍲', title: 'Authentic Recipes', desc: 'Family recipes passed down through generations'  },
    { ic: '🌿', title: 'Fresh Ingredients', desc: 'Sourced fresh every morning from local markets'   },
    { ic: '👨‍🍳', title: 'Expert Chefs',   desc: 'Over 10 years of culinary experience'             },
    { ic: '🏅', title: 'Award Winning',    desc: 'Best Food Restaurant, City Awards 2024'            },
  ],

  /* ── 6. EVENTS ──────────────────────────────────────────────── */
  events: [
    { title: 'Catering Services', desc: 'We bring our food to your wedding, birthday or event.', emoji: '🍽️', btn: 'Enquire Now', href: '#contact' },
    { title: 'Bulk Orders',       desc: 'Special pricing on orders above 20 packs.',              emoji: '📦', btn: 'Call Now',    href: 'tel:+919876543210' },
  ],

  /* ── 7. OUTLETS ─────────────────────────────────────────────── */
  outlets: [
    {
      name:    'Main Branch',
      address: 'No. 10, Main Road\nYour City – 600001',
      phone:   '+91 98765 43210',
      hours:   '10 AM – 10 PM',
      map:     'https://maps.google.com/?q=Your+Restaurant+Location',
    },
    /* Add more outlets here if needed:
    {
      name:    'Branch 2',
      address: 'No. 20, Cross Road\nYour City – 600002',
      phone:   '+91 98765 43211',
      hours:   '10 AM – 9 PM',
      map:     'https://maps.google.com/?q=...',
    }, */
  ],

  /* ── 8. TESTIMONIALS ────────────────────────────────────────── */
  testimonials: [
    { name: 'Priya S.',  date: 'Jan 2025', stars: 5, review: 'Best food in the city! Comes here every week.' },
    { name: 'Arjun M.',  date: 'Dec 2024', stars: 5, review: 'The catering for my wedding was perfect. Everyone loved it!' },
    { name: 'Divya R.',  date: 'Feb 2025', stars: 5, review: 'Fresh, tasty and affordable. My family\'s favourite spot.' },
  ],

  /* ── 9. SOCIAL LINKS ────────────────────────────────────────── */
  social: {
    instagram: 'https://instagram.com/',
    facebook:  'https://facebook.com/',
    whatsapp:  'https://wa.me/919876543210',
    youtube:   '',
    zomato:    '',
    swiggy:    '',
  },

  /* ── 10. HERO SLIDES ────────────────────────────────────────── */
  heroSlides: [
    { tag: 'Since 2015 · Your City', h1Em: 'Roys',  h1Rest: ' Kitchen',      p: 'Authentic home-style food, served fresh every day.'   },
    { tag: 'Catering Available',     h1Em: 'Feed',  h1Rest: ' Your Crowd',   p: 'Bulk orders & catering for weddings and events.'       },
    { tag: 'Fresh Every Day',        h1Em: 'Fresh', h1Rest: ' Every Morning',p: 'No preservatives. Just real ingredients, real taste.'  },
  ],

  /* ── 11. CONTACT FORM URL ───────────────────────────────────── */
  formURL: '',   // Optional: Apps Script URL to receive table reservations

  /* ── 12. DEMO MENU (shown when Sheet not connected) ─────────── */
  demoMenu: [
    { Category: 'Mains',   Name: 'Chicken Curry',   Description: 'Spiced chicken in rich gravy',  Price: '160', Type: 'NonVeg', ImageURL: '', Badge: 'Bestseller', Available: 'Yes' },
    { Category: 'Mains',   Name: 'Fish Fry',         Description: 'Crispy spiced fish fillets',    Price: '200', Type: 'NonVeg', ImageURL: '', Badge: '',           Available: 'Yes' },
    { Category: 'Mains',   Name: 'Dal Tadka',        Description: 'Yellow lentils with tempering', Price: '100', Type: 'Veg',    ImageURL: '', Badge: '',           Available: 'Yes' },
    { Category: 'Rice',    Name: 'Fried Rice',       Description: 'Wok-tossed egg fried rice',     Price: '120', Type: 'NonVeg', ImageURL: '', Badge: 'New',        Available: 'Yes' },
    { Category: 'Rice',    Name: 'Plain Rice',       Description: 'Steamed basmati rice',          Price: '40',  Type: 'Veg',    ImageURL: '', Badge: '',           Available: 'Yes' },
    { Category: 'Drinks',  Name: 'Fresh Lime Soda',  Description: 'Chilled lime with soda',        Price: '50',  Type: 'Veg',    ImageURL: '', Badge: '',           Available: 'Yes' },
  ],

};

/* ═══ Auto-apply CSS theme variables ═══
   Runs immediately so brand colors appear with zero flicker.  */
(function applyTheme() {
  var t = window.APP_CONFIG.theme || {};
  var r = document.documentElement;
  if (t.primary)     r.style.setProperty('--red',   t.primary);
  if (t.primaryDark) r.style.setProperty('--red2',  t.primaryDark);
  if (t.gold)        r.style.setProperty('--gold',  t.gold);
  if (t.goldLight)   r.style.setProperty('--gold2', t.goldLight);
  if (t.dark)        r.style.setProperty('--dark',  t.dark);
  if (t.darkBg)      r.style.setProperty('--dark2', t.darkBg);
})();
