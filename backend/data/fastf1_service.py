"""
FastF1 Data Service Module
===========================
Provides structured data retrieval from FastF1 and Ergast APIs for:
- Event schedules and standings
- Weekend session information and dynamic circuit geometry
- Session lap time pace distributions and tyre stint strategies
- Multi-driver distance-synchronized telemetry
- Head-to-head driver comparisons
- Replay telemetry frames (25 FPS)
"""

import os
import math

import json
from pathlib import Path
import numpy as np
import pandas as pd
import fastf1
import fastf1.ergast as ergast
import fastf1.plotting
from backend.config import FASTF1_CACHE_DIR, COMPUTED_DATA_DIR

# Team Color map for rich UI consistency
TEAM_COLORS = {
    "Red Bull": "#3671C6",
    "Red Bull Racing": "#3671C6",
    "McLaren": "#FF8000",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "AlphaTauri": "#6692FF",
    "Racing Bulls": "#6692FF",
    "Sauber": "#52E252",
    "Kick Sauber": "#52E252",
    "Alfa Romeo": "#C92D4B",
    "Haas": "#B6BABD",
    "Haas F1 Team": "#B6BABD",
    "Cadillac": "#FFD700",
    "Cadillac F1": "#FFD700",
}

DRIVER_COLORS = {
    "VER": "#3671C6",
    "NOR": "#FF8000",
    "LEC": "#E8002D",
    "PIA": "#FFB000",
    "SAI": "#E8002D",
    "HAM": "#27F4D2",
    "RUS": "#27F4D2",
    "PER": "#3671C6",
    "ALO": "#229971",
    "STR": "#229971",
    "GAS": "#0093CC",
    "OCO": "#0093CC",
    "TSU": "#6692FF",
    "LAW": "#6692FF",
    "RIC": "#6692FF",
    "HUL": "#B6BABD",
    "MAG": "#B6BABD",
    "ALB": "#64C4FF",
    "COL": "#64C4FF",
    "BEA": "#B6BABD",
    "ANT": "#27F4D2",
    "BOT": "#52E252",
    "ZHO": "#52E252",
}

def get_team_color(team_name: str) -> str:
    if not team_name:
        return "#41A1CF"
    for k, color in TEAM_COLORS.items():
        if k.lower() in str(team_name).lower():
            return color
    return "#41A1CF"

def get_driver_color(driver_code: str, team_name: str = "") -> str:
    if driver_code in DRIVER_COLORS:
        return DRIVER_COLORS[driver_code]
    return get_team_color(team_name)


def enable_fastf1_cache():
    """Enable global FastF1 disk cache."""
    cache_path = str(FASTF1_CACHE_DIR)
    os.makedirs(cache_path, exist_ok=True)
    try:
        fastf1.Cache.enable_cache(cache_path)
    except Exception as e:
        print(f"FastF1 cache enable warning: {e}")

# Enable cache on module load
enable_fastf1_cache()


def get_available_seasons() -> list[int]:
    """Return available F1 season years."""
    return list(range(2018, 2027))


def format_lap_time(seconds: float) -> str:
    """Format float seconds into standard M:SS.sss lap string."""
    if pd.isna(seconds) or seconds <= 0:
        return "N/A"
    minutes = int(seconds // 60)
    rem_seconds = seconds % 60
    return f"{minutes}:{rem_seconds:06.3f}"


def get_event_schedule(year: int, include_testing: bool = False) -> pd.DataFrame:
    """Retrieve event schedule for a given season year."""
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=include_testing)
        return schedule
    except Exception as e:
        print(f"Error fetching schedule for {year}: {e}")
        return pd.DataFrame()


def get_session(year: int, event, session_id: str = "R", telemetry: bool = True, laps: bool = True, weather: bool = True):
    """Load a full FastF1 session."""
    try:
        session = fastf1.get_session(year, event, session_id)
        session.load(telemetry=telemetry, laps=laps, weather=weather)
        return session
    except Exception as e:
        print(f"Error loading session {year} {event} {session_id}: {e}")
        return None





from fastf1.ergast import Ergast

def _get_season_results_cached(year: int) -> list[dict]:
    """Fetch and cache all round race results for a season using fast Ergast API."""
    cache_file = COMPUTED_DATA_DIR / f"ergast_results_{year}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception:
            pass

    try:
        erg = Ergast()
        results_obj = erg.get_race_results(season=year, limit=1000)
        if not results_obj or not results_obj.content:
            return []

        desc_df = results_obj.description
        all_results = []

        for idx, race_df in enumerate(results_obj.content):
            if idx < len(desc_df):
                round_num = int(desc_df.iloc[idx].get('round', idx + 1))
                event_name = str(desc_df.iloc[idx].get('raceName', f'Round {round_num}'))
                circuit = str(desc_df.iloc[idx].get('circuitName', event_name))
            else:
                round_num = idx + 1
                event_name = f'Round {round_num}'
                circuit = event_name

            for _, row in race_df.iterrows():
                drv_code = str(row.get('driverCode') or (str(row.get('familyName', 'UNK'))[:3].upper()))
                if not drv_code or drv_code == 'NAN':
                    continue
                first_name = str(row.get('givenName', ''))
                last_name = str(row.get('familyName', ''))
                full_name = f"{first_name} {last_name}".strip() or drv_code
                team = str(row.get('constructorName', 'Unknown'))
                pos = pd.to_numeric(row.get('position'), errors='coerce')
                grid = pd.to_numeric(row.get('grid'), errors='coerce')
                pts = pd.to_numeric(row.get('points'), errors='coerce')

                all_results.append({
                    'DriverNumber': str(row.get('driverNumber') or row.get('number') or ''),
                    'Abbreviation': drv_code,
                    'DriverName': full_name,
                    'TeamName': team,
                    'GridPosition': float(grid) if pd.notna(grid) else 20.0,
                    'FinishPosition': float(pos) if pd.notna(pos) else 20.0,
                    'Points': float(pts) if pd.notna(pts) else 0.0,
                    'Year': int(year),
                    'Round': int(round_num),
                    'EventName': event_name,
                    'Circuit': circuit,
                })

        if all_results:
            try:
                with open(cache_file, "w") as f:
                    json.dump(all_results, f)
            except Exception:
                pass

        return all_results
    except Exception as e:
        print(f"Error in _get_season_results_cached for {year}: {e}")
        return []


def fetch_historical_race_data(seasons: list) -> pd.DataFrame:
    """Collect race-result training data for specified seasons."""
    seasons = sorted({int(s) for s in seasons})
    records = []

    for year in seasons:
        year_records = _get_season_results_cached(year)
        records.extend(year_records)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df.dropna(subset=['FinishPosition', 'GridPosition'], inplace=True)
    return df


def fetch_driver_standings(year: int) -> tuple[pd.DataFrame, dict]:
    """Build driver standings matrix for completed rounds of a season using Ergast API."""
    try:
        schedule = get_event_schedule(year)
        total_rounds = len(schedule) if not schedule.empty else 24

        records = _get_season_results_cached(year)
        if not records:
            # Fallback to direct driver standings endpoint
            try:
                erg = Ergast()
                st_obj = erg.get_driver_standings(season=year)
                if st_obj and st_obj.content:
                    st_df = st_obj.content[0]
                    rows = []
                    for _, r in st_df.iterrows():
                        code = str(r.get('driverCode') or str(r.get('familyName', 'UNK'))[:3].upper())
                        name = f"{r.get('givenName', '')} {r.get('familyName', '')}".strip()
                        team = r.get('constructorNames', ['Unknown'])[0] if isinstance(r.get('constructorNames'), list) and len(r.get('constructorNames')) > 0 else 'Unknown'
                        pts = float(r.get('points', 0.0))
                        wins = int(r.get('wins', 0))
                        pos = int(r.get('position', 1))
                        rows.append({
                            "Position": pos,
                            "Abbreviation": code,
                            "DriverName": name,
                            "TeamName": team,
                            "Points": pts,
                            "Wins": wins,
                            "Podiums": max(wins, int(pts // 20)),
                            "Color": get_driver_color(code, team)
                        })
                    df = pd.DataFrame(rows)
                    return df, {"completed_rounds": len(st_df), "total_rounds": total_rounds}
            except Exception:
                pass
            return pd.DataFrame(), {"completed_rounds": 0, "total_rounds": total_rounds}

        completed_rounds = len(set(r['Round'] for r in records))

        driver_stats = {}
        for r in records:
            code = r['Abbreviation']
            if code not in driver_stats:
                driver_stats[code] = {
                    "name": r['DriverName'],
                    "team": r['TeamName'],
                    "points": 0.0,
                    "wins": 0,
                    "podiums": 0,
                }
            pts = r['Points']
            pos = r['FinishPosition']
            driver_stats[code]["points"] += pts
            if pos == 1:
                driver_stats[code]["wins"] += 1
            if pos <= 3:
                driver_stats[code]["podiums"] += 1

        rows = []
        for code, stats in driver_stats.items():
            rows.append({
                "Abbreviation": code,
                "DriverName": stats["name"] or code,
                "TeamName": stats["team"],
                "Points": round(stats["points"], 1),
                "Wins": stats["wins"],
                "Podiums": stats["podiums"],
                "Color": get_driver_color(code, stats["team"])
            })

        df = pd.DataFrame(rows).sort_values(by=["Points", "Wins", "Podiums"], ascending=[False, False, False]).reset_index(drop=True)
        df["Position"] = range(1, len(df) + 1)
        meta = {"completed_rounds": completed_rounds, "total_rounds": total_rounds}
        return df, meta
    except Exception as e:
        print(f"Error fetching standings for {year}: {e}")
        return pd.DataFrame(), {"completed_rounds": 0, "total_rounds": 0}


def fetch_season_progression(year: int) -> list[dict]:
    """Calculate cumulative points progression by round for top drivers."""
    records = _get_season_results_cached(year)
    if not records:
        return []

    rounds = sorted(list(set(r['Round'] for r in records)))
    standings_df, _ = fetch_driver_standings(year)
    if standings_df.empty:
        return []

    top_drivers = standings_df['Abbreviation'].head(8).tolist()

    progression = []
    cumulative = {drv: 0.0 for drv in top_drivers}

    # Map round -> driver -> points
    round_pts_map = {rnd: {drv: 0.0 for drv in top_drivers} for rnd in rounds}
    for r in records:
        if r['Round'] in round_pts_map and r['Abbreviation'] in round_pts_map[r['Round']]:
            round_pts_map[r['Round']][r['Abbreviation']] += r['Points']

    for rnd in rounds:
        row = {"round": f"R{rnd}"}
        for drv in top_drivers:
            cumulative[drv] += round_pts_map[rnd][drv]
            row[drv] = round(cumulative[drv], 1)
        progression.append(row)

    return progression


def fetch_round_matrix(year: int) -> list[dict]:
    """Build round-by-round points score matrix for heatmap visualization."""
    records = _get_season_results_cached(year)
    if not records:
        return []

    rounds = sorted(list(set(r['Round'] for r in records)))
    standings_df, _ = fetch_driver_standings(year)
    if standings_df.empty:
        return []

    all_drivers = standings_df['Abbreviation'].tolist()
    matrix_map = {drv: {f"R{rnd}": 0.0 for rnd in rounds} for drv in all_drivers}

    for r in records:
        drv = r['Abbreviation']
        rnd = r['Round']
        if drv in matrix_map and f"R{rnd}" in matrix_map[drv]:
            matrix_map[drv][f"R{rnd}"] += r['Points']

    rows = []
    for drv in all_drivers:
        row = {
            "driver": drv,
            "team": standings_df.loc[standings_df['Abbreviation'] == drv, 'TeamName'].iloc[0],
            "totalPoints": float(standings_df.loc[standings_df['Abbreviation'] == drv, 'Points'].iloc[0])
        }
        for rnd in rounds:
            row[f"R{rnd}"] = int(matrix_map[drv][f"R{rnd}"])
        rows.append(row)

    return rows





def extract_circuit_geometry(telemetry_df: pd.DataFrame) -> dict:
    """Extract smooth, normalized 2D SVG track contour and turn telemetry from FastF1 telemetry."""
    if telemetry_df.empty or 'X' not in telemetry_df.columns or 'Y' not in telemetry_df.columns:
        return None

    xs = telemetry_df['X'].to_numpy().astype(float)
    ys = telemetry_df['Y'].to_numpy().astype(float)
    speeds = telemetry_df['Speed'].to_numpy().astype(float) if 'Speed' in telemetry_df.columns else np.zeros_like(xs)
    drs_arr = telemetry_df['DRS'].to_numpy().astype(float) if 'DRS' in telemetry_df.columns else np.zeros_like(xs)

    valid = np.isfinite(xs) & np.isfinite(ys)
    xs, ys, speeds, drs_arr = xs[valid], ys[valid], speeds[valid], drs_arr[valid]

    if len(xs) < 10:
        return None

    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()

    range_x = max(max_x - min_x, 1.0)
    range_y = max(max_y - min_y, 1.0)

    scale = min(680.0 / range_x, 380.0 / range_y)

    scaled_x = (xs - min_x) * scale + 60.0
    scaled_y = 440.0 - (ys - min_y) * scale

    step = max(1, len(scaled_x) // 180)
    pts_x = scaled_x[::step]
    pts_y = scaled_y[::step]
    pts_speed = speeds[::step]
    pts_drs = drs_arr[::step]

    path_d = f"M {pts_x[0]:.1f} {pts_y[0]:.1f}"
    for px, py in zip(pts_x[1:], pts_y[1:]):
        path_d += f" L {px:.1f} {py:.1f}"
    path_d += " Z"

    start_line = {
        "x1": round(float(pts_x[0] - 6), 1),
        "y1": round(float(pts_y[0] - 6), 1),
        "x2": round(float(pts_x[0] + 6), 1),
        "y2": round(float(pts_y[0] + 6), 1),
    }

    turns = []
    if len(pts_speed) > 10:
        kernel_size = 5
        smoothed_speed = np.convolve(pts_speed, np.ones(kernel_size)/kernel_size, mode='same')
        local_min_indices = []
        for i in range(2, len(smoothed_speed) - 2):
            if smoothed_speed[i] < smoothed_speed[i-1] and smoothed_speed[i] < smoothed_speed[i+1]:
                if smoothed_speed[i] < 180:
                    local_min_indices.append(i)

        if len(local_min_indices) > 0:
            spaced_indices = [local_min_indices[0]]
            for idx in local_min_indices[1:]:
                if idx - spaced_indices[-1] > 12:
                    spaced_indices.append(idx)
            for turn_no, idx in enumerate(spaced_indices[:8], 1):
                turns.append({
                    "number": turn_no,
                    "name": f"T{turn_no}",
                    "x": round(float(pts_x[idx]), 1),
                    "y": round(float(pts_y[idx]), 1)
                })

    drs_zones = []
    drs_active_indices = np.where(pts_drs >= 10)[0]
    if len(drs_active_indices) > 0:
        drs_mid = drs_active_indices[len(drs_active_indices)//2]
        drs_zones.append({
            "name": "DRS Zone 1",
            "x": round(float(pts_x[drs_mid]), 1),
            "y": round(float(pts_y[drs_mid]), 1)
        })

    return {
        "pathD": path_d,
        "viewBox": "0 0 800 500",
        "startLine": start_line,
        "turns": turns,
        "drsZones": drs_zones,
        "points": [{"x": round(float(px), 1), "y": round(float(py), 1)} for px, py in zip(pts_x, pts_y)]
    }



