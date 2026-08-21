"""
F1 Analysis & Telemetry Service
=================================
Processes FastF1 session laps and telemetry into structured REST payloads
for Weekend Overview, Session Pace, Telemetry Lab, Driver Comparison, and Replay.
"""

import numpy as np
import pandas as pd
import fastf1
from backend.data.fastf1_service import (
    get_session,
    extract_circuit_geometry,
    get_driver_color,
    get_team_color,
    format_lap_time,
    get_event_schedule
)
from backend.engine.replay import get_race_telemetry

def get_weekend_overview(year: int, event_identifier: str | int) -> dict:
    """Retrieve event details, weekend session schedules, and 2D track map geometry."""
    try:
        schedule = get_event_schedule(year)
        if schedule.empty:
            return {"error": f"No schedule for {year}"}

        # Match event
        if str(event_identifier).isdigit():
            rnd = int(event_identifier)
            match = schedule[schedule['RoundNumber'] == rnd]
        else:
            match = schedule[schedule['EventName'].astype(str).str.contains(str(event_identifier), case=False, na=False)]

        if match.empty:
            match = schedule.iloc[0:1]

        event = match.iloc[0]
        round_num = int(event.get('RoundNumber', 1))
        event_name = str(event.get('EventName', f'Round {round_num}'))
        country = str(event.get('Country', 'Grand Prix'))
        location = str(event.get('Location', event_name))
        date_str = str(event.get('EventDate', ''))[:10]

        # Extract sessions schedule
        sessions = []
        for s_idx in range(1, 6):
            s_name_col = f"Session{s_idx}"
            s_date_col = f"Session{s_idx}Date"
            if s_name_col in event and pd.notna(event[s_name_col]):
                name = str(event[s_name_col])
                dt = str(event.get(s_date_col, ''))[:16].replace("T", " ")
                sessions.append({
                    "name": name,
                    "date": dt,
                    "status": "Completed"
                })

        if not sessions:
            sessions = [
                {"name": "Free Practice 1", "date": f"{date_str} 11:30", "status": "Completed"},
                {"name": "Free Practice 2", "date": f"{date_str} 15:00", "status": "Completed"},
                {"name": "Free Practice 3", "date": f"{date_str} 12:00", "status": "Completed"},
                {"name": "Qualifying", "date": f"{date_str} 15:00", "status": "Completed"},
                {"name": "Grand Prix Race", "date": f"{date_str} 14:00", "status": "Completed"},
            ]

        # Attempt to load session for authentic circuit contour geometry
        track_geometry = None
        session = get_session(year, round_num, "Q") or get_session(year, round_num, "R")
        if session is not None and hasattr(session, 'laps') and not session.laps.empty:
            fastest_lap = session.laps.pick_fastest()
            if fastest_lap is not None:
                try:
                    tel = fastest_lap.get_telemetry()
                    track_geometry = extract_circuit_geometry(tel)
                except Exception:
                    pass

        return {
            "round": round_num,
            "eventName": event_name,
            "country": country,
            "location": location,
            "date": date_str,
            "sessions": sessions,
            "trackGeometry": track_geometry,
            "specs": {
                "distance": "306.7 km",
                "laps": 53,
                "record": "1:21.046",
                "recordHolder": "Rubens Barrichello (2004)",
                "fullThrottlePct": "76%"
            }
        }
    except Exception as e:
        print(f"Error in get_weekend_overview: {e}")
        return {"error": str(e)}


def get_session_pace(year: int, event_identifier: str | int, session_id: str = "R") -> dict:
    """Retrieve session fastest lap leaderboard, lap pace distribution boxplots, and tyre strategy stints."""
    session = get_session(year, event_identifier, session_id)
    if session is None or not hasattr(session, 'laps') or session.laps.empty:
        return {"leaderboard": [], "paceDistribution": [], "tyreStrategies": []}

    laps = session.laps
    clean_laps = laps.pick_quicklaps() if hasattr(laps, 'pick_quicklaps') else laps

    # Leaderboard (fastest lap per driver)
    leaderboard = []
    pace_dist = []
    tyre_strategies = []

    drivers = session.drivers
    driver_fastest_sec = {}

    for drv_no in drivers:
        try:
            drv_info = session.get_driver(drv_no)
            code = drv_info.get("Abbreviation", str(drv_no))
            team = drv_info.get("TeamName", "Constructor")
            color = get_driver_color(code, team)

            drv_laps = laps.pick_drivers(drv_no)
            if drv_laps.empty:
                continue

            fastest = drv_laps.pick_fastest()
            if fastest is not None and pd.notna(fastest.LapTime):
                sec = fastest.LapTime.total_seconds()
                driver_fastest_sec[code] = sec
                leaderboard.append({
                    "driver": code,
                    "number": str(drv_no),
                    "team": team,
                    "color": color,
                    "lapTime": format_lap_time(sec),
                    "rawSeconds": sec,
                    "compound": str(fastest.Compound or "UNKNOWN").upper(),
                    "lapNumber": int(fastest.LapNumber)
                })

            # Pace statistics from clean laps
            drv_clean = clean_laps.pick_drivers(drv_no)
            if not drv_clean.empty:
                valid_sec = drv_clean['LapTime'].dt.total_seconds().dropna()
                valid_sec = valid_sec[valid_sec > 50] # Filter out anomalies
                if len(valid_sec) > 0:
                    med = float(valid_sec.median())
                    min_l = float(valid_sec.min())
                    max_l = float(valid_sec.max())
                    q1 = float(valid_sec.quantile(0.25))
                    q3 = float(valid_sec.quantile(0.75))
                    spread = float(q3 - q1)

                    pace_dist.append({
                        "driver": code,
                        "team": team,
                        "color": color,
                        "medianLap": format_lap_time(med),
                        "minLap": format_lap_time(min_l),
                        "maxLap": format_lap_time(max_l),
                        "spread": f"{spread:.2f}s",
                        "medianSec": med,
                        "minSec": min_l,
                        "maxSec": max_l,
                        "q1Sec": q1,
                        "q3Sec": q3
                    })

            # Tyre Stints
            stint_list = []
            current_compound = None
            start_lap = 1
            stint_laps = 0

            for _, lap_row in drv_laps.iterrows():
                lap_no = int(lap_row.LapNumber)
                comp = str(lap_row.Compound or "UNKNOWN").upper()
                if current_compound is None:
                    current_compound = comp
                    start_lap = lap_no
                    stint_laps = 1
                elif comp == current_compound:
                    stint_laps += 1
                else:
                    stint_list.append({
                        "compound": current_compound,
                        "startLap": start_lap,
                        "laps": stint_laps
                    })
                    current_compound = comp
                    start_lap = lap_no
                    stint_laps = 1

            if current_compound and stint_laps > 0:
                stint_list.append({
                    "compound": current_compound,
                    "startLap": start_lap,
                    "laps": stint_laps
                })

            if stint_list:
                tyre_strategies.append({
                    "driver": code,
                    "stints": stint_list
                })

        except Exception as e:
            print(f"Error processing driver {drv_no} pace: {e}")
            continue

    # Sort leaderboard by raw seconds
    leaderboard.sort(key=lambda x: x["rawSeconds"])
    if leaderboard:
        best_sec = leaderboard[0]["rawSeconds"]
        for idx, row in enumerate(leaderboard):
            row["position"] = idx + 1
            gap = row["rawSeconds"] - best_sec
            row["gap"] = "Leader" if idx == 0 else f"+{gap:.3f}s"

    pace_dist.sort(key=lambda x: x["medianSec"])
    return {
        "leaderboard": leaderboard,
        "paceDistribution": pace_dist,
        "tyreStrategies": tyre_strategies
    }


def get_telemetry_lab(year: int, event_identifier: str | int, session_id: str = "R", driver_codes: list[str] = None) -> dict:
    """Retrieve distance-synchronized micro-telemetry (speed, throttle, brake, gear, drs) for selected drivers."""
    if not driver_codes:
        driver_codes = ["VER", "NOR"]

    session = get_session(year, event_identifier, session_id)
    if session is None or not hasattr(session, 'laps') or session.laps.empty:
        return {"mergedData": [], "driverInfo": {}}

    driver_telemetries = {}
    max_dist = 0.0

    for code in driver_codes:
        try:
            drv_laps = session.laps.pick_drivers(code)
            if drv_laps.empty:
                continue
            fastest = drv_laps.pick_fastest()
            if fastest is None:
                continue

            tel = fastest.get_telemetry()
            if tel.empty or 'Distance' not in tel.columns:
                continue

            dists = tel['Distance'].to_numpy().astype(float)
            speeds = tel['Speed'].to_numpy().astype(float) if 'Speed' in tel.columns else np.zeros_like(dists)
            throttles = tel['Throttle'].to_numpy().astype(float) if 'Throttle' in tel.columns else np.zeros_like(dists)
            brakes = tel['Brake'].to_numpy().astype(float) if 'Brake' in tel.columns else np.zeros_like(dists)
            gears = tel['nGear'].to_numpy().astype(float) if 'nGear' in tel.columns else np.ones_like(dists)
            drs = tel['DRS'].to_numpy().astype(float) if 'DRS' in tel.columns else np.zeros_like(dists)

            max_dist = max(max_dist, float(dists.max()))

            driver_telemetries[code] = {
                "dists": dists,
                "speeds": speeds,
                "throttles": throttles,
                "brakes": brakes,
                "gears": gears,
                "drs": drs,
                "lapTime": format_lap_time(fastest.LapTime.total_seconds()) if pd.notna(fastest.LapTime) else "N/A",
                "color": get_driver_color(code)
            }
        except Exception as e:
            print(f"Error extracting telemetry for {code}: {e}")
            continue

    if not driver_telemetries:
        return {"mergedData": [], "driverInfo": {}}

    # Interpolate onto a uniform distance axis (e.g. step = 20m)
    target_dists = np.arange(0.0, max_dist, 25.0)
    merged_data = []

    for d in target_dists:
        row = {"distance": int(d)}
        for code, tel_data in driver_telemetries.items():
            orig_d = tel_data["dists"]
            row[f"speed_{code}"] = round(float(np.interp(d, orig_d, tel_data["speeds"])), 1)
            row[f"throttle_{code}"] = round(float(np.interp(d, orig_d, tel_data["throttles"])), 1)
            row[f"brake_{code}"] = round(float(np.interp(d, orig_d, tel_data["brakes"])), 1)
            row[f"gear_{code}"] = int(round(float(np.interp(d, orig_d, tel_data["gears"]))))
            row[f"drs_{code}"] = int(round(float(np.interp(d, orig_d, tel_data["drs"]))))
        merged_data.append(row)

    driver_info = {code: {"lapTime": info["lapTime"], "color": info["color"]} for code, info in driver_telemetries.items()}
    return {
        "mergedData": merged_data,
        "driverInfo": driver_info
    }


def get_driver_comparison(year: int, event_identifier: str | int, session_id: str = "R", driver_a: str = "VER", driver_b: str = "NOR") -> dict:
    """Retrieve head-to-head metrics and continuous delta time over distance between two drivers."""
    session = get_session(year, event_identifier, session_id)
    if session is None or not hasattr(session, 'laps') or session.laps.empty:
        return {"error": "Session unavailable"}

    laps_a = session.laps.pick_drivers(driver_a)
    laps_b = session.laps.pick_drivers(driver_b)

    if laps_a.empty or laps_b.empty:
        return {"error": f"Laps missing for {driver_a} or {driver_b}"}

    fastest_a = laps_a.pick_fastest()
    fastest_b = laps_b.pick_fastest()

    if fastest_a is None or fastest_b is None:
        return {"error": "Fastest lap missing"}

    sec_a = fastest_a.LapTime.total_seconds() if pd.notna(fastest_a.LapTime) else 0.0
    sec_b = fastest_b.LapTime.total_seconds() if pd.notna(fastest_b.LapTime) else 0.0

    s1_a = fastest_a.Sector1Time.total_seconds() if pd.notna(fastest_a.Sector1Time) else 0.0
    s1_b = fastest_b.Sector1Time.total_seconds() if pd.notna(fastest_b.Sector1Time) else 0.0

    s2_a = fastest_a.Sector2Time.total_seconds() if pd.notna(fastest_a.Sector2Time) else 0.0
    s2_b = fastest_b.Sector2Time.total_seconds() if pd.notna(fastest_b.Sector2Time) else 0.0

    s3_a = fastest_a.Sector3Time.total_seconds() if pd.notna(fastest_a.Sector3Time) else 0.0
    s3_b = fastest_b.Sector3Time.total_seconds() if pd.notna(fastest_b.Sector3Time) else 0.0

    tel_a = fastest_a.get_telemetry()
    tel_b = fastest_b.get_telemetry()

    top_speed_a = float(tel_a['Speed'].max()) if 'Speed' in tel_a.columns else 0.0
    top_speed_b = float(tel_b['Speed'].max()) if 'Speed' in tel_b.columns else 0.0

    # Compute delta time over distance
    delta_data = []
    if not tel_a.empty and not tel_b.empty and 'Distance' in tel_a.columns and 'Distance' in tel_b.columns:
        d_a = tel_a['Distance'].to_numpy().astype(float)
        t_a = tel_a['Time'].dt.total_seconds().to_numpy().astype(float)

        d_b = tel_b['Distance'].to_numpy().astype(float)
        t_b = tel_b['Time'].dt.total_seconds().to_numpy().astype(float)

        max_d = min(d_a.max(), d_b.max())
        sample_d = np.arange(0.0, max_d, 40.0)

        interp_t_a = np.interp(sample_d, d_a, t_a)
        interp_t_b = np.interp(sample_d, d_b, t_b)
        delta_arr = interp_t_a - interp_t_b # Negative = A is ahead/faster

        for dist_val, d_val in zip(sample_d, delta_arr):
            delta_data.append({
                "distance": int(dist_val),
                "delta": round(float(d_val), 3)
            })

    delta_sec = sec_a - sec_b
    faster_driver = driver_a if delta_sec <= 0 else driver_b

    return {
        "driverA": {
            "code": driver_a,
            "color": get_driver_color(driver_a),
            "fastestLap": format_lap_time(sec_a),
            "sector1": f"{s1_a:.3f}s" if s1_a > 0 else "N/A",
            "sector2": f"{s2_a:.3f}s" if s2_a > 0 else "N/A",
            "sector3": f"{s3_a:.3f}s" if s3_a > 0 else "N/A",
            "topSpeed": f"{top_speed_a:.1f} km/h"
        },
        "driverB": {
            "code": driver_b,
            "color": get_driver_color(driver_b),
            "fastestLap": format_lap_time(sec_b),
            "sector1": f"{s1_b:.3f}s" if s1_b > 0 else "N/A",
            "sector2": f"{s2_b:.3f}s" if s2_b > 0 else "N/A",
            "sector3": f"{s3_b:.3f}s" if s3_b > 0 else "N/A",
            "topSpeed": f"{top_speed_b:.1f} km/h"
        },
        "deltaSec": round(abs(delta_sec), 3),
        "fasterDriver": faster_driver,
        "deltaData": delta_data
    }
