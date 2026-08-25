<div align="center">

# 🛰️ ORVEXA

### *Orbital Vigilance & Space Situational Awareness Platform*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![CesiumJS](https://img.shields.io/badge/CesiumJS-1.144-6CADDF?style=for-the-badge&logo=cesium&logoColor=white)](https://cesium.com)

> **Real-time 3D satellite tracking, collision avoidance, debris reentry prediction, and AI-powered space compliance — all in one platform.**

[🚀 Live Demo](#) · [📖 Docs](#documentation) · [🐛 Issues](https://github.com/yug0973/ORVEXA/issues)

</div>

---

## 📸 Platform Screenshots

### 🌍 3D Globe — Live Satellite Tracking
![3D Globe Dashboard](./docs/screenshots/01_globe_dashboard.png)
> *Interactive Cesium 3D globe showing 104 tracked satellites with real-time TLE propagation, live alerts and replay controls*

---

### 💥 Collision Risk & Conjunction Analysis
![Conjunction Dashboard](./docs/screenshots/02_conjunction_dashboard.png)
> *Critical conjunction event: ISS (ZARYA) vs COSMOS 2251 DEBRIS — showing 4.82×10⁻⁴ collision probability, 8h countdown to TCA, B-Plane encounter plot, and Delta-V maneuver simulator*

---

### 🎯 Collision Simulation Panel
![Collision Simulation](./docs/screenshots/02b_collision_simulation.png)
> *Coming soon — interactive collision trajectory simulation with delta-V burn optimization and IN-SPACe filing integration*

---

### 🔥 Reentry & Decay Console
![Reentry Map](./docs/screenshots/03_reentry_map.png)
> *CALSPHERE 1 reentry at 185.4 km altitude — decay corridor on Leaflet map, fragment survival rate 18.5%, casualty risk 1.25×10⁻⁵ (NASA EVM)*

---

### ☀️ Solar Weather — Aditya-L1 Real-Time Feed
![Solar Weather](./docs/screenshots/04_solar_weather.png)
> *Live Aditya-L1 SoLEXS & HEL1OS X-ray spectrometer telemetry, solar flux F10.7 = 136 SFU, Ap index 5.8 nT, drag multiplier 1.94×*

---

### 🤖 Flight Copilot — AI Space Operations Assistant
![AI Copilot](./docs/screenshots/05_ai_copilot.png)
> *Air-gapped LLM assistant querying conjunction hazards, B-plane collision risks, and deorbit profiles — raw database telemetry fallback when Llama 3.2 is offline*

---

### 📋 Regulatory Compliance Manager
![Compliance Manager](./docs/screenshots/06_compliance.png)
> *Auto-generates ITU/FCC IN-SPACe filings, tracks compliance status, manages operator licensing — coming soon*

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 🌍 **3D Globe** | Live Cesium globe rendering 100+ satellites via CZML streaming with replay |
| 🛰️ **TLE Propagator** | SGP4 orbital propagation with Skyfield — sub-second accuracy |
| 💥 **Collision Risk** | Chan PC + Foster-Elrod collision probability, TCA countdown, miss distance |
| 🎯 **Delta-V Simulator** | Interactive maneuver burn optimizer with recalculated Pc |
| 📊 **B-Plane Plotter** | 2D/3D covariance ellipse encounter geometry visualization |
| 🔥 **Reentry Prediction** | Monte Carlo atmospheric decay with NRLMSISE-00 density model |
| ☀️ **Solar Weather** | Aditya-L1 SoLEXS/HEL1OS real-time feed + NOAA Kp/F10.7 indices |
| 🤖 **Flight Copilot** | Llama 3.2 (air-gapped) with raw DB telemetry fallback |
| 📋 **IN-SPACe Compliance** | Auto ITU/FCC regulatory filing generator + one-click submission |
| 📡 **WebSocket Alerts** | Real-time push alerts for critical conjunction and reentry events |
| 🌊 **Swarm Orchestrator** | Multi-satellite maneuver planning and constellation management |
| 📤 **Data Exporter** | CCSDS, JSON, and CSV export for orbital state vectors |

---

## 🏗️ Architecture

```
ORVEXA/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # App entrypoint, CORS, routers
│   ├── config.py               # Pydantic settings
│   ├── routers/                # API route handlers
│   │   ├── satellites.py       # TLE ingestion, CZML streaming
│   │   ├── conjunctions.py     # Collision probability endpoints
│   │   ├── reentry.py          # Decay prediction endpoints
│   │   ├── solar.py            # Space weather + Aditya-L1
│   │   ├── copilot.py          # AI copilot (Ollama/LLM)
│   │   └── compliance.py       # Regulatory filing generation
│   └── services/               # Business logic layer
│       ├── compliance_generator.py
│       └── swarm_orchestrator.py
│
├── orbital_mechanics/          # Pure physics computation layer
│   ├── propagator.py           # SGP4 / Skyfield orbit propagation
│   ├── screening.py            # Conjunction screening algorithms
│   ├── chan_pc.py              # Chan probability of collision
│   ├── foster_elrod.py        # Foster-Elrod Pc method
│   ├── decay_engine.py         # Atmospheric drag decay model
│   ├── monte_carlo_reentry.py  # Reentry corridor Monte Carlo
│   ├── solar_weather.py        # NOAA/Aditya-L1 solar pipeline
│   ├── breakup_model.py        # Debris cloud fragmentation
│   └── data_exporter.py        # CCSDS/JSON/CSV export
│
├── orvexa-frontend/            # Vite + React 19 + TypeScript frontend
│   └── src/
│       ├── components/
│       │   ├── Topbar.tsx          # Navigation + live alerts
│       │   ├── CopilotDrawer.tsx   # AI assistant side panel
│       │   ├── EntryPortal.tsx     # Auth/login screen
│       │   ├── BPlanePlotter.tsx   # B-plane encounter geometry
│       │   ├── CollisionSimulationPanel.tsx  # Delta-V simulator
│       │   ├── OrbitGlobe.tsx      # CesiumJS 3D globe
│       │   └── ReentryMap.tsx      # Leaflet decay map
│       └── pages/
│           ├── GlobePage.tsx       # 3D Cesium satellite globe
│           ├── ConjunctionPage.tsx # Collision risk dashboard
│           ├── ReentryPage.tsx     # Decay prediction + map
│           ├── SolarPage.tsx       # Space weather monitor
│           ├── CopilotPage.tsx     # AI chat interface
│           └── CompliancePage.tsx  # Regulatory compliance
│
├── tests/                      # Pytest test suite (11 modules)
├── docs/                       # Technical documentation + screenshots
└── docker-compose.yml          # Docker deployment config
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+

### 1. Clone the Repository

```bash
git clone https://github.com/yug0973/ORVEXA.git
cd ORVEXA
```

### 2. Backend Setup

```bash
pip install -r requirements.txt
cp .env.template .env
python backend/seed_db.py
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

> API: **http://localhost:8000** · Docs: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd orvexa-frontend
npm install
npm run dev
```

> Frontend: **http://localhost:5173**

---

## 🔧 Environment Variables

```env
DATABASE_URL=sqlite+aiosqlite:///./orvexa.db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
SPACETRACK_USER=your_email@example.com
SPACETRACK_PASS=your_password
FRONTEND_URL=http://localhost:5173
```

---

## 🧠 Key Algorithms

| Algorithm | File | Use Case |
|-----------|------|----------|
| **SGP4** | Skyfield library | TLE orbit propagation |
| **Chan P(c)** | `chan_pc.py` | Collision probability |
| **Foster-Elrod** | `foster_elrod.py` | Alternative Pc method |
| **NRLMSISE-00** | `nrlmsise00` package | Atmospheric density |
| **Monte Carlo** | `monte_carlo_reentry.py` | Reentry corridor uncertainty |
| **Breakup Model** | `breakup_model.py` | Debris cloud distribution |

---

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/satellites/czml` | GET | CZML stream for 3D globe |
| `/api/conjunctions` | GET | Active conjunction events |
| `/api/conjunctions/{id}` | GET | Detailed Pc + TCA analysis |
| `/api/reentry` | GET | Active reentry predictions |
| `/api/reentry/{id}/map` | GET | GeoJSON reentry corridor |
| `/api/solar` | GET | Current solar indices |
| `/api/solar/aditya-l1` | GET | Aditya-L1 live telemetry |
| `/api/copilot/brief` | POST | AI mission briefing |
| `/api/compliance/filings` | GET | All compliance filings |
| `/api/compliance/file` | POST | Generate new filing |
| `/api/compliance/download/{id}` | GET | Download filing PDF |
| `/api/ws/alerts` | WS | Real-time threat alerts |
| `/api/ws/swarm/run` | WS | Swarm maneuver planner |

---

## 🛰️ Data Sources

- **TLE Catalog** — CelesTrak (16,000+ active satellites)
- **Solar Weather** — NOAA Space Weather Prediction Center  
- **Aditya-L1** — ISRO SoLEXS & HEL1OS real-time telemetry
- **Atmospheric Model** — NRLMSISE-00 density profile

---

## 🧪 Running Tests

```bash
pytest tests/ -v
pytest tests/test_conjunction_math.py -v
pytest tests/test_decay_reentry.py -v
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

---

## 🗺️ Roadmap

- [ ] Space-Track.org live TLE feed integration
- [ ] Multi-user auth with JWT + operator roles
- [ ] Maneuver planning with delta-V optimizer
- [ ] ITU IN-SPACe filing auto-submission
- [ ] Mobile-responsive dashboard
- [ ] PostgreSQL production database

---

## 👨‍💻 Author

**Yug Brahmbhatt**
- GitHub: [@yug0973](https://github.com/yug0973)
- Email: yugbrahmbhatt000@gmail.com

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for the future of space safety**

⭐ Star this repo if you find it useful!

</div>