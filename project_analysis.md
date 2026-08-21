# Formula 1 Analytics Platform Architecture

This document details the updated, decoupled architecture of the **F1 Analytics Workspace**, structured into a standalone Python **Backend Package** and an empty **Frontend Workspace**.

---

## 🏗️ Project Architecture

```
.
├── backend/                  # Clean Python backend package
│   ├── data/                 # FastF1 & Ergast API data services
│   │   └── fastf1_service.py # Event schedules, standings, results, and session telemetry
│   ├── engine/               # Simulation and telemetry playback engines
│   │   ├── race_engine.py    # Lap-by-lap race simulation engine
│   │   ├── replay.py         # 25 FPS telemetry interpolation & Safety Car simulation
│   │   └── season_2026.py    # 2026 season projection engine
│   ├── ml/                   # Machine learning model pipeline
│   │   └── predictor.py      # Gradient Boosting race outcome & podium predictor
│   └── config.py             # Global paths, caching, and runtime settings
├── frontend/                 # Clean directory ready for new frontend development
├── computed_data/            # Local cache for processed telemetry and prediction models
├── .fastf1-cache/            # FastF1 disk cache
├── requirements.txt          # Backend Python dependencies
└── README.md
```

---

## 📦 Core Modules

### 1. Data Service (`backend/data/fastf1_service.py`)
- **FastF1 Integration**: Handles disk caching (`.fastf1-cache`) and loads full session object (laps, telemetry, weather).
- **Ergast API Integration**: Fetches historical race results and computes driver standings matrices across seasons.

### 2. Simulation Engines (`backend/engine/`)
- **Race Engine (`race_engine.py`)**: Lap-by-lap simulation engine supporting weather conditions and circuit parameters.
- **Replay Engine (`replay.py`)**: Resamples raw driver telemetry into uniform 25 FPS timelines, handling driver positions, tyre compounds, speeds, and Safety Car logic.
- **2026 Season Projection (`season_2026.py`)**: Monte Carlo style season simulator forecasting standings and round-by-round race outcomes for the 2026 F1 season calendar.

### 3. ML Predictor (`backend/ml/predictor.py`)
- **Model**: `F1RacePredictor` class using Gradient Boosting (`scikit-learn`).
- **Features**: Features grid positions, driver encodings, and constructor encodings to predict finishing positions, podium probabilities, and feature importances.
