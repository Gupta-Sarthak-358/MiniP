# Product Requirements Document (PRD) & Operational Brief
## Real-Time Traffic & Parking Operations Console (Tactical ATC Interface)

---

### Executive Summary & Metadata
- **Product Title:** Real-Time Traffic & Parking Forecasting & Dispatch Console
- **System Codename:** SINPA / ATC Tactical Telemetry Console
- **Target Release:** v2.4-tactical
- **Platform Scope:** Responsive Web (Optimized for Desktop 1440px+ Control Room Monitors and Mobile 390px iOS/Android Field Dispatch Handhelds)
- **Primary Stakeholders:** Municipal Traffic Authorities, Parking System Operators, Transit Dispatchers, Sensor Network Engineers

---

## 1. Problem Statement & Operational Objective

### 1.1 The Problem
Existing municipal monitoring tools present disconnected, equal-weight telemetry cards with no clear operational hierarchy. Critical road hazards, overpass bottlenecks, and severe parking attrition are frequently buried beneath raw tables or delayed batch metrics. Furthermore, legacy systems present raw machine learning forecasts without calibrated uncertainty bounds (confidence intervals) or feature explainability (SHAP attribution), creating operator skepticism and hesitation during high-density surge events (e.g., stadium matches, severe weather, mega-sale influx).

### 1.2 The Objective
The Tactical Operations Console solves the question operators face every 5 seconds:
> **"What is happening across our city sectors right now, what will happen in the next 15–60 minutes, what factors are driving the surge, and what concrete routing actions should I take immediately?"**

The interface adheres to an **"Air-Traffic-Control (ATC) Calm"** philosophy: high data density, zero decorative visual noise (no glassmorphism, glowing ambient blobs, or non-functional gradients), instantaneous scannability, strict WCAG 2.1 AA contrast compliance, and sub-second decision support.

---

## 2. Personas & Core User Journeys

### 2.1 Primary Operator Personas
1. **Central Traffic Controller (Desktop Operations Room, 1440px–4K):**
   - Monitors multi-sector telemetry across 5 core municipal zones and external sensor benchmarks.
   - Evaluates corridor throughput curves, ensemble surge forecasts, and conformal uncertainty envelopes to enact regional arterial reroutes.
2. **Field Tactical Dispatcher / Transit Supervisor (Mobile Handheld, 390px):**
   - Operates on-the-go at stadiums, major parking garages, or transit hubs.
   - Requires one-thumb accessible controls ($\ge 44\text{px}$ touch targets), prioritized hazard triage, rapid +15m/+1h time stepping, and 1-tap dispatch triggers.
3. **ML Telemetry & Sensor Engineer:**
   - Audits model drift (MAE divergence against baseline thresholds), inspects walk-forward conformal calibration coverage (target: $\ge 0.90$), and verifies live sensor replay against historical baselines (e.g., UCI Birmingham feed).

### 2.2 Core Operational Workflows
- **Hazard Triage Workflow:** Operator receives live 5s heartbeat $\to$ Top hazard pipeline flags critical overpass obstruction (`+14m delay forecast`) $\to$ Operator reviews 1-click ATC routing recommendation $\to$ Deploys variable message signs (VMS) to shift incoming vehicles to adjacent under-utilized facilities (North Arena Garage).
- **Surge Horizon Forecasting Workflow:** Operator inspects +30m projection pillar $\to$ Observes available bays dropping towards critical deficit threshold ($<100$ bays) with $90\%$ conformal envelope $[172 - 198]$ bays $\to$ Cross-references SHAP attribution to identify whether surge is driven by stadium arrival ($+0.21$) or retail flash-sales ($+0.18$).

---

## 3. System Architecture & Content Inventory

The system must deliver 10 mandatory operational content modules structured across 6 layout tiers:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. COMMAND STRIP (Sticky): Title · UTC Clock · 5s Heartbeat · Zone Selector · Step Controls · Demo Sim │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. OPERATIONAL HAZARD PIPELINE: Collapsible severity-ranked alert cards (Critical > Drift > Surge)     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. HERO STATE STRIP (3 Pillars): Tactical Load · Sector Reserve · +30m Conformal Projection            │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│ 4. LEFT COLUMN (Telemetry & Forensic Time-Series) │ 5. RIGHT COLUMN (Decision Support & Routing)│
│  - Corridor Throughput (Observed vs Ensemble)     │  - SHAP Factor Explainability Bars         │
│  - Parking Attrition (Trajectory + 90% Conformal) │  - ATC Routing Optimization Top Pick       │
│  - Horizon Calibrated Telemetry Matrix (Tabular)  │  - Ranked Facility Capacity Breakdown      │
│                                                   │  - 5-Zone Saturation Grid Heatmap          │
│                                                   │  - Real-Zone Sensor Replay (Birmingham)    │
├───────────────────────────────────────────┴────────────────────────────────────────────┤
│ 6. FOOTER AUDIT TRAIL: Data provenance (UCI Birmingham UK OGL) · Calibration spec · API links          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Module Specifications:
1. **Unified Command Bar:**
   - Live UTC clock with pulsing $5\text{s}$ heartbeat dot (`ops-heartbeat`).
   - Sector selector: All Sectors, Mall, Stadium Hub, Central Station, Commercial Office, Residential Node.
   - Simulation time-travel triggers (`+15M`, `+1H`), Auto-Sync toggle, and instant `SIM INJECT` incident emulator.
2. **Prioritized Hazard Pipeline:**
   - Strict severity sort: **Critical Emergency** (Crimson `#ef4444`, direct detour routing CTA) $\to$ **Event Horizon** (Indigo `#818cf8`, pre-stage signage CTA) $\to$ **Model Drift** (Amber `#f59e0b`, inductive loop recalibration CTA).
   - Collapsible drawer state preserving viewport density when resolved.
3. **3-Pillar Operational Hero Strip:**
   - **Now Tactical Load:** Density in $\text{veh/km}^2$, mean travel velocity, network saturation percentage, and double-coded congestion status badge.
   - **Sector Reserve:** Available vs. Total bay count, graphic capacity fill bar, and live weather telemetry (temperature + condition).
   - **+30m Projection:** Predictive available bay forecast, expected vehicle density, and conformal $90\%$ prediction interval $[lo - hi]$.
   - **Context Pipeline Ribbon:** Active operational flags (Mega-Sale Day intensity, PM rush incoming, normal rainfall drift).
4. **Dual Time-Series Forensics:**
   - **Corridor Flow & 60m Horizon:** Historical throughput ($T-60$ to $T-0$) with continuous curve and dotted forward ensemble forecast meeting the $3{,}200\text{ veh/hr}$ critical capacity threshold.
   - **Parking Attrition Trajectory:** Median forecast attrition curve enveloped by an upper/lower $90\%$ conformal prediction interval band.
5. **Accessible Telemetry Data Table:**
   - Tabular-numbers matrix (`tabular-nums`) displaying step intervals ($T-0, +15m, +30m, +45m, +60m$) with vehicle counts, confidence bounds, and walk-forward empirical validation coverage ($0.90$).
6. **Decision Support & Explainability Engine:**
   - **SHAP Attribution Breakdown:** 6 feature bars showing exact operational log-odds delta (Event impact, Sale promotion, PM rush profile, Overpass incident, Weather friction, Holiday attenuation).
   - **ATC Routing Dispatch:** Algorithmic recommendation engine identifying the optimal destination facility with free bay count and drive-time delta, backed by ranked facility listings.
   - **5-Zone Saturation Grid:** Rapid percentage dials for all monitored city nodes.
   - **Real-Zone Sensor Replay:** Historical replay and persistence baseline comparison using the open municipal feed (UCI Birmingham Park-and-Ride).

---

## 4. Technical Specifications & API Contracts

### 4.1 Endpoint Schema & Contracts
All real-time endpoints communicate via JSON over HTTPS/WSS at 5-second polling intervals or push-based websocket updates.

```typescript
// 1. GET /api/current-status?location={zone_id}
interface CurrentStatusResponse {
  zone_id: string;
  vehicle_count: number;         // e.g. 310
  avg_speed_kmh: number;         // e.g. 22.4
  occupancy_pct: number;         // e.g. 78.0
  available_bays: number;        // e.g. 220
  total_capacity: number;        // e.g. 1000
  weather_condition: string;     // "cloudy"
  temperature_c: number;         // 29
  congestion_level: 'Low' | 'Moderate' | 'High' | 'Severe';
  flags: {
    is_sale_day: boolean;
    sale_intensity: number;      // 1 - 5
    is_event_day: boolean;
    is_incident: boolean;
  };
  last_updated: string;          // ISO UTC
}

// 2. GET /api/prediction?location={zone_id}&horizon=60
interface PredictionResponse {
  zone_id: string;
  interval_method: "conformal-q90";
  calibration_coverage: number;  // 0.90
  predictions: Array<{
    horizon_min: 0 | 15 | 30 | 45 | 60;
    available_bays: number;
    ci_lower: number;
    ci_upper: number;
    vehicle_density: number;
    congestion_level: 'Low' | 'Moderate' | 'High' | 'Severe';
  }>;
  critical_breach_min: number | null; // e.g. 45 or null
}

// 3. GET /api/explain?location={zone_id}&horizon=30
interface ExplainabilityResponse {
  model_id: string;              // "XGB-v4.1"
  base_value: number;
  factors: Array<{
    feature_name: string;        // "event_impact" | "sale_intensity" | ...
    label: string;
    importance_weight: number;   // +0.21
    raw_value: string | number;
  }>;
}

// 4. GET /api/recommendation?location={zone_id}
interface RecommendationResponse {
  top_recommendation: {
    target_facility: string;     // "North Arena Garage"
    free_bays: number;           // 117
    signal_delay_min: number;    // 3
    action_type: "DEPLOY_VMS" | "REROUTE_FLOW";
  };
  rankings: Array<{
    facility_name: string;
    available_bays: number;
    total_capacity: number;
    status: 'OPTIMAL' | 'BALANCED' | 'CONGESTED' | 'CRITICAL' | 'SATURATED';
  }>;
}
```

---

## 5. Non-Functional Requirements & Design Principles

### 5.1 Design System & Token Compliance
- **Color Palettes:** Zero gloss, zero translucent blur. Surfaces: `#0b1220` (canvas), `#141d33` (cards), `#1b2642` (raised/active).
- **Double-Coded Status:** Congestion levels must never rely on color alone. Each state must combine explicit uppercase text (`LOW`, `MODERATE`, `HIGH`, `SEVERE`) with WCAG-audited contrasting background and border pairs.
- **Strict 8-pt Spatial Rhythm:** Spacing restricted strictly to `4px, 8px, 12px, 16px, 24px, 32px, 48px`.
- **Motion Bounds:** Animate `transform` and `opacity` only. Micro-interactions under $160\text{ms}$; panel animations under $240\text{ms}$. Full compliance with `@media (prefers-reduced-motion: reduce)`.

### 5.2 Accessibility & Ergonomics (WCAG 2.1 AA)
- Semantic HTML5 landmark structure (`<header role="banner">`, `<main id="main-content">`, `<aside aria-label="Decision Support">`, `<footer>`).
- Skip navigation link to bypass sticky command headers.
- Tabular text alternatives accompanying all time-series chart canvases.
- Visible high-contrast focus rings (`outline: 2px solid #38bdf8; outline-offset: 2px;`).
- Mobile touch targets guaranteed $\ge 44\text{px} \times 44\text{px}$.

---

## 6. Implementation Roadmap & Milestones

| Milestone | Deliverables | Status |
|---|---|---|
| **Phase 1: Visual Design & System Specs** | Desktop 1440px target, Mobile 390px layout, complete Token Sheet & Responsive Component CSS Specs | **Completed** |
| **Phase 2: Frontend Client Integration** | HTML5/Vanilla implementation, Chart.js dual-axis canvases, sticky command bar state machine | In Progress |
| **Phase 3: Live API & Telemetry Wiring** | REST & WebSocket hookup for live 5s heartbeat, real-time alert triage queue, SHAP weight parsing | Next |
| **Phase 4: Field Validation & Simulation** | Operator user testing, incident injection dry runs, and latency benchmarking under packet loss | Scheduled |
