/* SafeGround web app — landing page, map-first workspace (Overview / Readiness / Simulate), docs pages.
   Computed facts come first; Gemini text is shown beneath them and labelled. */
"use strict";

/* ---------------------------------------------------------------- icons (Lucide, inline SVG) */
const ICONS = {
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
  help: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  phone: '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
  dashboard: '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
  clipboard: '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
  crosshair: '<circle cx="12" cy="12" r="10"/><path d="M22 12h-4"/><path d="M6 12H2"/><path d="M12 6V2"/><path d="M12 22v-4"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  layers: '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>', minus: '<path d="M5 12h14"/>',
  locate: '<path d="M2 12h3"/><path d="M19 12h3"/><path d="M12 2v3"/><path d="M12 19v3"/><circle cx="12" cy="12" r="7"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  pin: '<path d="M20 10c0 5-5.54 10.19-7.4 11.8a1 1 0 0 1-1.2 0C9.54 20.19 4 15 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
  chev: '<path d="m9 18 6-6-6-6"/>', arrowRight: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>', arrowLeft: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  check: '<path d="M20 6 9 17l-5-5"/>', checkCircle: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  link: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  nav: '<polygon points="3 11 22 2 13 21 11 13 3 11"/>',
  printer: '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6"/><rect x="6" y="14" width="12" height="8" rx="1"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.83 3.98"/><path d="m15.41 6.51-6.82 3.98"/>',
  route: '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  compass: '<circle cx="12" cy="12" r="10"/><path d="m16.24 7.76-1.8 5.41a2 2 0 0 1-1.27 1.27L7.76 16.24l1.8-5.41a2 2 0 0 1 1.27-1.27z"/>',
  target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  ban: '<circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
  sparkles: '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0L14.06 8.5A2 2 0 0 0 15.5 9.94l6.14 1.58a.5.5 0 0 1 0 .96L15.5 14.06a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/>',
  database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
  book: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
  satellite: '<path d="M13 7 9 3 5 7l4 4"/><path d="m17 11 4 4-4 4-4-4"/><path d="m8 12 4 4 6-6-4-4Z"/><path d="m16 8 3-3"/><path d="M9 21a6 6 0 0 0-6-6"/>',
  hospital: '<path d="M12 6v4"/><path d="M14 14h-4"/><path d="M14 18h-4"/><path d="M14 8h-4"/><path d="M18 12h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h2"/><path d="M18 22V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v18"/>',
  school: '<path d="M14 22v-4a2 2 0 1 0-4 0v4"/><path d="m18 10 3.45 1.72a1 1 0 0 1 .55.9V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-7.38a1 1 0 0 1 .55-.9L6 10"/><path d="M18 5v17"/><path d="m4 6 7.1-3.55a2 2 0 0 1 1.8 0L20 6"/><path d="M6 5v17"/><circle cx="12" cy="9" r="2"/>',
  leaf: '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
  paw: '<circle cx="11" cy="4" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="20" cy="16" r="2"/><path d="M9 10a5 5 0 0 1 5 5v3.5a3.5 3.5 0 0 1-6.84 1.05Q6.52 17.48 4.46 16.84A3.5 3.5 0 0 1 5.5 10Z"/>',
  mountain: '<path d="m8 3 4 8 5-5 5 15H2L8 3z"/>',
  home: '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .71-1.53l7-6a2 2 0 0 1 2.58 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  building: '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
  walk: '<circle cx="13" cy="4" r="1.5"/><path d="m7 21 3-6.5 2.5 2V21"/><path d="m10 14.5 1-5L8 11v3"/><path d="m11 9.5 3 2.5 3 .5"/>',
  car: '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>',
  accessibility: '<circle cx="16" cy="4" r="1"/><path d="m18 19 1-7-6 1"/><path d="m5 8 3-3 5.5 3-2.36 3.5"/><path d="M4.24 14.5a5 5 0 0 0 6.88 6"/><path d="M13.76 17.5a5 5 0 0 0-6.88-6"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  bellOff: '<path d="M8.7 3A6 6 0 0 1 18 8a21.3 21.3 0 0 0 .6 5"/><path d="M17 17H3s3-2 3-9a4.67 4.67 0 0 1 .3-1.7"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/><path d="m2 2 20 20"/>',
  waves: '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>',
  activity: '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
  tornado: '<path d="M21 4H3"/><path d="M18 8H6"/><path d="M19 12H9"/><path d="M16 16h-6"/><path d="M11 20H9"/>',
  tsunami: '<path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M3 14c2-6 7-10 13-9-3 1.5-4 4-3.5 6.5"/><path d="M12.5 11.5c1.6-.9 3.5-.9 5 .5"/>',
  flame: '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
  thermo: '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
  cloud: '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
  bomb: '<circle cx="11" cy="13" r="9"/><path d="M14.35 4.65 16.3 2.7a2.41 2.41 0 0 1 3.4 0l1.6 1.6a2.4 2.4 0 0 1 0 3.4l-1.95 1.95"/><path d="m22 2-1.5 1.5"/>',
  siren: '<path d="M7 18v-6a5 5 0 1 1 10 0v6"/><path d="M5 21a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-1a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2z"/><path d="M21 12h1"/><path d="M18.5 4.5 18 5"/><path d="M2 12h1"/><path d="M12 2v1"/><path d="m4.93 4.93.7.7"/><path d="M12 12v6"/>',
  arrowUp: '<path d="M9 18v-6H5l7-7 7 7h-4v6H9z"/>', arrowDown: '<path d="M15 6v6h4l-7 7-7-7h4V6h6z"/>',
  moveAway: '<path d="m18 8 4 4-4 4"/><path d="M2 12h20"/><path d="m6 8-4 4 4 4"/>',
  wind: '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
  eye: '<path d="M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0"/><circle cx="12" cy="12" r="3"/>',
  octagon: '<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
  triangle: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
};
const svg = (n, cls = "") => `<svg class="ic ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ""}</svg>`;

/* ---------------------------------------------------------------- constants */
const HZ_ICON = { flood: "waves", earthquake: "activity", cyclone: "tornado", tsunami: "tsunami", wildfire: "flame", heat: "thermo", gas: "cloud", explosion: "bomb", air_raid: "siren" };
const HZ_SHORT = { flood: "Flood", earthquake: "Earthquake", cyclone: "Cyclone", tsunami: "Tsunami", wildfire: "Wildfire", heat: "Extreme heat", gas: "Gas leak", explosion: "Bomb / blast", air_raid: "Air raid" };
const GROUP_TITLE = { natural: "Natural hazards", industrial: "Industrial accidents", security: "Security threats" };
const HZ_NOTE = {
  flood: "Susceptibility from land height, surface water and 24-hour rain (IMD categories) — not a forecast. Streets you mark as flooded override the estimate.",
  earthquake: "Protective actions from Ready.gov. After shaking stops, SafeGround routes to the nearest mapped open area.",
  cyclone: "Low-lying blocks (possible surge or flooding) are separated from wind-only blocks. Strength uses the Saffir-Simpson scale.",
  tsunami: "Ready.gov: shelter 100 ft (30 m) or more above sea level. SafeGround routes to the nearest such ground.",
  wildfire: "Spread ≈ 10% of wind speed (Cruz & Alexander 2019). The zone turns with the wind.",
  heat: "Heat index from temperature and humidity, using the US National Weather Service equation and danger classes.",
  gas: "Distances from the Emergency Response Guidebook 2024 (Tables 1 and 3). The zone turns with the wind.",
  explosion: "Distances from the US DHS/FBI Bomb Threat Stand-Off Chart and ERG 2024.",
  air_raid: "Whole-area alert. SafeGround finds the nearest mapped underground shelter (metro, underground car park) and a walking route.",
};
const INCIDENT_LABEL = { gas: "Leak source", explosion: "Device", wildfire: "Fire" };
const TIER_NAMES = { gas: { red: "Isolate", orange: "Protect / shelter", yellow: "Wind uncertainty" }, explosion: { red: "Evacuate", orange: "Shelter inside" },
  flood: { red: "Flooded / very likely", orange: "Likely to flood", yellow: "Somewhat low" }, wildfire: { red: "Reached within ~1 h", orange: "Within ~3 h", yellow: "Wind uncertainty" },
  tsunami: { red: "Below 30 m above sea level" }, cyclone: { red: "Surge / flood exposed", orange: "Damaging winds", yellow: "Strong winds" } };
const TIER_RGB = { red: [240, 86, 91], orange: [240, 138, 62], yellow: [233, 181, 59], green: [63, 191, 127], unknown: [141, 154, 173] };
const LEVEL = { red: ["Immediate danger", "octagon"], orange: ["High risk", "triangle"], yellow: ["Caution", "alert"], green: ["Lower risk here", "checkCircle"], unknown: ["Not available in public data", "help"] };
const REL = { high: ["danger", "Frequent here"], medium: ["high", "Recorded or possible"], low: ["", "No record in loaded data"] };
const MOVE_ICON = { GO_UP: "arrowUp", GO_DOWN_INSIDE: "arrowDown", MOVE_AWAY: "moveAway", MOVE_CROSSWIND_UPWIND: "wind", STAY_IN_SEAL: "home",
  STAY_INSIDE_AWAY_FROM_WINDOWS: "building", STAY_ALERT: "eye", AVOID: "ban", DROP_COVER_HOLD: "shield", MOVE_TO_OPEN_AREA: "moveAway",
  GO_TO_HIGH_GROUND: "mountain", SHELTER_INTERIOR: "home", EVACUATE_AWAY_FROM_FIRE: "moveAway", STAY_COOL: "thermo" };
const PRESETS = [
  { id: "indoors", label: "Person indoors", icon: "home", sit: "home_ground", note: "At home or indoors, ground floor." },
  { id: "outdoors", label: "Person outdoors", icon: "walk", sit: "outdoors", note: "On foot, outside." },
  { id: "mobility", label: "Mobility limitation", icon: "accessibility", sit: "needs_assistance", note: "Routes use a slower walking speed (0.8 m/s) and advice for helping others." },
  { id: "school", label: "School group", icon: "school", sit: "institution", note: "In a school, hospital or other institution." },
  { id: "pets", label: "Pet owner", icon: "paw", sit: "home_ground", note: "At home; official advice about pets is included where the guidance has it." },
  { id: "upper", label: "Upper floor", icon: "building", sit: "home_upper", note: "At home or indoors, upper floor." },
  { id: "vehicle", label: "In a vehicle", icon: "car", sit: "vehicle", note: "Driving or in a parked vehicle." },
];
const DATA_LAYERS = [
  { id: "", name: "None", src: "Basemap only" },
  { id: "population", name: "Population", src: "WorldPop 2020", unit: "residents per block (~0.1 km²)", min: 0, max: 3000, fmt: (v) => Math.round(v).toLocaleString("en-US"),
    ramp: [[0, [219, 230, 255]], [0.35, [120, 156, 255]], [0.7, [52, 102, 240]], [1, [30, 32, 130]]], extrude: (v) => v * 0.12 },
  { id: "elevation", name: "Terrain: height above sea level", src: "Copernicus DEM GLO-30", unit: "m above sea level", min: 0, max: 60, fmt: (v) => `${Math.round(v)} m`,
    ramp: [[0, [24, 96, 196]], [0.5, [190, 222, 200]], [1, [150, 100, 40]]] },
  { id: "low_lying", name: "Low-lying land", src: "Copernicus DEM GLO-30", unit: "m below (blue) / above (brown) surroundings", min: -5, max: 5, fmt: (v) => `${v > 0 ? "+" : ""}${v.toFixed(1)} m`,
    ramp: [[0, [23, 103, 208]], [0.5, [236, 240, 245]], [1, [161, 98, 7]]] },
  { id: "building_height", name: "Building height", src: "Google Open Buildings", unit: "m, typical per block", min: 0, max: 30, fmt: (v) => `${v.toFixed(1)} m`,
    ramp: [[0, [209, 242, 236]], [0.4, [20, 170, 150]], [0.75, [52, 102, 240]], [1, [91, 60, 196]]], extrude: (v) => v * 9 },
  { id: "tree_change", name: "Tree cover change 2016→2025", src: "Google Dynamic World", unit: "percentage points per block", min: -50, max: 50, fmt: (v) => `${v > 0 ? "+" : ""}${Math.round(v)} pts`,
    ramp: [[0, [240, 86, 91]], [0.5, [236, 240, 245]], [1, [63, 191, 127]]] },
];
const POINT_LAYERS = [
  { id: "medical", name: "Hospitals and clinics", cats: ["hospital", "clinic"], rgb: [56, 189, 248], src: "OpenStreetMap" },
  { id: "care", name: "Schools and elderly homes", cats: ["school", "elderly_home"], rgb: [192, 132, 252], src: "OpenStreetMap" },
  { id: "refuge", name: "Underground shelters and open areas", cats: ["metro_underground", "parking_underground", "open_ground"], rgb: [45, 212, 191], src: "OpenStreetMap" },
];
const QUICK = [["Lahaina", "rp20887m156675_3000", "US"], ["Antakya", "rp36204p36164_3000", "TR"], ["Derna", "rp32759p22638_3000", "LY"], ["Shibuya", "rp35663p139696_3000", "JP"],
  ["Beirut", "rp33905p35505_3000", "LB"], ["Paiporta", "rp39428m0418_3000", "ES"], ["Kyiv", "rp50490p30429_3000", "UA"]];
const DELHI = { name: "New Delhi", label: "New Delhi, Delhi, India", lat: 28.6139, lon: 77.2090, admin: "Delhi", country: "India", country_code: "IN" };

/* ---------------------------------------------------------------- state & helpers */
const S = {
  page: "landing", view: "overview", rid: null, place: null, overview: null, ready: [], pick: null, meta: null, HZ: {},
  sim: { hazard: "flood", params: {}, preset: "indoors", incident: null, person: null, placing: "person", res: null, dirty: false, busy: false },
  zone: null, route: null, target: null, report: null, reportBusy: false, highlight: [], areaCells: [],
  dataLayer: null, points: { medical: true, care: true, refuge: false }, pointData: {}, is3d: true, layerOpen: false,
};
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmtN = (n) => (n === null || n === undefined || Number.isNaN(+n) ? "—" : Number(n).toLocaleString("en-US"));
const titleCase = (s) => String(s || "").replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
const COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
const compass = (d) => COMPASS[Math.round((((d % 360) + 360) % 360) / 22.5) % 16];
const rq = (pre = "?") => (S.rid ? `${pre}region=${encodeURIComponent(S.rid)}` : "");
const small = () => window.matchMedia("(max-width: 760px)").matches;
const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const regionId = (lat, lon) => { const f = (v) => (v >= 0 ? "p" : "m") + Math.abs(v).toFixed(3).replace(".", ""); return `r${f(lat)}${f(lon)}_3000`; };
const gmapsDir = (o, d, mode = "walking") => `https://www.google.com/maps/dir/?api=1&origin=${o.lat.toFixed(6)},${o.lon.toFixed(6)}&destination=${d.lat.toFixed(6)},${d.lon.toFixed(6)}${mode ? `&travelmode=${mode}` : ""}`;
const gmapsAt = (lat, lon) => `https://www.google.com/maps/search/?api=1&query=${lat.toFixed(6)},${lon.toFixed(6)}`;
const fmtDate = (iso) => { if (!iso) return "—"; const d = new Date(iso); return Number.isNaN(+d) ? String(iso).slice(0, 10) : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }); };
const dist = (la1, lo1, la2, lo2) => { const k = Math.PI / 180, x = (lo2 - lo1) * k * Math.cos(((la1 + la2) / 2) * k), y = (la2 - la1) * k; return 6371000 * Math.hypot(x, y); };
const parseCoords = (q) => { const m = String(q || "").trim().match(/^(-?\d{1,2}(?:\.\d+)?)\s*[, ]\s*(-?\d{1,3}(?:\.\d+)?)$/); if (!m) return null; const lat = +m[1], lon = +m[2]; return Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? { lat, lon } : null; };
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => { t.hidden = true; }, 3200); }
async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) { let m = r.statusText; try { const j = await r.json(); m = j.detail || JSON.stringify(j); } catch (e) { /* not json */ } throw new Error(String(m).slice(0, 300)); }
  return r.json();
}
const post = (path, body) => api(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
const checklist = (steps, k) => `<ul class="checklist">${steps.map((t, i) => `<li class="${i < k ? "done" : i === k ? "on" : ""}"><span class="st">${i < k ? svg("check") : ""}</span>${esc(t)}</li>`).join("")}</ul>`;

/* ---------------------------------------------------------------- theme (dark-first) */
const STYLES = { light: "https://tiles.openfreemap.org/styles/positron", dark: "https://tiles.openfreemap.org/styles/dark" };
const theme = () => (document.documentElement.dataset.theme === "light" ? "light" : "dark");
function paintChrome() {
  const t = theme();
  $("#themeBtn").innerHTML = svg(t === "dark" ? "sun" : "moon");
  $("#themeBtn").setAttribute("aria-label", t === "dark" ? "Switch to light theme" : "Switch to dark theme");
  $("#helpBtn").innerHTML = svg("help");
  $("#zoomIn").innerHTML = svg("plus"); $("#zoomOut").innerHTML = svg("minus"); $("#locateBtn").innerHTML = svg("locate");
  $$(".ws-tab").forEach((a) => { const ic = { overview: "dashboard", readiness: "clipboard", simulate: "crosshair" }[a.dataset.view]; if (!a.querySelector("svg")) a.insertAdjacentHTML("afterbegin", svg(ic)); });
}
$("#themeBtn").addEventListener("click", () => {
  const t = theme() === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem("sg-theme", t); } catch (e) { /* storage blocked */ }
  paintChrome(); if (map) map.setStyle(STYLES[t], { diff: false }); render();
});

/* ---------------------------------------------------------------- map */
let map = null, overlay = null;
const markers = {};
function ensureMap() {
  if (map) { setTimeout(() => map.resize(), 0); return; }
  map = new maplibregl.Map({ container: "map", style: STYLES[theme()], center: [DELHI.lon, DELHI.lat], zoom: small() ? 3.6 : 4.4, maxPitch: 70, attributionControl: { compact: true } });
  overlay = new deck.MapboxOverlay({ interleaved: false, layers: [], getTooltip: tooltip });
  map.addControl(overlay);
  map.on("style.load", styleLoaded);
  map.on("click", (e) => onMapClick(e.lngLat.lat, e.lngLat.lng));
  map.on("mousemove", () => { map.getCanvas().style.cursor = S.view === "simulate" && S.rid ? "crosshair" : ""; });
}
function styleLoaded() {
  const st = map.getStyle(); const src = Object.keys(st.sources).find((k) => st.sources[k].type === "vector");
  for (const l of st.layers) if (l.type === "symbol" && l.layout?.["text-field"]) map.setLayoutProperty(l.id, "text-field", ["coalesce", ["get", "name:en"], ["get", "name_en"], ["get", "name:latin"], ["get", "name"]]);
  if (!src || map.getLayer("sg-3d")) return;
  const before = st.layers.find((l) => l.type === "symbol")?.id, dark = theme() === "dark";
  map.addLayer({ id: "sg-3d", type: "fill-extrusion", source: src, "source-layer": "building", minzoom: 13.5, layout: { visibility: S.is3d ? "visible" : "none" },
    paint: { "fill-extrusion-color": dark ? "#263243" : "#DDDAD2", "fill-extrusion-opacity": 0.8,
      "fill-extrusion-height": ["coalesce", ["get", "render_height"], 5], "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0] } }, before);
}
function flyTo(lat, lon, zoom = 14, dur = 1300) { if (!map) return; map.flyTo({ center: [lon, lat], zoom, pitch: S.is3d ? 50 : 0, bearing: S.is3d ? -12 : 0, duration: reduced() ? 0 : dur, essential: true }); }
function fitPts(pts) {
  if (!map || pts.length < 2) return;
  const b = pts.reduce((a, [x, y]) => [Math.min(a[0], x), Math.min(a[1], y), Math.max(a[2], x), Math.max(a[3], y)], [180, 90, -180, -90]);
  map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: small() ? 50 : { top: 90, bottom: 90, left: 80, right: 80 }, maxZoom: 16.2, pitch: S.is3d ? 48 : 0, bearing: S.is3d ? -12 : 0, duration: reduced() ? 0 : 900 });
}
function rampColor(ramp, t) {
  t = Math.max(0, Math.min(1, t));
  for (let i = 1; i < ramp.length; i++) { const [t1, c1] = ramp[i], [t0, c0] = ramp[i - 1]; if (t <= t1) { const k = (t - t0) / (t1 - t0 || 1); return c0.map((c, j) => Math.round(c + (c1[j] - c) * k)); } }
  return ramp[ramp.length - 1][1];
}
const rampCss = (ramp) => `linear-gradient(90deg, ${ramp.map(([t, c]) => `rgb(${c.join(",")}) ${t * 100}%`).join(", ")})`;
const HEXB = new Map();
const hexB = (h) => { if (!HEXB.has(h)) HEXB.set(h, h3.cellToBoundary(h, true)); return HEXB.get(h); };
const hexLayer = ({ getHexagon, ...p }) => new deck.PolygonLayer({ ...p, getPolygon: (d) => hexB(getHexagon(d)) });
const accentRgb = () => (theme() === "dark" ? [147, 176, 255] : [36, 80, 216]);

function render() {
  if (!overlay) return;
  const L = [], A = accentRgb(), sim = S.view === "simulate";
  if (S.place) L.push(new deck.ScatterplotLayer({ id: "region", data: [S.place], getPosition: (d) => [d.lon, d.lat], getRadius: (d) => d.radius_m, radiusUnits: "meters",
    filled: true, getFillColor: [...A, 10], stroked: true, getLineColor: [...A, 190], lineWidthMinPixels: 1.5 }));
  if (S.dataLayer && S.rid) {
    const D = DATA_LAYERS.find((l) => l.id === S.dataLayer.layer), ext = S.is3d && !!D.extrude;
    L.push(hexLayer({ id: "data", data: S.dataLayer.cells, getHexagon: (d) => d.h, pickable: true, stroked: false, extruded: ext, getElevation: (d) => (ext ? D.extrude(d.v) : 0),
      getFillColor: (d) => { const neutral = (D.id === "low_lying" || D.id === "tree_change") && Math.abs(d.v) < (D.id === "low_lying" ? 0.5 : 2);
        return [...rampColor(D.ramp, (d.v - D.min) / (D.max - D.min)), neutral ? 0 : D.id === "population" && d.v < 50 ? 50 : ext ? 230 : 165]; },
      updateTriggers: { getFillColor: D.id, getElevation: [D.id, ext] } }));
  }
  if (S.areaCells.length && S.view === "readiness") L.push(hexLayer({ id: "area", data: S.areaCells, getHexagon: (d) => d, getFillColor: [...A, 18], stroked: true, getLineColor: [...A, 110], lineWidthMinPixels: 1 }));
  if (S.highlight.length && S.view === "readiness") L.push(hexLayer({ id: "hl", data: S.highlight, getHexagon: (d) => d, getFillColor: [240, 138, 62, 200], stroked: true, getLineColor: [255, 255, 255], lineWidthMinPixels: 1.5 }));
  if (sim && S.zone?.type === "polygons") L.push(new deck.GeoJsonLayer({ id: "zone", data: S.zone.geojson, filled: true, stroked: true,
    getFillColor: (f) => [...TIER_RGB[f.properties.tier], f.properties.tier === "red" ? 115 : f.properties.tier === "orange" ? 80 : 55], getLineColor: (f) => [...TIER_RGB[f.properties.tier], 235], lineWidthMinPixels: 1.5 }));
  if (sim && S.zone?.type === "hex") L.push(hexLayer({ id: "zonehex", data: S.zone.cells, getHexagon: (d) => d.h, stroked: false, getFillColor: (d) => [...TIER_RGB[d.t], d.t === "red" ? 140 : S.sim.hazard === "cyclone" ? 40 : 95] }));
  if (S.rid) for (const P of POINT_LAYERS) if (S.points[P.id] && S.pointData[P.id]) L.push(new deck.ScatterplotLayer({ id: `pt-${P.id}`, data: S.pointData[P.id], getPosition: (d) => [d.lon, d.lat],
    getFillColor: P.rgb, getRadius: 5, radiusUnits: "pixels", stroked: true, getLineColor: [255, 255, 255], lineWidthMinPixels: 1.5, pickable: true }));
  if (sim && S.route) {
    const path = [{ p: S.route.map(([la, lo]) => [lo, la]) }];
    L.push(new deck.PathLayer({ id: "route-case", data: path, getPath: (d) => d.p, getColor: theme() === "dark" ? [11, 16, 24] : [255, 255, 255], widthMinPixels: 9, capRounded: true, jointRounded: true }));
    L.push(new deck.PathLayer({ id: "route", data: path, getPath: (d) => d.p, getColor: A, widthMinPixels: 5, capRounded: true, jointRounded: true }));
  }
  overlay.setProps({ layers: L });
  syncMarkers(); renderLegend(); renderCoach();
}
function tooltip({ object, layer }) {
  if (!object) return null;
  if (layer?.id === "data") { const D = DATA_LAYERS.find((l) => l.id === S.dataLayer.layer); return { text: `${D.name}: ${D.fmt(object.v)}\nSource: ${D.src}`, className: "deck-tooltip" }; }
  if (layer?.id?.startsWith("pt-")) { const P = POINT_LAYERS.find((p) => `pt-${p.id}` === layer.id); return { text: `${object.name || "Unnamed"}\n${titleCase(object.cat)} · ${P.src}`, className: "deck-tooltip" }; }
  return null;
}
const PIN_SVG = '<svg viewBox="0 0 34 42"><path d="M17 41c-1.2-1.4-14-13.6-14-24.5a14 14 0 0 1 28 0C31 27.4 18.2 39.6 17 41z" fill="var(--accent)" stroke="#fff" stroke-width="2"/><circle cx="17" cy="16.5" r="5.2" fill="#fff"/></svg>';
function marker(key, ll, html) {
  if (!map) return;
  if (!ll) { if (markers[key]) { markers[key].remove(); delete markers[key]; } return; }
  if (!markers[key]) { const el = document.createElement("div"); el.setAttribute("aria-hidden", "true"); markers[key] = new maplibregl.Marker({ element: el, anchor: "bottom" }).setLngLat([ll.lon, ll.lat]).addTo(map); }
  markers[key].setLngLat([ll.lon, ll.lat]); const el = markers[key].getElement(); if (el.dataset.h !== html) { el.innerHTML = html; el.dataset.h = html; }
}
const dotMk = (label, color) => `<div class="mk">${label ? `<div class="lbl">${esc(label)}</div>` : ""}<div class="dotm" style="background:${color}"></div></div>`;
function syncMarkers() {
  const sim = S.view === "simulate" && S.page === "ws" && S.rid;
  marker("pick", S.page === "ws" && !S.rid && S.pick ? S.pick : null, `<div class="mk mk-pin">${PIN_SVG}</div>`);
  marker("incident", sim ? S.sim.incident : null, dotMk(INCIDENT_LABEL[S.sim.hazard] || "Incident", "rgb(240,86,91)"));
  marker("person", sim ? S.sim.person : null, dotMk("Person", theme() === "dark" ? "#E8EDF4" : "#121821"));
  marker("target", sim ? S.target : null, dotMk(S.target?.short || "Safe destination", "rgb(63,191,127)"));
  const pts = sim ? (S.sim.params.reported_points || []) : [];
  Object.keys(markers).filter((k) => k.startsWith("rp") && +k.slice(2) >= pts.length).forEach((k) => marker(k, null));
  pts.forEach((p, i) => marker(`rp${i}`, { lat: p[0], lon: p[1] }, dotMk(i === 0 ? "Reported flooding" : "", "rgb(52,102,240)")));
}

/* legend + layer control */
function renderLegend() {
  const el = $("#legend"); if (!el) return;
  const rows = [];
  if (S.place && S.rid) rows.push(`<div class="li"><span class="sw" style="border:2px solid rgb(${accentRgb()});background:transparent"></span>Analysis area (3 km radius)</div>`);
  if (S.view === "simulate" && S.zone && S.zone.type !== "citywide" && TIER_NAMES[S.sim.hazard]) {
    rows.push(`<div class="gap"></div><h2>${esc(HZ_SHORT[S.sim.hazard])} danger zone</h2>`);
    for (const [t, n] of Object.entries(TIER_NAMES[S.sim.hazard])) rows.push(`<div class="li"><span class="sw" style="background:rgb(${TIER_RGB[t]})"></span>${esc(LEVEL[t][0])} · ${esc(n)}</div>`);
  }
  if (S.view === "simulate" && (S.sim.person || S.sim.incident)) {
    rows.push(`<div class="gap"></div>`);
    if (S.sim.incident) rows.push(`<div class="li"><span class="pt" style="background:rgb(240,86,91)"></span>${esc(INCIDENT_LABEL[S.sim.hazard] || "Incident")}</div>`);
    if (S.sim.person) rows.push(`<div class="li"><span class="pt" style="background:${theme() === "dark" ? "#E8EDF4" : "#121821"}"></span>Person</div>`);
    if (S.target) rows.push(`<div class="li"><span class="pt" style="background:rgb(63,191,127)"></span>Safe destination</div>`);
    if (S.route) rows.push(`<div class="li"><span class="ln" style="background:rgb(${accentRgb()})"></span>Walking route</div>`);
  }
  if (S.view === "readiness" && S.highlight.length) rows.push(`<div class="li"><span class="sw" style="background:rgb(240,138,62)"></span>Blocks for the selected action</div>`);
  if (S.rid) for (const P of POINT_LAYERS) if (S.points[P.id]) rows.push(`<div class="li"><span class="pt" style="background:rgb(${P.rgb})"></span>${esc(P.name)}</div>`);
  const D = S.dataLayer && DATA_LAYERS.find((l) => l.id === S.dataLayer.layer);
  if (D) rows.push(`<div class="gap"></div><h2>${esc(D.name)}</h2><div class="ramp" style="background:${rampCss(D.ramp)}"></div><div class="rl"><span>${D.fmt(D.min)}</span><span>${D.fmt(D.max)}+</span></div><div class="note">${esc(D.unit)} · ${esc(D.src)}</div>`);
  el.innerHTML = rows.length ? `<h2>Legend</h2>${rows.join("")}` : "";
  el.hidden = !rows.length || S.page !== "ws";
}
function renderLayerCtl() {
  const el = $("#layerCtl");
  const cur = S.dataLayer?.layer || "";
  el.innerHTML = `<button class="tool-btn" id="layersBtn" type="button" aria-expanded="${S.layerOpen}" aria-controls="layerPop">${svg("layers")}Layers</button>
    <div class="layer-pop" id="layerPop" ${S.layerOpen ? "" : "hidden"}>
      ${S.rid ? `<fieldset><legend>Satellite data (per ~0.1 km² block)</legend>${DATA_LAYERS.map((L) => `<label class="lyr"><input type="radio" name="dl" value="${L.id}" ${cur === L.id ? "checked" : ""}>
        <span class="sw" style="background:${L.ramp ? rampCss(L.ramp) : "var(--surface-3)"}"></span><span>${esc(L.name)}<span class="ls">${esc(L.src)}</span></span></label>`).join("")}</fieldset>
      <fieldset><legend>Facilities (mapped only)</legend>${POINT_LAYERS.map((P) => `<label class="lyr"><input type="checkbox" value="${P.id}" ${S.points[P.id] ? "checked" : ""}>
        <span class="sw" style="background:rgb(${P.rgb});border-radius:50%;width:12px;height:12px"></span><span>${esc(P.name)}<span class="ls">${esc(P.src)}</span></span></label>`).join("")}</fieldset>
      <p class="note">Flood history, rainfall extremes, earthquakes and alerts are place-level records, listed in the Overview timeline.</p>`
      : `<p class="note">Load a place to see its satellite data and facilities.</p>`}
    </div>`;
  $("#layersBtn").addEventListener("click", () => { S.layerOpen = !S.layerOpen; renderLayerCtl(); });
  $$("input[name=dl]", el).forEach((r) => r.addEventListener("change", () => setDataLayer(r.value)));
  $$("input[type=checkbox]", el).forEach((c) => c.addEventListener("change", () => { S.points[c.value] = c.checked; loadPoints().then(render); }));
}
async function setDataLayer(name) {
  if (!name) { S.dataLayer = null; return render(); }
  try { S.dataLayer = await api(`/api/layers/${name}${rq()}`); } catch (e) { toast(`Layer not available: ${e.message}`); S.dataLayer = null; }
  render();
}
async function loadPoints() {
  if (!S.rid) return;
  const rid = S.rid;
  await Promise.all(POINT_LAYERS.filter((P) => S.points[P.id] && !S.pointData[P.id]).map(async (P) => {
    const lists = await Promise.all(P.cats.map((c) => api(`/api/features/${c}?region=${encodeURIComponent(rid)}`).then((r) => r.items.map((x) => ({ ...x, cat: c }))).catch(() => [])));
    if (S.rid === rid) S.pointData[P.id] = lists.flat();
  }));
}
function renderCoach() {
  let t = S.coachMsg || "";
  if (!t && S.page === "ws") {
    if (!S.rid) t = `${small() ? "Tap" : "Click"} the map to move the pin, or search a place`;
    else if (S.view === "overview") t = `${small() ? "Tap" : "Click"} a block inside the circle for its data`;
    else if (S.view === "readiness") t = S.report ? "Select “Show blocks on map” on an action to see where it applies" : "Generate the readiness assessment to see actions on the map";
    else if (S.sim.placing === "flood_report") t = "Click a street that is already flooded";
    else if (S.sim.placing === "incident") t = `Click where the ${(INCIDENT_LABEL[S.sim.hazard] || "incident").toLowerCase()} is`;
    else if (!S.sim.person) t = "Click where the person is";
    else t = "Click to move the person, then generate the plan again";
  }
  $("#coachText").textContent = t; $("#coach").hidden = !t || S.page !== "ws";
}
function flashCoach(msg) { S.coachMsg = msg; renderCoach(); clearTimeout(S.coachT); S.coachT = setTimeout(() => { S.coachMsg = null; renderCoach(); }, 4500); }
$("#zoomIn").addEventListener("click", () => map?.zoomIn());
$("#zoomOut").addEventListener("click", () => map?.zoomOut());
$("#toggle3d").addEventListener("click", () => {
  S.is3d = !S.is3d; $("#toggle3d").classList.toggle("on", S.is3d); $("#toggle3d").setAttribute("aria-pressed", String(S.is3d));
  if (map?.getLayer("sg-3d")) map.setLayoutProperty("sg-3d", "visibility", S.is3d ? "visible" : "none");
  map?.easeTo({ pitch: S.is3d ? 50 : 0, bearing: S.is3d ? -12 : 0, duration: reduced() ? 0 : 600 }); render();
});
$("#locateBtn").addEventListener("click", () => useMyLocation());
function useMyLocation() {
  if (!navigator.geolocation) return toast("Location is not available in this browser");
  navigator.geolocation.getCurrentPosition((p) => goPick(p.coords.latitude, p.coords.longitude), () => toast("Location permission was not given"), { timeout: 10000 });
}

/* ---------------------------------------------------------------- search (header + landing) */
function bindSearch(input, list) {
  let timer = null, results = [], kb = -1;
  const close = () => { list.hidden = true; input.setAttribute("aria-expanded", "false"); };
  const draw = (items, q) => {
    results = items; kb = -1;
    const ready = new Set(S.ready.map((x) => x.id));
    list.innerHTML = items.length ? items.map((p, i) => `<button class="sr" type="button" role="option" id="${list.id}-${i}" data-i="${i}" aria-selected="false">${svg(p.coord ? "crosshair" : "pin")}<span><b>${esc(p.name)}</b><span class="sub">${esc(p.label)}</span></span>${ready.has(p.region_id) ? '<span class="chip safe tag">Ready</span>' : ""}</button>`).join("")
      : `<div class="sr-empty">No places found for “${esc(q)}”. Try a city, address, landmark or “lat, lon”.</div>`;
    list.hidden = false; input.setAttribute("aria-expanded", "true");
  };
  const choose = (i) => { const p = results[i]; if (!p) return; close(); input.value = p.label || p.name; input.blur(); choosePlace(p); };
  input.addEventListener("input", () => {
    clearTimeout(timer); const q = input.value.trim();
    if (q.length < 2) return close();
    const c = parseCoords(q);
    if (c) return draw([{ name: `${c.lat.toFixed(4)}, ${c.lon.toFixed(4)}`, label: "Coordinates · assess the area around this point", lat: c.lat, lon: c.lon, coord: true, region_id: regionId(c.lat, c.lon) }], q);
    timer = setTimeout(async () => {
      try { const r = await api(`/api/geocode?q=${encodeURIComponent(q)}`); draw(r.results, q); } catch (e) { list.innerHTML = `<div class="sr-empty">Place search unavailable: ${esc(e.message)}</div>`; list.hidden = false; }
    }, 260);
  });
  input.addEventListener("keydown", (e) => {
    const items = $$(".sr", list);
    if (e.key === "Escape") return close();
    if (!items.length || list.hidden) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); kb = (kb + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      items.forEach((x, i) => x.setAttribute("aria-selected", String(i === kb))); input.setAttribute("aria-activedescendant", items[kb].id);
    }
    if (e.key === "Enter") { e.preventDefault(); choose(Math.max(0, kb)); }
  });
  list.addEventListener("click", (e) => { const b = e.target.closest(".sr"); if (b) choose(+b.dataset.i); });
  document.addEventListener("click", (e) => { if (!list.contains(e.target) && e.target !== input) close(); });
}
function choosePlace(p) {
  const rid = p.region_id || regionId(p.lat, p.lon);
  if (S.ready.some((r) => r.id === rid)) location.hash = `#/place/${rid}/overview`;
  else goPick(p.lat, p.lon, p.coord ? null : p);
}
function goPick(lat, lon, named = null) {
  S.pick = named ? { ...named, region_id: named.region_id || regionId(lat, lon) } : { name: "Selected point", label: "", lat, lon, region_id: regionId(lat, lon) };
  if (location.hash.startsWith("#/pick")) route(); else location.hash = "#/pick";
  if (!named) reverseName(lat, lon);
}
async function reverseName(lat, lon) {
  try { const r = await api(`/api/reverse?lat=${lat}&lon=${lon}`); if (r.place && S.pick && S.pick.lat === lat) { S.pick = { ...r.place, lat, lon }; if (!S.rid) renderPickPanel(); else renderPop(); } }
  catch (e) { /* keep the coordinates */ }
}

/* ---------------------------------------------------------------- router */
window.addEventListener("hashchange", route);
async function route() {
  const h = location.hash || "#/";
  const [path, qs] = h.slice(1).split("?");
  const parts = path.split("/").filter(Boolean), q = new URLSearchParams(qs || "");
  $("#mapPop").hidden = true;
  document.title = "SafeGround · Hazard readiness and response planning for any place on Earth";
  if (!parts.length) return showPage("landing");
  if (["methodology", "sources", "limitations", "accessibility"].includes(parts[0])) return showPage("doc", parts[0]);
  if (parts[0] === "pick") { S.rid = null; S.place = null; S.view = "overview"; showPage("ws"); return renderPick(); }
  if (parts[0] === "place" && parts[1]) {
    const rid = parts[1], view = ["overview", "readiness", "simulate"].includes(parts[2]) ? parts[2] : "overview";
    showPage("ws");
    if (S.rid !== rid) { const ok = await loadRegion(rid); if (!ok) return; }
    setView(view, q);
    return;
  }
  location.hash = "#/";
}
function showPage(page, doc) {
  S.page = page;
  $("#landing").hidden = page !== "landing"; $("#workspace").hidden = page !== "ws"; $("#docPage").hidden = page !== "doc";
  $("#wsTabs").hidden = page !== "ws"; $("#topSearch").hidden = page !== "ws"; $("#topLinks").hidden = page === "ws";
  $$("#topLinks a").forEach((a) => (a.getAttribute("href") === `#/${doc}` ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
  if (page === "landing") renderLanding();
  if (page === "doc") renderDoc(doc);
  if (page === "ws") { ensureMap(); renderLayerCtl(); }
  $("#main").scrollTop = 0;
  syncMarkers(); renderLegend(); renderCoach();
}
function updateTabs() {
  $$(".ws-tab").forEach((a) => {
    const v = a.dataset.view; a.href = S.rid ? `#/place/${S.rid}/${v}` : "#/pick";
    if (S.rid && v === S.view) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    a.setAttribute("aria-disabled", String(!S.rid));
  });
  $("#wsTitle").textContent = S.rid ? `${S.place?.name || "Place"} — ${titleCase(S.view)}` : "Choose a place";
}

/* ---------------------------------------------------------------- landing page */
function renderLanding() {
  const el = $("#landing");
  if (el.dataset.done) { $("#heroSearch").value = ""; return; }
  el.dataset.done = "1";
  el.innerHTML = `
    <div class="hero">
      <div>
        <div class="brand" style="gap:12px"><span class="brand-mark" style="width:44px;height:44px;border-radius:11px" aria-hidden="true"><svg viewBox="0 0 24 24" style="width:28px;height:28px"><path d="M12 18.5s-5.5-4.6-5.5-9.2a5.5 5.5 0 0 1 11 0c0 4.6-5.5 9.2-5.5 9.2z"/><path d="m9.7 9.4 1.6 1.6 3-3.1"/><path d="M5 21.5h14"/></svg></span><span class="brand-name" style="font-size:22px">SafeGround</span></div>
        <h1 id="landingTitle" style="margin-top:22px">Hazard readiness and response planning for any place on Earth.</h1>
        <p class="lead">See what hits a place, how ready it is, and what people should do if it happens there — with official guidance, a route to safety and every claim traced to its source.</p>
        <div class="hero-search" role="search">
          <div class="search">${svg("search")}<label class="sr-only" for="heroSearch">Search a city, address, landmark or coordinates</label>
            <input id="heroSearch" type="search" placeholder="City, address, landmark or “lat, lon”" autocomplete="off" aria-controls="heroResults" aria-autocomplete="list" aria-expanded="false">
            <div class="results" id="heroResults" role="listbox" aria-label="Places" hidden></div></div>
          <div class="hero-alt"><a class="link-btn" href="#/pick">${svg("pin", "sm")}Drop a pin on the map</a><button class="link-btn" type="button" id="heroLocate">${svg("locate", "sm")}Use my location</button></div>
        </div>
        <div class="quick"><div class="eyebrow" id="qsH">Quick start · opens instantly</div><div class="quick-row" role="group" aria-labelledby="qsH">${QUICK.map(([n, rid, cc]) => `<button type="button" data-rid="${rid}"><span class="cc">${cc}</span>${n}</button>`).join("")}</div></div>
      </div>
      <div class="hero-art" aria-hidden="true">
        <div class="eyebrow" style="margin-bottom:8px">Example · Shibuya, Tokyo · one street corner</div>
        ${[["activity", "Earthquake", "Drop, cover, hold — then open area 185 m away", "high"], ["siren", "Air-raid alert", "Go down — underground car park 120 m away", "medium"],
           ["cloud", "Chlorine leak", "Stay in and seal; exits crosswind, never downwind", "medium"], ["tsunami", "Tsunami warning", "Stay put — this spot is above 30 m", ""]]
          .map(([ic, t, d, c]) => `<div class="row"><span class="hz-ic ${c}">${svg(ic)}</span><div><b style="font-size:14.5px">${t}</b><div class="note">${d}</div></div></div>`).join("")}
        <p class="note" style="margin-top:8px">Computed by the SafeGround engine from official guidance and map data.</p>
      </div>
    </div>
    <div class="caps">
      <article class="cap"><span class="k">${svg("dashboard", "sm")}Overview</span><h2>What hits this place?</h2><p>A hazard profile from the place’s own records — floods, rain extremes, earthquakes, cyclones, fires, checked news — and who is exposed.</p></article>
      <article class="cap"><span class="k">${svg("clipboard", "sm")}Readiness</span><h2>How ready is this place?</h2><p>Before, during and after each recorded disaster, for people, animals and nature — with ranked fixes and the evidence behind each one.</p></article>
      <article class="cap"><span class="k">${svg("crosshair", "sm")}Simulate</span><h2>What should people do if it happens here?</h2><p>Nine hazards. A danger zone from official guidance, the protective move, the nearest safe place and a walking route, in plain language.</p></article>
    </div>
    <div class="trust" role="list" aria-label="How SafeGround keeps your trust">
      <div role="listitem">${svg("database")}<div><b>Public datasets</b><span>Google Earth Engine, OpenStreetMap, USGS, GDACS — each metric cites its source.</span></div></div>
      <div role="listitem">${svg("shield")}<div><b>Validated AI output</b><span>Code checks every number and instruction before it is shown.</span></div></div>
      <div role="listitem">${svg("bellOff")}<div><b>No alerts</b><span>A planning and training tool; it never sends warnings.</span></div></div>
      <div role="listitem">${svg("lock")}<div><b>No personal data</b><span>No accounts, no tracking of people or locations.</span></div></div>
    </div>
    <section class="how" aria-labelledby="howTitle"><h2 id="howTitle">How SafeGround works</h2>
      <ol class="how-steps"><li><b>Choose a place</b><span>Search, drop a pin or pick a quick start. A 3 km area is built in 1–2 minutes the first time.</span></li>
        <li><b>Build its hazard profile</b><span>Satellite data, map data and disaster records describe what hits it and who is exposed.</span></li>
        <li><b>Assess readiness</b><span>An AI investigator runs measured checks and ranks what to fix first.</span></li>
        <li><b>Simulate a response</b><span>Pick a hazard, a spot and a person; get a checked safety plan with a route.</span></li></ol></section>
    <nav class="land-links" aria-label="More about SafeGround"><a href="#/methodology">Methodology</a><a href="#/sources">Data &amp; Sources</a><a href="#/limitations">Limitations</a><a href="#/accessibility">Accessibility</a></nav>`;
  bindSearch($("#heroSearch"), $("#heroResults"));
  $$(".quick-row [data-rid]", el).forEach((b) => b.addEventListener("click", () => { location.hash = `#/place/${b.dataset.rid}/overview`; }));
  $("#heroLocate").addEventListener("click", useMyLocation);
}

/* ---------------------------------------------------------------- workspace: pick a place */
function renderPick() {
  if (!S.pick) S.pick = { ...DELHI, region_id: regionId(DELHI.lat, DELHI.lon) };
  S.dataLayer = null; S.zone = null; S.route = null; S.target = null; S.report = null; S.highlight = []; S.areaCells = [];
  updateTabs(); renderLayerCtl(); renderPickPanel(); $("#placeSearch").value = "";
  $("#workspace").classList.add("drawer-closed"); $("#drawer").innerHTML = "";
  flyTo(S.pick.lat, S.pick.lon, S.pick.name === DELHI.name && S.pick.lat === DELHI.lat ? (small() ? 3.6 : 4.4) : 11.5);
  render();
}
function renderPickPanel() {
  const p = S.pick, isReady = S.ready.some((r) => r.id === p.region_id);
  $("#leftPanel").innerHTML = `
    <div class="eyebrow">Choose a place</div>
    <h2 style="font-size:20px;margin:6px 0 4px">Assess any place on Earth</h2>
    <p class="note">Search above, ${small() ? "tap" : "click"} the map to move the pin, or use your location.</p>
    <div class="card flat sec" id="pickCard">
      <div class="place"><span class="place-ic">${svg("pin")}</span><div><div class="eyebrow">Selected location</div><h3 style="font-size:16px;margin-top:2px">${esc(p.name || "Selected point")}</h3>
        <div class="sub">${esc(p.label && p.label !== p.name ? p.label : [p.admin, p.country].filter(Boolean).join(", "))}${p.label || p.country ? " · " : ""}<span class="num">${p.lat.toFixed(4)}, ${p.lon.toFixed(4)}</span></div></div></div>
      <button class="btn primary block" type="button" id="assessBtn" style="margin-top:14px">${isReady ? `Open ${esc(p.name)}` : "Assess this area"}${svg("arrowRight")}</button>
      <p class="note" style="margin-top:8px">${isReady ? "Already built — opens instantly." : "Covers 3 km around the pin. The first time takes 1–2 minutes: map data, satellite data and disaster history are fetched, then kept."}</p>
    </div>
    <div class="sec"><div class="sec-h"><h3>Quick start</h3><span class="src">opens instantly</span></div>
      <div class="stack">${S.ready.map((r) => `<button class="btn block" type="button" data-rid="${esc(r.id)}" style="justify-content:flex-start"><span class="chip">${esc(r.country_code || "—")}</span>${esc(r.name)}<span class="muted" style="margin-left:auto;font-weight:500">${esc(r.country || "")}</span></button>`).join("")}</div></div>`;
  $("#assessBtn").addEventListener("click", () => (isReady ? (location.hash = `#/place/${p.region_id}/overview`) : buildRegion(p)));
  $$("[data-rid]", $("#leftPanel")).forEach((b) => b.addEventListener("click", () => { location.hash = `#/place/${b.dataset.rid}/overview`; }));
  syncMarkers();
}
const BUILD_STEPS = ["Fetching roads and facilities from OpenStreetMap", "Measuring population, buildings, land and water with Google Earth Engine", "Collecting past disasters (Earth Engine, USGS, GDACS)", "Saving the place"];
async function buildRegion(p) {
  const box = $("#pickCard");
  flyTo(p.lat, p.lon, 12.5);
  const draw = (k) => { box.innerHTML = `<div style="font-weight:700">Building ${esc(p.name)}${p.country ? `, ${esc(p.country)}` : ""}</div>
    ${checklist(BUILD_STEPS, k)}<p class="note" style="margin-top:12px">This takes 1–2 minutes the first time. Keep this tab open; the place is kept afterwards.</p>`; };
  draw(0);
  const poll = setInterval(async () => { try { const s = await api(`/api/region/${encodeURIComponent(p.region_id)}`); if (s.step) draw(Math.max(0, BUILD_STEPS.indexOf(s.step))); } catch (e) { /* keep polling */ } }, 1500);
  try {
    const st = await post("/api/region", { lat: p.lat, lon: p.lon, name: p.name || "Selected point", country: p.country, country_code: p.country_code, admin: p.admin });
    clearInterval(poll); draw(4); await loadReady(); location.hash = `#/place/${st.id}/overview`;
  } catch (e) {
    clearInterval(poll);
    box.innerHTML = `<div class="callout error">${svg("alert")}<div><b>Could not build ${esc(p.name)}.</b> ${esc(e.message)}<br>Public map services are sometimes busy; trying again usually works.</div></div><button class="btn block" type="button" id="retryBtn" style="margin-top:10px">Try again</button>`;
    $("#retryBtn").addEventListener("click", () => buildRegion(p));
  }
}
async function loadReady() { try { S.ready = (await api("/api/regions")).regions; } catch (e) { S.ready = []; } }

/* ---------------------------------------------------------------- workspace: a loaded place */
async function loadRegion(rid) {
  $("#workspace").classList.remove("drawer-closed");
  $("#leftPanel").innerHTML = `<div class="card"><div style="display:flex;gap:10px;align-items:center;font-weight:600"><span class="spinner"></span>Opening the place…</div><div class="skel"></div><div class="skel" style="width:70%"></div></div>`;
  $("#drawer").innerHTML = "";
  try {
    const m = await api(`/api/region/${encodeURIComponent(rid)}`);
    if (m.state !== "ready") throw new Error("This place has not been built yet. Choose it on the map and select “Assess this area”.");
    S.rid = rid; S.place = m; S.pick = null; S.overview = null; S.report = null; S.highlight = []; S.areaCells = []; S.dataLayer = null; S.pointData = {};
    S.sim = { ...S.sim, params: {}, incident: null, person: null, res: null, dirty: false, placing: S.HZ[S.sim.hazard]?.needs_incident ? "incident" : "person" }; S.zone = null; S.route = null; S.target = null;
    $("#placeSearch").value = [m.name, m.country].filter(Boolean).join(", ");
    flyTo(m.lat, m.lon, 13.3);
    loadPoints().then(render);
    api(`/api/region/${encodeURIComponent(rid)}/overview`).then((o) => { S.overview = o; if (S.view === "overview") renderOverview(); if (S.view === "simulate") renderSimulate(); }).catch(() => { S.overview = { error: true }; if (S.view === "overview") renderOverview(); });
    return true;
  } catch (e) {
    $("#leftPanel").innerHTML = `<div class="callout error">${svg("alert")}<div><b>Could not open this place.</b> ${esc(e.message)}</div></div><a class="btn block" href="#/pick" style="margin-top:10px">Choose another place</a>`;
    return false;
  }
}
function setView(view, q) {
  S.view = view; updateTabs();
  $("#workspace").classList.remove("drawer-closed");
  if (view === "overview") renderOverview();
  if (view === "readiness") renderReadiness();
  if (view === "simulate") { if (q && q.get("hz")) restoreShare(q); renderSimulate(); refreshZone(); }
  $("#leftPanel").scrollTop = 0; $("#drawer").scrollTop = 0;
  render();
}
function placeHeader(extra = "") {
  const m = S.place, o = S.overview?.region || {};
  const osm = o.osm_timestamp || m.osm_timestamp;
  return `<div class="place"><span class="place-ic">${svg("pin")}</span><div><h2>${esc(m.name)}</h2><div class="sub">${esc([m.admin, m.country].filter(Boolean).join(", "))}</div></div>
      <a class="btn sm" href="#/pick" aria-label="Change place">Change</a></div>
    <div class="facts-row"><span class="chip">${svg("target")}3 km radius</span><span class="chip num">${m.lat.toFixed(4)}, ${m.lon.toFixed(4)}</span>
      <span class="chip" title="When this place's data was built">${svg("clock")}Built ${esc(fmtDate(m.built_at))}</span>${osm ? `<span class="chip" title="OpenStreetMap snapshot">${svg("pin")}Map data ${esc(fmtDate(osm))}</span>` : ""}</div>${extra}`;
}

/* overview */
function renderOverview() {
  const o = S.overview;
  if (!o) {
    $("#leftPanel").innerHTML = placeHeader(`<div class="sec"><div class="skel"></div><div class="skel"></div><div class="skel" style="width:60%"></div></div>`);
    $("#drawer").innerHTML = `<div class="skel"></div><div class="skel"></div>`;
    return;
  }
  if (o.error) { $("#leftPanel").innerHTML = placeHeader(`<div class="callout error sec">${svg("alert")}<div>The hazard profile could not be loaded. Try reloading the page.</div></div>`); $("#drawer").innerHTML = ""; return; }
  const top = o.hazards.filter((h) => h.level === "high").map((h) => (HZ_SHORT[h.id] || h.title).toLowerCase());
  const cards = o.hazards.map((h) => { const [cls, lbl] = REL[h.level]; const e = h.evidence.find((x) => !x.summary) || h.evidence[0];
    return `<article class="hz-card"><span class="hz-ic ${h.level}">${svg(HZ_ICON[h.id])}</span><div><h3>${esc(HZ_SHORT[h.id] || h.title)}<span class="chip ${cls}">${lbl}${h.events ? ` · ${h.events}` : ""}</span></h3>
      <div class="ev">${e ? `${esc(e.date || "")} · ${esc((e.text || "").slice(0, 110))}${(e.text || "").length > 110 ? "…" : ""}` : esc(h.signal || "No events in the loaded records")}</div>
      <div class="acts"><a class="link-btn" href="#/place/${S.rid}/simulate?hz=${h.id}">${svg("crosshair", "sm")}Simulate</a>${e?.source ? `<a class="link-btn" href="${esc(e.source)}" target="_blank" rel="noopener">${svg("link", "sm")}Source</a>` : ""}</div></div></article>`; }).join("");
  $("#leftPanel").innerHTML = placeHeader(`
    <div class="callout info sec">${svg("info")}<div>${top.length ? `<b>On record here: ${esc(top.join(", "))}.</b>` : "<b>No frequent hazard on record in the loaded data.</b>"} Next: assess <a href="#/place/${S.rid}/readiness">Readiness</a> or <a href="#/place/${S.rid}/simulate">Simulate</a> a hazard.</div></div>
    <section class="sec" aria-labelledby="hpH"><div class="sec-h"><h3 id="hpH">Hazard profile</h3><span class="src">ranked by this place’s records</span></div>${cards}</section>`);
  const p = o.profile, c = o.counts, em = o.region.emergency || {};
  const metric = (ic, k, v, s, na) => `<div class="metric"><div class="k">${svg(ic, "sm")}${k}</div>${na ? `<div class="na">${na}</div>` : `<div class="v">${v}</div>`}<div class="s">${s}</div></div>`;
  $("#drawer").innerHTML = `
    <div class="drawer-h"><div><h2>Exposure and history</h2><div class="sub">${esc(S.place.name)} · computed from public data, no AI</div></div></div>
    <section aria-labelledby="exH"><div class="sec-h"><h3 id="exH">Exposure summary</h3><span class="src">3 km around the centre</span></div>
      <div class="metrics">
        ${metric("users", "Residents", fmtN(p.residents_estimate), "WorldPop 2020 · modelled estimate", p.residents_estimate === undefined ? "Not available in public data" : null)}
        ${metric("mountain", "Height above sea level", o.elevation_m ? `${o.elevation_m.min}–${o.elevation_m.max} m` : "", "Copernicus DEM · block averages", o.elevation_m ? null : "Not available in public data")}
        ${metric("waves", "Low-lying blocks", p.low_lying_blocks_pct !== undefined ? `${p.low_lying_blocks_pct}%` : "", "≥1.5 m below surroundings · DEM", p.low_lying_blocks_pct === undefined ? "Not available in public data" : null)}
        ${metric("leaf", "Tree cover 2016 → 2025", p.trees_share_2016_pct !== undefined ? `${p.trees_share_2016_pct}→${p.trees_share_2025_pct}%` : "", "Google Dynamic World", p.trees_share_2016_pct === undefined ? "Not available in public data" : null)}
        ${metric("school", "Schools", fmtN(c.school), "OpenStreetMap · mapped only", c.school ? null : "None mapped")}
        ${metric("home", "Elderly homes", fmtN(c.elderly_home), "OpenStreetMap · mapped only", c.elderly_home ? null : "None mapped")}
        ${metric("hospital", "Hospitals · clinics", `${fmtN(c.hospital)} · ${fmtN(c.clinic)}`, "OpenStreetMap · mapped only")}
        ${metric("arrowDown", "Underground shelters", fmtN(c.underground_shelter), "Metro, underground car parks · OSM", c.underground_shelter ? null : "None mapped")}
      </div>
      <p class="note" style="margin-top:8px">“None mapped” means OpenStreetMap has no record — some may exist. Hospital capacity is not available in public data.</p></section>
    <section class="sec" aria-labelledby="tlH"><div class="sec-h"><h3 id="tlH">Historical events</h3><span class="src">newest first</span></div>
      ${o.timeline?.length ? `<ol class="tl">${o.timeline.map((e) => `<li class="${e.kind === "news" ? "news" : ""}"><div class="d">${esc(e.date || "")}</div><p>${esc(e.text || "")}</p>
        <div class="meta"><span class="chip">${svg(HZ_ICON[e.hazard] || "alert")}${esc(HZ_SHORT[e.hazard] || e.hazard)}</span><span class="chip ${e.kind === "news" ? "accent" : ""}">${e.kind === "news" ? "News · link checked" : "Dataset"}</span>${e.source ? `<a class="chip" href="${esc(e.source)}" target="_blank" rel="noopener">${svg("link")}Source</a>` : ""}</div></li>`).join("")}</ol>`
      : `<div class="empty"><h3>No dated events in the loaded records</h3><p class="note">Global catalogues and checked news found nothing dated within range. This does not mean the place is risk-free.</p></div>`}</section>
    <section class="sec" aria-labelledby="emH"><div class="sec-h"><h3 id="emH">Emergency numbers</h3><span class="src">${esc(o.region.country || "")}</span></div>
      ${(em.call || []).length ? `<div class="calls">${em.call.map((x) => `<a class="call" href="tel:${esc(x.number)}">${svg("phone")}<b>${esc(x.number)}</b><span>${esc(x.for)}</span></a>`).join("")}</div><p class="note" style="margin-top:6px">From a checked table · <a href="${esc(em.source)}" target="_blank" rel="noopener">source</a></p>`
        : `<div class="callout warn">${svg("alert")}<div>${esc(em.note || "No checked number for this country.")} <a href="${esc(em.source || "#")}" target="_blank" rel="noopener">List of emergency numbers</a></div></div>`}</section>
    <p class="note sec">Map data: ${esc(o.region.map_data_source || "OpenStreetMap")} · Satellite: Google Earth Engine · History: Earth Engine, USGS, GDACS and link-checked news. <a href="#/sources">All sources</a></p>`;
  render();
}

/* readiness */
const RD_STEPS = ["Finding past disasters and checking every link", "Measuring flood, hospital and shelter access", "Checking land cover, wetlands and animal care", "Writing the report and validating every number"];
function renderReadiness() {
  const ready = S.overview?.report_ready;
  const left = S.report ? readinessLeft() : `
    <section class="sec card flat"><h3 style="font-size:16px">Readiness assessment</h3>
      <p class="note" style="margin:6px 0 12px">An AI investigator selects measured checks for ${esc(S.place.name)}, then writes a report. Code validates every number and link before it is shown.</p>
      <button class="btn primary block" type="button" id="analyseBtn" ${S.reportBusy ? "disabled" : ""}>${ready ? "Open the assessment" : "Generate the assessment"}${svg("arrowRight")}</button>
      <p class="note" style="margin-top:8px">${ready ? "A validated assessment is saved for this place." : "Takes about a minute (Gemini with Google Search)."}</p></section>
    <section class="sec"><div class="sec-h"><h3>How it is assessed</h3></div><ol class="steps"><li>Past disasters: datasets plus news, every link opened and checked for the place and year.</li><li>Measured checks: flood exposure, walking access to hospitals and shelters, land-cover change, animal care.</li><li>Readiness before, during and after, for people, animals and nature.</li><li>Ranked fixes, each with evidence and confidence.</li></ol></section>`;
  $("#leftPanel").innerHTML = placeHeader(left);
  $("#analyseBtn")?.addEventListener("click", analyse);
  if (S.report) return renderReportDrawer();
  if (S.reportBusy) return;
  $("#drawer").innerHTML = `<div class="drawer-h"><div><h2>Readiness</h2><div class="sub">${esc(S.place.name)}</div></div></div><div class="empty"><h3>No assessment shown yet</h3><p>Generate or open the assessment to see the readiness scorecard, what to fix first and the evidence behind each fix.</p></div>`;
}
function readinessLeft() {
  const { res } = S.report, r = res.report;
  const checked = Object.values(res.sources_checked || {}).filter((v) => v.verified).length;
  return `<section class="sec">${provenance([true, !!res.validated, checked > 0 || (r?.calamities || []).length > 0, true], res.validated ? null : "partial")}</section>
    <section class="sec"><div class="sec-h"><h3>Calamities assessed</h3></div><div class="stack">${(r?.readiness || []).map((c) => `<div class="card flat" style="padding:10px 12px;display:flex;justify-content:space-between;align-items:center;gap:8px"><b style="text-transform:capitalize">${esc(c.calamity)}</b>${levelChip(c.overall)}</div>`).join("") || '<p class="note">None.</p>'}</div></section>
    <section class="sec"><p class="note">${checked} news link${checked === 1 ? "" : "s"} opened and checked · ${(r?.recommendations || []).length} ranked fixes · ${(r?.data_gaps || []).length} data gaps shown</p></section>`;
}
const levelChip = (lv) => { const m = { good: ["safe", "checkCircle", "Good"], fair: ["caution", "alert", "Fair"], poor: ["danger", "octagon", "Poor"], unknown: ["", "help", "Not available"] }[lv] || ["", "help", titleCase(lv)];
  return `<span class="chip ${m[0]}">${svg(m[1])}${m[2]}</span>`; };
async function analyse() {
  S.reportBusy = true; renderReadiness();
  const el = $("#drawer"); let k = 0;
  const draw = () => { el.innerHTML = `<div class="drawer-h"><div><h2>Assessing ${esc(S.place.name)}</h2><div class="sub">About a minute when generated fresh</div></div></div>${checklist(RD_STEPS, k)}`; };
  draw(); const timer = setInterval(() => { if (k < RD_STEPS.length - 1) { k++; draw(); } }, 1600);
  try {
    const name = S.place.name;
    const [res, ind] = await Promise.all([api(`/api/prepare/${encodeURIComponent(name)}${rq()}`), api(`/api/area/${encodeURIComponent(name)}/indicators${rq()}`)]);
    S.report = { res, ind }; S.areaCells = ind.cells; if (S.overview && !S.overview.error) S.overview.report_ready = true;
  } catch (e) { el.innerHTML = `<div class="callout error">${svg("alert")}<div><b>The assessment could not be completed.</b> ${esc(e.message)}</div></div><button class="btn block" type="button" id="retryRd" style="margin-top:10px">Try again</button>`; $("#retryRd").addEventListener("click", analyse); }
  clearInterval(timer); S.reportBusy = false;
  if (S.report && S.view === "readiness") renderReadiness();
  render();
}
function provenance(ok, mode) {
  const items = [["Computed by SafeGround engine", ok[0]], ["Checked against official rulebook", ok[1]], ["Sources cited", ok[2]], ["Data gaps shown", ok[3]]];
  const label = mode === "fallback" ? "Narrative withheld (fallback shown)" : mode === "partial" ? "Partly validated" : null;
  return `<div class="prov" role="list" aria-label="Provenance">${items.map(([t, y], i) => `<div role="listitem" class="${y ? "ok" : "warn"}">${svg(y ? "checkCircle" : "alert")}<span>${i === 1 && label ? label : t}</span></div>`).join("")}</div>`;
}
function scorecard(r, ind) {
  const groups = { people: "users", animals: "paw", nature: "leaf" }, val = { good: 3, fair: 2, poor: 1 };
  const out = Object.entries(groups).map(([g, ic]) => {
    const cells = r.readiness.flatMap((c) => c.matrix.filter((m) => m.group === g)), known = cells.filter((m) => val[m.level]);
    const cnt = ["good", "fair", "poor", "unknown"].map((l) => [l, cells.filter((m) => m.level === l).length]).filter(([, n]) => n);
    const avg = known.length ? known.reduce((a, m) => a + val[m.level], 0) / known.length : null;
    const lv = avg === null ? "unknown" : avg >= 2.5 ? "good" : avg >= 1.7 ? "fair" : "poor";
    return `<div class="sc"><div class="k">${svg(ic)}${titleCase(g)}</div><div class="lv">${levelChip(lv)}</div><div class="s">${cnt.map(([l, n]) => `${n} ${l}`).join(" · ")} · from the validated grid</div></div>`;
  });
  const h = ind.hospital_access.share_within_1000m_pct, s = ind.shelter_access.share_within_1000m_pct;
  const lvI = h === undefined || h === null ? "unknown" : h >= 60 ? "good" : h >= 30 ? "fair" : "poor";
  out.splice(1, 0, `<div class="sc"><div class="k">${svg("building")}Infrastructure</div><div class="lv">${levelChip(lvI)}</div><div class="s num">Hospital ≤1 km walk: ${h ?? "—"}% · shelter ≤1 km: ${s ?? "—"}% · computed (≥60% good, 30–59% fair, &lt;30% poor)</div></div>`);
  return `<div class="score">${out.join("")}</div>`;
}
function hexCentroid(hs) { const ll = hs.map((x) => h3.cellToLatLng(x)); return [ll.reduce((a, c) => a + c[0], 0) / ll.length, ll.reduce((a, c) => a + c[1], 0) / ll.length]; }
function renderReportDrawer() {
  const { res, ind } = S.report, r = res.report, el = $("#drawer");
  if (!r) { el.innerHTML = `<div class="callout warn">${svg("alert")}<div><b>AI narrative withheld.</b> The generated report did not pass SafeGround’s validator, so it is not shown. The measured indicators below are computed by code.</div></div>${indicatorsHtml(ind)}`; return; }
  const gaps = r.data_gaps || [];
  el.innerHTML = `
    <div class="drawer-h"><div><h2>Readiness · ${esc(S.place.name)}</h2><div class="sub">Scorecard and indicators are computed; summary and fixes are written by Gemini and validated</div></div><button class="icon-btn" type="button" aria-label="Print assessment" onclick="window.print()">${svg("printer")}</button></div>
    <section aria-labelledby="scH"><div class="sec-h"><h3 id="scH">Readiness scorecard</h3></div>${scorecard(r, ind)}</section>
    <section class="sec" aria-labelledby="fxH"><div class="sec-h"><h3 id="fxH">Fix first</h3><span class="src">ranked · validated by code</span></div>
      ${r.recommendations.map((x, i) => { const hs = x.map_hexes || [], c = hs.length ? hexCentroid(hs) : null;
        return `<article class="rec" data-i="${i}"><div class="rec-top"><span class="rank">${x.rank}</span><div><h3>${esc(x.what)}</h3><div class="where">${svg("pin", "sm")} ${esc(x.where)}</div>
          <div class="chips"><span class="chip">${esc(titleCase(x.calamity))}</span><span class="chip">${esc(titleCase(x.phase))}</span><span class="chip ${x.confidence === "high" ? "safe" : x.confidence === "medium" ? "caution" : ""}">${esc(titleCase(x.confidence))} confidence</span></div></div></div>
          <details class="acc"><summary>Impact, evidence and sources${svg("chev", "chev")}</summary><div class="acc-body"><dl>
            <dt>Impact</dt><dd>${esc(x.protects)}</dd><dt>Evidence</dt><dd>${esc(x.why)}</dd>
            <dt>Source</dt><dd>${(x.evidence || []).map((e) => `<span class="chip" style="margin:0 4px 4px 0">${svg("database")}${esc(e)}</span>`).join("") || "—"}</dd>
            <dt>Data gaps</dt><dd>${gaps.length ? `${gaps.length} report-wide gaps apply — see “What we could not measure” below.` : "None reported."}</dd></dl>
            ${c ? `<div style="display:flex;gap:14px;margin-top:10px;flex-wrap:wrap"><button class="link-btn" type="button" data-show="${i}">${svg("pin", "sm")}Show ${hs.length} block${hs.length === 1 ? "" : "s"} on map</button><a class="link-btn" href="${gmapsAt(c[0], c[1])}" target="_blank" rel="noopener">${svg("link", "sm")}Google Maps</a></div>` : ""}</div></details></article>`; }).join("")}</section>
    <section class="sec" aria-labelledby="bdaH"><div class="sec-h"><h3 id="bdaH">Before · during · after</h3></div>
      ${r.readiness.map((c, ci) => `<div class="stack" style="margin-bottom:16px"><div style="display:flex;justify-content:space-between;align-items:center"><b style="text-transform:capitalize">${esc(c.calamity)}</b>${levelChip(c.overall)}</div>
        <p class="note">${esc(c.why_it_matters_here)}</p>${matrixHtml(c.matrix, ci)}<div class="cell-detail" id="cd${ci}" hidden></div></div>`).join("")}</section>
    <section class="sec" aria-labelledby="sumH"><div class="sec-h"><h3 id="sumH">Summary</h3><span class="src">Gemini · validated</span></div><p style="font-size:14.5px;color:var(--text-2)">${esc(r.summary)}</p></section>
    <section class="sec"><details class="acc"><summary>${svg("book")}Past disasters used (${r.calamities.length})${svg("chev", "chev")}</summary><div class="acc-body"><ol class="tl">${r.calamities.map((c) => `<li class="${c.evidence_kind === "news" ? "news" : ""}"><div class="d">${esc(c.date)}</div><p>${esc(c.what_happened)}</p>
        <div class="meta"><span class="chip">${esc(titleCase(c.type))}</span><a class="chip accent" href="${esc(c.source_url)}" target="_blank" rel="noopener">${svg("link")}${c.evidence_kind === "dataset" ? "Dataset" : "Source"}</a>${verifiedChip(res, c)}</div></li>`).join("")}</ol></div></details>
      <details class="acc"><summary>${svg("help")}What we could not measure (${gaps.length})${svg("chev", "chev")}</summary><div class="acc-body"><ul style="margin:0;padding-left:18px">${gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul></div></details>
      <details class="acc"><summary>${svg("database")}Measured indicators (no AI)${svg("chev", "chev")}</summary><div class="acc-body">${indicatorsHtml(ind, true)}</div></details></section>`;
  $$("[data-show]", el).forEach((b) => b.addEventListener("click", () => {
    const i = +b.dataset.show; $$(".rec", el).forEach((x) => x.classList.toggle("active", +x.dataset.i === i));
    S.highlight = r.recommendations[i].map_hexes || []; const [la, lo] = hexCentroid(S.highlight); flyTo(la, lo, 14.8, 900); render();
  }));
  $$(".cell[data-c]", el).forEach((b) => b.addEventListener("click", () => {
    const [ci, i] = b.dataset.c.split(":").map(Number), cell = r.readiness[ci].matrix[i], box = $(`#cd${ci}`);
    $$(`.cell[data-c^="${ci}:"]`, el).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    box.innerHTML = `<b>${esc(titleCase(cell.phase))} · ${esc(cell.group)}:</b> ${esc(cell.finding)}<div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px">${cell.evidence.map((e) => `<span class="chip">${svg("database")}${esc(e)}</span>`).join("")}</div>`;
    box.hidden = false;
  }));
}
function verifiedChip(res, c) {
  if (c.evidence_kind === "dataset") return `<span class="chip">${svg("satellite")}Catalogue data</span>`;
  const ev = (res.sources_checked || {})[c.source_url]; if (!ev) return "";
  return ev.verified ? `<span class="chip safe" title="${esc(ev.reason)}">${svg("check")}${/Internet Archive/.test(ev.reason || "") ? "Checked via archive" : "Link checked"}</span>` : `<span class="chip caution">Not auto-checked</span>`;
}
function matrixHtml(cells, ci) {
  const groups = [["people", "users"], ["animals", "paw"], ["nature", "leaf"]], ic = { good: "checkCircle", fair: "alert", poor: "octagon", unknown: "help" };
  let h = `<div class="matrix" role="group" aria-label="Readiness grid"><div></div>${groups.map(([g, i]) => `<div class="h">${svg(i, "sm")}${g}</div>`).join("")}`;
  for (const p of ["before", "during", "after"]) {
    h += `<div class="h">${p}</div>`;
    for (const [g] of groups) { const i = cells.findIndex((x) => x.phase === p && x.group === g), c = cells[i];
      h += c ? `<button type="button" class="cell ${c.level}" data-c="${ci}:${i}" aria-pressed="false" aria-label="${esc(p)}, ${esc(g)}: ${esc(c.level)}"><b>${svg(ic[c.level] || "help", "sm")}${esc(c.level === "unknown" ? "Not available" : c.level)}</b>${esc(c.finding.slice(0, 46))}${c.finding.length > 46 ? "…" : ""}</button>` : `<div class="cell unknown"><b>—</b>Not assessed</div>`; }
  }
  return h + "</div>";
}
function indicatorsHtml(ind, bare) {
  const p = ind.profile, f = ind.flood, ha = ind.hospital_access, sa = ind.shelter_access;
  const row = (k, v, src) => (v === undefined || v === null || v === "" ? `<tr><th>${k}</th><td>Not available in public data</td></tr>` : `<tr><th>${k}<br><span class="note" style="font-weight:400">${src}</span></th><td class="num">${esc(v)}</td></tr>`);
  const t = `<table class="kv">${row("Residents", fmtN(p.residents_estimate), "WorldPop 2020")}
    ${row("Flood-prone blocks", f.flood_prone_blocks !== undefined ? `${f.flood_prone_blocks} · ${fmtN(f.residents_in_flood_prone_blocks)} residents` : null, "Copernicus DEM, reported flooding")}
    ${row("No tall-building refuge ≤300 m", f.residents_without_refuge_within_300m !== undefined ? `${fmtN(f.residents_without_refuge_within_300m)} residents` : null, "OSM + Open Buildings")}
    ${row("Major hospital ≤1 km walk", ha.share_within_1000m_pct !== undefined ? `${ha.share_within_1000m_pct}% of residents` : null, "Walking network + WorldPop")}
    ${row("Underground shelter ≤1 km walk", sa.share_within_1000m_pct !== undefined ? `${sa.share_within_1000m_pct}% of residents` : null, "Metro, underground parking")}
    ${row("Tree cover 2016 → 2025", p.trees_share_2016_pct !== undefined ? `${p.trees_share_2016_pct}% → ${p.trees_share_2025_pct}%` : null, "Google Dynamic World")}</table>`;
  return bare ? t : `<div class="card sec"><h3 style="font-size:14px;margin-bottom:6px">Measured indicators (no AI)</h3>${t}</div>`;
}

/* ---------------------------------------------------------------- simulate */
function hazardOrder() {
  const ids = S.meta.hazards.map((h) => h.id), lv = {};
  if (S.overview?.hazards) for (const h of S.overview.hazards) lv[h.id] = h.level;
  return ids.map((id) => [id, lv[id] || "low"]);
}
function renderSimulate() {
  if (!S.meta || !S.place) return;
  const sim = S.sim, hz = S.HZ[sim.hazard], need = hz.needs_incident;
  const groups = {};
  for (const [id, lv] of hazardOrder()) (groups[S.HZ[id].group] ||= []).push([id, lv]);
  const picker = Object.entries(groups).map(([g, list]) => `<div class="hz-group"><div class="gt" id="g-${g}">${esc(GROUP_TITLE[g] || g)}</div>
    <div class="hz-picker" role="radiogroup" aria-labelledby="g-${g}">${list.map(([id, lv]) => `<button type="button" class="hz-opt" role="radio" data-hz="${id}" aria-checked="${id === sim.hazard}" tabindex="${id === sim.hazard ? 0 : -1}">
      ${svg(HZ_ICON[id])}<span class="t">${esc(HZ_SHORT[id])}</span>${lv !== "low" ? `<span class="r ${lv}">${svg(lv === "high" ? "octagon" : "alert")}${lv === "high" ? "Frequent here" : "Recorded"}</span>` : ""}</button>`).join("")}</div></div>`).join("");
  const preset = PRESETS.find((p) => p.id === sim.preset) || PRESETS[0];
  const locRow = (key, label, color, ll) => `<div class="loc-row ${sim.placing === key ? "active" : ""}"><span class="dot" style="background:${color}"></span><div><b style="font-size:14px">${label}</b><div class="v num">${ll ? `${ll.lat.toFixed(5)}, ${ll.lon.toFixed(5)}` : "Not placed yet"}</div></div>
      <div class="acts"><button type="button" class="link-btn" data-place="${key}" aria-pressed="${sim.placing === key}">${sim.placing === key ? "Click the map…" : ll ? "Move" : "Place on map"}</button></div>
      <form class="coord-form" data-coord="${key}"><label class="sr-only" for="cf-${key}">${label} coordinates</label><input id="cf-${key}" type="text" class="field" placeholder="lat, lon" inputmode="decimal"><button class="btn sm" type="submit">Set</button>${key === "person" ? '<button class="btn sm" type="button" data-centre="1">Centre</button>' : ""}</form></div>`;
  const locDone = !!sim.person && (!need || !!sim.incident);
  $("#leftPanel").innerHTML = `${placeHeader()}
    <ol class="stepper sec" aria-label="Simulation steps">
      <li class="step done" data-n="1"><h3>Hazard<span class="val">${esc(HZ_SHORT[sim.hazard])}</span></h3>${picker}</li>
      <li class="step done" data-n="2"><h3>Conditions</h3><div class="params" id="hzParams"></div></li>
      <li class="step ${locDone ? "done" : "now"}" data-n="3"><h3>Location</h3>${need ? locRow("incident", INCIDENT_LABEL[sim.hazard] || "Incident", "rgb(240,86,91)", sim.incident) : ""}${locRow("person", "Person", theme() === "dark" ? "#E8EDF4" : "#121821", sim.person)}
        <p class="note" style="margin-top:8px">Click the map, type “lat, lon”, or use “Centre” for the place centre.</p></li>
      <li class="step done" data-n="4"><h3>Person profile<span class="val">${esc(preset.label)}</span></h3>
        <div class="presets" role="radiogroup" aria-label="Person profile">${PRESETS.map((p) => `<button type="button" class="preset" role="radio" data-preset="${p.id}" aria-checked="${p.id === sim.preset}" tabindex="${p.id === sim.preset ? 0 : -1}">${svg(p.icon)}${esc(p.label)}</button>`).join("")}</div>
        <p class="note" style="margin-top:8px">${esc(preset.note)}</p></li>
      <li class="step ${sim.res && !sim.dirty ? "done" : locDone ? "now" : ""}" data-n="5"><h3>Safety plan</h3>
        <div class="gen-bar"><button class="btn primary block" type="button" id="genBtn" ${!locDone || sim.busy ? "disabled" : ""}>${sim.busy ? '<span class="spinner"></span>Generating…' : `${svg("shield")}${sim.res ? "Generate again" : "Generate safety plan"}`}</button>
          ${!locDone ? `<p class="note" style="margin-top:8px">Place the ${need && !sim.incident ? `${(INCIDENT_LABEL[sim.hazard] || "incident").toLowerCase()} and the ` : ""}person first.</p>` : sim.dirty ? `<p class="dirty">${svg("alert", "sm")}Settings changed — generate again to update the plan.</p>` : ""}</div></li>
    </ol>`;
  paramsUI();
  bindSimulate();
  if (!sim.res && !sim.busy) renderPlanEmpty();
  render();
}
function bindSimulate() {
  const lp = $("#leftPanel");
  $$(".hz-opt", lp).forEach((b) => b.addEventListener("click", () => selectHazard(b.dataset.hz)));
  $$(".preset", lp).forEach((b) => b.addEventListener("click", () => selectPreset(b.dataset.preset)));
  lp.addEventListener("keydown", (e) => {
    const t = e.target, k = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!k || !(t.classList.contains("hz-opt") || t.classList.contains("preset"))) return;
    e.preventDefault();
    const items = t.classList.contains("hz-opt") ? $$(".hz-opt", lp) : $$(".preset", lp), n = items[(items.indexOf(t) + k + items.length) % items.length];
    if (n.dataset.hz) selectHazard(n.dataset.hz); else selectPreset(n.dataset.preset);
  });
  $$("[data-place]", lp).forEach((b) => b.addEventListener("click", () => { S.sim.placing = b.dataset.place; renderSimulate(); }));
  $$("form[data-coord]", lp).forEach((f) => f.addEventListener("submit", (e) => {
    e.preventDefault(); const c = parseCoords($("input", f).value);
    if (!c) return toast("Enter coordinates as “lat, lon”"); setLocation(f.dataset.coord, c.lat, c.lon);
  }));
  $$("[data-centre]", lp).forEach((b) => b.addEventListener("click", () => setLocation("person", S.place.lat, S.place.lon)));
  $("#genBtn")?.addEventListener("click", runPlan);
}
function selectPreset(id) { S.sim.preset = id; markDirty(); renderSimulate(); $(`.preset[data-preset="${id}"]`)?.focus(); }
function selectHazard(id) {
  if (id === S.sim.hazard) return;
  Object.assign(S.sim, { hazard: id, params: {}, incident: null, res: null, dirty: false, placing: S.HZ[id].needs_incident ? "incident" : (S.sim.person ? null : "person") });
  S.zone = null; S.route = null; S.target = null;
  renderSimulate(); refreshZone(); $(`.hz-opt[data-hz="${id}"]`)?.focus();
}
function markDirty() { if (S.sim.res) S.sim.dirty = true; }
function setLocation(key, lat, lon) {
  if (dist(S.place.lat, S.place.lon, lat, lon) > S.place.radius_m) return toast(`That point is outside the 3 km area around ${S.place.name}`);
  if (key === "flood_report") { S.sim.params.reported_points = [...(S.sim.params.reported_points || []), [lat, lon]]; S.sim.placing = S.sim.person ? null : "person"; }
  else S.sim[key] = { lat, lon };
  if (key === "incident") S.sim.placing = S.sim.person ? null : "person";
  if (key === "person") S.sim.placing = null;
  markDirty(); renderSimulate();
  if (key !== "person") refreshZone(); else render();
}
const seg = (key, opts, cur, label) => `<div class="seg" role="radiogroup" aria-label="${esc(label)}" data-pk="${key}">${opts.map(([v, t]) => `<button type="button" role="radio" data-pv="${esc(v)}" aria-checked="${String(v) === String(cur)}">${esc(t)}</button>`).join("")}</div>`;
function paramsUI() {
  const hz = S.HZ[S.sim.hazard], el = $("#hzParams"), P = S.sim.params;
  for (const p of hz.params) {
    if (p.type === "wind") { P.wind_from_deg ??= p.default_from; P.wind_speed_ms ??= p.default_speed; }
    else if (p.type === "points") P.reported_points ??= [];
    else if (P[p.key] === undefined) P[p.key] = p.default;
  }
  const oh = S.overview?.hazards?.find((h) => h.id === S.sim.hazard), ev = oh?.evidence?.find((e) => !e.summary);
  const rows = hz.params.map((p) => {
    if (p.type === "choice") return `<div><span class="lbl">${esc(p.label)}</span>${seg(p.key, p.options, P[p.key], p.label)}</div>`;
    if (p.type === "select") return `<div><label class="lbl" for="p_${p.key}">${esc(p.label)}</label><select id="p_${p.key}" data-p="${p.key}">${p.options.map(([v, t]) => `<option value="${esc(v)}" ${String(v) === String(P[p.key]) ? "selected" : ""}>${esc(t)}</option>`).join("")}</select></div>`;
    if (p.type === "wind") return `<div><span class="lbl">Wind</span><div class="wind"><div class="dial" aria-hidden="true"><span class="n">N</span><span class="e">E</span><span class="s">S</span><span class="w">W</span><div class="arrow" id="windArrow"><svg viewBox="0 0 24 24"><path d="M12 19V5"/><path d="m6 11 6-6 6 6"/></svg></div></div>
      <div><div class="wind-read" id="windRead"></div><div class="wind-row"><label class="sr-only" for="pWind">Wind from (degrees)</label><input type="range" id="pWind" data-p="wind_from_deg" min="0" max="355" step="5" value="${P.wind_from_deg}"></div>
        <div class="wind-row" style="margin-top:6px"><label for="pSpeed" class="note">Speed (m/s)</label><input type="number" id="pSpeed" data-p="wind_speed_ms" step="0.5" min="0" value="${P.wind_speed_ms}"></div></div></div></div>`;
    if (p.type === "points") return `<div><span class="lbl">${esc(p.label)} <span class="muted" style="font-weight:500">· optional</span></span><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
      <button type="button" class="btn sm" id="markBtn" aria-pressed="${S.sim.placing === "flood_report"}">${svg("pin", "sm")}${S.sim.placing === "flood_report" ? "Click the map…" : "Mark a flooded street"}</button><span class="note">${(P.reported_points || []).length} marked</span>
      ${(P.reported_points || []).length ? '<button type="button" class="link-btn" id="clearPts">Clear</button>' : ""}</div></div>`;
    return "";
  }).join("");
  el.innerHTML = (ev ? `<div class="callout ${oh.level === "high" ? "warn" : "info"}" style="font-size:13px">${svg("database")}<div><b>On record here:</b> ${esc(ev.date || "")} · ${esc((ev.text || "").slice(0, 140))}</div></div>` : "")
    + (rows || `<p class="note">No conditions to set: this alert covers the whole area.</p>`) + `<p class="note">${esc(HZ_NOTE[S.sim.hazard] || "")}</p>`;
  const wind = $("#pWind");
  if (wind) { const upd = () => { const d = +wind.value; $("#windArrow").style.transform = `rotate(${d + 180}deg)`; $("#windRead").innerHTML = `From <b>${compass(d)} (${d}°)</b> · drifts toward <b>${compass(d + 180)}</b>`; }; wind.addEventListener("input", upd); upd(); }
  $$("[data-p]", el).forEach((inp) => inp.addEventListener("change", () => { P[inp.dataset.p] = inp.type === "number" || inp.type === "range" ? +inp.value : inp.value; markDirty(); refreshZone(); showDirty(); }));
  $$(".seg[data-pk]", el).forEach((g) => g.addEventListener("click", (e) => {
    const b = e.target.closest("[data-pv]"); if (!b) return; $$("button", g).forEach((x) => x.setAttribute("aria-checked", String(x === b)));
    const v = b.dataset.pv; P[g.dataset.pk] = /^-?\d+(\.\d+)?$/.test(v) ? +v : v; markDirty(); refreshZone(); showDirty();
  }));
  $("#markBtn")?.addEventListener("click", () => { S.sim.placing = S.sim.placing === "flood_report" ? null : "flood_report"; paramsUI(); renderCoach(); });
  $("#clearPts")?.addEventListener("click", () => { P.reported_points = []; markDirty(); paramsUI(); refreshZone(); });
}
function showDirty() { if (S.sim.dirty && !$(".dirty") && $("#genBtn")) $("#genBtn").insertAdjacentHTML("afterend", `<p class="dirty">${svg("alert", "sm")}Settings changed — generate again to update the plan.</p>`); }
async function refreshZone() {
  if (S.view !== "simulate" || !S.rid) return;
  const sim = S.sim;
  if (S.HZ[sim.hazard].needs_incident && !sim.incident) { S.zone = null; return render(); }
  const body = { hazard: sim.hazard, lat: sim.incident?.lat ?? S.place.lat, lon: sim.incident?.lon ?? S.place.lon, situation: "outdoors", incident_lat: sim.incident?.lat, incident_lon: sim.incident?.lon, params: sim.params, region: S.rid };
  try { const z = await post("/api/zone", body); S.zone = z.type === "hex" ? { ...z, cells: z.cells.filter((c) => c.t !== "green") } : z; } catch (e) { S.zone = null; }
  render();
}

async function onMapClick(lat, lon) {
  if (S.page !== "ws") return;
  if (!S.rid) { S.pick = { name: "Selected point", label: "", lat, lon, region_id: regionId(lat, lon) }; renderPickPanel(); reverseName(lat, lon); return; }
  const inside = dist(S.place.lat, S.place.lon, lat, lon) <= S.place.radius_m;
  if (!inside) {
    if (S.view === "simulate") return flashCoach(`Outside the 3 km area around ${S.place.name} — click inside the circle`);
    S.pick = { name: "Selected point", label: "", lat, lon, region_id: regionId(lat, lon) }; renderPop(); reverseName(lat, lon); return;
  }
  if (S.view !== "simulate") return blockInfo(lat, lon);
  const sim = S.sim, need = S.HZ[sim.hazard].needs_incident;
  setLocation(sim.placing || (need && !sim.incident ? "incident" : "person"), lat, lon);
}
function renderPop() {
  const p = S.pick, el = $("#mapPop"); if (!p) { el.hidden = true; return; }
  const isReady = S.ready.some((r) => r.id === p.region_id);
  el.innerHTML = `<button class="icon-btn x" type="button" aria-label="Close">${svg("x")}</button><div class="eyebrow">New location</div><h3 style="font-size:16px;margin:4px 0 2px">${esc(p.name || "Selected point")}</h3>
    <div class="note">${esc([p.admin, p.country].filter(Boolean).join(", "))} · ${p.lat.toFixed(4)}, ${p.lon.toFixed(4)}</div>
    <button class="btn primary block" type="button" style="margin-top:10px">${isReady ? "Open" : "Assess this area"}${svg("arrowRight")}</button>`;
  el.hidden = false; marker("pick2", p, `<div class="mk mk-pin">${PIN_SVG}</div>`);
  $(".x", el).addEventListener("click", () => { el.hidden = true; marker("pick2", null); S.pick = null; });
  $(".btn", el).addEventListener("click", () => { el.hidden = true; marker("pick2", null); location.hash = isReady ? `#/place/${p.region_id}/overview` : "#/pick"; });
}
async function blockInfo(lat, lon) {
  const cell = h3.latLngToCell(lat, lon, 9);
  try {
    const r = await api(`/api/hex/${cell}${rq()}`), p = r.props || {}, el = $("#mapPop");
    const row = (k, v, src) => `<tr><th>${k}<br><span class="note" style="font-weight:400">${src}</span></th><td class="num">${v ?? "Not available"}</td></tr>`;
    el.innerHTML = `<button class="icon-btn x" type="button" aria-label="Close">${svg("x")}</button><div class="eyebrow">Block · about 0.1 km²</div><h3 style="font-size:16px;margin:4px 0 8px">${esc(r.place || S.place.name)}</h3>
      ${Object.keys(p).length ? `<table class="kv">${row("Residents", p.pop !== undefined && p.pop !== null ? fmtN(Math.round(p.pop)) : null, "WorldPop 2020")}
        ${row("Height above sea level", p.elev_mean !== undefined && p.elev_mean !== null ? `${Math.round(p.elev_mean)} m` : null, "Copernicus DEM")}
        ${row("Relative to surroundings", p.rel_elev !== undefined && p.rel_elev !== null ? `${p.rel_elev > 0 ? "+" : ""}${p.rel_elev.toFixed(1)} m` : null, "Copernicus DEM")}
        ${row("Nearest surface water", p.water_near_m !== undefined && p.water_near_m !== null ? `${fmtN(Math.round(p.water_near_m))} m` : null, "JRC Global Surface Water")}
        ${row("Tree cover 2025", p.dw_trees_2025 !== undefined && p.dw_trees_2025 !== null ? `${Math.round(p.dw_trees_2025 * 100)}%` : null, "Dynamic World")}</table>` : '<p class="note">Satellite data is not available in public data for this block.</p>'}`;
    el.hidden = false; $(".x", el).addEventListener("click", () => { el.hidden = true; });
  } catch (e) { /* ignore */ }
}

/* ---------------------------------------------------------------- safety plan (drawer) */
const PLAN_STEPS = ["Danger zone from official guidance", "Safe destination and a route that avoids the danger", "Plain-language plan from the computed facts", "SafeGround validator checks every number and step"];
function renderPlanEmpty() {
  $("#drawer").innerHTML = `<div class="drawer-h"><div><h2>Safety plan</h2><div class="sub">${esc(S.place.name)} · ${esc(HZ_SHORT[S.sim.hazard])}</div></div></div>
    <div class="empty"><h3>Your safety plan will appear here</h3><p>Complete the steps on the left, then select <b>Generate safety plan</b>. You will get the danger level, the protective move, a safe destination with a walking route and Google Maps directions, a numbered plan with official citations, and the data gaps.</p></div>`;
}
const presetSit = () => (PRESETS.find((p) => p.id === S.sim.preset) || PRESETS[0]).sit;
async function runPlan() {
  const sim = S.sim; if (!sim.person) return;
  sim.busy = true; renderSimulate();
  let k = 0; const el = $("#drawer");
  const draw = () => { el.innerHTML = `<div class="drawer-h"><div><h2>Building the safety plan</h2><div class="sub">${esc(HZ_SHORT[sim.hazard])} · ${esc(S.place.name)}</div></div></div>${checklist(PLAN_STEPS, k)}`; };
  draw(); const timer = setInterval(() => { if (k < PLAN_STEPS.length - 1) { k++; draw(); } }, 1800);
  if (small()) setTimeout(() => el.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "start" }), 50);
  const body = { hazard: sim.hazard, lat: sim.person.lat, lon: sim.person.lon, situation: presetSit(), incident_lat: sim.incident?.lat, incident_lon: sim.incident?.lon, params: sim.params, use_ai: true, region: S.rid };
  try {
    const res = await post("/api/respond", body);
    const t = res.facts.target;
    sim.res = res; sim.dirty = false; S.route = res.facts.route_coords;
    S.target = t ? { ...t, short: (t.name && !/^Unnamed|^Safe point/.test(t.name) ? t.name : t.label || t.name || "Safe destination").slice(0, 44) } : null;
    clearInterval(timer); sim.busy = false; renderSimulate(); renderPlan(res);
    fitPts([sim.person, sim.incident, S.target].filter(Boolean).map((p) => [p.lon, p.lat]).concat((S.route || []).map(([la, lo]) => [lo, la])));
  } catch (e) {
    clearInterval(timer); sim.busy = false; renderSimulate();
    el.innerHTML = `<div class="callout error">${svg("alert")}<div><b>The plan could not be built.</b> ${esc(e.message)}</div></div><button class="btn block" type="button" id="retryPlan" style="margin-top:10px">Try again</button>`;
    $("#retryPlan").addEventListener("click", runPlan);
  }
}
function renderPlan(res) {
  const p = res.plan, f = res.facts, lvl = f.tier in LEVEL ? f.tier : "unknown", ok = res.generated_by === "gemini";
  const preset = PRESETS.find((x) => x.id === S.sim.preset) || PRESETS[0];
  const adv = Object.fromEntries((f.advice || []).map((a) => [a.id, a]));
  const cites = (ids) => ((ids || []).length ? `<div class="cites">${ids.map((id) => `<button type="button" class="cite" aria-expanded="false" data-cite="${esc(id)}" aria-label="Show official text ${esc(id)}">${esc(id)}</button>`).join("")}</div>` : "");
  const steps = (arr, cls) => `<ol class="steps ${cls}">${arr.map((s) => `<li><div>${esc(s.text)}${cites(s.advice_ids)}</div></li>`).join("")}</ol>`;
  const rt = f.route, tg = f.target, inc = f.incident?.source_from_spot, near = f.nearby_500m || {};
  const nearChips = Object.entries(near).map(([k, n]) => `<span class="chip">${svg(k.startsWith("school") ? "school" : k.startsWith("elderly") ? "home" : "hospital")}${n} ${esc(k.replace("_", " "))}</span>`).join("");
  const facts = [rt ? ["Walking route", `${fmtN(rt.length_m)} m`] : null, rt ? ["Walking time", `~${rt.walk_minutes} min`] : null, tg?.direction ? ["Direction", `Head ${tg.direction}`] : null,
    inc ? [INCIDENT_LABEL[f.hazard] || "Incident", `${fmtN(inc.distance_m)} m ${inc.direction}`] : null].filter(Boolean);
  const basis = Object.entries(f.zone_basis || {}).filter(([k]) => !["thresholds", "method"].includes(k));
  const gaps = [...(f.data_gaps || []), ...(f.caveats || [])];
  const calls = (f.call || []).map((c) => `<a class="call" href="tel:${esc(c.number)}">${svg("phone")}<b>${esc(c.number)}</b><span>${esc(c.for)}</span></a>`).join("");
  const hosp = (f.nearest_hospitals || []).map((h) => `<div class="hosp">${svg("hospital", "sm")}<span><b>${esc(h.name)}</b><br><span class="d num">${fmtN(h.straight_m)} m ${esc(h.direction)} (straight line)${h.in_danger_zone ? " · inside the danger zone" : ""}</span></span><a class="link-btn" href="${gmapsDir(S.sim.person, h, "")}" target="_blank" rel="noopener">${svg("nav", "sm")}Directions</a></div>`).join("");
  const [lvText, lvIc] = LEVEL[lvl];
  $("#drawer").innerHTML = `
    <div class="drawer-h"><div><h2>Safety plan</h2><div class="sub">${esc(f.hazard_title)} · ${esc(S.place.name)} · ${esc(preset.label)}</div></div></div>
    ${provenance([true, ok, Object.keys(f.sources || {}).length > 0, true], ok ? null : "fallback")}
    ${ok ? "" : `<div class="callout warn" style="margin-top:10px">${svg("alert")}<div><b>Generated narrative withheld.</b> The AI explanation did not pass SafeGround’s validator, so the official guidance is shown word for word instead.</div></div>`}
    <section class="sec" aria-labelledby="dlH"><h3 class="sr-only" id="dlH">Danger level and protective move</h3>
      <div class="dlevel ${lvl}"><div class="lv">${svg(lvIc)}${esc(lvText)}</div><p class="why">${esc(f.tier_meaning)}</p><p class="src">Computed by the SafeGround engine from the ${esc(f.hazard_title.toLowerCase())} rulebook</p></div>
      <div class="move"><span class="move-ic">${svg(MOVE_ICON[f.main_move] || "shield")}</span><div><div class="k">Recommended protective move</div><div class="t">${esc(f.main_move_text)}</div></div></div></section>
    <section class="sec" aria-labelledby="dsH"><div class="sec-h"><h3 id="dsH">Safe destination and route</h3><span class="src">computed</span></div>
      ${tg ? `<div class="dest"><div class="k">Destination</div><div class="t">${esc(tg.label || tg.name)}</div>${rt?.via?.length ? `<div class="via">Via ${esc(rt.via.slice(0, 4).join(" → "))}</div>` : ""}
        <div class="acts"><a class="btn primary sm" href="${gmapsDir(S.sim.person, tg)}" target="_blank" rel="noopener">${svg("nav", "sm")}Directions in Google Maps</a><a class="btn sm" href="${gmapsAt(tg.lat, tg.lon)}" target="_blank" rel="noopener">${svg("pin", "sm")}View place</a></div></div>`
        : `<div class="dest"><div class="k">Destination</div><div class="t">Stay where you are</div><div class="via">The protective move for this situation does not require travel.</div></div>`}
      ${facts.length ? `<div class="fact-grid">${facts.map(([k, v]) => `<div class="fact"><div class="k">${k}</div><div class="v">${esc(v)}</div></div>`).join("")}</div>` : ""}</section>
    ${nearChips ? `<section class="sec"><div class="sec-h"><h3>Within 500 m</h3><span class="src">mapped in OpenStreetMap</span></div><div class="near">${nearChips}</div><p class="note" style="margin-top:6px">People here may need help first.</p></section>` : ""}
    <section class="sec" aria-labelledby="plH"><div class="sec-h"><h3 id="plH">What to do</h3></div>
      <div class="ai-note">${svg(ok ? "sparkles" : "book", "sm")}${ok ? "Written by Gemini from the facts above · passed the SafeGround validator · each step cites official guidance" : "Official guidance, quoted word for word"}</div>
      <p style="font-size:14.5px;margin-bottom:12px"><b>Where to go:</b> ${esc(p.where_to_go)}</p>
      ${steps(p.do_now, "")}<div class="sec-h sec"><h3>Do not</h3></div>${steps(p.do_not, "dont")}
      ${p.if_you_are.length ? `<details class="acc sec"><summary>${svg("users")}If the person is… (${p.if_you_are.length})${svg("chev", "chev")}</summary><div class="acc-body">${p.if_you_are.map((s) => `<p style="margin-bottom:4px"><b>${esc(titleCase(s.situation))}:</b> ${esc(s.text)}</p>${cites(s.advice_ids)}`).join("")}</div></details>` : ""}</section>
    <section class="sec" aria-labelledby="clH"><div class="sec-h"><h3 id="clH">Call</h3><span class="src">checked table</span></div>${calls ? `<div class="calls">${calls}</div>` : `<div class="callout warn">${svg("alert")}<div>A checked emergency number is not available for this country. Find the local number now.</div></div>`}</section>
    ${hosp ? `<section class="sec"><div class="sec-h"><h3>Nearest major hospitals</h3><span class="src">OpenStreetMap</span></div>${hosp}</section>` : ""}
    <section class="sec">
      <details class="acc"><summary>${svg("book")}Evidence and official sources (${Object.keys(f.sources || {}).length})${svg("chev", "chev")}</summary><div class="acc-body">
        <table class="kv">${basis.map(([k, v]) => `<tr><th>${esc(titleCase(k))}</th><td>${esc(typeof v === "object" ? JSON.stringify(v) : v)}</td></tr>`).join("")}</table>
        <p style="margin:12px 0 6px;font-weight:600;color:var(--text)">Sources</p>${Object.values(f.sources || {}).map((s) => `<p style="margin-bottom:4px"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></p>`).join("")}</div></details>
      <details class="acc" ${gaps.length ? "open" : ""}><summary>${svg("help")}Data gaps and limitations (${gaps.length})${svg("chev", "chev")}</summary><div class="acc-body"><ul style="margin:0;padding-left:18px">${gaps.map((g) => `<li style="margin-bottom:4px">${esc(g)}</li>`).join("")}</ul>
        <p style="margin-top:10px"><b>Confidence:</b> <span class="conf" style="display:inline-flex"><span class="bars ${esc(p.confidence)}"><span></span><span></span><span></span></span>${esc(p.confidence)}</span> — ${esc(p.confidence_reason)}</p>
        ${p.valid_while.length ? `<p style="margin-top:6px"><b>Valid while:</b> ${p.valid_while.map(esc).join("; ")}</p>` : ""}</div></details></section>
    <div class="plan-actions"><button class="btn" type="button" id="aPrint">${svg("printer")}Print plan</button><button class="btn" type="button" id="aPdf">${svg("download")}Download PDF</button>
      <button class="btn" type="button" id="aCopy">${svg("copy")}Copy plain text</button><button class="btn" type="button" id="aShare">${svg("share")}Share link</button></div>
    <p class="note sec">Computed in ${res.latency_s}s. Planning and training only — follow authorities in a real emergency.</p>`;
  $$(".cite", $("#drawer")).forEach((b) => b.addEventListener("click", () => {
    const wrap = b.parentElement, open = b.getAttribute("aria-expanded") === "true", a = adv[b.dataset.cite];
    $$(".cite", wrap).forEach((x) => x.setAttribute("aria-expanded", "false"));
    if (wrap.nextElementSibling?.classList.contains("cite-text")) wrap.nextElementSibling.remove();
    if (!open) { b.setAttribute("aria-expanded", "true"); wrap.insertAdjacentHTML("afterend", `<div class="cite-text">“${esc(a?.text || b.dataset.cite)}”<br><span class="note">${esc(f.sources?.[a?.source]?.title || "Official rulebook")}</span></div>`); }
  }));
  $("#aPrint").addEventListener("click", () => printPlan(res));
  $("#aPdf").addEventListener("click", () => downloadPdf(res));
  $("#aCopy").addEventListener("click", async () => { try { await navigator.clipboard.writeText(planText(res)); toast("Plan copied as plain text"); } catch (e) { toast("Copy is not available in this browser"); } });
  $("#aShare").addEventListener("click", async () => { const url = shareUrl(); try { await navigator.clipboard.writeText(url); toast("Share link copied"); } catch (e) { window.prompt("Copy this link", url); } });
}
function shareUrl() {
  const s = S.sim, q = new URLSearchParams({ hz: s.hazard, pr: s.preset });
  if (s.person) q.set("p", `${s.person.lat.toFixed(5)},${s.person.lon.toFixed(5)}`);
  if (s.incident) q.set("i", `${s.incident.lat.toFixed(5)},${s.incident.lon.toFixed(5)}`);
  q.set("c", JSON.stringify(s.params)); q.set("run", "1");
  return `${location.origin}${location.pathname}#/place/${S.rid}/simulate?${q.toString()}`;
}
function restoreShare(q) {
  const hz = q.get("hz"); if (!S.HZ[hz]) return;
  const ll = (v) => { const c = parseCoords(v); return c ? { lat: c.lat, lon: c.lon } : null; };
  let params = {}; try { params = JSON.parse(q.get("c") || "{}"); } catch (e) { params = {}; }
  Object.assign(S.sim, { hazard: hz, preset: PRESETS.some((p) => p.id === q.get("pr")) ? q.get("pr") : S.sim.preset, params, person: ll(q.get("p")), incident: ll(q.get("i")), res: null, dirty: false, placing: null });
  if (!S.sim.person) S.sim.placing = S.HZ[hz].needs_incident && !S.sim.incident ? "incident" : "person";
  S.zone = null; S.route = null; S.target = null;
  history.replaceState(null, "", `#/place/${S.rid}/simulate`);
  if (q.get("run") && S.sim.person && (!S.HZ[hz].needs_incident || S.sim.incident)) setTimeout(runPlan, 300);
}
function planText(res) {
  const p = res.plan, f = res.facts, L = [];
  const preset = PRESETS.find((x) => x.id === S.sim.preset) || PRESETS[0];
  L.push(`SAFEGROUND SAFETY PLAN — ${f.hazard_title}`, `${S.place.name}${S.place.country ? `, ${S.place.country}` : ""} · ${preset.label} · ${new Date().toLocaleString("en-GB")}`, "");
  L.push(`DANGER LEVEL: ${LEVEL[f.tier]?.[0] || f.tier} — ${f.tier_meaning}`, `PROTECTIVE MOVE: ${f.main_move_text}`, `WHERE TO GO: ${p.where_to_go}`);
  if (f.route) L.push(`ROUTE: ${f.route.length_m} m, about ${f.route.walk_minutes} min walk${f.target?.direction ? `, head ${f.target.direction}` : ""}`);
  if (f.target) L.push(`DIRECTIONS: ${gmapsDir(S.sim.person, f.target)}`);
  L.push("", "DO NOW:"); p.do_now.forEach((s, i) => L.push(`${i + 1}. ${s.text} [${s.advice_ids.join(", ")}]`));
  L.push("", "DO NOT:"); p.do_not.forEach((s) => L.push(`- ${s.text}`));
  if ((f.call || []).length) L.push("", `CALL: ${f.call.map((c) => `${c.number} (${c.for})`).join("; ")}`);
  L.push("", "DATA GAPS AND LIMITATIONS:"); [...(f.data_gaps || []), ...(f.caveats || [])].forEach((g) => L.push(`- ${g}`));
  L.push("", "SOURCES:"); Object.values(f.sources || {}).forEach((s) => L.push(`- ${s.title} — ${s.url}`));
  L.push("", res.generated_by === "gemini" ? "Validator: passed (Gemini explanation checked against computed facts and the official rulebook)." : "Validator: AI narrative withheld; official guidance quoted word for word.");
  L.push("SafeGround is a planning and training tool. In a real emergency, follow authorities and call your local emergency number.");
  return L.join("\n");
}
function printPlan(res) {
  const p = res.plan, f = res.facts, preset = PRESETS.find((x) => x.id === S.sim.preset) || PRESETS[0];
  $("#printRoot").innerHTML = `<div class="ph"><div><div class="pbrand">SafeGround</div><div style="font-size:9pt">Hazard readiness and response planning for any place on Earth</div></div><div style="text-align:right;font-size:9pt">${esc(new Date().toLocaleString("en-GB"))}<br>${esc(S.place.name)}${S.place.country ? `, ${esc(S.place.country)}` : ""}</div></div>
    <h1>Safety plan — ${esc(f.hazard_title)}</h1><p style="margin-top:4pt">Person profile: ${esc(preset.label)} · Location ${S.sim.person.lat.toFixed(5)}, ${S.sim.person.lon.toFixed(5)}</p>
    <div class="plevel">${esc(LEVEL[f.tier]?.[0] || f.tier)} — ${esc(f.tier_meaning)}</div>
    <table><tr><th>Protective move</th><td>${esc(f.main_move_text)}</td></tr><tr><th>Where to go</th><td>${esc(p.where_to_go)}</td></tr>
      ${f.route ? `<tr><th>Route</th><td>${f.route.length_m} m · ~${f.route.walk_minutes} min walk${f.target?.direction ? ` · head ${esc(f.target.direction)}` : ""}${f.route.via?.length ? ` · via ${esc(f.route.via.slice(0, 4).join(", "))}` : ""}</td></tr>` : ""}
      ${f.target ? `<tr><th>Directions</th><td style="word-break:break-all">${esc(gmapsDir(S.sim.person, f.target))}</td></tr>` : ""}
      <tr><th>Call</th><td>${(f.call || []).map((c) => `${esc(c.number)} (${esc(c.for)})`).join(" · ") || "Find the local emergency number"}</td></tr></table>
    <h2>Do now</h2><ol>${p.do_now.map((s) => `<li>${esc(s.text)} <span class="cid">[${esc(s.advice_ids.join(", "))}]</span></li>`).join("")}</ol>
    <h2>Do not</h2><ul>${p.do_not.map((s) => `<li>${esc(s.text)}</li>`).join("")}</ul>
    <h2>Data gaps and limitations</h2><ul>${[...(f.data_gaps || []), ...(f.caveats || [])].map((g) => `<li>${esc(g)}</li>`).join("")}</ul>
    <h2>Official sources</h2><ul>${Object.values(f.sources || {}).map((s) => `<li>${esc(s.title)} — ${esc(s.url)}</li>`).join("")}</ul>
    <div class="pfoot">${res.generated_by === "gemini" ? "Validator: passed — every number and step was checked against the computed facts and the official rulebook." : "Validator: AI narrative withheld — official guidance quoted word for word."}<br>SafeGround is a planning and training tool. In a real emergency, follow authorities and call your local emergency number.</div>`;
  window.print();
}
function loadScript(src) { return new Promise((ok, bad) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = bad; document.head.appendChild(s); }); }
async function downloadPdf(res) {
  try {
    if (!window.jspdf) await loadScript("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js");
    const doc = new window.jspdf.jsPDF({ unit: "pt", format: "a4" }), W = 515, x = 40; let y = 50;
    const latin = (t) => String(t).normalize("NFKD").replace(/[^\x20-\x7E°–—’“”•]/g, "");
    const write = (t, size = 10, bold = false, gap = 4) => { doc.setFont("helvetica", bold ? "bold" : "normal"); doc.setFontSize(size);
      for (const line of doc.splitTextToSize(latin(t), W)) { if (y > 790) { doc.addPage(); y = 50; } doc.text(line, x, y); y += size * 1.35; } y += gap; };
    planText(res).split("\n").forEach((line, i) => { if (i === 0) write(line, 15, true, 6); else if (/^[A-Z][A-Z ]+:$/.test(line)) write(line, 10.5, true, 2); else write(line || " ", 10, false, line ? 2 : 0); });
    doc.save(`SafeGround-plan-${S.sim.hazard}-${(S.place.name || "place").replace(/\W+/g, "-")}.pdf`);
    toast("PDF downloaded");
  } catch (e) { toast("PDF could not be created here — use Print plan and choose “Save as PDF”"); }
}

/* ---------------------------------------------------------------- docs pages */
const DOCS = {
  methodology: () => `<h1>Methodology</h1><p class="lead">SafeGround separates what code computes from what AI explains. Every zone, distance, route and count is computed; Gemini writes plain-language explanations that a validator checks before anyone sees them.</p>
    <h2>1 · Building a place</h2><p>For a 3 km circle around the chosen point, SafeGround fetches roads and facilities from OpenStreetMap, measures population, height, water and land cover for about 300 hexagonal blocks with Google Earth Engine, and collects disaster records (Global Flood Database, CHIRPS / ERA5-Land rain extremes, FIRMS fires, USGS earthquakes, GDACS alerts).</p>
    <h2>2 · Overview</h2><p>Hazards are ranked by the place’s own records: “Frequent here” means a link-checked news event or three or more catalogue events; “Recorded or possible” means one or two, or a strong exposure signal (for example several industrial sites).</p>
    <h2>3 · Readiness</h2><p>An investigator agent (Gemini on Google ADK) chooses measured checks — flood exposure, walking access to hospitals and shelters, land-cover change, animal care — and a writer agent produces the report. Every number must appear in a tool result and every news link must have been opened and checked for the place and year. The infrastructure score is computed directly: share of residents within a 1 km walk of a major hospital (≥60% good, 30–59% fair, under 30% poor).</p>
    <h2>4 · Simulation</h2><table><tr><th>Hazard</th><th>How the danger is computed</th><th>Guidance</th></tr>
      <tr><td>Flood</td><td>Low land (DEM), surface water, 24 h rain category; marked flooded streets override</td><td>State flood do’s and don’ts</td></tr>
      <tr><td>Earthquake</td><td>Shaking now / after shaking; nearest mapped open area</td><td>Ready.gov (FEMA)</td></tr>
      <tr><td>Cyclone</td><td>Surge-exposed vs wind-only blocks; Saffir-Simpson strength</td><td>Ready.gov, NOAA NHC</td></tr>
      <tr><td>Tsunami</td><td>Height vs 100 ft (30 m) above sea level</td><td>Ready.gov</td></tr>
      <tr><td>Wildfire</td><td>Fire point and wind; spread ≈ 10% of wind speed</td><td>Ready.gov; Cruz &amp; Alexander 2019</td></tr>
      <tr><td>Extreme heat</td><td>NWS heat index from temperature and humidity</td><td>Ready.gov, US NWS</td></tr>
      <tr><td>Gas leak</td><td>ERG 2024 Table 1/3 distances shaped by wind</td><td>ERG 2024, Ready.gov</td></tr>
      <tr><td>Bomb / blast</td><td>DHS/FBI stand-off distances</td><td>DHS/FBI chart, ERG 2024</td></tr>
      <tr><td>Air raid</td><td>Whole-area alert; nearest mapped underground shelter</td><td>Civil-defence drill guidance</td></tr></table>
    <p style="margin-top:10px">Routes are shortest walks on the OpenStreetMap network that avoid the danger zone (and underpasses for floods and tsunamis).</p>
    <h2>5 · The validator</h2><p>Before a plan is shown, code checks that the danger level and move match the computed facts, every number appears in those facts, every step cites an allowed rulebook line, and no unsafe instruction appears (a basement in a gas leak, downwind in a wildfire, the shore in a tsunami, a doorway in an earthquake). Failing answers are sent back with the reasons up to three times; after that the official text is shown word for word and the AI narrative is withheld.</p>`,
  sources: () => `<h1>Data &amp; Sources</h1><p class="lead">Every metric in SafeGround names its source. These are the datasets and official guidance it uses.</p>
    <h2>Datasets</h2><table><tr><th>Dataset</th><th>Used for</th><th>Licence</th></tr>
      <tr><td>OpenStreetMap (Overpass API; OpenFreeMap vector tiles)</td><td>Roads, walking network, hospitals, schools, elderly homes, shelters, open areas, industry</td><td>ODbL</td></tr>
      <tr><td>WorldPop 2020 (Earth Engine)</td><td>Residents per block</td><td>CC BY 4.0</td></tr>
      <tr><td>Copernicus DEM GLO-30 (Earth Engine)</td><td>Height above sea level, low-lying land</td><td>Copernicus licence</td></tr>
      <tr><td>JRC Global Surface Water (Earth Engine)</td><td>Distance to water, water occurrence</td><td>Copernicus / JRC</td></tr>
      <tr><td>Google Open Buildings 2.5D (Earth Engine)</td><td>Building heights (Africa, South/Southeast Asia, Latin America)</td><td>CC BY 4.0</td></tr>
      <tr><td>Google Dynamic World (Earth Engine)</td><td>Tree, built and water cover 2016 → 2025</td><td>CC BY 4.0</td></tr>
      <tr><td>Global Flood Database; CHIRPS; ERA5-Land; FIRMS</td><td>Flood, rain-extreme and fire records</td><td>Open data</td></tr>
      <tr><td>USGS earthquake catalogue</td><td>Earthquakes M5.5+ within 200 km since 1970</td><td>Public domain</td></tr>
      <tr><td>GDACS</td><td>Disaster alerts near the place</td><td>Open data</td></tr>
      <tr><td>Photon (Komoot)</td><td>Place search and naming</td><td>OSM data</td></tr></table>
    <h2>Official guidance (rulebooks)</h2><ul><li>Ready.gov (US FEMA): earthquakes, tsunamis, hurricanes, wildfires, extreme heat, chemical emergencies</li>
      <li>Emergency Response Guidebook 2024 (US DOT / NOAA CAMEO): gas and explosives distances</li><li>US DHS/FBI Bomb Threat Stand-Off Chart</li>
      <li>NOAA National Hurricane Center (Saffir-Simpson); US National Weather Service (heat index)</li><li>Cruz &amp; Alexander (2019), Annals of Forest Science — wildfire spread rule of thumb</li>
      <li>State disaster-management flood do’s and don’ts; civil-defence drill guidance (May 2025)</li></ul>
    <h2>AI</h2><p>Gemini 3.5 Flash on Google ADK, with Google Search grounding for news. AI text is always labelled and validated.</p>`,
  limitations: () => `<h1>Limitations</h1><p class="lead">SafeGround is a planning and training tool. It does not detect live incidents, send alerts or replace official emergency instructions.</p>
    <ul><li><b>Estimates, not forecasts.</b> Flood, surge and tsunami tiers come from a 30 m elevation model with metres of error. Drain and built-over-wetland flooding is missed — marked flooded streets override the estimate. Distance from the coast is not measured.</li>
      <li><b>Screening distances.</b> ERG distances are designed for transport incidents; for fixed facilities they are a screening estimate. Bomb stand-off distances “do not guarantee safety”. Wildfire spread is a rule of thumb, not a fire-behaviour model.</li>
      <li><b>Mapped data only.</b> OpenStreetMap completeness varies; hospital capacity, basements, elderly homes and animals are poorly mapped. “None mapped” does not mean none exist.</li>
      <li><b>Models.</b> Population and building heights are model estimates. Past-event lists are not complete.</li>
      <li><b>Area.</b> Each place covers a 3 km circle; facilities just outside it are not counted. Google Open Buildings heights do not cover Europe or North America.</li>
      <li><b>Conditions are set by you.</b> Wind, rain, temperature and storm strength are inputs, not live observations.</li>
      <li><b>Guidance.</b> Official advice comes from US and Indian sources; local guidance may differ. Emergency numbers come from a checked table; if a country is missing, SafeGround says so instead of guessing.</li>
      <li><b>Privacy.</b> No accounts and no personal data. Places you build are kept on the server so others can open them.</li></ul>`,
  accessibility: () => `<h1>Accessibility</h1><p class="lead">SafeGround targets WCAG 2.2 AA. This is the checklist the interface is built and tested against.</p>
    <ul><li>Semantic landmarks (header, navigation, main, complementary panels, footer) and a skip link.</li><li>Logical heading order on every page and panel.</li>
      <li>Full keyboard use: tabs, search with arrow keys, hazard and profile pickers as radio groups with arrow-key navigation, accordions and dialogs.</li>
      <li>Map alternatives: every location can be set by typing coordinates or using the place centre; results are always in the text panels.</li>
      <li>Visible focus ring (3 px) on every control; minimum target size 24 × 24 px (most are 32–44 px).</li>
      <li>Colour is never the only signal: danger levels pair colour with an icon and a text label; the map always has a legend.</li>
      <li>Text contrast of at least 4.5:1 in both themes (body text 9–15:1); hazard colours stay distinct in light and dark themes.</li>
      <li>Status updates (progress, toasts, plan results) use polite live regions.</li><li>Respects “reduce motion”: map flights and spinners stop animating.</li>
      <li>Text resizes to 200% without loss; the layout reflows down to 320 px wide.</li><li>The printable plan uses plain black text with no colour dependence.</li></ul>`,
};
function renderDoc(name) {
  const el = $("#docPage");
  el.innerHTML = `<a class="back link-btn" href="#/">${svg("arrowLeft", "sm")}Back to SafeGround</a>${DOCS[name]()}<nav class="land-links" aria-label="More"><a href="#/methodology">Methodology</a><a href="#/sources">Data &amp; Sources</a><a href="#/limitations">Limitations</a><a href="#/accessibility">Accessibility</a></nav>`;
  document.title = `${titleCase(name)} · SafeGround`;
}

/* ---------------------------------------------------------------- help */
$("#helpBtn").addEventListener("click", () => {
  const d = $("#helpDlg");
  d.innerHTML = `<div class="dlg"><div class="dlg-h"><h2 id="helpTitle">Using SafeGround</h2><button class="icon-btn" type="button" aria-label="Close help" id="helpClose">${svg("x")}</button></div>
    <ol class="steps"><li>Choose a place: search, drop a pin or pick a quick start.</li><li><b>Overview</b> — what hits this place and who is exposed.</li><li><b>Readiness</b> — the scorecard and what to fix first.</li><li><b>Simulate</b> — pick a hazard, place the person, choose a profile, then generate the plan.</li></ol>
    <h3>Keyboard</h3><ul><li><kbd>/</kbd> focuses place search · <kbd>Esc</kbd> closes lists and dialogs</li><li>Arrow keys move between hazards and person profiles</li><li>Locations can be typed as “lat, lon”</li></ul>
    <h3>Learn more</h3><p><a href="#/methodology">Methodology</a> · <a href="#/sources">Data &amp; Sources</a> · <a href="#/limitations">Limitations</a> · <a href="#/accessibility">Accessibility</a></p>
    <p class="note" style="margin-top:14px">SafeGround is a planning and training tool. In a real emergency, follow authorities and call your local emergency number.</p></div>`;
  d.showModal(); $("#helpClose").addEventListener("click", () => d.close()); $$("a", d).forEach((a) => a.addEventListener("click", () => d.close()));
});
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) { e.preventDefault(); (S.page === "landing" ? $("#heroSearch") : $("#placeSearch"))?.focus(); }
  if (e.key === "Escape") { $("#mapPop").hidden = true; if (S.layerOpen) { S.layerOpen = false; renderLayerCtl(); } }
});
$$(".ws-tab").forEach((a) => a.addEventListener("click", (e) => { if (!S.rid) e.preventDefault(); }));

/* ---------------------------------------------------------------- boot */
(async function boot() {
  paintChrome();
  bindSearch($("#placeSearch"), $("#placeResults"));
  try {
    const [meta] = await Promise.all([api("/api/meta"), loadReady()]);
    S.meta = meta; S.HZ = Object.fromEntries(meta.hazards.map((h) => [h.id, h]));
  } catch (e) { document.body.insertAdjacentHTML("afterbegin", `<div class="callout error" style="position:fixed;top:64px;left:16px;right:16px;z-index:50">${svg("alert")}<div>Server not reachable: ${esc(e.message)}</div></div>`); }
  route();
})();
