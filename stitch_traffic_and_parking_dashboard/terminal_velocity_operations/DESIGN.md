---
name: Terminal Velocity Operations
colors:
  surface: '#0c1321'
  surface-dim: '#0c1321'
  surface-bright: '#323949'
  surface-container-lowest: '#070e1c'
  surface-container-low: '#151b2a'
  surface-container: '#19202e'
  surface-container-high: '#232a39'
  surface-container-highest: '#2e3544'
  on-surface: '#dce2f6'
  on-surface-variant: '#bdc8d1'
  inverse-surface: '#dce2f6'
  inverse-on-surface: '#2a3040'
  outline: '#87929a'
  outline-variant: '#3e484f'
  surface-tint: '#7bd0ff'
  primary: '#8ed5ff'
  on-primary: '#00354a'
  primary-container: '#38bdf8'
  on-primary-container: '#004965'
  inverse-primary: '#00668a'
  secondary: '#93ccff'
  on-secondary: '#003351'
  secondary-container: '#3198dc'
  on-secondary-container: '#002c47'
  tertiary: '#ffc176'
  on-tertiary: '#472a00'
  tertiary-container: '#f1a02b'
  on-tertiary-container: '#613b00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c4e7ff'
  primary-fixed-dim: '#7bd0ff'
  on-primary-fixed: '#001e2c'
  on-primary-fixed-variant: '#004c69'
  secondary-fixed: '#cce5ff'
  secondary-fixed-dim: '#93ccff'
  on-secondary-fixed: '#001d31'
  on-secondary-fixed-variant: '#004b73'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb960'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0c1321'
  on-background: '#dce2f6'
  surface-variant: '#2e3544'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Geist
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  card-title:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.08em
  body-default:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-medium:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0em
  small:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: -0.01em
  mono-data-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  mono-badge:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-dense: 0.75rem
  margin: 1rem
  margin-lg: 1.5rem
  space-2xs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style

This design system is engineered for mission-critical, high-stress monitoring environments: real-time airport ground operations, municipal traffic command centers, and automated parking logistics hubs. The aesthetic evokes the deliberate composure, precision, and focus of an air traffic control radar console.

### Key Tenets
- **Cognitive Quiet:** Visual noise is actively suppressed. Decorative flourishes, excessive gradients, glassmorphic blurs, and fuzzy ambient glow effects are prohibited.
- **Instrument Precision:** Surfaces are built with flat architectural tiers, strict linear boundaries, and tabular typography that guarantees numerical data scans cleanly without horizontal jitter.
- **Immediate Chromatic Semantics:** Color is strictly functional. The neutral canvas remains resolutely dark and low-energy; saturated hues exist solely to signify system status, routing alerts, and live operational thresholds.

## Colors

The palette is tuned specifically for sustained monitoring in ambient low-light control rooms while meeting strict WCAG AA/AAA contrast ratios against deep slate backdrops.

### Surface System
- **Canvas Base (`#0b1220`):** Deep navy slate. Absorbs ambient screen glare and serves as the bottom baseline.
- **Card Surface (`#141d33`):** Primary structural surface for telemetry panels, data grids, and partitioned chart containers.
- **Surface Raised (`#1b2642`):** Elevated state for tooltips, floating toolbars, active row selections, and modal sheets.
- **Structural Border (`#233152`):** Crisp, single-pixel delimitation between all cards, dividers, and table cells.

### Operational Congestion Hierarchy
Status tokens are strictly reserved for operational state indication and cannot be used for decorative styling:
- **Low Congestion (`#10b981` Emerald):** Normal flow, target clearance within limits, parking capacity under 70%.
- **Moderate Congestion (`#f59e0b` Amber):** Elevated density, cautionary thresholds, parking capacity 70–85%.
- **High Congestion (`#f97316` Orange):** Approaching gridlock, delayed clearance rates, parking capacity 85–95%.
- **Severe Congestion (`#ef4444` Red):** Critical incident, deadlocks, total saturation (>95%), immediate intervention required.

### Tactical Accents
- **Cyan Accent (`#38bdf8` High-Cyan / `#0284c7` Deep-Cyan):** Reserved for active interaction states, focused inputs, timeline cursors, and primary operational readouts.

## Typography

Typography prioritizes scanning velocity, zero spatial drift under numeric value shifts, and absolute legibility.

### Font Pairing
- **Primary Interface (`Geist`):** Delivers clean neo-grotesque structural clarity for body text, general labels, and layout headings.
- **Telemetry & Monospace (`JetBrains Mono`):** Applied to card titles (uppercase tracked), operational metrics, IP addresses, license plate logs, sensor readings, and coordinate grids.

### Rules
- All numeric readouts, metric panels, and table data cells must activate `font-variant-numeric: tabular-nums` or rely on `JetBrains Mono` to prevent UI jitter during real-time streaming updates.
- **Card Titles:** Strictly 13px, uppercase, medium-to-bold weight, with an expanded tracking of `+0.08em` for distinct sector separation.

## Layout & Spacing

The spatial model runs on a rigorous multi-tier rhythm conforming to explicit layout intervals: `4px` (`space-2xs`), `8px` (`space-xs`), `12px` (`space-sm`), `16px` (`space-md`), `24px` (`space-lg`), `32px` (`space-xl`), and `48px` (`space-2xl`).

### Layout Philosophy
- **Fluid Modular Grid:** Layouts employ a full-bleed 12-column grid system with `16px` gutters and `16px` canvas margins (expandable to `24px` on ultra-wide screens).
- **Dense Tactical Paneling:** Telemetry dashboards favor density over whitespace. Space is allocated proportionally to data priority; panels pack tightly with uniform `1px` borders to create an interconnected console surface.
- **Reflow Rules:**
  - **Desktop / Multi-Monitor (>1440px):** 12-column persistent dashboard. Left navigation collapses to an icon rail (56px), central tactical map or feed spans 7–8 columns, auxiliary data drawers occupy remaining columns.
  - **Laptop / Tablet (768px–1439px):** 6-column reflow. Auxiliary telemetry converts to tabbed trays beneath the primary view.
  - **Mobile (<768px):** Single-column stacked stream. Map/radar view pins to top viewport with a fixed 40vh ratio; critical alerts stack chronologically below.

## Elevation & Depth

This system intentionally rejects ambient box shadows, colored lighting spills, and fuzzy blurred backdrop filters. Tactical displays prioritize clean lines and high contrast.

### Depth by Tonal Stacking
1. **Base Floor (`#0b1220`):** Background grid and system viewport frame.
2. **Standard Surface (`#141d33`):** Default level for all metric cards, control groupings, and tabular panels.
3. **Raised Surface (`#1b2642`):** Transient dialogs, popovers, dropdown lists, and hover-state card treatments.

### Boundary Definitions
- **No Drop Shadows:** All elevation differences are demarcated strictly through background color shifting and solid `1px` structural borders (`#233152`).
- **Focus & Selection Rings:** Interacted or focused elements utilize a sharp `1px` inner or outer border of `#38bdf8`, with no outer glow or diffused drop shadow.

## Shapes

The geometric personality is sharp, industrial, and utilitarian. Overly rounded corners and pill-shaped aesthetics compromise compact information density and contradict the operational tone.

- **Base Radius:** `4px` (`0.25rem`) applied to cards, inputs, buttons, and status tags.
- **Nested Radii:** Child elements inside cards (such as inner status blocks or table containers) use `2px` or `0px` where borders converge cleanly.
- **Status Indicator Geometry:** Congestion indicators use sharp square or pill badges with minimal internal padding, never exceeding `4px` corner curvature.

## Components

### Buttons & Trigger Controls
- **Primary Operational Button:** Background `#0284c7`, text `#ffffff`, hover `#38bdf8`, active state `#0369a1`. Border: `1px solid #38bdf8`. Height: `32px` (compact) or `36px` (standard). Border-radius: `4px`. Font: `Geist` 13px weight 500.
- **Secondary / Surface Button:** Background `#1b2642`, text `#e2e8f0`, border `1px solid #233152`, hover border `#38bdf8`.
- **Destructive Button:** Background transparent, text `#ef4444`, border `1px solid #ef4444`, hover background `rgba(239, 68, 68, 0.1)`.

### Cards & Telemetry Containers
- Background: `#141d33`.
- Border: `1px solid #233152`.
- Border Radius: `4px`.
- Header: Fixed height `36px`, border-bottom `1px solid #233152`, padding `0 12px`. Displays the uppercase tracked title in `#94a3b8` alongside a real-time heartbeat or status dot.

### Data Tables & Tabular Feeds
- Header Row: Background `#0b1220`, height `32px`, typography `JetBrains Mono` 11px uppercase tracked, text `#64748b`.
- Data Row: Height `36px` (dense) or `44px` (standard), bottom border `1px solid #233152`. Alternate row zebra-striping is omitted in favor of a subtle hover tint `#1b2642`.
- Numeric Cells: `JetBrains Mono` 13px or 14px, right-aligned, tabular spacing.

### Status Chips & Congestion Badges
- Strict monochrome or status-tinted fill with high-contrast text:
  - **Low:** Background `rgba(16, 185, 129, 0.12)`, text `#10b981`, border `1px solid rgba(16, 185, 129, 0.4)`.
  - **Moderate:** Background `rgba(245, 158, 11, 0.12)`, text `#f59e0b`, border `1px solid rgba(245, 158, 11, 0.4)`.
  - **High:** Background `rgba(249, 115, 22, 0.12)`, text `#f97316`, border `1px solid rgba(249, 115, 22, 0.4)`.
  - **Severe:** Background `rgba(239, 68, 68, 0.15)`, text `#ef4444`, border `1px solid #ef4444`.
- Padding: `2px 6px`. Font: `JetBrains Mono` 11px bold uppercase.

### Inputs & Search Bars
- Background: `#0b1220`.
- Border: `1px solid #233152`.
- Font: `Geist` 14px, placeholder `#475569`.
- Focus State: Border color `#38bdf8`, no box-shadow ring.

### Metric Readout Tiles
- Giant data summary tiles feature the metric value (`display-lg` Geist, 32px or `display-md` 28px) flanked by a directional delta indicator (`JetBrains Mono` 12px) and a micro-sparkline rendered with sharp, non-smoothed vectors (1.5px stroke).