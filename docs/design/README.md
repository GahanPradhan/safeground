# SafeGround design system

SafeGround is a map-first web workspace for planners, emergency managers, companies and residents. This file documents the design deliverables. The code that implements them is in:
- [`web/styles.css`](../../web/styles.css): tokens and components
- [`web/app.js`](../../web/app.js): screens, states and interactions
- [`web/index.html`](../../web/index.html): page structure

**Brand**
- Name: SafeGround.
- Tagline: *Hazard readiness and response planning for any place on Earth.*
- Feeling: calm, credible, technical but humane, official, trustworthy.
- Logo: a map pin with a check mark, standing on a ground line.

## 1 · Screens

| Deliverable | Route | Where in code |
|---|---|---|
| Landing page | `#/` | `renderLanding()` |
| Choose a place (pin on the map, starts on New Delhi) | `#/pick` | `renderPick()` |
| Overview workspace | `#/place/<id>/overview` | `renderOverview()` |
| Readiness workspace | `#/place/<id>/readiness` | `renderReadiness()`, `renderReportDrawer()` |
| Simulation workspace | `#/place/<id>/simulate` | `renderSimulate()` |
| Safety-plan result drawer | right panel in Simulate | `renderPlan()` |
| Methodology, Data & Sources, Limitations, Accessibility | `#/methodology` etc. | `DOCS` |

**Workspace layout (desktop)**
- Sticky header: logo, the Overview / Readiness / Simulate tabs, place search, theme toggle and help.
- Left control panel (360 px).
- Map canvas in the centre.
- Right result drawer (440 px).
- Persistent footer disclaimer.

**One primary task per screen**
| Screen | Left panel | Drawer |
|---|---|---|
| Overview | Hazard profile | Exposure and history |
| Readiness | Context and action | Scorecard and fixes |
| Simulate | Five-step flow | Safety plan |

## 2 · Components

**Hazard picker (`.hz-picker`)**
- A radio group per category: Natural hazards, Industrial accidents, Security threats.
- Arrow keys move the selection.
- Each option has an icon, a name and a relevance label from the place's records: "Frequent here" (octagon icon) or "Recorded" (triangle icon). Colour is never the only cue.

**Conditions (`#hzParams`)**
- Generated from each hazard rulebook's `params`, so only the controls relevant to that hazard appear.
- Control types:
  - segmented choice
  - select
  - wind dial with a slider and speed
  - "mark flooded streets" points

**Location (`.loc-row`)**
- Incident and person rows.
- Each location can be set three ways: by clicking the map, by typing "lat, lon", or with the "Centre" button.

**Person profile presets (`.presets`)**

| Preset | Maps to the engine situation | Notes |
|---|---|---|
| Person indoors | `home_ground` | |
| Person outdoors | `outdoors` | |
| Mobility limitation | `needs_assistance` | Walking speed 0.8 m/s |
| School group | `institution` | |
| Pet owner | `home_ground` | Official pet advice is included where the guidance has it |
| Upper floor | `home_upper` | |
| In a vehicle | `vehicle` | |

**Safety-plan drawer (`renderPlan`), in order**
1. Provenance
2. Danger level, from the rulebook tier, with an icon and a text label
3. Recommended protective move
4. Safe destination with the walking route, plus *Directions in Google Maps* and *View place*
5. Computed facts: route length, time, direction, distance to the incident
6. Schools, elderly homes and clinics within 500 m
7. The numbered plan (Gemini, validated), with citation buttons that reveal the official text
8. Do-nots, and variants for other people
9. Emergency numbers
10. Nearest major hospitals with directions
11. Evidence and sources
12. Data gaps and limitations, with confidence and "valid while"
13. Actions: Print plan, Download PDF, Copy plain text, Share link

**Provenance (`.prov`)** shows four checks:
- Computed by SafeGround engine
- Checked against official rulebook
- Sources cited
- Data gaps shown

When validation fails, the second check reads "Narrative withheld (fallback shown)", and a callout explains that the official guidance is shown word for word.

**Evidence and source panel**
- In plans: an accordion holding the zone-basis table and the official source links.
- In Readiness: each fix expands to show impact, evidence, sources and data gaps, plus "Show blocks on map" and a Google Maps link.

**Map legend and layer control**
- *Layers* button with:
  - satellite data layers as a radio group: population, terrain, low-lying land, building height, tree-cover change
  - facility point layers as checkboxes
  - a note that flood history, rain extremes, earthquakes and alerts are place-level records, shown in the timeline
- The legend always lists the analysis area, the zone tiers (colour plus text), the markers and the route, and the active data ramp with its unit and source.

**Printable safety-plan template (`#printRoot`, `@media print`)**
- Black and white, with no colour dependence.
- Header: brand, place and date.
- Body:
  - danger level
  - move, destination, route and the directions link
  - call numbers
  - do now, with citation IDs
  - do not
  - data gaps
  - sources
- Footer: validator status and disclaimer.

## 3 · Design tokens

The dark theme is the default; the light theme is off-white. One interactive accent (blue). Hazard colours mean risk only and are always paired with an icon and a text label.

| Token | Dark | Light | Use |
|---|---|---|---|
| `--bg` | `#0B1018` | `#F4F3EF` | App background |
| `--surface` | `#111823` | `#FFFFFF` | Panels |
| `--surface-2` | `#151E2B` | `#FAF9F6` | Inputs, raised rows |
| `--surface-3` | `#1C2737` | `#EFEEE9` | Hover, chips |
| `--border` / `--border-strong` | `#243145` / `#33435B` | `#DEDCD4` / `#C9C6BC` | Dividers, controls |
| `--text` | `#E8EDF4` (14.9:1) | `#121821` | Body text |
| `--text-2` | `#B3BECD` (9.4:1) | `#3D4757` | Secondary text |
| `--text-3` | `#8D9AAD` (5.9:1) | `#5B6575` | Metadata (≥4.5:1) |
| `--accent` | `#3466F0` | `#2450D8` | Primary buttons, active tab |
| `--accent-text` | `#93B0FF` | `#1F46C4` | Links |
| `--danger` | `#F0565B` | `#D33036` | Immediate danger (red) |
| `--high` | `#F08A3E` | `#D9620B` | High risk (orange) |
| `--caution` | `#E9B53B` | `#C08A00` | Caution (amber) |
| `--safe` | `#3FBF7F` | `#1E8A55` | Lower risk, completed checks (green) |

Each risk colour also has a `-weak` background token and a `-text` token that meets AA contrast on that background.

Other tokens:
- **Type:** Inter, with tabular numerals for metrics. Sizes 12.5–15 px for UI, 18–22 px for metrics, 44 px for the landing headline.
- **Radius:** 10 px for cards, 7–9 px for controls.
- **Spacing:** steps of 4 px; sections are 22 px apart.
- **Elevation:** soft, two-layer shadows only on floating map controls and popovers.

## 4 · States
- **Empty:** dashed panels that explain what will appear and how to get it ("Your safety plan will appear here").
- **Loading:**
  - Progress checklists, not bare spinners. The place build has four steps; the readiness assessment, four; the safety plan, four, ending with "validator checks every number and step".
  - Skeleton bars while the overview loads.
- **Partial data:** calm labels, never a guessed value:
  - "Not available in public data"
  - "None mapped" (with a note that OpenStreetMap may be incomplete)
  - "No checked emergency number for this country"
- **Error:** a red-bordered callout with the reason, what usually helps, and a *Try again* button.
- **Success:** provenance first, then computed facts, then the labelled AI explanation.

## 5 · Accessibility checklist (WCAG 2.2 AA)

**Structure**
- [x] Semantic landmarks (header, nav, main, aside, footer), a skip link, and a logical heading order.

**Keyboard**
- [x] Tabs, search listbox (arrow keys and Enter), radio-group pickers (arrow keys), accordions (`details`), dialog (Esc).
- [x] Shortcut: <kbd>/</kbd> focuses search.

**Map alternatives**
- [x] Coordinates entry and a "Centre" button.
- [x] All results are available as text in the panels.

**Focus and targets**
- [x] Focus is always visible (a 3 px ring with a token colour).
- [x] Targets are at least 24 × 24 px; primary controls are 38–44 px.

**Colour and contrast**
- [x] Colour plus icon plus text for every danger level; the map legend is always present.
- [x] Text contrast is at least 4.5:1 in both themes (token ratios above).

**Status, motion and text**
- [x] Live regions for build progress, plan results and toasts (`aria-live="polite"`).
- [x] `prefers-reduced-motion` stops map flights, spinners and transitions.
- [x] Text resizes to 200% and reflows down to 320 px.
- [x] Alternative text and labels: icons are `aria-hidden` and every control has a text label or `aria-label`.

## 6 · Responsive website (not an app)

| Width | Layout |
|---|---|
| > 1100 px | Three columns: controls, map, drawer |
| 760–1100 px | Controls and map; the result drawer becomes an overlay panel on the map's right side |
| < 760 px | Single column in reading order: header with full-width tabs and search, then the map (52 vh), the controls, the results, and the footer disclaimer. The map legend hides (the same information is in the panels) and the map hint moves to the bottom. |

The landing page reflows from two columns to one, and its capability cards and trust strip stack.
