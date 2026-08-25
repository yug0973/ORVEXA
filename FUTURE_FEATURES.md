# ORVEXA — Future Feature Roadmap & Architecture Specifications

This document outlines the proposed professional astrodynamics and space situational awareness (SSA) enhancements planned for future integration into the ORVEXA platform.

---

## 1. 🛰️ Live Real-Time SGP4 Position & Eclipse Tracker

### Overview
Provide real-time instantaneous orbital coordinates and illumination conditions for any selected satellite, calculating subsatellite telemetry dynamically in the frontend or via a high-frequency backend stream.

### Technical Specifications
- **Real-Time SGP4 Propagation:** Compute the instantaneous geocentric/geodetic coordinates:
  - **Latitude & Longitude:** Subsatellite ground point $(\phi(t), \lambda(t))$ updating every second.
  - **Instantaneous Altitude:** $h(t) = \|\mathbf{r}(t)\| - R_{\text{Earth}}$.
  - **Orbital Speed:** $v(t) = \|\mathbf{v}(t)\|$ in both $\text{km/s}$ and $\text{km/h}$.
- **Solar Illumination & Eclipse Duty Cycle:**
  - Calculate the angle between the satellite position vector $\mathbf{r}_{\text{sat}}$ and the Sun vector $\mathbf{r}_{\text{sun}}$.
  - Detect whether the satellite is in:
    - **Full Daylight ($100\%$ illuminated)**
    - **Penumbra (Partial eclipse shadow)**
    - **Umbra (Total eclipse / Earth shadow)**
  - Display power generation estimates based on illumination angle and solar panel orientation.

---

## 2. 📡 Ground Station Pass Prediction & Tracking Windows

### Overview
Calculate upcoming overhead tracking passes and line-of-sight acquisition windows for primary ground station networks (e.g., ISTRAC Bengaluru, Dhruva Hyderabad, NASA DSN, ESA Kiruna, Svalbard Radar).

### Key Features
- **Pass Schedule Table:**
  - **AOS (Acquisition of Signal):** Exact UTC timestamp when elevation exceeds horizon threshold ($\ge 5^\circ$).
  - **TCA / Max Elevation:** Peak elevation angle (e.g., $\text{Max El: } 78.4^\circ$) and azimuth direction.
  - **LOS (Loss of Signal):** Timestamp when satellite sets below tracking horizon.
  - **Contact Duration:** Total communication window in minutes/seconds.
- **Visual Polar Sky Track Radar:**
  - Mini polar projection widget showing the satellite's path across the station's local azimuth/elevation dome ($0^\circ\text{–}360^\circ\text{ Az}, 0^\circ\text{–}90^\circ\text{ El}$).

---

## 3. ☀️ Space Weather Drag & Orbit Sensitivity Profile

### Overview
Directly ingest Aditya-L1 solar observatory metrics to determine the atmospheric drag profile and lifetime decay sensitivity for specific satellites in Low Earth Orbit (LEO).

### Mathematical Model & Metrics
- **Atmospheric Drag Acceleration:**
  $$\mathbf{a}_{\text{drag}} = -\frac{1}{2} \rho(h, F_{10.7}, A_p) \cdot \left(\frac{C_D A}{m}\right) \cdot v_{\text{rel}} \cdot \mathbf{v}_{\text{rel}}$$
- **Real-Time Integration:**
  - **$F_{10.7}$ Solar Flux Sensitivity:** Scaling density variations in the thermosphere based on observed solar radio flux.
  - **$A_p$ Geomagnetic Drag Multiplier:** Dynamic multiplier ($\times 1.0\text{ to }\times 3.5$) applied during active geomagnetic storms or Coronal Mass Ejections (CMEs).
  - **Ballistic Coefficient ($B^*$):** Display drag susceptibility directly from TLE Line 1 with historical drag variation graphs.
  - **Projected Lifetime without Burns:** Estimated orbit decay duration under quiet vs. storm space weather regimes.

---

## 4. 📜 Interactive TLE Ephemeris Inspector & Checksum Verifier

### Overview
A comprehensive Two-Line Element (TLE) inspection and diagnostic tool designed for orbital mechanics operators and space mission teams.

### Features
- **Interactive Syntax Highlighting:**
  - Hovering over individual TLE segments highlights and explains:
    - Line 1: Satellite Catalog Number, Classification, International Designator, Epoch Year/Day, First/Second Time Derivatives of Mean Motion, BSTAR Drag Term, Element Number, Checksum.
    - Line 2: Inclination ($i$), Right Ascension of Ascending Node ($\Omega$), Eccentricity ($e$), Argument of Perigee ($\omega$), Mean Anomaly ($M$), Mean Motion ($n$), Revolution Number at Epoch.
- **Ephemeris Quality & Freshness Assessment:**
  - Real-time epoch age calculation:
    - 🟢 **Fresh ($\le 24\text{ hours}$):** High-precision propagation accuracy.
    - 🟡 **Aging ($24\text{–}72\text{ hours}$):** Moderate accuracy; covariance envelope expanding.
    - 🔴 **Stale ($> 72\text{ hours}$):** Degraded positional certainty; update required.

---

## 5. 🎯 Tactical Mission & Navigation Shortcuts

### Overview
Deep linking actions connecting the Satellite Directory to ORVEXA's other operational consoles.

### Shortcuts
1. **"Track in 3D Live Globe":**
   - 1-click transition to Cesium Orbit Globe with this satellite centered, highlighted, and its 48-hour trajectory pre-pinned.
2. **"Simulate Emergency Avoidance Maneuver":**
   - Auto-fills the satellite's state vector into the Collision Avoidance Maneuver ($\Delta V$) solver on the Conjunction page.
3. **"Ask AI Astrometry Copilot":**
   - Passes satellite telemetry and active hazard matrices directly into Llama 3.2 Copilot for automated threat briefings.
4. **"Generate IN-SPACE Compliance Report":**
   - 1-click generation of collision avoidance filing reports formatted to Indian space regulatory guidelines (IN-SPACE / IS4OM standards).

---

## 6. 🤖 Autonomous Multi-Agent Conjunction Avoidance Swarm

### Overview
Integration with the Agent Swarm subsystem to automatically calculate fuel-optimal collision avoidance burns for high-probability close approaches ($P_c \ge 1.0 \times 10^{-4}$).

### Capabilities
- Proposes along-track (In-Track) or radial $\Delta V$ burns with minimal propellant expenditure.
- Evaluates secondary collision risks for proposed post-maneuver orbits before burn execution.
- Generates downloadable CCSDS Orbit Parameter Message (OPM) text files ready for uplink to the satellite ground station.
