import io
import json
import random
import importlib.util
from datetime import date
from pathlib import Path

import fastf1
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

from utils.ml_predictions import (
    fetch_historical_race_data,
    fetch_driver_standings,
    train_model,
    predict_race,
    get_feature_importance,
)


st.set_page_config(
    page_title="Race Predictions · Kinetic Pulse",
    page_icon="🔮",
    layout="wide",
)

st.title("🔮 F1 Predictor Pro · ML Suite")
st.caption(
    "Formula-style ML prediction workspace: top-3 probability, full-grid race prediction, "
    "weather/tire impact, feature importance, driver head-to-head, and season projection."
)


WEATHER_CHOICES = ["DRY", "LIGHT_RAIN", "HEAVY_RAIN"]
TIRE_CHOICES = ["SOFT", "MEDIUM", "HARD"]
CIRCUIT_CHOICES = ["STANDARD", "STREET", "FAST", "DESERT", "TECHNICAL"]

WEATHER_IMPACT = {"DRY": 1.00, "LIGHT_RAIN": 1.05, "HEAVY_RAIN": 1.15}
TIRE_DEG = {"SOFT": 0.08, "MEDIUM": 0.05, "HARD": 0.03}
TIRE_ADV = {"SOFT": 1.00, "MEDIUM": 0.80, "HARD": 0.60}
OPTIMAL_PIT = {"SOFT": 25, "MEDIUM": 35, "HARD": 45}

DRIVER_NAME_MAP = {
    "VER": "Max Verstappen",
    "NOR": "Lando Norris",
    "LEC": "Charles Leclerc",
    "HAM": "Lewis Hamilton",
    "PIA": "Oscar Piastri",
    "RUS": "George Russell",
    "ALO": "Fernando Alonso",
    "SAI": "Carlos Sainz",
    "ALB": "Alexander Albon",
    "TSU": "Yuki Tsunoda",
    "LAW": "Liam Lawson",
    "HAD": "Isack Hadjar",
    "GAS": "Pierre Gasly",
    "DOO": "Jack Doohan",
    "OCO": "Esteban Ocon",
    "BEA": "Oliver Bearman",
    "STR": "Lance Stroll",
    "ANT": "Kimi Antonelli",
    "HUL": "Nico Hulkenberg",
    "BOR": "Gabriel Bortoleto",
    "BOT": "Valtteri Bottas",
    "PER": "Sergio Perez",
}


FALLBACK_GRID = [
    ("NOR", "McLaren", 1), ("PIA", "McLaren", 2),
    ("LEC", "Ferrari", 3), ("HAM", "Ferrari", 4),
    ("VER", "Red Bull Racing", 5), ("TSU", "Red Bull Racing", 6),
    ("RUS", "Mercedes", 7), ("ANT", "Mercedes", 8),
    ("ALO", "Aston Martin", 9), ("STR", "Aston Martin", 10),
    ("SAI", "Williams", 11), ("ALB", "Williams", 12),
    ("LAW", "Racing Bulls", 13), ("HAD", "Racing Bulls", 14),
    ("GAS", "Alpine", 15), ("DOO", "Alpine", 16),
    ("OCO", "Haas F1 Team", 17), ("BEA", "Haas F1 Team", 18),
    ("HUL", "Sauber", 19), ("BOR", "Sauber", 20),
    ("BOT", "Cadillac", 21), ("PER", "Cadillac", 22),
]

RACE_POINTS_BY_POS = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1,
}


def classify_circuit(circuit_name: str) -> str:
    txt = str(circuit_name).upper()
    if any(k in txt for k in ["MONACO", "SINGAPORE", "BAKU", "JEDDAH", "MIAMI", "MELBOURNE", "LAS VEGAS"]):
        return "STREET"
    if any(k in txt for k in ["BAHRAIN", "ABU DHABI", "QATAR"]):
        return "DESERT"
    if any(k in txt for k in ["MONZA", "SILVERSTONE", "SPA", "RED BULL RING"]):
        return "FAST"
    if any(k in txt for k in ["HUNGARY", "HUNGARORING", "SUZUKA", "IMOLA", "BARCELONA"]):
        return "TECHNICAL"
    return "STANDARD"


def stable_weather(year: int, rnd: int) -> str:
    rng = np.random.default_rng(int(year * 1000 + rnd * 17 + 7))
    return str(rng.choice(WEATHER_CHOICES, p=[0.72, 0.20, 0.08]))


def stable_tire_choice(year: int, rnd: int, code: str, grid_pos: float) -> str:
    seed = int(year * 10000 + rnd * 113 + sum(ord(c) for c in str(code)))
    rng = np.random.default_rng(seed)
    if grid_pos <= 6:
        probs = [0.50, 0.40, 0.10]
    elif grid_pos <= 12:
        probs = [0.35, 0.50, 0.15]
    else:
        probs = [0.20, 0.45, 0.35]
    return str(rng.choice(TIRE_CHOICES, p=probs))


def build_default_grid(history: pd.DataFrame, season: int) -> tuple[pd.DataFrame, str]:
    fallback_df = pd.DataFrame(FALLBACK_GRID, columns=["Driver", "Team", "GridPosition"])
    season_df = history[history["Year"] == int(season)] if "Year" in history.columns else pd.DataFrame()
    note = ""

    if season_df.empty and "Year" in history.columns and not history.empty:
        latest_year = int(pd.to_numeric(history["Year"], errors="coerce").dropna().max())
        season_df = history[history["Year"] == latest_year]
        note = f"No history for {season}; prefilled grid from latest available season ({latest_year})."

    if season_df.empty:
        return fallback_df.copy(), "Using built-in 22-driver fallback grid."

    latest_round = int(pd.to_numeric(season_df["Round"], errors="coerce").dropna().max())
    snap = season_df[season_df["Round"] == latest_round][["Abbreviation", "TeamName", "GridPosition"]].copy()
    snap = snap.dropna(subset=["Abbreviation", "GridPosition"]).drop_duplicates(subset=["Abbreviation"], keep="first")
    snap["GridPosition"] = pd.to_numeric(snap["GridPosition"], errors="coerce")
    snap = snap.dropna(subset=["GridPosition"]).sort_values("GridPosition")

    if snap.empty:
        return fallback_df.copy(), "Could not infer season grid from history; using 22-driver fallback grid."

    grid = snap.rename(columns={"Abbreviation": "Driver", "TeamName": "Team"})
    grid["Driver"] = grid["Driver"].astype(str).str.upper().str.strip()
    grid["Team"] = grid["Team"].fillna("Unknown")
    grid["GridPosition"] = grid["GridPosition"].astype(int)

    missing = fallback_df[~fallback_df["Driver"].isin(grid["Driver"])].copy()
    if not missing.empty:
        grid = pd.concat([grid, missing], ignore_index=True)

    grid = (
        grid.drop_duplicates(subset=["Driver"], keep="first")
        .sort_values("GridPosition")
        .head(22)
        .reset_index(drop=True)
    )
    grid["GridPosition"] = np.arange(1, len(grid) + 1)

    if not note:
        note = f"Prefilled grid from season {season} round {latest_round} race data."
    return grid.reset_index(drop=True), note


def build_projected_final_standings(
    predictions_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    total_rounds: int,
    selected_round: int,
) -> tuple[pd.DataFrame, int]:
    remaining_rounds = max(int(total_rounds) - int(selected_round) + 1, 1)

    pred = predictions_df.copy()
    pred["PredictedPosition"] = pd.to_numeric(pred["PredictedPosition"], errors="coerce")
    pred["ProjectedPointsPerRace"] = pred["PredictedPosition"].map(RACE_POINTS_BY_POS).fillna(0.0)
    pred["ProjectedPointsToAdd"] = pred["ProjectedPointsPerRace"] * remaining_rounds
    pred["ProjectedWinsToAdd"] = (pred["PredictedPosition"] == 1).astype(int) * remaining_rounds
    pred["ProjectedPodiumsToAdd"] = (pred["PredictedPosition"] <= 3).astype(int) * remaining_rounds

    base = baseline_df.copy() if baseline_df is not None else pd.DataFrame()
    if base.empty:
        base = pd.DataFrame({
            "Driver": pred["Driver"],
            "DriverName": pred["Driver"],
            "Team": pred["Team"],
            "Points": 0.0,
            "Wins": 0,
            "Podiums": 0,
        })
    else:
        for c in ["Driver", "DriverName", "Team", "Points", "Wins", "Podiums"]:
            if c not in base.columns:
                base[c] = 0 if c in ["Points", "Wins", "Podiums"] else ""
        base = base[["Driver", "DriverName", "Team", "Points", "Wins", "Podiums"]].copy()

    merged = base.merge(
        pred[["Driver", "Team", "ProjectedPointsToAdd", "ProjectedWinsToAdd", "ProjectedPodiumsToAdd"]],
        on="Driver",
        how="outer",
        suffixes=("_base", "_pred"),
    )
    merged["Team"] = merged["Team_base"].fillna(merged["Team_pred"]).fillna("Unknown")
    merged["DriverName"] = merged["DriverName"].fillna(merged["Driver"])
    merged["Points"] = pd.to_numeric(merged["Points"], errors="coerce").fillna(0.0)
    merged["Wins"] = pd.to_numeric(merged["Wins"], errors="coerce").fillna(0).astype(int)
    merged["Podiums"] = pd.to_numeric(merged["Podiums"], errors="coerce").fillna(0).astype(int)

    merged["FinalProjectedPoints"] = (
        merged["Points"] + merged["ProjectedPointsToAdd"].fillna(0.0)
    ).round(1)
    merged["FinalProjectedWins"] = merged["Wins"] + merged["ProjectedWinsToAdd"].fillna(0).astype(int)
    merged["FinalProjectedPodiums"] = merged["Podiums"] + merged["ProjectedPodiumsToAdd"].fillna(0).astype(int)

    out = merged[[
        "Driver",
        "DriverName",
        "Team",
        "FinalProjectedPoints",
        "FinalProjectedWins",
        "FinalProjectedPodiums",
    ]].copy()
    out = out.sort_values(
        ["FinalProjectedPoints", "FinalProjectedWins", "FinalProjectedPodiums", "Driver"],
        ascending=[False, False, False, True]
    ).reset_index(drop=True)
    out["Pos"] = np.arange(1, len(out) + 1)
    return out[[
        "Pos", "Driver", "DriverName", "Team",
        "FinalProjectedPoints", "FinalProjectedWins", "FinalProjectedPodiums",
    ]], remaining_rounds


def build_enhanced_training_frame(history: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = history.copy()
    if df.empty:
        return pd.DataFrame(), []

    if "Circuit" not in df.columns:
        df["Circuit"] = df.get("EventName", "Unknown")
    if "Points" not in df.columns:
        df["Points"] = 0.0

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Round"] = pd.to_numeric(df["Round"], errors="coerce")
    df["GridPosition"] = pd.to_numeric(df["GridPosition"], errors="coerce")
    df["FinishPosition"] = pd.to_numeric(df["FinishPosition"], errors="coerce")
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce").fillna(0.0)
    df = df.dropna(subset=["Year", "Round", "GridPosition", "FinishPosition", "Abbreviation", "TeamName"]).copy()

    df["Year"] = df["Year"].astype(int)
    df["Round"] = df["Round"].astype(int)
    df = df.sort_values(["Year", "Round"]).reset_index(drop=True)

    event_df = df[["Year", "Round"]].drop_duplicates().copy()
    event_df["Weather"] = event_df.apply(lambda r: stable_weather(int(r["Year"]), int(r["Round"])), axis=1)
    df = df.merge(event_df, on=["Year", "Round"], how="left")
    df["CircuitType"] = df["Circuit"].map(classify_circuit)
    df["Starting_Tire"] = df.apply(
        lambda r: stable_tire_choice(int(r["Year"]), int(r["Round"]), str(r["Abbreviation"]), float(r["GridPosition"])),
        axis=1,
    )

    df["Driver_AvgPosition"] = df.groupby("Abbreviation")["FinishPosition"].transform(
        lambda s: s.shift(1).expanding().mean()
    )
    df["Driver_AvgPoints"] = df.groupby("Abbreviation")["Points"].transform(
        lambda s: s.shift(1).expanding().mean()
    )
    df["Driver_TotalWins"] = df.groupby("Abbreviation")["FinishPosition"].transform(
        lambda s: (s.shift(1) == 1).fillna(False).cumsum()
    )
    df["Driver_TotalPodiums"] = df.groupby("Abbreviation")["FinishPosition"].transform(
        lambda s: (s.shift(1) <= 3).fillna(False).cumsum()
    )

    df["Team_AvgPosition"] = df.groupby("TeamName")["FinishPosition"].transform(
        lambda s: s.shift(1).expanding().mean()
    )
    df["Team_TotalWins"] = df.groupby("TeamName")["FinishPosition"].transform(
        lambda s: (s.shift(1) == 1).fillna(False).cumsum()
    )
    df["Team_AvgPoints"] = df.groupby("TeamName")["Points"].transform(
        lambda s: s.shift(1).expanding().mean()
    )

    df["Circuit_Familiarity"] = df.groupby(["Abbreviation", "Circuit"]).cumcount()
    df["Circuit_AvgPosition"] = df.groupby(["Abbreviation", "Circuit"])["FinishPosition"].transform(
        lambda s: s.shift(1).expanding().mean()
    )

    df["Weather_Impact"] = df["Weather"].map(WEATHER_IMPACT).fillna(1.0)
    df["Is_Wet_Race"] = (df["Weather"] != "DRY").astype(int)
    df["Tire_Degradation_Rate"] = df["Starting_Tire"].map(TIRE_DEG).fillna(TIRE_DEG["MEDIUM"])
    df["Optimal_Pit_Lap"] = df["Starting_Tire"].map(OPTIMAL_PIT).fillna(OPTIMAL_PIT["MEDIUM"])
    df["Tire_Advantage"] = df["Starting_Tire"].map(TIRE_ADV).fillna(TIRE_ADV["MEDIUM"])
    df["Is_Street_Circuit"] = (df["CircuitType"] == "STREET").astype(int)
    df["Is_High_Speed"] = (df["CircuitType"] == "FAST").astype(int)

    for weather in WEATHER_CHOICES:
        df[f"Weather_{weather}"] = (df["Weather"] == weather).astype(int)
    for tire in TIRE_CHOICES:
        df[f"Tire_{tire}"] = (df["Starting_Tire"] == tire).astype(int)
    for ctype in CIRCUIT_CHOICES:
        df[f"Circuit_{ctype}"] = (df["CircuitType"] == ctype).astype(int)

    feature_cols = [
        "GridPosition",
        "Driver_AvgPosition", "Driver_AvgPoints", "Driver_TotalWins", "Driver_TotalPodiums",
        "Weather_Impact", "Is_Wet_Race",
        "Tire_Degradation_Rate", "Optimal_Pit_Lap", "Tire_Advantage",
        "Circuit_Familiarity", "Circuit_AvgPosition", "Is_Street_Circuit", "Is_High_Speed",
        "Team_AvgPosition", "Team_TotalWins", "Team_AvgPoints",
        "Weather_DRY", "Weather_LIGHT_RAIN", "Weather_HEAVY_RAIN",
        "Tire_SOFT", "Tire_MEDIUM", "Tire_HARD",
        "Circuit_STANDARD", "Circuit_STREET", "Circuit_FAST", "Circuit_DESERT", "Circuit_TECHNICAL",
    ]

    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce")
        median = float(df[col].median()) if df[col].notna().any() else 0.0
        df[col] = df[col].fillna(median)

    df["TargetTop3"] = (df["FinishPosition"] <= 3).astype(int)
    return df, feature_cols


def train_enhanced_top3_model(enhanced_df: pd.DataFrame, feature_cols: list[str]) -> tuple[RandomForestClassifier, float]:
    X = enhanced_df[feature_cols].copy()
    y = enhanced_df["TargetTop3"].copy()
    model = RandomForestClassifier(
        n_estimators=180,
        max_depth=12,
        min_samples_split=8,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    cv_acc = float("nan")
    if y.nunique() > 1 and len(X) >= 120:
        min_class = int(y.value_counts().min())
        cv_folds = min(5, max(2, min_class))
        if cv_folds >= 2:
            scores = cross_val_score(model, X, y, cv=cv_folds, scoring="accuracy")
            cv_acc = float(scores.mean())
    return model, cv_acc


def build_single_scenario_features(
    grid_pos: int,
    weather: str,
    tire: str,
    circuit_type: str,
    feature_cols: list[str],
    enhanced_df: pd.DataFrame,
) -> pd.DataFrame:
    med = enhanced_df.median(numeric_only=True)
    row = {f: 0.0 for f in feature_cols}
    row["GridPosition"] = int(grid_pos)
    row["Driver_AvgPosition"] = float(med.get("Driver_AvgPosition", 8.0))
    row["Driver_AvgPoints"] = float(med.get("Driver_AvgPoints", 6.0))
    row["Driver_TotalWins"] = float(med.get("Driver_TotalWins", 1.0))
    row["Driver_TotalPodiums"] = float(med.get("Driver_TotalPodiums", 3.0))
    row["Team_AvgPosition"] = float(med.get("Team_AvgPosition", 8.5))
    row["Team_TotalWins"] = float(med.get("Team_TotalWins", 2.0))
    row["Team_AvgPoints"] = float(med.get("Team_AvgPoints", 8.0))
    row["Circuit_Familiarity"] = float(med.get("Circuit_Familiarity", 2.0))
    row["Circuit_AvgPosition"] = float(med.get("Circuit_AvgPosition", 8.0))
    row["Weather_Impact"] = WEATHER_IMPACT.get(weather, 1.0)
    row["Is_Wet_Race"] = 0 if weather == "DRY" else 1
    row["Tire_Degradation_Rate"] = TIRE_DEG.get(tire, 0.05)
    row["Optimal_Pit_Lap"] = OPTIMAL_PIT.get(tire, 35)
    row["Tire_Advantage"] = TIRE_ADV.get(tire, 0.8)
    row["Is_Street_Circuit"] = 1 if circuit_type == "STREET" else 0
    row["Is_High_Speed"] = 1 if circuit_type == "FAST" else 0

    for w in WEATHER_CHOICES:
        key = f"Weather_{w}"
        if key in row:
            row[key] = 1 if weather == w else 0
    for t in TIRE_CHOICES:
        key = f"Tire_{t}"
        if key in row:
            row[key] = 1 if tire == t else 0
    for c in CIRCUIT_CHOICES:
        key = f"Circuit_{c}"
        if key in row:
            row[key] = 1 if circuit_type == c else 0

    return pd.DataFrame([row])[feature_cols]


def build_driver_stats(history: pd.DataFrame, enhanced_df: pd.DataFrame) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame()

    hist = history.copy()
    hist["FinishPosition"] = pd.to_numeric(hist["FinishPosition"], errors="coerce")
    hist["GridPosition"] = pd.to_numeric(hist["GridPosition"], errors="coerce")
    hist["Points"] = pd.to_numeric(hist.get("Points", 0), errors="coerce").fillna(0.0)

    latest_team = (
        hist.sort_values(["Year", "Round"])
        .dropna(subset=["Abbreviation"])
        .drop_duplicates(subset=["Abbreviation"], keep="last")
        .set_index("Abbreviation")["TeamName"]
    )

    base = hist.groupby("Abbreviation", as_index=False).agg(
        races=("FinishPosition", "count"),
        wins=("FinishPosition", lambda s: int((s == 1).sum())),
        podiums=("FinishPosition", lambda s: int((s <= 3).sum())),
        poles=("GridPosition", lambda s: int((s == 1).sum())),
        career_points=("Points", "sum"),
        avg_finish=("FinishPosition", "mean"),
    )

    base["team"] = base["Abbreviation"].map(latest_team).fillna("Unknown")
    base["win_rate"] = (base["wins"] / base["races"] * 100).replace([np.inf, -np.inf], 0).fillna(0).round(1)

    wet_wins = enhanced_df[(enhanced_df["Weather"] != "DRY") & (enhanced_df["FinishPosition"] == 1)]
    wet_wins = wet_wins.groupby("Abbreviation").size().to_dict()

    street_wins = enhanced_df[(enhanced_df["CircuitType"] == "STREET") & (enhanced_df["FinishPosition"] == 1)]
    street_wins = street_wins.groupby("Abbreviation").size().to_dict()

    base["wet_wins"] = base["Abbreviation"].map(wet_wins).fillna(0).astype(int)
    base["street_wins"] = base["Abbreviation"].map(street_wins).fillna(0).astype(int)
    base["name"] = base["Abbreviation"].map(DRIVER_NAME_MAP).fillna(base["Abbreviation"])

    return base.sort_values(["wins", "podiums", "career_points"], ascending=[False, False, False]).reset_index(drop=True)


def simulate_standard_race(drivers: list[str], weather: str) -> pd.DataFrame:
    seed = 42 if weather == "DRY" else 123
    rng = random.Random(seed)
    positions = list(range(1, len(drivers) + 1))
    rng.shuffle(positions)
    if weather != "DRY":
        rng.shuffle(positions)
    result = sorted(zip(drivers, positions), key=lambda x: x[1])
    return pd.DataFrame(
        [{"Driver": d, "Position": p} for d, p in result]
    )


def simulate_championship(drivers: list[str], rounds: int = 5) -> pd.DataFrame:
    top = drivers[:5] if len(drivers) >= 5 else drivers
    points = [25, 18, 15, 12, 10]
    tally = {d: 0 for d in top}
    rng = random.Random(2026)
    for _ in range(rounds):
        order = top.copy()
        rng.shuffle(order)
        for i, drv in enumerate(order):
            tally[drv] += points[i]
    standings = pd.DataFrame(
        [{"Driver": drv, "Points": pts} for drv, pts in tally.items()]
    ).sort_values(["Points", "Driver"], ascending=[False, True]).reset_index(drop=True)
    standings["Pos"] = np.arange(1, len(standings) + 1)
    return standings[["Pos", "Driver", "Points"]]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_saved_2026_prediction() -> dict | None:
    candidates = [
        repo_root() / "Formula-1-prediction" / "data" / "2026_prediction.json",
        repo_root() / "data" / "2026_prediction.json",
    ]
    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
    return None


def generate_2026_prediction() -> dict:
    script_path = repo_root() / "Formula-1-prediction" / "season_2026_calendar.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Missing generator script: {script_path}")

    spec = importlib.util.spec_from_file_location("season_2026_calendar", str(script_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "predict_full_season"):
        raise AttributeError("season_2026_calendar.py does not expose predict_full_season()")
    return module.predict_full_season()


with st.sidebar:
    st.header("⚙️ Prediction Settings")

    current_year = date.today().year
    training_year_options = list(range(max(2021, current_year - 5), current_year + 1))
    default_training = training_year_options[-3:] if len(training_year_options) >= 3 else training_year_options

    training_seasons = st.multiselect(
        "Training Seasons",
        options=training_year_options,
        default=default_training,
        help="More seasons gives stronger models but can take longer.",
    )

    predict_year_options = sorted({current_year - 1, current_year, current_year + 1})
    predict_year = st.selectbox(
        "Predict for Season",
        predict_year_options,
        index=predict_year_options.index(current_year),
    )

    selected_event_name = None
    circuit_name = None
    predict_round = 1
    try:
        _sched_preview = fastf1.get_event_schedule(predict_year, include_testing=False)
        _sched_preview = _sched_preview[_sched_preview["EventFormat"] != "testing"].copy()
        _sched_preview["RoundNumber"] = pd.to_numeric(_sched_preview["RoundNumber"], errors="coerce")
        _sched_preview = _sched_preview.dropna(subset=["RoundNumber"]).sort_values("RoundNumber")
        _sched_preview["RoundNumber"] = _sched_preview["RoundNumber"].astype(int)
        _sched_preview["RaceLabel"] = (
            "R" + _sched_preview["RoundNumber"].astype(str).str.zfill(2)
            + " - " + _sched_preview["EventName"].astype(str)
        )
        _race_label = st.selectbox("Race", _sched_preview["RaceLabel"].tolist(), index=0)
        _event_row = _sched_preview[_sched_preview["RaceLabel"] == _race_label].iloc[0]
        predict_round = int(_event_row["RoundNumber"])
        selected_event_name = str(_event_row["EventName"])
        circuit_name = str(_event_row.get("Location", selected_event_name))
    except Exception:
        predict_round = st.number_input("Round Number", min_value=1, max_value=24, value=1)

    st.divider()
    st.caption("FastF1/Ergast responses are cached locally after first load.")


if not training_seasons:
    st.warning("Please select at least one training season in the sidebar.")
    st.stop()

with st.spinner("📦 Loading historical race data..."):
    hist_df = fetch_historical_race_data(tuple(training_seasons))

if hist_df.empty:
    st.error("Could not load historical race data.")
    st.stop()

with st.spinner("🧠 Training race-order model..."):
    finish_model, finish_le, finish_mae = train_model(hist_df)

top3_key = f"{tuple(training_seasons)}::{len(hist_df)}::{int(pd.to_numeric(hist_df['Year'], errors='coerce').max())}"
if st.session_state.get("top3_model_key") != top3_key:
    with st.spinner("🌲 Training enhanced top-3 classifier..."):
        enhanced_df, enhanced_feature_cols = build_enhanced_training_frame(hist_df)
        if enhanced_df.empty:
            st.error("Enhanced training frame could not be built.")
            st.stop()
        top3_model, top3_cv_acc = train_enhanced_top3_model(enhanced_df, enhanced_feature_cols)
        st.session_state.top3_model_key = top3_key
        st.session_state.top3_model = top3_model
        st.session_state.top3_cv_acc = top3_cv_acc
        st.session_state.enhanced_df = enhanced_df
        st.session_state.enhanced_feature_cols = enhanced_feature_cols

top3_model = st.session_state.top3_model
top3_cv_acc = st.session_state.top3_cv_acc
enhanced_df = st.session_state.enhanced_df
enhanced_feature_cols = st.session_state.enhanced_feature_cols

baseline_standings_df, standings_meta = fetch_driver_standings(int(predict_year))
driver_stats_df = build_driver_stats(hist_df, enhanced_df)

stat1, stat2, stat3, stat4 = st.columns(4)
stat1.metric("Training Records", f"{len(hist_df):,}")
stat2.metric("Seasons", len(training_seasons))
stat3.metric("Race Order MAE", f"±{finish_mae}")
stat4.metric("Top-3 CV Accuracy", f"{top3_cv_acc:.1%}" if not np.isnan(top3_cv_acc) else "N/A")

if selected_event_name and circuit_name:
    st.info(
        f"🏁 **{selected_event_name} {predict_year}** — Circuit: {circuit_name} | Round {predict_round}"
    )
else:
    circuit_name = st.text_input("Circuit Name", value="Bahrain")


tabs = st.tabs([
    "Winner Predictor",
    "Race Order",
    "Weather Impact",
    "Tire Strategy",
    "Feature Importance",
    "Driver Comparison",
    "Race Simulation",
    "2026 Season",
])


with tabs[0]:
    st.subheader("🏆 Enhanced Winner Predictor (Top-3 Probability)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        wp_grid = st.selectbox("Grid Position", [1, 2, 3, 5, 10, 15], index=0)
    with c2:
        wp_weather = st.selectbox("Weather", WEATHER_CHOICES, index=0, format_func=lambda x: x.replace("_", " ").title())
    with c3:
        wp_tire = st.selectbox("Starting Tire", TIRE_CHOICES, index=1)
    with c4:
        wp_circuit = st.selectbox("Circuit Type", CIRCUIT_CHOICES, index=0)

    if st.button("🎯 Predict with All Factors", type="primary", width="stretch"):
        row = build_single_scenario_features(
            grid_pos=wp_grid,
            weather=wp_weather,
            tire=wp_tire,
            circuit_type=wp_circuit,
            feature_cols=enhanced_feature_cols,
            enhanced_df=enhanced_df,
        )
        prob = float(top3_model.predict_proba(row)[0][1])
        pred = "Top-3 Likely" if prob > 0.5 else "Top-3 Unlikely"
        if prob > 0.7:
            insight = "Excellent podium chances."
        elif prob > 0.5:
            insight = "Good podium chances."
        else:
            insight = "Difficult podium path; strategy and race events are crucial."
        st.session_state.single_pred = {
            "prob": prob,
            "pred": pred,
            "insight": insight,
            "grid": wp_grid,
            "weather": wp_weather,
            "tire": wp_tire,
            "circuit": wp_circuit,
        }

    single_pred = st.session_state.get("single_pred")
    if single_pred:
        m1, m2 = st.columns(2)
        m1.metric("Top-3 Probability", f"{single_pred['prob']:.1%}")
        m2.metric("Prediction", single_pred["pred"])
        st.progress(float(single_pred["prob"]))
        st.caption(
            f"Grid P{single_pred['grid']} | Weather: {single_pred['weather']} | "
            f"Tire: {single_pred['tire']} | Circuit: {single_pred['circuit']}"
        )
        st.info(single_pred["insight"])


with tabs[1]:
    st.subheader("🏎️ Full Grid Race-Order Prediction")
    grid_df, grid_note = build_default_grid(hist_df, int(predict_year))
    st.caption(grid_note)
    edited_grid = st.data_editor(
        grid_df,
        num_rows="fixed",
        width="stretch",
        column_config={
            "Driver": st.column_config.TextColumn("Driver Code", max_chars=3),
            "Team": st.column_config.TextColumn("Team"),
            "GridPosition": st.column_config.NumberColumn("Grid Position", min_value=1, max_value=22, step=1),
        },
        key="race_order_grid_editor",
    )

    run_predict = st.button("🚀 Generate Race-Order Prediction", type="primary", width="stretch")
    if run_predict:
        cleaned = edited_grid.copy()
        cleaned["Driver"] = cleaned["Driver"].astype(str).str.upper().str.strip()
        cleaned["Team"] = cleaned["Team"].astype(str).str.strip()
        cleaned["GridPosition"] = pd.to_numeric(cleaned["GridPosition"], errors="coerce")
        cleaned = cleaned.dropna(subset=["Driver", "GridPosition"]).drop_duplicates(subset=["Driver"], keep="first")
        grid = dict(zip(cleaned["Driver"], cleaned["GridPosition"].astype(int)))
        teams = dict(zip(cleaned["Driver"], cleaned["Team"]))

        predictions = predict_race(
            model=finish_model,
            le=finish_le,
            historical_df=hist_df,
            grid=grid,
            teams=teams,
            circuit=circuit_name,
            predict_year=int(predict_year),
            predict_round=int(predict_round),
        )
        st.session_state.full_race_predictions = predictions
        st.session_state.full_race_grid = cleaned

    predictions = st.session_state.get("full_race_predictions")
    if predictions is not None and not predictions.empty:
        medals = ["🥇", "🥈", "🥉"]
        podium_cols = st.columns(3)
        for i, col in enumerate(podium_cols):
            if i < len(predictions):
                row = predictions.iloc[i]
                delta = int(row["GridPosition"]) - int(row["PredictedPosition"])
                arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
                col.metric(
                    f"{medals[i]} Predicted P{i + 1}",
                    row["Driver"],
                    f"Grid P{int(row['GridPosition'])} ({arrow}{abs(delta)})" if delta != 0 else f"Grid P{int(row['GridPosition'])}",
                )

        left, right = st.columns([3, 2])
        with left:
            display = predictions[["PredictedPosition", "Driver", "Team", "GridPosition", "Confidence"]].copy()
            display.columns = ["Pos", "Driver", "Team", "Grid", "Confidence %"]
            st.dataframe(display, hide_index=True, width="stretch")
        with right:
            p2 = predictions.copy()
            p2["PositionChange"] = p2["GridPosition"].astype(int) - p2["PredictedPosition"].astype(int)
            fig_pc = px.bar(
                p2.sort_values("PredictedPosition"),
                x="Driver",
                y="PositionChange",
                color="PositionChange",
                color_continuous_scale=["#e63946", "#f4f1de", "#2dc653"],
                color_continuous_midpoint=0,
            )
            fig_pc.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(t=10),
            )
            st.plotly_chart(fig_pc, width="stretch")

        projected_df, rounds_left = build_projected_final_standings(
            predictions_df=predictions,
            baseline_df=baseline_standings_df,
            total_rounds=int(standings_meta.get("total_rounds", 0)),
            selected_round=int(predict_round),
        )
        st.caption(
            f"Projected final standings if this predicted order repeated for the remaining {rounds_left} round(s)."
        )
        st.dataframe(projected_df, hide_index=True, width="stretch")

        dl_df = predictions[["PredictedPosition", "Driver", "Team", "GridPosition", "Confidence"]].copy()
        dl_df.columns = ["Predicted Position", "Driver", "Team", "Grid Position", "Confidence %"]
        dl_df.insert(0, "Race", f"{circuit_name} {predict_year}")
        cdl1, cdl2 = st.columns(2)
        cdl1.download_button(
            "📄 Download CSV",
            data=dl_df.to_csv(index=False).encode("utf-8"),
            file_name=f"f1_predictions_{str(circuit_name).replace(' ', '_')}_{predict_year}.csv",
            mime="text/csv",
            width="stretch",
        )
        if importlib.util.find_spec("openpyxl") is not None:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                dl_df.to_excel(writer, index=False, sheet_name="Predictions")
                projected_df.to_excel(writer, index=False, sheet_name="Projected_Standings")
            cdl2.download_button(
                "📊 Download Excel",
                data=excel_buffer.getvalue(),
                file_name=f"f1_predictions_{str(circuit_name).replace(' ', '_')}_{predict_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        else:
            cdl2.info("Install `openpyxl` to enable Excel export.")


with tabs[2]:
    st.subheader("🌦️ Weather Impact Analysis")
    w1, w2, w3 = st.columns(3)
    with w1:
        wa_grid = st.slider("Grid Position", min_value=1, max_value=20, value=5)
    with w2:
        wa_tire = st.selectbox("Starting Tire", TIRE_CHOICES, index=1, key="wa_tire")
    with w3:
        wa_circuit = st.selectbox("Circuit Type", CIRCUIT_CHOICES, index=0, key="wa_circuit")

    weather_rows = []
    for weather in WEATHER_CHOICES:
        row = build_single_scenario_features(
            grid_pos=int(wa_grid),
            weather=weather,
            tire=wa_tire,
            circuit_type=wa_circuit,
            feature_cols=enhanced_feature_cols,
            enhanced_df=enhanced_df,
        )
        prob = float(top3_model.predict_proba(row)[0][1])
        weather_rows.append({"Weather": weather, "Top3Probability": prob})
    weather_df = pd.DataFrame(weather_rows)

    wm1, wm2, wm3 = st.columns(3)
    wm1.metric("Dry", f"{weather_df.loc[weather_df['Weather']=='DRY', 'Top3Probability'].iloc[0]:.1%}")
    wm2.metric("Light Rain", f"{weather_df.loc[weather_df['Weather']=='LIGHT_RAIN', 'Top3Probability'].iloc[0]:.1%}")
    wm3.metric("Heavy Rain", f"{weather_df.loc[weather_df['Weather']=='HEAVY_RAIN', 'Top3Probability'].iloc[0]:.1%}")

    fig_weather = px.bar(
        weather_df,
        x="Weather",
        y="Top3Probability",
        color="Weather",
        text=weather_df["Top3Probability"].map(lambda x: f"{x:.1%}"),
        color_discrete_map={"DRY": "#f1c40f", "LIGHT_RAIN": "#3498db", "HEAVY_RAIN": "#2c3e50"},
    )
    fig_weather.update_layout(
        yaxis=dict(tickformat=".0%"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20),
        showlegend=False,
    )
    st.plotly_chart(fig_weather, width="stretch")

    st.caption(
        "Interpretation: this model estimates podium probability under each weather profile "
        f"for grid P{wa_grid}, tire {wa_tire}, circuit {wa_circuit}."
    )


with tabs[3]:
    st.subheader("🛞 Tire Strategy Optimizer")
    t1, t2, t3 = st.columns(3)
    with t1:
        ts_grid = st.slider("Grid Position", min_value=1, max_value=20, value=6, key="ts_grid")
    with t2:
        ts_weather = st.selectbox("Weather", WEATHER_CHOICES, index=0, key="ts_weather")
    with t3:
        ts_circuit = st.selectbox("Circuit Type", CIRCUIT_CHOICES, index=0, key="ts_circuit")

    tire_rows = []
    for tire in TIRE_CHOICES:
        row = build_single_scenario_features(
            grid_pos=int(ts_grid),
            weather=ts_weather,
            tire=tire,
            circuit_type=ts_circuit,
            feature_cols=enhanced_feature_cols,
            enhanced_df=enhanced_df,
        )
        prob = float(top3_model.predict_proba(row)[0][1])
        tire_rows.append(
            {
                "Tire": tire,
                "Top3Probability": prob,
                "DegRate_sPerLap": TIRE_DEG[tire],
                "SuggestedPitLap": OPTIMAL_PIT[tire],
            }
        )
    tire_df = pd.DataFrame(tire_rows).sort_values("Top3Probability", ascending=False).reset_index(drop=True)

    tm1, tm2, tm3 = st.columns(3)
    tm1.metric("Recommended Tire", tire_df.iloc[0]["Tire"])
    tm2.metric("Podium Probability", f"{tire_df.iloc[0]['Top3Probability']:.1%}")
    tm3.metric("Suggested Pit Lap", f"L{int(tire_df.iloc[0]['SuggestedPitLap'])}")

    fig_tire = px.bar(
        tire_df,
        x="Tire",
        y="Top3Probability",
        color="Tire",
        text=tire_df["Top3Probability"].map(lambda x: f"{x:.1%}"),
        color_discrete_map={"SOFT": "#e74c3c", "MEDIUM": "#f1c40f", "HARD": "#ecf0f1"},
    )
    fig_tire.update_layout(
        yaxis=dict(tickformat=".0%"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20),
        showlegend=False,
    )
    st.plotly_chart(fig_tire, width="stretch")

    st.dataframe(
        tire_df.rename(
            columns={
                "Top3Probability": "Top-3 Probability",
                "DegRate_sPerLap": "Degradation (s/lap)",
                "SuggestedPitLap": "Suggested Pit Lap",
            }
        ),
        hide_index=True,
        width="stretch",
    )


with tabs[4]:
    st.subheader("📈 Feature Importance")
    fi_top3 = pd.DataFrame(
        {"Feature": enhanced_feature_cols, "Importance": top3_model.feature_importances_}
    ).sort_values("Importance", ascending=False).head(20)

    fi_race = get_feature_importance(finish_model)
    left, right = st.columns(2)
    with left:
        fig_fi_top3 = px.bar(
            fi_top3.sort_values("Importance"),
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="viridis",
        )
        fig_fi_top3.update_layout(
            title="Enhanced Top-3 Model (Top 20)",
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40),
        )
        st.plotly_chart(fig_fi_top3, width="stretch")
    with right:
        fig_fi_race = px.bar(
            fi_race.sort_values("Importance"),
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="reds",
        )
        fig_fi_race.update_layout(
            title="Race-Order Model",
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40),
        )
        st.plotly_chart(fig_fi_race, width="stretch")


with tabs[5]:
    st.subheader("👥 Driver Head-to-Head")
    if driver_stats_df.empty:
        st.info("Driver comparison stats unavailable.")
    else:
        driver_options = driver_stats_df["Abbreviation"].tolist()
        d1, d2 = st.columns(2)
        with d1:
            driver1 = st.selectbox("Driver 1", driver_options, index=0, format_func=lambda x: f"{x} - {DRIVER_NAME_MAP.get(x, x)}")
        with d2:
            alt_index = 1 if len(driver_options) > 1 else 0
            driver2 = st.selectbox("Driver 2", driver_options, index=alt_index, format_func=lambda x: f"{x} - {DRIVER_NAME_MAP.get(x, x)}")

        s1 = driver_stats_df[driver_stats_df["Abbreviation"] == driver1].iloc[0]
        s2 = driver_stats_df[driver_stats_df["Abbreviation"] == driver2].iloc[0]

        categories = ["Wins", "Podiums", "Poles", "Wet Wins", "Street Wins", "Career Points"]
        s1_vals = [s1["wins"], s1["podiums"], s1["poles"], s1["wet_wins"], s1["street_wins"], s1["career_points"]]
        s2_vals = [s2["wins"], s2["podiums"], s2["poles"], s2["wet_wins"], s2["street_wins"], s2["career_points"]]

        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Bar(x=categories, y=s1_vals, name=f"{driver1} ({s1['team']})", marker_color="#1f77b4"))
        fig_cmp.add_trace(go.Bar(x=categories, y=s2_vals, name=f"{driver2} ({s2['team']})", marker_color="#e74c3c"))
        fig_cmp.update_layout(
            barmode="group",
            title=f"{s1['name']} vs {s2['name']}",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=45),
        )
        st.plotly_chart(fig_cmp, width="stretch")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"{driver1} Races", int(s1["races"]))
        c2.metric(f"{driver2} Races", int(s2["races"]))
        c3.metric(f"{driver1} Win Rate", f"{float(s1['win_rate']):.1f}%")
        c4.metric(f"{driver2} Win Rate", f"{float(s2['win_rate']):.1f}%")

        st.caption(
            f"{s1['name']}: {int(s1['wins'])} wins | {int(s1['podiums'])} podiums | {float(s1['career_points']):.1f} points | "
            f"avg finish {float(s1['avg_finish']):.2f}"
        )
        st.caption(
            f"{s2['name']}: {int(s2['wins'])} wins | {int(s2['podiums'])} podiums | {float(s2['career_points']):.1f} points | "
            f"avg finish {float(s2['avg_finish']):.2f}"
        )


with tabs[6]:
    st.subheader("🎮 Race & Championship Simulation")
    sim_drivers = build_default_grid(hist_df, int(predict_year))[0]["Driver"].head(20).tolist()
    s1, s2, s3 = st.columns([1, 1, 2])
    with s1:
        sim_weather = st.selectbox("Race Weather", ["DRY", "LIGHT_RAIN", "HEAVY_RAIN"], index=0)
    with s2:
        run_sim_race = st.button("Simulate Race", type="primary", width="stretch")
    with s3:
        run_sim_champ = st.button("Simulate 5-Race Championship", width="stretch")

    if run_sim_race:
        sim_df = simulate_standard_race(sim_drivers, sim_weather)
        st.session_state.quick_race_sim = sim_df
    if run_sim_champ:
        champ_df = simulate_championship(sim_drivers, rounds=5)
        st.session_state.quick_champ_sim = champ_df

    sim_df = st.session_state.get("quick_race_sim")
    if sim_df is not None and not sim_df.empty:
        st.markdown("**Race Result**")
        st.dataframe(sim_df.rename(columns={"Position": "Pos"}), hide_index=True, width="stretch")
        top10 = sim_df.head(10).copy().sort_values("Position", ascending=False)
        fig_sim = px.bar(
            top10,
            x="Position",
            y="Driver",
            orientation="h",
            text="Position",
            color="Position",
            color_continuous_scale="bluered",
        )
        fig_sim.update_layout(
            xaxis=dict(autorange="reversed"),
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20),
        )
        st.plotly_chart(fig_sim, width="stretch")

    champ_df = st.session_state.get("quick_champ_sim")
    if champ_df is not None and not champ_df.empty:
        st.markdown("**Championship Standings (5 races)**")
        st.dataframe(champ_df, hide_index=True, width="stretch")
        leader = champ_df.iloc[0]
        st.metric("Champion", leader["Driver"], f"{int(leader['Points'])} pts")


with tabs[7]:
    st.subheader("🔮 2026 Season Projection")
    st.caption(
        "Loads `2026_prediction.json` if present, or runs the Formula generator "
        "(`Formula-1-prediction/season_2026_calendar.py`) on demand."
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Load Saved 2026 Projection", width="stretch"):
            loaded = load_saved_2026_prediction()
            if loaded:
                st.session_state.pred_2026_data = loaded
            else:
                st.warning("No saved 2026 projection file found.")
    with b2:
        if st.button("Generate 2026 Projection", type="primary", width="stretch"):
            try:
                with st.spinner("Running 2026 simulation..."):
                    st.session_state.pred_2026_data = generate_2026_prediction()
            except Exception as exc:
                st.error(f"2026 generation failed: {exc}")

    season_data = st.session_state.get("pred_2026_data")
    if season_data:
        standings = pd.DataFrame(season_data.get("standings", []))
        if standings.empty:
            st.info("No standings found in projection payload.")
        else:
            standings = standings.copy()
            if "points" in standings.columns:
                standings = standings.sort_values("points", ascending=False).reset_index(drop=True)
            standings["Pos"] = np.arange(1, len(standings) + 1)

            leader = standings.iloc[0]
            m1, m2, m3 = st.columns(3)
            m1.metric("Predicted Champion", leader.get("name", leader.get("code", "N/A")))
            m2.metric("Team", leader.get("team", "N/A"))
            m3.metric("Points", int(leader.get("points", 0)))

            fig_2026 = px.bar(
                standings.head(10).sort_values("points"),
                x="points",
                y=standings.head(10).sort_values("points")["name"] if "name" in standings.columns else "code",
                orientation="h",
                color="points",
                color_continuous_scale="plasma",
            )
            fig_2026.update_layout(
                title="2026 Championship Points (Top 10)",
                coloraxis_showscale=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=45),
            )
            st.plotly_chart(fig_2026, width="stretch")
            st.dataframe(standings, hide_index=True, width="stretch")

            race_results = pd.DataFrame(season_data.get("race_results", []))
            if not race_results.empty:
                with st.expander("Show All 2026 Race Results"):
                    st.dataframe(race_results, hide_index=True, width="stretch")
