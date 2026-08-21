"""
FastAPI Server Entry Point
===========================
Exposes backend simulation, FastF1 telemetry, session analysis, and ML prediction endpoints over HTTP REST.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.data.fastf1_service import (
    get_available_seasons,
    get_event_schedule,
    fetch_driver_standings,
    fetch_season_progression,
    fetch_round_matrix
)
from backend.data.analysis_service import (
    get_weekend_overview,
    get_session_pace,
    get_telemetry_lab,
    get_driver_comparison
)
from backend.engine.replay import get_race_telemetry
from backend.engine.season_2026 import predict_full_season
from backend.ml.predictor import F1RacePredictor

app = FastAPI(title="F1 Analytics Backend API", version="1.0.0")

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ML Predictor Instance
predictor = F1RacePredictor()


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "F1 Analytics Backend API",
        "version": "1.0.0",
    }


@app.get("/api/seasons")
def seasons_endpoint():
    return {"seasons": get_available_seasons()}


@app.get("/api/schedule/{year}")
def schedule_endpoint(year: int):
    try:
        df = get_event_schedule(year)
        if df.empty:
            return {"year": year, "events": []}
        records = df.to_dict(orient="records")
        sanitized = []
        for r in records:
            clean_r = {}
            for k, v in r.items():
                if isinstance(v, float) and (v != v):
                    clean_r[k] = None
                elif hasattr(v, 'isoformat'):
                    clean_r[k] = v.isoformat()
                else:
                    clean_r[k] = v
            sanitized.append(clean_r)
        return {"year": year, "events": sanitized}
    except Exception as e:
        return {"status": "error", "message": str(e), "events": []}


@app.get("/api/standings/{year}")
def standings_endpoint(year: int):
    df, meta = fetch_driver_standings(year)
    return {
        "year": year,
        "meta": meta,
        "standings": df.to_dict(orient="records") if not df.empty else [],
    }


@app.get("/api/progression/{year}")
def progression_endpoint(year: int):
    try:
        prog = fetch_season_progression(year)
        return {"year": year, "progression": prog}
    except Exception as e:
        return {"year": year, "progression": [], "error": str(e)}


@app.get("/api/matrix/{year}")
def matrix_endpoint(year: int):
    try:
        matrix = fetch_round_matrix(year)
        return {"year": year, "matrix": matrix}
    except Exception as e:
        return {"year": year, "matrix": [], "error": str(e)}


@app.get("/api/weekend/{year}/{event_ref}")
def weekend_endpoint(year: int, event_ref: str):
    return get_weekend_overview(year, event_ref)


@app.get("/api/session/{year}/{event_ref}/{session_id}/pace")
def pace_endpoint(year: int, event_ref: str, session_id: str = "R"):
    return get_session_pace(year, event_ref, session_id)


@app.get("/api/session/{year}/{event_ref}/{session_id}/telemetry")
def telemetry_endpoint(year: int, event_ref: str, session_id: str = "R", drivers: str = "VER,NOR"):
    driver_list = [d.strip().upper() for d in drivers.split(",") if d.strip()]
    return get_telemetry_lab(year, event_ref, session_id, driver_list)


@app.get("/api/session/{year}/{event_ref}/{session_id}/comparison")
def comparison_endpoint(year: int, event_ref: str, session_id: str = "R", driver_a: str = "VER", driver_b: str = "NOR"):
    return get_driver_comparison(year, event_ref, session_id, driver_a, driver_b)


@app.get("/api/session/{year}/{event_ref}/{session_id}/replay")
def replay_endpoint(year: int, event_ref: str, session_id: str = "R"):
    try:
        from backend.data.fastf1_service import get_session
        session = get_session(year, event_ref, session_id)
        if session is None:
            return {"error": "Session could not be loaded"}
        replay_data = get_race_telemetry(session, session_type=session_id)
        return replay_data
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/predictions/{year}/{event_ref}")
def predictions_endpoint(year: int, event_ref: str):
    try:
        return predictor.predict_event(year, event_ref)
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/train-predictor")
@app.get("/api/train-predictor")
def train_predictor_endpoint(seasons: str = "2022,2023,2024"):
    try:
        season_list = [int(s.strip()) for s in seasons.split(",") if s.strip().isdigit()]
        res = predictor.train(season_list)
        return res
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/simulate-race")
def simulate_race_endpoint(weather: str = "DRY", circuit: str = "MONACO"):
    try:
        res = predictor.train([2023, 2024])
        return {"status": "success", "weather": weather, "circuit": circuit, "model_metrics": res}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/season-2026")
def season_2026_endpoint(seed: int = Query(default=2026)):
    return predict_full_season(seed=seed)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8001, reload=True)

