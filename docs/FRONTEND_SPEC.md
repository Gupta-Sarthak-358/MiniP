# Frontend Redesign Spec — handoff to designer
**You are designing ONE page:** a real-time operations dashboard for traffic + parking forecasting. Deliver **PNGs** (visual target) + optional static **HTML**. An engineer implements the live version from your design. Read this whole doc first — Section 8 lists exactly what to deliver.

## 1. Product in one paragraph
Operators watch 5 city zones (mall, stadium, station, office, residential) plus 1 real sensor replay. The page answers: *what's happening now, what happens in the next hour, why, and what should I do?* Data refreshes every 5 s and on demand. Tone: air-traffic-control calm, not marketing landing page.

## 2. What's wrong today (fix this)
Current page stacks ~10 equal-weight cards vertically: status cards → 2 charts → explainability → recommendations → heatmap → forecast table → real-zone card. Problems: no visual hierarchy (everything shouts), weak section rhythm, cramped spacing, alerts buried mid-page, table + charts repeat the same numbers without roles. **Your job: hierarchy, rhythm, density done right — not more widgets.** Do not add features; do not remove any existing data (inventory in §5).

## 3. Layout skeleton (required structure, style freely)
```
Header bar (sticky): title · live clock/updated stamp · zone selector · step controls · auto-refresh toggle · incident demo button
Alert lane (below header, collapsible): event / sale / critical / incident / drift banners — most severe first, max 3 visible + "n more"
HERO strip: Now (traffic pill + numbers) · Parking (big free/total + bar) · +30 min prediction (pill + slots + CI) · Context line
Main grid (2 cols ≥1024px, 1 col below):
  LEFT (wide):  Traffic history+forecast chart · Parking forecast chart w/ 90% band · Forecast table (collapsible on mobile)
  RIGHT (narrow): Why this prediction (bars) · Recommendation · Zone heatmap · Real-zone replay card
Footer: data sources (UCI Birmingham, UK OGL; SINPA cited) · model + calibration note · API link
```
Responsive: ≥1024 two-col · 768–1023 one-col (charts full width, table scrolls-x) · ≤480 one-col, hero stacks, touch targets ≥44px, no horizontal page scroll.

## 4. Design tokens (set these; engineer implements as CSS vars)
- Spacing scale (px): 4·8·12·16·24·32·48 — nothing off-scale. Section gap 24–32, card padding 16–20.
- Type scale: display 28–32 (hero numbers only) · H1 20 · H2/card-title 13 uppercase tracked · body 14 · small 12. One family (system stack OK). One H1 per page; don't skip heading levels.
- Color: dark ops theme preferred (current: bg #0b1220, card #141d33). Keep 4 congestion levels distinguishable WITHOUT color alone — every status pairs color + text pill (Low/Moderate/High/Severe). Contrast ≥4.5:1 body, ≥3:1 large text.
- Radius: one value for cards (10–14), one for pills/controls (8). No gradients/glassmorphism/glows/blobs (banned — "AI slop" rule).
- Motion (mandatory): animate `transform`/`opacity` ONLY, never layout props, never `transition: all`. Easing: enter `cubic-bezier(0.22,1,0.36,1)`; press feedback 100–160 ms; routine UI <300 ms. Honor `prefers-reduced-motion` (note where).

## 5. Content inventory (every item must appear; reorganize freely)
1. Zone selector (5 zones) · Step +15min/+1h · auto-5s toggle · Inject-incident button · last-updated stamp.
2. Alerts: upcoming event (name·venue·time·impact·forecast cascade) · mega-sale notice · critical-occupancy warning · active-incident banner · drift alarm (with recent MAE).
3. Hero: traffic pill + vehicles/kmh/occ% · parking free/total + occupied/weather · +30min pill + slots + 95/90% CI + vehicles · context line (sale/event/peak flags).
4. Charts: (a) vehicles history + forecast overlay, (b) free-slots now→+60 with band (lo/hi series). Both need text equivalents (table covers it — label canvases).
5. Explainability: 6 feature bars (name·value·relative weight).
6. Recommendation: top pick + ranked list (now→30min per zone) + critical warnings.
7. Heatmap: 5 zones, dot + label + congestion + free%.
8. Forecast table: Now/+15/+30/+45/+60 × avail, CI, vehicles, congestion + calibration note ("90% bands, walk-forward coverage 0.90").
9. Real-zone card: Birmingham free/total + pill + recorded timestamp + replay position + persistence forecast + source line.
10. States for EVERYTHING async: loading skeleton (no blank screens), error banner + Retry, empty history note.

## 6. Data contracts (design with REAL values, not lorem)
`GET /api/current-status?location=mall` → `{vehicle_count:310, avg_speed:22, occupancy_pct:78, available:220, capacity:1000, weather:"cloudy", temperature:29, congestion_label:"High", is_sale_day:1, sale_intensity:3, is_event_day:0, is_incident:0, ...}`
`GET /api/prediction` → `{predictions:[{horizon_min:15, available:201, lo:195, hi:207, vehicles:330, congestion_label:"High"}×4], critical_in_min:45, interval_method:"conformal-q90 (walk-forward calibrated)", calibration:{"30":{empirical_coverage:0.9}}}`
`GET /api/recommendation` → `{message:"Recommended parking: X (117 slots…)", ranking:[{label, now_available, pred30_available, congestion_label}×5], warnings:[…]}`
`GET /api/explain` → `{factors:[{feature:"event_impact", importance:0.21, value:3}×6]}` · `GET /api/real-zone` → `{meta:{label, source}, now:{available, capacity, timestamp}, forecast:[…]}` · Full API list: `README.md`.

## 7. Accessibility (must-haves, will be checked)
Skip link · landmarks (header/main) · labeled controls · `aria-live="polite"` alerts/status, `role="alert"` errors · visible focus rings · keyboard-operable everything · charts have text alternative · reduced-motion support. Aim WCAG 2.1 AA.

## 8. Deliverables (checklist for the designer)
- [ ] PNG @1440px (full page) + PNG @390px (mobile) of the complete dashboard, populated with §6 example values (include: an active event banner AND an incident banner state — two PNGs or one annotated).
- [ ] Component close-up PNGs (optional but helpful): hero strip, forecast chart w/ band, heatmap, real-zone card.
- [ ] Optional static HTML matching the PNGs (engineer will rewire it live; keep IDs from current `frontend/index.html` where possible, or provide an ID map).
- [ ] Token sheet: colors (hex + usage), type sizes, spacing, radius, easing values.
- [ ] One paragraph per section: what you changed vs today and why.
Constraints for HTML (if provided): single file, vanilla + Chart.js CDN only, no build step, no new runtime deps.
