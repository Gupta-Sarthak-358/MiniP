# Operations Design System — Complete CSS Variables & Responsive Implementation Specs
**System Version:** 2.4.0-tactical  
**Target Applications:** Real-Time Traffic & Parking Operations Console (Desktop & Mobile 390px)  
**Standard Compliance:** WCAG 2.1 AA Compliant · Zero-Gloss Tactical Dark Ops Architecture

---

## 1. Global CSS Custom Properties (`:root`)

```css
:root {
  /* ==========================================================================
     1. COLOR PALETTE (Strict Dark Operations Palette)
     ========================================================================== */
  /* Surfaces & Canvas */
  --ops-bg-canvas: #0b1220;
  --ops-bg-surface: #141d33;
  --ops-bg-surface-raised: #1b2642;
  --ops-bg-surface-hover: #222f50;
  --ops-bg-surface-active: #293860;
  --ops-bg-input: #0e1628;

  /* Borders & Separators */
  --ops-border-subtle: #1e2a44;
  --ops-border-default: #233152;
  --ops-border-strong: #33466e;
  --ops-border-focus: #38bdf8;

  /* Typography & Text Contrast (WCAG 2.1 AA Compliant) */
  --ops-text-primary: #f1f5f9;      /* Contrast > 11:1 against --ops-bg-surface */
  --ops-text-secondary: #94a3b8;    /* Contrast > 5:1 against --ops-bg-surface */
  --ops-text-muted: #64748b;        /* Auxiliary labels, axis lines, timestamps */
  --ops-text-disabled: #475569;

  /* Brand & Operational Accents */
  --ops-color-cyan-base: #38bdf8;
  --ops-color-cyan-glow: rgba(56, 189, 248, 0.15);
  --ops-color-teal: #2dd4bf;
  --ops-color-indigo: #818cf8;

  /* ==========================================================================
     2. 4-LEVEL CONGESTION TOKENS (Double-Coded: Text Pill + High-Contrast Pair)
     ========================================================================== */
  /* Level 1: Low */
  --ops-status-low-bg: #064e3b;
  --ops-status-low-border: #059669;
  --ops-status-low-text: #34d399;

  /* Level 2: Moderate */
  --ops-status-moderate-bg: #451a03;
  --ops-status-moderate-border: #d97706;
  --ops-status-moderate-text: #fbbf24;

  /* Level 3: High */
  --ops-status-high-bg: #431407;
  --ops-status-high-border: #ea580c;
  --ops-status-high-text: #fb923c;

  /* Level 4: Severe / Critical */
  --ops-status-severe-bg: #450a0a;
  --ops-status-severe-border: #dc2626;
  --ops-status-severe-text: #f87171;

  /* Alert Channel Overrides */
  --ops-alert-incident-bg: #200b0f;
  --ops-alert-incident-border: #ef4444;
  --ops-alert-incident-badge: #b91c1c;
  --ops-alert-drift-bg: #241b0b;
  --ops-alert-drift-border: #f59e0b;
  --ops-alert-event-bg: #141228;
  --ops-alert-event-border: #818cf8;

  /* ==========================================================================
     3. TYPOGRAPHY SCALE (System Inter / Geist + Tabular Mono)
     ========================================================================== */
  --ops-font-sans: 'Geist', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --ops-font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  /* Display & Headings */
  --ops-type-display-size: 32px;
  --ops-type-display-lh: 36px;
  --ops-type-display-weight: 700;

  --ops-type-h1-size: 20px;
  --ops-type-h1-lh: 26px;
  --ops-type-h1-weight: 600;

  --ops-type-h2-size: 13px;
  --ops-type-h2-lh: 16px;
  --ops-type-h2-weight: 600;
  --ops-type-h2-tracking: 0.06em;

  --ops-type-body-size: 14px;
  --ops-type-body-lh: 20px;
  --ops-type-body-weight: 400;

  --ops-type-small-size: 12px;
  --ops-type-small-lh: 16px;
  --ops-type-small-weight: 500;

  --ops-type-mono-size: 11px;
  --ops-type-mono-lh: 14px;
  --ops-type-mono-weight: 500;

  /* ==========================================================================
     4. SPACING SCALE (Strict 8-pt Base System)
     ========================================================================== */
  --ops-space-1: 4px;
  --ops-space-2: 8px;
  --ops-space-3: 12px;
  --ops-space-4: 16px;
  --ops-space-6: 24px;
  --ops-space-8: 32px;
  --ops-space-12: 48px;

  /* Architectural Gaps & Padding */
  --ops-grid-gap: var(--ops-space-6);
  --ops-card-padding: var(--ops-space-4);
  --ops-card-item-gap: var(--ops-space-3);

  /* ==========================================================================
     5. GEOMETRY, ELEVATION & RADII
     ========================================================================== */
  --ops-radius-card: 12px;
  --ops-radius-control: 8px;
  --ops-radius-pill: 9999px;

  /* Flat tactical borders - No blurred ambient dropshadows */
  --ops-elevation-card: 0 0 0 1px var(--ops-border-default);
  --ops-elevation-overlay: 0 4px 16px rgba(0, 0, 0, 0.4), 0 0 0 1px var(--ops-border-strong);

  /* Touch Targets */
  --ops-touch-min-target: 44px;

  /* ==========================================================================
     6. MOTION & INTERACTION TOKENS (Strict Opacity & Transform Only)
     ========================================================================== */
  --ops-motion-ease: cubic-bezier(0.22, 1, 0.36, 1);
  --ops-motion-duration-fast: 120ms;
  --ops-motion-duration-medium: 240ms;
  --ops-motion-transition-press: transform var(--ops-motion-duration-fast) ease-out, opacity var(--ops-motion-duration-fast) ease-out;
  --ops-motion-transition-panel: opacity var(--ops-motion-duration-medium) var(--ops-motion-ease), transform var(--ops-motion-duration-medium) var(--ops-motion-ease);
}
```

---

## 2. Responsive Breakpoint Variables & Layout Grid

```css
/* Responsive Breakpoint Matrix */
@custom-media --ops-viewport-mobile (max-width: 767px);
@custom-media --ops-viewport-tablet (min-width: 768px) and (max-width: 1023px);
@custom-media --ops-viewport-desktop (min-width: 1024px);

/* Desktop 2-Column Asymmetric Layout (>= 1024px) */
.ops-dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: var(--ops-grid-gap);
  align-items: start;
}

/* Tablet Single-Column Layout (768px - 1023px) */
@media (max-width: 1023px) {
  :root {
    --ops-type-display-size: 28px;
    --ops-type-display-lh: 32px;
    --ops-grid-gap: var(--ops-space-4);
  }
  .ops-dashboard-grid {
    grid-template-columns: 1fr;
  }
}

/* Mobile Single-Column & Touch Layout (<= 480px / 390px iPhone Viewport) */
@media (max-width: 480px) {
  :root {
    --ops-type-display-size: 26px;
    --ops-type-display-lh: 30px;
    --ops-card-padding: var(--ops-space-3);
    --ops-grid-gap: var(--ops-space-3);
  }

  .ops-dashboard-grid {
    grid-template-columns: 1fr;
    gap: var(--ops-grid-gap);
  }

  /* Interactive Elements Touch Target Guarantee */
  button, 
  select, 
  .ops-action-trigger, 
  .ops-pill-filter {
    min-height: var(--ops-touch-min-target);
  }
}

/* Mandatory Prefers-Reduced-Motion Fallback */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 3. Core Component Implementation Specs

### 3.1. Tactical Header & Sticky Command Strip
```css
.ops-command-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ops-space-3);
  padding: var(--ops-space-2) var(--ops-space-4);
  background: var(--ops-bg-canvas);
  border-bottom: 1px solid var(--ops-border-default);
  backdrop-filter: blur(8px);
}

.ops-heartbeat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--ops-color-teal);
  box-shadow: 0 0 0 2px rgba(45, 212, 191, 0.2);
  animation: ops-heartbeat 5s ease-in-out infinite;
}

@keyframes ops-heartbeat {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}
```

### 3.2. Prioritized Alert Lane
```css
.ops-alert-container {
  display: flex;
  flex-direction: column;
  gap: var(--ops-space-2);
  margin-bottom: var(--ops-space-4);
}

.ops-alert-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ops-space-3) var(--ops-space-4);
  border-radius: var(--ops-radius-control);
  font-size: var(--ops-type-small-size);
  line-height: var(--ops-type-small-lh);
}

.ops-alert-card.critical {
  background: var(--ops-alert-incident-bg);
  border: 1px solid var(--ops-alert-incident-border);
  color: #fca5a5;
}

.ops-alert-card.drift {
  background: var(--ops-alert-drift-bg);
  border: 1px solid var(--ops-alert-drift-border);
  color: #fde68a;
}

.ops-alert-card.event {
  background: var(--ops-alert-event-bg);
  border: 1px solid var(--ops-alert-event-border);
  color: #c7d2fe;
}
```

### 3.3. Double-Coded Congestion Status Badges
```css
.ops-status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--ops-space-1);
  padding: 2px var(--ops-space-2);
  border-radius: var(--ops-radius-control);
  font-family: var(--ops-font-mono);
  font-size: var(--ops-type-mono-size);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ops-status-badge[data-level="low"] {
  background-color: var(--ops-status-low-bg);
  border: 1px solid var(--ops-status-low-border);
  color: var(--ops-status-low-text);
}

.ops-status-badge[data-level="moderate"] {
  background-color: var(--ops-status-moderate-bg);
  border: 1px solid var(--ops-status-moderate-border);
  color: var(--ops-status-moderate-text);
}

.ops-status-badge[data-level="high"] {
  background-color: var(--ops-status-high-bg);
  border: 1px solid var(--ops-status-high-border);
  color: var(--ops-status-high-text);
}

.ops-status-badge[data-level="severe"] {
  background-color: var(--ops-status-severe-bg);
  border: 1px solid var(--ops-status-severe-border);
  color: var(--ops-status-severe-text);
}
```

### 3.4. Hero Strip Node Layout
```css
.ops-hero-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--ops-space-4);
  margin-bottom: var(--ops-space-6);
}

@media (max-width: 767px) {
  .ops-hero-strip {
    grid-template-columns: 1fr;
    gap: var(--ops-space-3);
  }
}

.ops-hero-card {
  background: var(--ops-bg-surface);
  border: 1px solid var(--ops-border-default);
  border-radius: var(--ops-radius-card);
  padding: var(--ops-card-padding);
}

.ops-metric-value {
  font-family: var(--ops-font-mono);
  font-size: var(--ops-type-display-size);
  line-height: var(--ops-type-display-lh);
  font-weight: var(--ops-type-display-weight);
  color: var(--ops-text-primary);
  font-variant-numeric: tabular-nums;
}
```

### 3.5. Accessible Telemetry Data Table
```css
.ops-telemetry-table-wrapper {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border: 1px solid var(--ops-border-default);
  border-radius: var(--ops-radius-card);
  background: var(--ops-bg-surface);
}

.ops-telemetry-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--ops-type-small-size);
  text-align: left;
}

.ops-telemetry-table th {
  padding: var(--ops-space-3) var(--ops-space-4);
  background: var(--ops-bg-input);
  color: var(--ops-text-muted);
  font-family: var(--ops-font-mono);
  font-size: var(--ops-type-mono-size);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--ops-border-default);
}

.ops-telemetry-table td {
  padding: var(--ops-space-3) var(--ops-space-4);
  border-bottom: 1px solid var(--ops-border-subtle);
  color: var(--ops-text-secondary);
  font-variant-numeric: tabular-nums;
}

.ops-telemetry-table tr:last-child td {
  border-bottom: none;
}
```

---

## 4. Engineering Implementation & Integration Map
1. **Import Order**: Inject the `:root` custom properties at the highest point in `frontend/styles.css`.
2. **Chart.js Color Mapping**:
   - Primary observed series: `var(--ops-color-cyan-base)` (`#38bdf8`)
   - Ensemble forecast series (dashed): `#fb923c` (`var(--ops-status-high-text)`)
   - 90% Conformal Upper/Lower envelope: `rgba(56, 189, 248, 0.12)`
   - Critical threshold line: `#dc2626` (`var(--ops-status-severe-border)`)
3. **Screen Readers & Focus**:
   - Maintain the `.skip-link` pointing to `#main-content`.
   - All interactive controls feature focus rings mapped to `outline: 2px solid var(--ops-border-focus); outline-offset: 2px;`.
