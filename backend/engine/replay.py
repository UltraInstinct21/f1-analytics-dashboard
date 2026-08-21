"""
Race Replay Telemetry Engine
============================
Processes raw FastF1 session telemetry into synchronized 2D coordinate timelines,
handling driver inputs, spatial track normalization, tyre compounds, dynamic safety car
events, and live race leaderboards.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from backend.config import COMPUTED_DATA_DIR

TYRE_COMPOUND_INTS = {
    "SOFT": 0,
    "MEDIUM": 1,
    "HARD": 2,
    "INTERMEDIATE": 3,
    "WET": 4,
}

TYRE_COMPOUND_NAMES = {
    0: "SOFT",
    1: "MEDIUM",
    2: "HARD",
    3: "INTER",
    4: "WET",
    -1: "UNKNOWN",
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
    "SAR": "#64C4FF",
}

TEAM_COLORS = {
    "Red Bull": "#3671C6",
    "McLaren": "#FF8000",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Racing Bulls": "#6692FF",
    "Sauber": "#52E252",
    "Kick Sauber": "#52E252",
    "Haas": "#B6BABD",
}

def get_driver_color(code: str, team: str = "") -> str:
    if code in DRIVER_COLORS:
        return DRIVER_COLORS[code]
    for k, c in TEAM_COLORS.items():
        if k.lower() in str(team).lower():
            return c
    return "#41A1CF"


def get_tyre_compound_int(compound_str: str) -> int:
    if not compound_str:
        return -1
    return int(TYRE_COMPOUND_INTS.get(str(compound_str).upper(), -1))


def process_driver_telemetry(session, drv_no: str, drv_code: str, t_start: float, t_end: float):
    """Extract full time-indexed telemetry for a single driver across the entire race."""
    try:
        drv_laps = session.laps.pick_drivers(drv_no)
        if drv_laps.empty:
            return None

        # Load full race telemetry for driver in one fast call
        try:
            tel = drv_laps.get_telemetry()
        except Exception:
            return None

        if tel.empty or 'SessionTime' not in tel.columns or 'X' not in tel.columns:
            return None

        t_arr = tel['SessionTime'].dt.total_seconds().to_numpy().astype(float)
        x_arr = tel['X'].to_numpy().astype(float)
        y_arr = tel['Y'].to_numpy().astype(float)
        d_arr = tel['Distance'].to_numpy().astype(float) if 'Distance' in tel.columns else np.zeros_like(x_arr)
        s_arr = tel['Speed'].to_numpy().astype(float) if 'Speed' in tel.columns else np.zeros_like(x_arr)

        valid = np.isfinite(t_arr) & np.isfinite(x_arr) & np.isfinite(y_arr)
        if not np.any(valid):
            return None

        t_arr, x_arr, y_arr, d_arr, s_arr = t_arr[valid], x_arr[valid], y_arr[valid], d_arr[valid], s_arr[valid]

        # Calculate lap numbers and tyre compounds across timestamps
        lap_nums = np.ones_like(t_arr, dtype=int)
        tyre_ints = np.full_like(t_arr, 1, dtype=int) # Default MEDIUM

        for _, lap_row in drv_laps.iterrows():
            lap_n = int(lap_row.get('LapNumber', 1))
            c_int = get_tyre_compound_int(lap_row.get('Compound'))
            start_t = lap_row.get('LapStartTime')
            end_t = lap_row.get('Time')

            if pd.notna(start_t) and pd.notna(end_t):
                s_sec = start_t.total_seconds()
                e_sec = end_t.total_seconds()
                mask = (t_arr >= s_sec) & (t_arr <= e_sec)
                lap_nums[mask] = lap_n
                tyre_ints[mask] = c_int
            elif pd.notna(end_t):
                e_sec = end_t.total_seconds()
                mask = t_arr <= e_sec
                # Fill preceding
                lap_nums[mask] = lap_n
                tyre_ints[mask] = c_int

        order = np.argsort(t_arr)
        return {
            "code": drv_code,
            "t": t_arr[order],
            "x": x_arr[order],
            "y": y_arr[order],
            "dist": d_arr[order],
            "speed": s_arr[order],
            "lap": lap_nums[order],
            "tyre": tyre_ints[order],
            "t_min": float(t_arr[order][0]),
            "t_max": float(t_arr[order][-1]),
        }
    except Exception as e:
        print(f"Error processing telemetry for driver {drv_code}: {e}")
        return None


def get_race_telemetry(session, session_type="R", num_frames=1000) -> dict:
    """
    Extract and process full race session telemetry into uniform timeline replay frames
    with normalized SVG coordinates, dynamic leaderboard metrics, and complete lap coverage.
    """
    try:
        year = getattr(session, 'event', {}).get('Year') or 2024
        event_name = getattr(session, 'event', {}).get('EventName') or 'Grand Prix'
        round_num = getattr(session, 'event', {}).get('RoundNumber') or 1

        # Check disk cache
        cache_key = f"replay_{year}_R{round_num}_{session_type}_f{num_frames}.json"
        cache_file = COMPUTED_DATA_DIR / cache_key
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        total_laps = int(session.laps['LapNumber'].max()) if hasattr(session, 'laps') and not session.laps.empty else 57

        # Determine true race start (green light lap 1) and finish (chequered flag final lap)
        laps_df = session.laps
        lap1_laps = laps_df[laps_df['LapNumber'] == 1]
        t_start = float(lap1_laps['LapStartTime'].dropna().min().total_seconds()) if not lap1_laps.empty and pd.notna(lap1_laps['LapStartTime'].dropna().min()) else float(laps_df['LapStartTime'].dropna().min().total_seconds())
        final_laps = laps_df[laps_df['LapNumber'] == total_laps]
        t_end = float(final_laps['Time'].dropna().max().total_seconds()) if not final_laps.empty else float(laps_df['Time'].dropna().max().total_seconds())

        driver_results = []
        driver_meta = {}

        for drv_no in session.drivers:
            try:
                drv_info = session.get_driver(drv_no)
                drv_code = str(drv_info.get("Abbreviation") or drv_no)
                drv_name = f"{drv_info.get('FirstName', '')} {drv_info.get('LastName', drv_code)}".strip()
                drv_team = str(drv_info.get("TeamName") or "Unknown")
                color = get_driver_color(drv_code, drv_team)

                driver_meta[drv_code] = {
                    "code": drv_code,
                    "name": drv_name,
                    "team": drv_team,
                    "color": color,
                }

                res = process_driver_telemetry(session, drv_no, drv_code, t_start, t_end)
                if res is not None:
                    driver_results.append(res)
            except Exception as e:
                print(f"Error loading driver {drv_no}: {e}")
                continue

        if not driver_results:
            return {"error": "No driver telemetry available for session"}

        # Determine spatial bounding box across all telemetry for SVG normalization
        all_xs = np.concatenate([r["x"] for r in driver_results])
        all_ys = np.concatenate([r["y"] for r in driver_results])

        min_x, max_x = float(all_xs.min()), float(all_xs.max())
        min_y, max_y = float(all_ys.min()), float(all_ys.max())
        range_x = max(max_x - min_x, 1.0)
        range_y = max(max_y - min_y, 1.0)

        scale = min(680.0 / range_x, 380.0 / range_y)
        offset_x = 60.0
        offset_y = 440.0

        def to_svg_x(raw_x):
            return (raw_x - min_x) * scale + offset_x

        def to_svg_y(raw_y):
            return offset_y - (raw_y - min_y) * scale

        # Track contour from fastest lap
        track_geometry = None
        try:
            fastest_lap = session.laps.pick_fastest()
            if fastest_lap is not None:
                fastest_tel = fastest_lap.get_telemetry()
                if not fastest_tel.empty and 'X' in fastest_tel.columns:
                    fx = fastest_tel['X'].to_numpy().astype(float)
                    fy = fastest_tel['Y'].to_numpy().astype(float)
                    step = max(1, len(fx) // 200)
                    fx_s = to_svg_x(fx[::step])
                    fy_s = to_svg_y(fy[::step])

                    path_d = f"M {fx_s[0]:.1f} {fy_s[0]:.1f}"
                    for px, py in zip(fx_s[1:], fy_s[1:]):
                        path_d += f" L {px:.1f} {py:.1f}"
                    path_d += " Z"

                    track_geometry = {
                        "pathD": path_d,
                        "viewBox": "0 0 800 500",
                        "startLine": {
                            "x1": round(float(fx_s[0] - 6), 1),
                            "y1": round(float(fy_s[0] - 6), 1),
                            "x2": round(float(fx_s[0] + 6), 1),
                            "y2": round(float(fy_s[0] + 6), 1),
                        },
                        "points": [{"x": round(float(px), 1), "y": round(float(py), 1)} for px, py in zip(fx_s, fy_s)]
                    }
        except Exception as e:
            print(f"Error generating track geometry for replay: {e}")

        # Safety Car / VSC intervals from session track status
        sc_intervals = []
        vsc_intervals = []
        try:
            if hasattr(session, 'track_status') and not session.track_status.empty:
                ts = session.track_status
                # Status '4' is SC, '6' / '7' is VSC
                for _, row in ts.iterrows():
                    status_code = str(row.get('Status', '1'))
                    start_t = row.get('Time').total_seconds() if pd.notna(row.get('Time')) else 0.0
                    if '4' in status_code:
                        sc_intervals.append((start_t, start_t + 180.0))
                    elif '6' in status_code or '7' in status_code:
                        vsc_intervals.append((start_t, start_t + 120.0))
        except Exception:
            pass

        def is_sc_active(t):
            return any(start <= t <= end for start, end in sc_intervals)

        def is_vsc_active(t):
            return any(start <= t <= end for start, end in vsc_intervals)

        # Build timeline from race start to chequered flag
        timeline = np.linspace(t_start, t_end, num_frames)

        frames = []
        for frame_idx, t in enumerate(timeline):
            sc_active = bool(is_sc_active(t))
            vsc_active = bool(is_vsc_active(t))
            status_text = "SAFETY CAR DEPLOYED" if sc_active else ("VIRTUAL SAFETY CAR" if vsc_active else "GREEN TRACK STATUS")

            frame_drivers = {}
            active_list = []

            for r in driver_results:
                code = str(r["code"])
                t_arr = r["t"]
                idx = int(np.searchsorted(t_arr, t))
                if idx >= len(t_arr):
                    idx = len(t_arr) - 1
                if idx < 0:
                    idx = 0

                raw_x = float(r["x"][idx])
                raw_y = float(r["y"][idx])
                svg_x = round(float(to_svg_x(raw_x)), 1)
                svg_y = round(float(to_svg_y(raw_y)), 1)
                speed_val = round(float(r["speed"][idx]), 1)
                lap_val = int(r["lap"][idx])
                dist_val = float(r["dist"][idx])
                tyre_int = int(r["tyre"][idx])
                meta = driver_meta.get(code, {"name": code, "team": "F1 Team", "color": "#3671C6"})

                drv_entry = {
                    "code": code,
                    "name": str(meta["name"]),
                    "team": str(meta["team"]),
                    "color": str(meta["color"]),
                    "x": svg_x,
                    "y": svg_y,
                    "speed": speed_val,
                    "lap": lap_val,
                    "dist": dist_val,
                    "tyre": str(TYRE_COMPOUND_NAMES.get(tyre_int, "MEDIUM")),
                }
                frame_drivers[code] = drv_entry
                active_list.append(drv_entry)

            # Sort active drivers by total race distance to get running order
            active_list.sort(key=lambda d: d["dist"], reverse=True)
            leader_dist = active_list[0]["dist"] if active_list else 0.0

            leaderboard = []
            for pos, drv in enumerate(active_list, 1):
                gap_dist = float(leader_dist - drv["dist"])
                gap_sec = float(max(0.0, gap_dist / 60.0))
                gap_str = "Leader" if pos == 1 else f"+{gap_sec:.1f}s"
                leaderboard_entry = {
                    "position": int(pos),
                    "code": drv["code"],
                    "name": drv["name"],
                    "team": drv["team"],
                    "color": drv["color"],
                    "speed": drv["speed"],
                    "lap": drv["lap"],
                    "tyre": drv["tyre"],
                    "gap": gap_str,
                }
                leaderboard.append(leaderboard_entry)

            current_lap = int(active_list[0]["lap"]) if active_list else 1

            frames.append({
                "frame": int(frame_idx),
                "time": round(float(t - t_start), 1),
                "lap": int(min(current_lap, total_laps)),
                "safetyCar": sc_active,
                "vsc": vsc_active,
                "statusText": status_text,
                "drivers": frame_drivers,
                "leaderboard": leaderboard[:10],
            })

        result = {
            "year": int(year),
            "round": int(round_num),
            "eventName": str(event_name),
            "totalLaps": int(total_laps),
            "total_frames": int(len(frames)),
            "trackGeometry": track_geometry,
            "driversList": list(driver_meta.values()),
            "frames": frames,
        }

        # Cache on disk
        try:
            with open(cache_file, "w") as f:
                json.dump(result, f)
        except Exception as e:
            print(f"Warning: could not cache replay: {e}")

        return result
    except Exception as e:
        print(f"Error in get_race_telemetry: {e}")
        return {"error": str(e)}

