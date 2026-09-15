# Design Token Sheet & Specifications (Handoff to Engineering)

## 1. Color Tokens (Hex & Semantic Usage)
- **Canvas / Background**: `#0b1220` (Dark deep slate background, zero reflection)
- **Surface / Card Background**: `#141d33` (Card and panel backgrounds)
- **Surface Raised / Active Element**: `#1b2642` (Elevated cards, hover pills, active segment items)
- **Border Default**: `#233152` (Subtle 1px solid separators and card borders)
- **Border Strong**: `#33466e` (Active inputs, focus rings)
- **Text Primary**: `#f1f5f9` (Headings, primary values, display numbers, contrast ratio > 11:1)
- **Text Secondary / Muted**: `#94a3b8` (Labels, captions, secondary specs, contrast > 5:1)
- **Text Subtle**: `#64748b` (Timestamps, meta notes, axis lines)

### 4 Congestion Levels (Double-coded: Text Pill + High-Contrast Color)
- **Low**: Pill text "LOW", background `#064e3b`, text `#34d399`, border `#059669`
- **Moderate**: Pill text "MODERATE", background `#451a03` / `#78350f`, text `#fbbf24`, border `#d97706`
- **High**: Pill text "HIGH", background `#431407`, text `#fb923c`, border `#ea580c`
- **Severe / Critical**: Pill text "SEVERE", background `#450a0a`, text `#f87171`, border `#dc2626`

### Alert Banners
- **Incident / Emergency**: Crimson border `#ef4444`, background `#200b0f`, badge `#b91c1c`
- **Event / Sale**: Violet/Indigo `#818cf8`, background `#141228`
- **Drift Warning**: Amber `#f59e0b`, background `#241b0b`

---

## 2. Typography Scale (Inter / Roboto Mono System Stack)
- **Display Hero Numbers**: 28px - 32px / line-height 36px / Weight 700 / Tabular numbers (`font-variant-numeric: tabular-nums`)
- **Page Heading (H1)**: 20px / line-height 26px / Weight 600 (Only one per page in header)
- **Card Titles (H2) / Section Headers**: 13px / line-height 16px / Weight 600 / `text-transform: uppercase` / `letter-spacing: 0.06em`
- **Body / Main copy**: 14px / line-height 20px / Weight 400 & 500
- **Small / Metadata / Tables**: 12px / line-height 16px / Weight 400 & 500
- **Mono / Chips / Metrics**: 11px - 12px monospace / Tabular figures

---

## 3. Spacing Scale (Strict 8-pt base scale)
- 4px (`space-1`), 8px (`space-2`), 12px (`space-3`), 16px (`space-4`), 24px (`space-6`), 32px (`space-8`), 48px (`space-12`)
- **Section gaps**: 24px to 32px
- **Card internal padding**: 16px to 20px
- **Item gap inside cards**: 12px

---

## 4. Radii & Elevation
- **Card Corner Radius**: `12px`
- **Control / Pill / Button Radius**: `8px`
- **Box Shadow**: Subtle ambient border only (`border: 1px solid #233152`), zero glossy blur, zero colored glow blobs.

---

## 5. Motion Tokens
- **Allowed Properties**: `transform` and `opacity` ONLY (Zero layout shifts or `transition: all`).
- **Timing / Easing**:
  - Enter / State transitions: `cubic-bezier(0.22, 1, 0.36, 1)`
  - Press / Micro feedback: `120ms ease-out`
  - Alert dropdown / Drawer: `240ms cubic-bezier(0.22, 1, 0.36, 1)`
- **Prefers-reduced-motion**:
  `@media (prefers-reduced-motion: reduce) { * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }`

---

## 6. Architectural Section Improvements (Before vs. After)
1. **Header & Navigation**: Before stacked controls loosely across lines. New header integrates the live 5s heartbeat indicator, zone dropdown, manual step intervals (+15m/+1h), and quick incident injector into a streamlined single-bar command surface.
2. **Prioritized Alert Lane**: Alerts previously appeared in the middle of page cards. Now elevated directly under the header with severity ordering (Incident > Drift > Sale/Event) and accordion toggle to keep critical items impossible to miss without cluttering viewports.
3. **Hero Strip Hierarchy**: Replaced 10 disconnected cards with an immediate 3-part operational summary: Now Status, Parking Availability, and +30 min Forecast with 90% confidence boundaries.
4. **Balanced Two-Column Main Grid**:
   - **Left Column**: High-resolution dual time-series (traffic flow + forecast overlay & parking prediction with conformal 90% confidence envelope) backed by full tabular breakdown for screen readers and auditing.
   - **Right Column**: Decision-support column with 6-feature SHAP explainability weights, ranked routing recommendations, live 5-zone grid heatmap, and real-zone Birmingham sensor replay card.
5. **Accessibility & WCAG 2.1 AA Compliance**: Double-coded status badges, explicit ARIA live regions, skip links, semantic HTML5, and full tabular fallback for Canvas charts.
