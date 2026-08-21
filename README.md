# 🏎️ F1 Analysis Dashboard & Backend Platform

A decoupled Formula 1 telemetry, 25 FPS race replay, simulation, and predictive analytics workspace.

---

## 🏗️ Repository Architecture

The repository structure is organized into a modular **Python Backend API** and a **Vite + React + shadcn/ui Frontend**.

```
.
├── backend/                  # Python backend package
│   ├── data/                 # FastF1 & Ergast API data services
│   │   └── fastf1_service.py # Event schedules, standings, results, and session telemetry
│   ├── engine/               # Simulation and telemetry playback engines
│   │   ├── race_engine.py    # Lap-by-lap race simulation engine
│   │   ├── replay.py         # 25 FPS telemetry interpolation & Safety Car logic (from f1-race-replay)
│   │   └── season_2026.py    # 2026 season projection engine
│   ├── ml/                   # Machine learning model pipeline
│   │   └── predictor.py      # Gradient Boosting race & podium predictor
│   ├── server.py             # FastAPI REST HTTP server
│   └── config.py             # Global paths, caching, and runtime settings
├── frontend/                 # Vite + React + TypeScript + Tailwind + shadcn UI
│   ├── src/
│   │   ├── api/f1Api.ts      # REST API client connecting to FastAPI backend
│   │   ├── components/       # Navigation pill, Footer, TrackMap
│   │   ├── views/            # ControlRoom, SeasonOverview, WeekendOverview, SessionAnalysis, TelemetryLab, DriverComparison, RaceReplay, RacePredictions
│   │   └── data/             # Circuit coordinates & baseline fallback models
│   ├── DESIGN.md             # Visual design tokens & editorial style guide
├── computed_data/            # Local cache for processed telemetry and prediction models
├── .fastf1-cache/            # FastF1 disk cache
├── requirements.txt          # Backend Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1. Backend Server Setup
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
.venv/bin/python -m uvicorn backend.server:app --host 0.0.0.0 --port 8001
```

- **API Base URL**: `http://localhost:8001`
- **Swagger Documentation**: `http://localhost:8001/docs`

### 2. Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```

- **Local App URL**: `http://localhost:5174`

---

## 🏎️ F1 Sub-repository Engine (`f1-race-replay`)

The race replay engine located in `backend/engine/replay.py` incorporates the 25 FPS telemetry resampling, multiprocessing worker pipeline, and KD-Tree Safety Car position simulator based on the [`f1-race-replay`](https://github.com/IAmTomShaw/f1-race-replay.git) architecture.

- **25 FPS Fixed Timeline**: Resamples non-uniform FastF1 telemetry into uniform time steps (`dt = 1/25`).
- **Safety Car Simulation**: Tracks FastF1 status flag `4` (Safety Car deployed) and calculates realistic SC positioning ahead of the race leader using spatial KD-Trees (`scipy.spatial.cKDTree`).
