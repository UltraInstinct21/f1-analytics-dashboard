# utils/ml_predictions.py
import fastf1
import fastf1.ergast as ergast
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

fastf1.Cache.enable_cache('.fastf1-cache')


# ─────────────────────────────────────────────
# 1. DATA COLLECTION
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_historical_race_data(seasons: list) -> pd.DataFrame:
    """
    Collects race-result training rows for the given seasons.
    Returns a flat DataFrame with one row per driver per race.
    """
    seasons = sorted({int(s) for s in seasons})
    records = []

    for year in seasons:
        try:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
        except Exception:
            continue
        completed = schedule[schedule['EventFormat'] != 'testing'].copy()
        event_date_col = next(
            (c for c in ['EventDate', 'Session5Date', 'RaceDate'] if c in completed.columns),
            None
        )
        if event_date_col:
            event_dates = pd.to_datetime(completed[event_date_col], errors='coerce', utc=True)
            now_utc = pd.Timestamp.now(tz='UTC')
            completed = completed[event_dates.notna() & (event_dates <= now_utc)]

        for _, event in completed.iterrows():
            round_num = int(event.get('RoundNumber', 0) or 0)
            if round_num <= 0:
                continue
            event_name = event.get('EventName', f'Round {round_num}')
            circuit = event.get('Location', event_name)

            try:
                race_results = ergast.fetch_results(year, round_num, 'Race')
            except Exception:
                continue

            if not race_results:
                continue

            for row in race_results:
                driver = row.get('Driver', {}) or {}
                team = row.get('Constructor', {}) or {}
                drv_code = driver.get('code') or (driver.get('familyName', 'UNK')[:3].upper())

                finish_pos = pd.to_numeric(row.get('position'), errors='coerce')
                grid_pos = pd.to_numeric(row.get('grid'), errors='coerce')
                if pd.isna(finish_pos) or pd.isna(grid_pos):
                    continue

                records.append({
                    'DriverNumber': driver.get('permanentNumber', row.get('number')),
                    'Abbreviation': drv_code,
                    'TeamName': team.get('name', 'Unknown'),
                    'GridPosition': float(grid_pos),
                    'FinishPosition': float(finish_pos),
                    'Points': pd.to_numeric(row.get('points'), errors='coerce'),
                    'Year': int(year),
                    'Round': int(round_num),
                    'EventName': event_name,
                    'Circuit': circuit,
                })

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df.dropna(subset=['FinishPosition', 'GridPosition'], inplace=True)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_driver_standings(year: int) -> tuple[pd.DataFrame, dict]:
    """
    Builds driver standings from completed rounds for a season.
    Includes race points and sprint points (when available).
    """
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception:
        return pd.DataFrame(), {"completed_rounds": 0, "total_rounds": 0}

    schedule = schedule[schedule['EventFormat'] != 'testing'].copy()
    schedule['RoundNumber'] = pd.to_numeric(schedule['RoundNumber'], errors='coerce')
    schedule = schedule.dropna(subset=['RoundNumber']).sort_values('RoundNumber')
    schedule['RoundNumber'] = schedule['RoundNumber'].astype(int)

    total_rounds = int(schedule['RoundNumber'].nunique()) if not schedule.empty else 0
    event_date_col = next(
        (c for c in ['EventDate', 'Session5Date', 'RaceDate'] if c in schedule.columns),
        None
    )
    if event_date_col:
        event_dates = pd.to_datetime(schedule[event_date_col], errors='coerce', utc=True)
        now_utc = pd.Timestamp.now(tz='UTC')
        schedule = schedule[event_dates.notna() & (event_dates <= now_utc)]

    if schedule.empty:
        return pd.DataFrame(), {"completed_rounds": 0, "total_rounds": total_rounds}

    completed_rounds = int(schedule['RoundNumber'].nunique())
    race_rows = []
    bonus_rows = []

    for _, event in schedule.iterrows():
        round_num = int(event['RoundNumber'])

        try:
            race_results = ergast.fetch_results(year, round_num, 'Race') or []
        except Exception:
            race_results = []

        for row in race_results:
            driver = row.get('Driver', {}) or {}
            team = row.get('Constructor', {}) or {}
            code = driver.get('code') or (driver.get('familyName', 'UNK')[:3].upper())
            full_name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip() or code

            finish = pd.to_numeric(row.get('position'), errors='coerce')
            points = pd.to_numeric(row.get('points'), errors='coerce')
            if pd.isna(finish) or pd.isna(points):
                continue

            race_rows.append({
                'Driver': code,
                'DriverName': full_name,
                'Team': team.get('name', 'Unknown'),
                'FinishPosition': int(finish),
                'RacePoints': float(points),
            })

        # Sprint points are part of championship standings; add when present.
        try:
            sprint_results = ergast.fetch_results(year, round_num, 'Sprint') or []
        except Exception:
            sprint_results = []

        for row in sprint_results:
            driver = row.get('Driver', {}) or {}
            code = driver.get('code') or (driver.get('familyName', 'UNK')[:3].upper())
            sprint_pts = pd.to_numeric(row.get('points'), errors='coerce')
            if pd.isna(sprint_pts):
                continue
            bonus_rows.append({'Driver': code, 'SprintPoints': float(sprint_pts)})

    if not race_rows:
        return pd.DataFrame(), {"completed_rounds": completed_rounds, "total_rounds": total_rounds}

    race_df = pd.DataFrame(race_rows)
    st_df = race_df.groupby(['Driver', 'DriverName', 'Team'], as_index=False).agg(
        RacePoints=('RacePoints', 'sum'),
        Wins=('FinishPosition', lambda s: int((s == 1).sum())),
        Podiums=('FinishPosition', lambda s: int((s <= 3).sum())),
        BestFinish=('FinishPosition', 'min'),
    )

    if bonus_rows:
        sprint_df = pd.DataFrame(bonus_rows).groupby('Driver', as_index=False).agg(
            SprintPoints=('SprintPoints', 'sum')
        )
        st_df = st_df.merge(sprint_df, on='Driver', how='left')
    else:
        st_df['SprintPoints'] = 0.0

    st_df['SprintPoints'] = st_df['SprintPoints'].fillna(0.0)
    st_df['Points'] = (st_df['RacePoints'] + st_df['SprintPoints']).round(1)
    st_df = st_df.sort_values(
        ['Points', 'Wins', 'Podiums', 'BestFinish', 'Driver'],
        ascending=[False, False, False, True, True]
    ).reset_index(drop=True)
    st_df['Pos'] = np.arange(1, len(st_df) + 1)

    cols = ['Pos', 'Driver', 'DriverName', 'Team', 'Points', 'Wins', 'Podiums', 'BestFinish']
    return st_df[cols], {"completed_rounds": completed_rounds, "total_rounds": total_rounds}


# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────

def build_features(df: pd.DataFrame):
    """
    Adds rolling/historical features:
    - driver_avg_finish_last5: rolling avg finish position (last 5 races)
    - team_avg_finish_last5: team rolling avg
    - driver_circuit_avg: driver's historical avg at this circuit
    - grid_position: qualifying position
    Returns (df_with_features, label_encoder)
    """
    df = df.sort_values(['Year', 'Round']).copy()

    # Rolling avg finish for driver (last 5 races)
    df['driver_avg_finish_last5'] = (
        df.groupby('Abbreviation')['FinishPosition']
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    )

    # Rolling avg finish for team (last 5 races)
    df['team_avg_finish_last5'] = (
        df.groupby('TeamName')['FinishPosition']
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    )

    # Driver's historical avg at this specific circuit
    df['driver_circuit_avg'] = (
        df.groupby(['Abbreviation', 'Circuit'])['FinishPosition']
        .transform(lambda x: x.shift(1).expanding().mean())
    )
    df['driver_circuit_avg'].fillna(df['driver_avg_finish_last5'], inplace=True)

    # Encode team name
    le = LabelEncoder()
    df['team_encoded'] = le.fit_transform(df['TeamName'].fillna('Unknown'))

    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df['Round'] = pd.to_numeric(df['Round'], errors='coerce')

    return df, le


# ─────────────────────────────────────────────
# 3. MODEL TRAINING
# ─────────────────────────────────────────────

FEATURE_COLS = [
    'Year',
    'Round',
    'GridPosition',
    'driver_avg_finish_last5',
    'team_avg_finish_last5',
    'driver_circuit_avg',
    'team_encoded',
]


@st.cache_resource(show_spinner=False)
def train_model(df: pd.DataFrame):
    """
    Trains a GradientBoostingRegressor to predict finish position.
    Returns (model, label_encoder, cv_mae).
    """
    df_feat, le = build_features(df)
    df_feat = df_feat.dropna(subset=FEATURE_COLS).copy()

    X = df_feat[FEATURE_COLS]
    y = df_feat['FinishPosition']

    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        random_state=42
    )
    model.fit(X, y)

    cv_folds = min(5, len(X))
    if cv_folds >= 3:
        scores = cross_val_score(model, X, y, cv=cv_folds, scoring='neg_mean_absolute_error')
        mae = round(-scores.mean(), 2)
    else:
        mae = round(float(np.mean(np.abs(model.predict(X) - y))), 2)

    return model, le, mae


# ─────────────────────────────────────────────
# 4. PREDICTION FOR UPCOMING RACE
# ─────────────────────────────────────────────

def predict_race(
    model,
    le,
    historical_df: pd.DataFrame,
    grid: dict,
    teams: dict,
    circuit: str,
    predict_year: int,
    predict_round: int,
) -> pd.DataFrame:
    """
    Predicts finish positions for an upcoming race.

    Args:
        model: trained GradientBoostingRegressor
        le: fitted LabelEncoder for team names
        historical_df: raw historical DataFrame (will be feature-engineered internally)
        grid: {driver_abbrev: grid_position}  e.g. {'VER': 1, 'NOR': 2, ...}
        teams: {driver_abbrev: team_name}
        circuit: circuit location string (for circuit-specific history lookup)

    Returns:
        DataFrame with PredictedPosition, Driver, Team, GridPosition, Confidence
    """
    hist_feat, _ = build_features(historical_df)

    rows = []
    for driver, grid_pos in grid.items():
        team = teams.get(driver, 'Unknown')

        drv_hist  = hist_feat[hist_feat['Abbreviation'] == driver]
        team_hist = hist_feat[hist_feat['TeamName'] == team]
        circ_hist = drv_hist[drv_hist['Circuit'] == circuit]

        drv_avg  = drv_hist['FinishPosition'].tail(5).mean()  if len(drv_hist)  else 10.0
        team_avg = team_hist['FinishPosition'].tail(5).mean() if len(team_hist) else 10.0
        circ_avg = circ_hist['FinishPosition'].mean()         if len(circ_hist) else drv_avg

        try:
            team_enc = le.transform([team])[0]
        except ValueError:
            team_enc = 0  # unseen team (e.g. Cadillac debut)

        rows.append({
            'Driver':                   driver,
            'Team':                     team,
            'Year':                     int(predict_year),
            'Round':                    int(predict_round),
            'GridPosition':             grid_pos,
            'driver_avg_finish_last5':  drv_avg,
            'team_avg_finish_last5':    team_avg,
            'driver_circuit_avg':       circ_avg,
            'team_encoded':             team_enc,
        })

    X_pred = pd.DataFrame(rows)[FEATURE_COLS]
    raw_preds = model.predict(X_pred)

    result = pd.DataFrame({
        'Driver':        [r['Driver']      for r in rows],
        'Team':          [r['Team']        for r in rows],
        'GridPosition':  [r['GridPosition'] for r in rows],
        'RawPrediction': raw_preds,
    })
    result['Confidence'] = (
        (1 - np.abs(result['RawPrediction'] - np.round(result['RawPrediction']))) * 100
    ).clip(50, 99).astype(int)

    result = result.sort_values('RawPrediction').reset_index(drop=True)
    result['PredictedPosition'] = range(1, len(result) + 1)

    return result.drop(columns=['RawPrediction'])


# ─────────────────────────────────────────────
# 5. FEATURE IMPORTANCE
# ─────────────────────────────────────────────

def get_feature_importance(model) -> pd.DataFrame:
    labels = [
        'Season Year',
        'Round Number',
        'Grid Position',
        'Driver Form (last 5)',
        'Team Form (last 5)',
        'Driver Circuit History',
        'Team',
    ]
    return pd.DataFrame({
        'Feature':    labels,
        'Importance': model.feature_importances_,
    }).sort_values('Importance', ascending=False)
