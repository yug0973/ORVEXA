# 🛰️ ORVEXA — Ultra-Detailed Hinglish Technical & Operations Handbook
> **Event:** Smart Space Hackathon (22 August 2026)  
> **Domain:** Space Situational Awareness (SSA), Autonomous Space Traffic Management (STM) & IN-SPACe Regulatory Compliance  
> **Audience:** Hackathon Jury, Space Engineers, Technical Evaluators, and Core Developers

---

## 📑 COMPREHENSIVE TABLE OF CONTENTS
1. [Executive Summary & Problem Statement (ORVEXA Kya Hai aur Kyun Bana)](#1-executive-summary--problem-statement)
2. [Global Navigation, Topbar & Entry Portal (Har Ek Button Ka Kaam)](#2-global-navigation-topbar--entry-portal)
3. [Page 1: 3D Orbit Globe & Fleet Tracking (`OrbitMapPage.tsx` & `OrbitGlobe.tsx`)](#3-page-1-3d-orbit-globe--fleet-tracking)
   - Physics & SGP4 Orbital Propagation Math
   - State Vectors & ECI Coordinate Transformations
   - Every Button, Toggle, Slider & Drawer Action
   - Thruster Burn Simulator & Hohmann Transfer $\Delta V$
   - CCSDS 502.0-B-2 OPM Exporter
   - 3D Kinetic Hypervelocity Collision Simulation
4. [Page 2: Conjunction Hazards & B-Plane Astrodynamics (`ConjunctionPage.tsx`)](#4-page-2-conjunction-hazards--b-plane-astrodynamics)
   - Spatial KD-Tree 3D Nearest Neighbor Search ($O(N \log N)$)
   - TCA (Time of Closest Approach) Numerical Root-Finding
   - Foster-Elrod 2D Collision Probability ($P_c$) Algorithm
   - Interactive 2D B-Plane Plotter (Canvas / SVG)
   - Autonomous Maneuver Allocation Wheel (Game-Theoretic De-confliction)
   - Every Button, Card Click, and State Machine Action
5. [Page 3: Atmospheric Decay, Reentry & ISRO Aditya-L1 Solar Weather (`ReentryPage.tsx`)](#5-page-3-atmospheric-decay-reentry--isro-aditya-l1-solar-weather)
   - King-Hele Atmospheric Drag & Perigee Decay Equations
   - Solar Extreme Ultraviolet (EUV) & Geomagnetic Storm Coupling ($F_{10.7}$ & $A_p$)
   - 50-Run Monte Carlo Stochastic Dispersion Landing Corridor
   - Spacecraft Demise Aerothermal Ablation & Ground Casualty Expectation ($E_c$)
   - Every Button, Tab, and Map Interaction
6. [Page 4: Regulatory Compliance & Multi-Agent Swarm (`CompliancePage.tsx`)](#6-page-4-regulatory-compliance--multi-agent-swarm)
   - 5-Agent Autonomous Swarm Architecture & WebSocket Stream
   - Manual & Automated IN-SPACe / IADC Legal Filing Generation
   - ReportLab PDF Compilation Engine & Download Vault
   - Every Button, Form Field, and Swarm Execution Step
7. [Air-Gapped AI Astrometry Copilot (`CopilotDrawer.tsx` & `copilot.py`)](#7-air-gapped-ai-astrometry-copilot)
   - 100% Local Quantized Llama 3.2 via Ollama (Port 11434)
   - Dynamic RAG Telemetry Context Injection & Real-Time UTC Synchronization
   - Dual-Mode Architecture & Offline Fallback Table
8. [Judges Q&A Defense Script (Top 10 Technical Questions & Winning Answers)](#8-judges-qa-defense-script)
9. [2-Minute Winning Elevator Pitch (Exact Stage Script)](#9-2-minute-winning-elevator-pitch)

---

## 1. Executive Summary & Problem Statement

### 🚀 Space Problem Kya Hai? (In Simple Hinglish)
Aaj Earth ke low orbit (LEO - 200 km se 2,000 km) mein **30,000 se zyada trackable objects** ghoom rahe hain: active satellites, dead rocket stages, aur paint flecks se lekar spent fuel tanks tak.
- Har ek object **28,000 km/h (7.8 km/s)** ki hypersonic speed se travel karta hai.
- Is speed par ek **1 cm ka aluminium piece** bhi ek military hand grenade ke barabar kinetic energy release karta hai.
- Agar do satellites takrayi, toh chain reaction shuru ho jayegi jise **Kessler Syndrome** kehte hain — isse poori orbit hazaron saal ke liye unusable ho jayegi.

### 🛡️ ORVEXA Kya Solution Deta Hai?
ORVEXA India ka comprehensive **Autonomous Space Traffic Management (STM) & Space Situational Awareness (SSA)** platform hai jo:
1. **Predict Karta Hai:** Live satellite TLEs se 48-hour forward collision trajectories aur close encounters calculate karta hai.
2. **Quantify Karta Hai:** Standard Foster-Elrod probability algorithms se exact **Collision Probability ($P_c$)** nikaalta hai.
3. **Coupled Space Weather:** ISRO ke **Aditya-L1** solar coronagraph data aur NOAA SWPC data se LEO atmospheric drag decay aur reentry risk adjust karta hai.
4. **Automate Karta Hai:** Multi-agent autonomous swarm se commercial operators ke beech coordination karwata hai aur official **IN-SPACe / IADC legal compliance documents (PDF)** generate karta hai.
5. **100% Defense Secure:** Air-gapped **Local Llama 3.2** AI Copilot ke sath zero cloud telemetry leakage guarantee karta hai.

---

## 2. Global Navigation, Topbar & Entry Portal

### 🌌 A. Entry Portal (`EntryPortal.tsx`)
- **`LAUNCH SSA MISSION DECK` Button:**
  - *Action:* WebGL ambient particle canvas se transition trigger karta hai, application audio synthesize karta hai, aur main mission dashboard par enter karta hai.
- **Sound Toggle Button (`Volume2` / `VolumeX` Icon):**
  - *Action:* Web Audio API generated sci-fi ambient telemetry sound effects ko mute/unmute karta hai.
- **Live HUD Readouts:**
  - *Active Orbits HUD:* Database mein loaded active objects count dikhata hai.
  - *Spatial Bubble HUD:* 10.0 km screening boundary radius dikhata hai.
  - *AI Core Readiness:* Local Ollama / Astrometry copilot connection verify karta hai.

### 🛰️ B. Topbar Header (`Topbar.tsx`)
- **System Status Badge (`LIVE LEO TELEMETRY — SGP4 PROPAGATOR`):**
  - *Action:* Backend SGP4 stream connection state aur real-time orbital time synchronization status display karta hai.
- **Tracked Satellite Count Badge (`104 SATELLITES TRACKED`):**
  - *Action:* Monitored active payloads, rocket bodies, aur debris fragments ka live count display karta hai.
- **Aditya-L1 / NOAA Weather Pill (`F10.7 | Ap | Drag Scaler`):**
  - *Action:* Live solar radio flux ($F_{10.7}$ in SFU), geomagnetic storm planetary index ($A_p$), aur thermospheric drag multiplier live stream karta hai.
- **`TRIGGER X-CLASS SOLAR FLARE` / `CLEAR SOLAR FLARE` Button:**
  - *Action:* Backend endpoint `POST /api/solar/trigger-flare/X` ko call karta hai.
  - *Behind the Scenes:* Real-time mein X-class flare inject karta hai, WebSockets par alert broadcast karta hai, atmospheric drag 3.5x spike karta hai, aur sabhi decaying objects ki ETA dynamically recalculate karta hai. Dubara click karne par `/api/solar/clear-flare` se quiet baseline restore ho jaati hai.
- **`DATA SOURCES & ACCURACY` Button:**
  - *Action:* Modal popup open karta hai jo CelesTrak, NOAA SWPC, ISRO Aditya-L1 coronagraph, aur numerical error budgets explain karta hai.
- **`ASTROMETRY COPILOT` Button:**
  - *Action:* Slide-out local AI assistant drawer ko screen ke right side se toggle karta hai.

### 🧭 C. Bottom Navigation Sidebar (`Sidebar.tsx`)
Exactly 4 core pillars switch karta hai:
1. `3D ORBIT MAP` (Globe Icon) &rarr; Page 1
2. `CONJUNCTION HAZARDS` (AlertTriangle Icon with critical alert count badge) &rarr; Page 2
3. `DECAY & REENTRY` (Flame / Activity Icon with active decay count) &rarr; Page 3
4. `COMPLIANCE & SWARM` (ShieldCheck / FileText Icon) &rarr; Page 4

---

## 3. Page 1: 3D Orbit Globe & Fleet Tracking (`OrbitMapPage.tsx` & `OrbitGlobe.tsx`)

### 🧠 A. Physics & Astrodynamics Math Behind Page 1
1. **TLE Ingestion & SGP4 Theory:**
   - Har satellite ka raw input **TLE (Two-Line Element)** set hota hai:
     ```
     1 25544U 98067A   26231.54166667  .00016717  00000-0  10270-3 0  9001
     2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49815043423402
     ```
   - **SGP4 (Simplified General Perturbations-4)** analytical propagator use hota hai jo classical Kepler elements ($a, e, i, \Omega, \omega, M$) ko propagate karta hai including Earth oblateness perturbations ($J_2, J_3, J_4$) aur atmospheric drag ($B^*$).

2. **State Vectors in ECI (EME2000) Frame:**
   - Output cartesian coordinate vector hota hai:
     $$\vec{r} = [X, Y, Z]^T \text{ (km)}, \quad \vec{v} = [V_x, V_y, V_z]^T \text{ (km/s)}$$
   - Earth-Centered Inertial (ECI) non-rotating frame use hota hai taaki orbital mechanics ke Newton's Laws correctly apply hon.

3. **Orbital Energy & Velocity Formula:**
   $$v = \sqrt{\mu \left(\frac{2}{r} - \frac{1}{a}\right)}$$
   - $\mu = 398,600.4418 \text{ km}^3/\text{s}^2$ (Earth standard gravitational parameter).
   - LEO mein orbital altitude $h \approx 400\text{ km} \implies r = R_E + h = 6778\text{ km}$, giving orbital speed $\approx 7.67\text{ km/s}$ and period $T \approx 92.5\text{ minutes}$.

4. **Hohmann Transfer Delta-V Math:**
   $$\Delta v_1 = \sqrt{\frac{\mu}{r_1}} \left( \sqrt{\frac{2 r_2}{r_1 + r_2}} - 1 \right)$$
   - Burn slider par delta-V lagane se orbit raise/lower transition calculate hokar green/orange trajectory render hoti hai.

### 🖥️ B. Every Button & Control on Page 1:
- **Camera Reset Button (Home / Compass Icon):** Camera ko smooth 1.5s animation se global orbit overview par fly-to karta hai.
- **Earth Style Selector Wheels (`Satellite` | `Dark` | `Natural`):**
  - `Satellite`: High-res Esri photorealistic daytime satellite imagery.
  - `Dark`: NASA VIIRS Black Marble night lights aesthetic.
  - `Natural`: World Street & Topographical map.
- **Time Multiplier Speed Controls (`1x, 10x, 60x, 300x`):** Cesium clock multiplier accelerate karta hai taaki orbit cycles fast-forward mein visualize hon.
- **Satellite Search Input & Autocomplete:** Name (`ISS`, `CARTOSAT`) ya NORAD ID (`25544`) search karke camera seedha us satellite par lock karta hai.
- **`Show Ground Stations` Toggle:** 4 Deep Space Radars (Svalbard, ISRO Bengaluru ISTRAC, Goldstone NASA, Hartebeesthoek) ke 800 km sensor coverage cones render karta hai.
- **`Show Hazard Shells` Toggle:** 700–900 km LEO Polar Debris Shell aur 35,786 km GEO Belt hollow 3D spheres render karta hai.
- **`3D Models Toggle`:** GLB realistic 3D mesh rendering vs 2D point billboard switch karta hai.
- **`Self-Serve TLE Import` Drawer:** Custom satellite name + TLE Line 1 + Line 2 enter karke **`IMPORT & SCREEN SATELLITE`** dabane par backend `/api/satellites/import` instant screening run karta hai.
- **Satellite Telemetry Drawer (Right Panel):**
  - Shows Semi-Major Axis ($a$), Eccentricity ($e$), Inclination ($i$), Period ($T$), Apogee, Perigee, Speed.
  - **`Pin Trajectory Line` Button:** Selected satellite ka continuous 3D orbital path Cesium `PolylineGraphics` se lock karta hai.
  - **Maneuver Delta-V Slider (-10 to +10 m/s):** Live computes post-burn Hohmann transfer trajectory and draws burn line.
  - **`Export CCSDS OPM` Button:** Appears when $\Delta V \neq 0$. Downloads official **CCSDS 502.0-B-2 Orbit Parameter Message** text file for mission uplinks.
  - **`View Conjunction Hazards` Button:** Page 2 par transition karta hai is satellite ke close approach events pre-selected ke sath.
- **`START CINEMATIC SIMULATION` Button (`CollisionSimulationPanel.tsx`):** 3-phase automated collision simulation run karta hai (Wide convergence &rarr; Close approach &rarr; Kinetic breakup with GPU debris blast).

---

## 4. Page 2: Conjunction Hazards & B-Plane Astrodynamics (`ConjunctionPage.tsx`)

### 🧠 A. Physics, Math & Foster-Elrod Algorithm
1. **Spatial KD-Tree Screening ($O(N \log N)$):**
   - 10,000 satellites ke brute-force checking ($50,000,000$ distance checks) ko 3D KD-Tree 10.0 km threshold filter se milliseconds mein reduce karta hai.

2. **Time of Closest Approach (TCA):**
   - Relative distance squared: $D(t)^2 = \|\vec{r}_p(t) - \vec{r}_s(t)\|^2$.
   - Minimum condition:
     $$\frac{d}{dt} D(t)^2 = 0 \implies \vec{r}_{rel}(t_{TCA}) \cdot \vec{v}_{rel}(t_{TCA}) = 0$$

3. **Foster-Elrod 2D Collision Probability ($P_c$):**
   - Relative motion frame $(R, T, N)$ mein primary aur secondary positional covariance matrices add hoti hain: $\mathbf{C} = \mathbf{C}_p + \mathbf{C}_s$.
   - Covariance ko relative velocity $\vec{v}_{rel}$ ke perpendicular plane (**B-Plane / Encounter Plane**) par project kiya jaata hai:
     $$P_c = \iint_{x^2+y^2 \le R_{HBR}^2} \frac{1}{2\pi \sigma_\xi \sigma_\zeta \sqrt{1-\rho^2}} \exp\left(-\frac{1}{2(1-\rho^2)}\left[\frac{(x-x_0)^2}{\sigma_\xi^2} - \frac{2\rho(x-x_0)(y-y_0)}{\sigma_\xi \sigma_\zeta} + \frac{(y-y_0)^2}{\sigma_\zeta^2}\right]\right) dx dy$$
   - Jahan $R_{HBR} = R_1 + R_2$ (Combined Hard Body Radius), aur $(\sigma_\xi, \sigma_\zeta, \rho)$ B-Plane covariance parameters hain.

### 🚦 B. Risk Thresholds (Judges Defense):
| Risk Level | Collision Probability ($P_c$) | Action Required |
|---|---|---|
| **CRITICAL** | $P_c \ge 1.0 \times 10^{-4}$ (1 in 10,000) | **Mandatory Collision Avoidance Maneuver (CAM) + IN-SPACe Filing** |
| **WARNING** | $1.0 \times 10^{-6} \le P_c < 1.0 \times 10^{-4}$ | High Alert — Radar updates & thruster readiness |
| **NOMINAL** | $P_c < 1.0 \times 10^{-6}$ | Safe corridor — Routine tracking |

### 🖥️ C. Every Button & Action on Page 2:
- **Conjunction Hazard Cards (Left List):** Primary vs Secondary name, TCA countdown, Miss Distance, and $P_c$ Probability. Click karne par us event ka B-Plane analysis load hota hai.
- **Filter Tabs (`ALL`, `CRITICAL (Pc >= 1e-4)`, `WARNING`):** Filters cards by risk severity.
- **2D Interactive B-Plane Plotter (Canvas):** Encounter plane $(\xi, \zeta)$ par $1\sigma, 2\sigma, 3\sigma$ covariance ellipses, HBR circle, aur miss distance vector render karta hai.
- **Maneuver Allocation Wheel (`OptionWheel.tsx`):** Game-theoretic de-confliction slider jo Primary vs Secondary operator ke beech fuel-optimal burn share ($\Delta V_R, \Delta V_I, \Delta V_C$) allot karta hai.
- **`PROPOSE MANEUVER PLAN` Button:** Backend `/api/compliance/negotiate` par coordinated maneuver plan propose karta hai.
- **`APPROVE & EXECUTE MANEUVER` Button:** Simulated clearance execute karke post-burn miss distance $>5.0\text{ km}$ verify karta hai.
- **`INITIATE REGULATORY FILING` Button:** Seedha Page 4 par le jaata hai pre-filled event parameters ke sath.

---

## 5. Page 3: Atmospheric Decay, Reentry & Aditya-L1 Solar Weather (`ReentryPage.tsx`)

### 🧠 A. Physics, Equations & Solar Coupling
1. **King-Hele Orbital Decay Equation:**
   $$\frac{da}{dt} = -2\pi \left(\frac{C_D A}{m}\right) \rho_0 a^2 \exp\left(-\frac{a(1-e) - R_E}{H}\right)$$
   - $C_D \approx 2.2$ (Hypersonic drag coefficient).
   - $A/m$: Spacecraft area-to-mass ratio $(\text{m}^2/\text{kg})$.
   - $\rho_0$: Thermospheric neutral density.
   - $H \approx 50-80\text{ km}$: Atmospheric scale height.

2. **Aditya-L1 Space Weather Drag Scaler:**
   $$\text{Drag Scaler} = 1.0 + 0.015 \cdot (F_{10.7} - 70) + 0.035 \cdot A_p$$
   - Solar Extreme Ultraviolet (EUV) radiation (measured by $F_{10.7}$ radio flux in SFU) aur geomagnetic storms (measured by $A_p/K_p$) thermosphere ko heat karke expand karte hain.
   - During X-class solar flares, the drag multiplier spikes to **$3.5\times$**, causing LEO satellites to drop 3.5 times faster.

3. **Ground Casualty Expectation ($E_c$):**
   $$E_c = P_{impact} \times \rho_{population} \times A_{casualty}$$
   - Evaluated against the international IADC / NASA threshold of **$10^{-4}$ (1 in 10,000)**. If $E_c > 10^{-4}$, controlled oceanic de-orbit is mandatory.

### 🖥️ B. Every Button & Control on Page 3:
- **Tabs Switcher (`DECAY CANDIDATES` | `ADITYA-L1 WEATHER`):** Orbital decay risk view aur solar physics dashboard ke beech switch karta hai.
- **Decay Candidate Cards:** Object name, NORAD ID, Altitude (km), Decay Rate (m/day), ETA, Survival %, Casualty risk dikhata hai. Click karne par 2D map par landing footprint load hota hai.
- **2D Leaflet World Reentry Corridor Map (`ReentryMap.tsx`):** 50 Monte Carlo stochastic runs se computed landing uncertainty corridor (GeoJSON MultiPolygon) world map par render karta hai.
- **Aditya-L1 Live Coronagraph Feed:** CME speed (km/s), Flare Class (X/M/C), CME Travel Progress %, aur Impact Active status display karta hai.

---

## 6. Page 4: Regulatory Compliance & Multi-Agent Swarm (`CompliancePage.tsx`)

### 🤖 A. 5-Agent Autonomous Swarm Architecture:
1. **Agent 1 (Data Ingestion):** CelesTrak / Space-Track live TLEs ingest aur validate karta hai.
2. **Agent 2 (Spatial Screening):** 3D KD-Tree nearest neighbor indexing se 10 km bounding box ke close encounters filter karta hai.
3. **Agent 3 (Astrodynamics & $P_c$):** Encounter frame $(R,T,N)$ mein Foster-Elrod 2D integration se $P_c$ calculate karta hai.
4. **Agent 4 (Autonomous Negotiation):** Primary aur secondary commercial operators ke beech fuel-optimal burn share negotiate karta hai.
5. **Agent 5 (Compliance Officer):** ReportLab engine trigger karke official **INSPACE-CAM-2026 PDF** generate karta hai.

### 🖥️ B. Every Button & Control on Page 4:
- **`TRIGGER AUTONOMOUS SWARM RUN` Button:** WebSocket `/api/ws/swarm/run` open karke sabhi 5 agents ko live sequence mein execute karta hai aur real-time terminal logs stream karta hai.
- **`GENERATE & SUBMIT IN-SPACe FILING` Button:** Form data (Operator Name, Sat ID, Maneuver Strategy) lekar backend `POST /api/compliance/file` par formal regulatory filing submit karta hai aur Llama 3.2 briefing add karta hai.
- **`DOWNLOAD OFFICIAL PDF` Button:** Generated INSPACE-CAM-2026 legal document ko new browser tab mein download/open karta hai.

---

## 7. Air-Gapped AI Astrometry Copilot (`CopilotDrawer.tsx` & `copilot.py`)

- **Why 100% Local Llama 3.2 via Ollama (Port 11434)?**
  - Space Situational Awareness involves sensitive defense and commercial telemetry.
  - Sending orbital state vectors to cloud APIs (OpenAI/Anthropic) violates Indian Data Sovereignty laws.
  - ORVEXA runs 100% air-gapped on the local machine with zero external leaks.
- **RAG Telemetry Injection:**
  - Extracts NORAD IDs (e.g. 25544), satellite names, conjunction events, and Aditya-L1 solar indices from queries and injects them directly into the context along with real-time UTC timestamps.
- **Buttons & Controls:**
  - **`Send Message` Button / Enter:** Submits prompt to `/api/copilot/chat`.
  - **`Clear Chat Logs` (Trash Icon):** Resets conversation memory.
  - **Suggestion Pills:** 1-click prompts (*"Is ISS safe from Cosmos debris?"*, *"Explain Foster-Elrod method"*, etc.).

---

## 8. Judges Q&A Defense Script (Top 10 Technical Questions)

1. **Q: SGP4 vs Numerical Cowell Propagator mein kya difference hai?**  
   *Ans:* SGP4 analytical closed-form equations solve karta hai (~1 ms per step), jo 10,000+ satellites ki real-time fleet screening ke liye ideal hai. High-precision numerical integrators final burn planning ke time use kiye jaate hain.

2. **Q: Foster-Elrod 2D algorithm Monte Carlo se better kyun hai?**  
   *Ans:* 3D Monte Carlo collision simulation requires 1,000,000 runs (~15-30 seconds). Foster-Elrod projects covariance onto the 2D B-Plane and reduces the 2D integral to a 1D numerical quadrature using modified Bessel functions ($I_0$), calculating exact $P_c$ in just 2 milliseconds.

3. **Q: Aditya-L1 data ka practical use case kya hai?**  
   *Ans:* 2022 mein SpaceX ke 40 Starlink satellites ek geomagnetic storm ke chalte re-enter karke destroy ho gaye the. ORVEXA Aditya-L1 data se thermospheric density spike ko live compute karta hai aur satellite operators ko 14 hours pehle warning deta hai.

4. **Q: Cloud LLM kyun nahi use kiya?**  
   *Ans:* Satellite telemetry defense aur national security asset hoti hai. ORVEXA local quantized Llama 3.2 model use karta hai jo secure military control rooms mein bina internet ke run hota hai.

5. **Q: System scalability kaisi hai?**  
   *Ans:* Spatial KD-Tree complexity $O(N^2)$ se $O(N \log N)$ kar deta hai. Backend async Python 3.12 + WebSockets par hai, aur 3D globe CesiumJS WebGL GPU instancing par 60 FPS deta hai.

---

## 9. 2-Minute Winning Elevator Pitch (Exact Script)

> *"Respected Judges, space mein aaj 30,000 se zyada satellites aur debris hain jo 28,000 km/h ki hypersonic speed par ghoom rahe hain. Ek single collision poori orbital altitude ko hazaron saalon ke liye tabah kar sakti hai.*  
>  
> *ORVEXA India ka pehla AI-powered, autonomous Space Situational Awareness & Traffic Management platform hai. Hum 3D KD-Tree se real-time close approaches detect karte hain, Foster-Elrod 2D B-Plane math se exact Collision Probability calculate karte hain, ISRO Aditya-L1 solar data se atmospheric drag decay predict karte hain, aur autonomous multi-agent swarm se official IN-SPACe regulatory filings automatically generate karte hain.*  
>  
> *Saath hi, hamara air-gapped local AI Copilot bina kisi cloud dependency ya data leakage ke 100% defense-grade security provide karta hai. ORVEXA makes our skies safe, sustainable, and future-ready! Thank you!"*
