# ORVEXA: Technical Deep Dive & Astrodynamics Cheat Sheet

This document compiles the absolute technical, mathematical, and architectural details of ORVEXA to prepare you for any deep engineering questions from the hackathon judges.

---

## 1. Mathematical Foundations & Astrodynamics Formulas

### 🪐 Keplerian Orbital Elements
A satellite's position in space is described using six Keplerian elements in the Geocentric Equatorial Frame (ECI):
1. **Semi-Major Axis ($a$):** Size of the orbit (km).
2. **Eccentricity ($e$):** Shape of the orbit (circular $e=0$, elliptical $0 < e < 1$).
3. **Inclination ($i$):** Tilt of the orbit plane relative to the Earth's equator (degrees).
4. **Right Ascension of the Ascending Node ($\Omega$):** The angle from the vernal equinox to the ascending node where the satellite crosses the equator from south to north (degrees).
5. **Argument of Perigee ($\omega$):** The angle from the ascending node to the point of closest approach to Earth (perigee) (degrees).
6. **Mean Anomaly ($M$):** Position of the satellite along the orbit relative to perigee, parameterized by time (degrees).

### 🛰️ SGP4 (Simplified General Perturbations 4) Propagation
* **What it is:** An analytical propagation model used to track near-Earth satellites ($Period < 225$ minutes) using Two-Line Element (TLE) datasets.
* **Math details:** It accounts for:
  - Earth's non-spherical shape ($J_2, J_3, J_4$ gravitational harmonics).
  - Atmospheric drag using a simplified power-law model scaled by the satellite's drag coefficient $B^*$ (B-star).
  - Lunar-solar gravitational perturbations.
* **Implementation:** Solved in Python using the `sgp4` and `skyfield` libraries, converting TLE data into Cartesian State Vectors $(\mathbf{r}, \mathbf{v})$ at any epoch $t$.

### ☄️ Chan's Analytical Probability of Collision ($P_c$)
Calculating $P_c$ requires projecting the 3D position uncertainty covariances of both satellites onto the **B-Plane** (Encounter Plane), which is perpendicular to the relative velocity vector $\mathbf{v}_{\text{rel}} = \mathbf{v}_p - \mathbf{v}_s$.
1. **Covariance Projection:**
   $$\Sigma_B = P \Sigma_{3D} P^T$$
   Where $P$ is the projection matrix and $\Sigma_{3D}$ is the combined relative covariance matrix ($\Sigma_p + \Sigma_s$).
2. **Diagonalization:**
   Projected covariance $\Sigma_B$ is diagonalized into principal axes eigenvalues $\sigma_x^2$ and $\sigma_y^2$, oriented at angle $\theta$:
   $$\theta = \frac{1}{2} \arctan\left(\frac{2\sigma_{xy}}{\sigma_x^2 - \sigma_y^2}\right)$$
3. **Mahalanobis Distance ($u$):**
   $$u = \left(\frac{x_m}{\sigma_x}\right)^2 + \left(\frac{y_m}{\sigma_y}\right)^2$$
   Where $(x_m, y_m)$ is the projected relative offset (miss distance) in the diagonalized B-Plane.
4. **Rician Series Integration (Chan's Formula):**
   Instead of integrating the 2D Gaussian probability density numerically, Chan solves it analytically using a converging Rician series with Bessel functions:
   $$P_c = e^{-\frac{v}{2}} \sum_{m=0}^{\infty} \frac{1}{m!} \left(\frac{v}{2}\right)^m I\left(\frac{u}{2}, m\right)$$
   Where $v = (R / \sigma)^2$ ($R$ is the combined Hard Body Radius, e.g. 15m), solved using `scipy.special.ive`.

### 🌀 Atmospheric Drag & Numerical Orbital Decay
For low-altitude satellites under 250 km (reentry candidates), SGP4 becomes highly inaccurate. We switch to a high-fidelity numerical propagator in Python:
* **Drag Acceleration:**
  $$\mathbf{a}_{\text{drag}} = -\frac{1}{2} C_d \frac{A}{m} \rho v_{\text{rel}} \mathbf{v}_{\text{rel}}$$
  Where $C_d$ is the drag coefficient, $A/m$ is the area-to-mass ratio, $v_{\text{rel}}$ is the velocity relative to the atmosphere, and $\rho$ is the atmospheric density.
* **Atmospheric Density ($\rho$):**
  Calculated using a multi-layer exponential scale height model:
  $$\rho(z) = \rho_{\text{ref}} \cdot e^{-\frac{z - z_{\text{ref}}}{H}}$$
  Where $H$ is the scale height. Density is dynamically scaled based on the live NOAA Space Weather $F_{10.7}$ (solar flux) and $A_p$ (geomagnetic index) values. High solar/geomagnetic activity heats and expands the thermosphere, increasing $\rho$ at LEO altitudes by up to 10-fold.
* **Numerical Integration:** Solved using a Runge-Kutta 4th Order (RK4) integrator including $J_2$ oblate perturbations:
  $$\mathbf{a}_{J2} = -\frac{3 G M J_2 R_{\text{earth}}^2}{2 r^5} \left[ \left(1 - \frac{5z^2}{r^2}\right) \mathbf{r} + 2z \mathbf{\hat{k}} \right]$$

### 🎯 Monte Carlo Reentry Landing footprint
To map the landing corridor, the backend runs **100 parallel orbital simulations**.
* We apply random Gaussian perturbations (errors) to:
  1. The drag coefficient ($C_d \pm 15\%$).
  2. The atmospheric density ($\rho \pm 10\%$).
  3. The initial altitude vector ($\mathbf{r} \pm 200\text{ m}$).
* The integration runs until the satellite drops below 80 km altitude (the drag break-up limit). The ECI coordinates at 80 km are converted to Geodetic latitude/longitude, and a convex hull algorithm projects these endpoints as a GeoJSON landing polygon.

### ☀️ Aditya-L1 Solar Physics & CME Propagator
To mitigate satellite loss due to atmospheric drag during major geomagnetic storms, ORVEXA models space weather forecasts using simulated instruments based on India's **Aditya-L1** solar observatory:
- **Telemetry Modelling:** We simulate Soft X-ray (SoLEXS flux, $1-8\text{ \AA}$) and Hard X-ray (HEL1OS counts, $10-150\text{ keV}$) telemetry. The rise phase of the flare is modeled as an exponential build-up:
  $$F(t) = F_0 \cdot e^{\lambda (t - t_0)}$$
- **CME Propagation Speed:** The Coronal Mass Ejection (CME) velocity is calculated based on the flare intensity ($v_{\text{CME}} \in [800, 2200]\text{ km/s}$).
- **CME Transit Progress & ETA:** The transit progress ($d$ in Astronomical Units) and travel duration ($t_{\text{transit}}$ in hours) are calculated as:
  $$d(t) = \frac{v_{\text{CME}} \cdot \Delta t}{1.496 \times 10^8\text{ km}}, \quad t_{\text{transit}} = \frac{1.496 \times 10^8\text{ km}}{v_{\text{CME}} \cdot 3600}$$
- **Drag Scaling:** When the CME arrives, it scales atmospheric drag density indices ($F_{10.7}$ and $A_p$), dynamically multiplying LEO satellite decay rates by up to **3.5x**.

### 🌙 Lunar A* Stereographic Polar Pathfinder
To plan safe paths near the Moon's South Pole ($\text{lat} \in [-90^\circ, -85^\circ]$), we implement a stereographic Cartesian grid to eliminate pole coordinate singularities:
- **Polar Stereographic Projection:**
  $$x = (\text{lat} + 90.0) \cdot \cos(\text{lon}_{\text{rad}})$$
  $$y = (\text{lat} + 90.0) \cdot \sin(\text{lon}_{\text{rad}})$$
- **A* Traversal Cost Matrix:**
  Grid step size is set to $0.08$ units ($\approx 2.4\text{ km}$). The traversal cost multiplier $C(x, y)$ is evaluated as:
  - Inside Crater Center ($d \le R_{\text{crater}}$): $C(x, y) = 20.0$ (High penalty allows path entry if destination is inside).
  - Near Crater Rim ($R_{\text{crater}} < d < 1.3 \cdot R_{\text{crater}}$):
    $$C(x, y) = 1.0 + 15.0 \cdot \left(1.0 - \frac{d - R_{\text{crater}}}{0.3 \cdot R_{\text{crater}}}\right)$$
    This represents steep slope hazards (0 to 30 degrees).
  - Safe Zones: $C(x, y) = 1.0$.

### 🛰️ CCSDS OPM Maneuver Specification
To export simulated maneuver parameters, the system generates standard Consultative Committee for Space Data Systems (CCSDS) Orbit Parameter Message (OPM) v2.0 text documents:
- **Reference Frame:** Coordinates are defined in the True Equator Mean Equinox (TEME) frame for the base state vectors (position $x, y, z$ in km and velocity $v_x, v_y, v_z$ in km/s).
- **Maneuver Local Frame:** The maneuver block uses the local Radial-In-Track-Cross-Track (RIC) reference frame (`MAN_REF_FRAME = RIC`).
- **Maneuver Burn Representation:** The simulated radial burn (delta-V in m/s) is scaled to km/s and stored in the radial field `MAN_DV_1` (e.g. `MAN_DV_1 = 0.015000000` for a 15.0 m/s outward burn). In-track and cross-track delta-V parameters are set to zero.

---

## 2. Database Schema & Spatial PostGIS Architecture

For local testing, the app runs on SQLite. In production (Docker deployment), it scales to **PostgreSQL with the PostGIS spatial extension**.

### Database Tables:
1. **`satellites`**
   - `norad_id` (Integer, Primary Key)
   - `name` (String)
   - `tle_line1` / `tle_line2` (String)
   - `operator` / `type` (String - e.g., SpaceX, ISRO / Payload, Debris)
   - `updated_at` (DateTime)
2. **`conjunction_events`**
   - `id` (Integer, Primary Key)
   - `primary_norad_id` / `secondary_norad_id` (Integer, Foreign Keys)
   - `tca` (DateTime - Time of Closest Approach)
   - `miss_distance` (Float - km)
   - `pc` (Float - Probability of Collision)
   - `covariance_json` (Text - projected $2 \times 2$ covariance matrix)
3. **`reentry_alerts`**
   - `id` (Integer, Primary key)
   - `norad_id` (Integer, Foreign Key)
   - `eta` (DateTime - Estimated Time of Reentry)
   - `decay_rate` (Float - km/day)
   - `survival_pct` (Float - survival fraction during fragmentation)
   - `casualty_probability` (Float - $E_c$ casualty index)
   - `corridor_geom` (**`GEOMETRY(Polygon, 4326)`** under PostGIS)
4. **`compliance_filings`**
   - `id` (Integer, Primary Key)
   - `conjunction_id` (Integer, Foreign Key)
   - `status` (String - Submitted, Approved)
   - `pdf_path` (String)
   - `delta_v_radial` / `delta_v_intrack` / `delta_v_crosstrack` (Float)
   - `created_at` (DateTime)

### Spatial Indexes (PostGIS optimization):
```sql
-- Speeds up spatial queries (e.g. checking if a reentry corridor intersects an airspace boundary)
CREATE INDEX idx_reentry_corridors_spatial ON reentry_alerts USING GIST(corridor_geom);
```
* **How it works:** GIST (Generalized Search Tree) indexes the bounding boxes (MBR) of the polygons. Bounding box intersection checks are $O(\log N)$, avoiding expensive coordinate-by-coordinate comparisons on the entire database.

---

## 3. FastAPI API Contracts & WebSocket Protocols

### REST Endpoints
* `GET /api/satellites/czml?limit=X`
  * Returns the orbit positions of the top X satellites formatted as a Cesium-compatible CZML stream.
* `GET /api/conjunctions`
  * Returns all upcoming close approach conjunction events.
* `GET /api/conjunctions/{id}`
  * Returns high-fidelity details, including relative states and the $2\times2$ covariance matrix.
* `GET /api/reentry`
  * Returns all satellites decaying under the 250 km threshold.
* `GET /api/reentry/{id}/map`
  * Returns the GeoJSON landing corridor corridor polygon for Leaflet mapping.
* `GET /api/solar`
  * Returns live planetary solar flux ($F_{10.7}$) and geomagnetic ($A_p$) indices.
* `GET /api/compliance`
  * Returns the list of submitted regulatory filings.
* `GET /api/compliance/download/{id}`
  * Downloads the generated safety PDF report.
* `GET /api/solar/aditya-l1`
  * Streams real-time simulated spectrograph flux telemetry and CME transit status.
* `POST /api/solar/trigger-flare/{flare_class}`
  * Triggers a manual solar flare simulation (C, M, or X-Class) for demonstrations.
* `POST /api/solar/clear-flare`
  * Clears any active solar flare simulations, returning weather to baseline.
* `POST /api/copilot/chat`
  * RAG chat endpoint: parses text, queries DB context, and executes local Llama 3.2 calls.
* `GET /api/lunar/hazards`
  * Returns lunar south pole crater coordinates, radii, and preset mission paths.
* `POST /api/lunar/pathfind`
  * Solves and returns A* waypoints and path statistics (distance, max slope, safety index).
* `POST /api/lunar/propagate`
  * Propagates spacecraft trajectory in Circular Restricted 3-Body Problem (CR3BP) space using RK4 integration.
* `POST /api/refinement/fit`
  * Performs Bayesian orbit determination covariance trace reduction using custom ground station ranging observations.
* `GET /api/negotiations/{conjunction_id}`
  * Retrieves maneuver proposals and negotiation status logs for a conjunction.
* `POST /api/negotiations/propose`
  * Submits a collision avoidance maneuver burn proposal using Clohessy-Wiltshire state-transition matrices.
* `POST /api/negotiations/resolve`
  * Resolves (approves or rejects) a maneuver burn proposal.
* `POST /api/deorbit/audit`
  * Conducts a 5-year orbit-averaged semi-analytical deorbit audit.

### Swarm WebSocket Pipeline (`ws://localhost:8000/api/ws/swarm/run`)
Triggers the multi-agent swarm compliance filing. Pushes live JSON event frames to the client:
```json
// Ingestion Node Frame
{ "step": 1, "status": "active", "message": "Ingesting TLE orbital states & live NOAA solar flux..." }
// Astrodynamics Node Frame
{ "step": 2, "status": "active", "message": "Evaluating relative orbits and B-Plane offsets..." }
// Risk Assessment Frame
{ "step": 3, "status": "active", "message": "Collision Probability calculated: 2.4e-4 (HIGH)" }
// Legal & Policy Frame
{ "step": 4, "status": "active", "message": "Drafting regulatory justifications matching IADC policies..." }
// Mitigation Planner Frame
{ "step": 5, "status": "active", "message": "Calculating delta-V burn vectors: Radial=-12m/s..." }
// Filing Node Frame
{ "step": 6, "status": "completed", "filing_id": 1, "message": "PDF Report generated. Database entry log committed." }
```

---

## 4. Local LLM Generation & Fallback Fail-Safes

* **Local LLM Engine:** Runs a local instance of **Llama 3.2** via Ollama API (`http://localhost:11434/api/generate`).
* **Generation Parameters:**
  - `model`: `"llama3.2"`
  - `prompt`: Injects TLE positions, miss distance, Pc values, and maneuver delta-V vectors.
  - `options`: `{ "temperature": 0.2 }`. A low temperature ensures strict, non-creative, fact-based professional legal wording for the compliance brief.
* **Fail-Safe Mechanism:** If Ollama is offline or timed out, the backend immediately catches the exception (`requests.exceptions.RequestException`) and fires a fallback parser using a string builder template containing formal astrodynamics terminology. This ensures a valid compliance PDF is generated even if the AI server crashes.
* **Copilot RAG Fallback:** Similarly, in the chat router, if the local LLM is unreachable, the system catches the exception and runs a structured database parser. It prints a formatted Markdown report listing matched satellite coordinates, TLE elements, close approach collision probabilities, and active space weather indices, preserving operational telemetry visibility.

---

## 5. Frontend Dynamic Code-Splitting Structure

To prevent long loading times, we split heavy libraries into separate dynamic chunks loaded asynchronously when the router mounts a specific view.

```typescript
// App.tsx Router dynamic chunk definition
const OrbitMapPage = React.lazy(() => import('./pages/OrbitMapPage').then(module => ({ default: module.OrbitMapPage })));
const ReentryPage = React.lazy(() => import('./pages/ReentryPage').then(module => ({ default: module.ReentryPage })));
```

* **Vite build chunking map:**
  - `index-[hash].js` (Core React/Tailwind/UI logic - 203 kB)
  - `OrbitMapPage-[hash].js` (Contains CesiumJS / Resium wrappers - ~500 kB, loaded only when viewing map)
  - `ReentryPage-[hash].js` (Contains Leaflet map components - ~170 kB, loaded only when viewing reentry list)
  - `CartesianChart-[hash].js` (Contains Recharts graphing library - ~340 kB, loaded on solar weather and decay pages)
* **Suspense Fallback UI:** A pulsing circular loader appears during chunk fetch, preventing blank frames during transition.
