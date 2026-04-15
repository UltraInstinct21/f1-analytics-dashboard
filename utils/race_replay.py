"""
Race Replay Utilities
====================

Consolidates all race replay functionality, including telemetry loading,
data processing, and visualization helpers. Acts as a wrapper around
the f1-race-replay module to keep dependencies localized.
"""

import sys
import os
from pathlib import Path
import pickle
import importlib.util
from functools import lru_cache

import fastf1
import numpy as np
import pandas as pd


# ========================
# F1 Race Replay Integration
# ========================

def _get_replay_module_path():
    """Get the path to the f1-race-replay module."""
    repo_root = Path(__file__).resolve().parents[1]
    replay_root = repo_root / "f1-race-replay"
    
    if not replay_root.exists():
        raise FileNotFoundError(
            f"\n❌ F1 Race Replay Module Not Found\n"
            f"The 'f1-race-replay' folder is required for the Race Replay feature.\n"
            f"\nExpected location: {replay_root}\n"
            f"Actual location: NOT FOUND\n"
            f"\nPlease restore the f1-race-replay folder from your backup or re-clone it from:\n"
            f"https://github.com/IAmTomShaw/f1-race-replay.git\n"
            f"\nNote: Race Replay is the only feature that depends on this folder."
        )
    
    return replay_root


def _import_replay_functions():
    """
    Dynamically import the core functions from f1-race-replay.
    
    Returns:
        tuple: (enable_cache, load_session, get_race_telemetry)
    """
    replay_root = _get_replay_module_path()
    replay_root_str = str(replay_root)
    
    if replay_root_str not in sys.path:
        sys.path.insert(0, replay_root_str)
    
    try:
        from src.f1_data import (  # type: ignore[import-not-found]
            enable_cache,
            load_session,
            get_race_telemetry,
        )
        return enable_cache, load_session, get_race_telemetry
    except ImportError as e:
        raise ImportError(
            f"Failed to import race replay core functions from f1-race-replay: {e}"
        ) from e


def _get_prediction_module_path():
    """Get the path to the Formula-1-prediction module."""
    repo_root = Path(__file__).resolve().parents[1]
    prediction_root = repo_root / "Formula-1-prediction"

    if not prediction_root.exists():
        raise FileNotFoundError(
            f"\n❌ Formula-1-prediction Module Not Found\n"
            f"The 'Formula-1-prediction' folder is required for race simulation.\n"
            f"\nExpected location: {prediction_root}\n"
            f"Actual location: NOT FOUND"
        )

    return prediction_root


@lru_cache(maxsize=1)
def _load_prediction_race_engine():
    """Load Formula-1-prediction race_engine.py as a module."""
    engine_path = _get_prediction_module_path() / "race_engine.py"
    if not engine_path.exists():
        raise FileNotFoundError(
            f"Race simulation engine not found at: {engine_path}"
        )

    spec = importlib.util.spec_from_file_location("formula_prediction_race_engine", str(engine_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {engine_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ========================
# Public API Functions
# ========================

def enable_cache():
    """Enable FastF1 caching for better performance."""
    _, _, _ = _import_replay_functions()
    enable_cache_fn, _, _ = _import_replay_functions()
    enable_cache_fn()


def load_session(year, round_number, session_type="R"):
    """
    Load a FastF1 session.
    
    Args:
        year (int): The year of the season
        round_number (int): The round number
        session_type (str): Session type ('R' for Race, 'S' for Sprint)
    
    Returns:
        fastf1.Session: The loaded session object
    """
    _, load_session_fn, _ = _import_replay_functions()
    return load_session_fn(year, round_number, session_type)


def get_race_telemetry(session, session_type="R"):
    """
    Extract and process race telemetry data.
    
    Args:
        session: A FastF1 session object
        session_type (str): Session type ('R' for Race, 'S' for Sprint)
    
    Returns:
        dict: Telemetry data containing frames, driver colors, track statuses, etc.
    """
    _, _, get_race_telemetry_fn = _import_replay_functions()
    return get_race_telemetry_fn(session, session_type)


# ========================
# Visualization Helpers
# ========================

def rgb_to_hex(rgb_tuple):
    """
    Convert RGB tuple to hex color string.
    
    Args:
        rgb_tuple (tuple): (R, G, B) values 0-255
    
    Returns:
        str: Hex color string (e.g., "#ff0000")
    """
    if not isinstance(rgb_tuple, tuple) or len(rgb_tuple) != 3:
        return "#9ca3af"
    r, g, b = [max(0, min(255, int(v))) for v in rgb_tuple]
    return f"#{r:02x}{g:02x}{b:02x}"


def build_track_reference(frames):
    """
    Extract track reference points from replay frames.
    
    Builds a polyline representing the track layout using the first driver's telemetry.
    Falls back to sparse point cloud if full trace unavailable.
    
    Args:
        frames (list): List of frame dictionaries
    
    Returns:
        tuple: (x_points, y_points) - Track layout coordinates
    """
    if not frames:
        return [], []

    first_frame = frames[0]
    driver_codes = sorted(first_frame.get("drivers", {}).keys())

    if driver_codes:
        reference_driver = driver_codes[0]
        x_points = []
        y_points = []
        for frame in frames:
            driver = frame.get("drivers", {}).get(reference_driver)
            if driver:
                x_points.append(driver.get("x", 0.0))
                y_points.append(driver.get("y", 0.0))
        if len(x_points) > 10:
            return x_points, y_points

    # Fallback: sparse point cloud from all drivers
    x_points = []
    y_points = []
    stride = max(1, len(frames) // 500)
    for i in range(0, len(frames), stride):
        for driver in frames[i].get("drivers", {}).values():
            x_points.append(driver.get("x", 0.0))
            y_points.append(driver.get("y", 0.0))
    return x_points, y_points


def load_replay_payload(year, round_number, session_code):
    """
    Load complete race replay payload.
    
    Args:
        year (int): Season year
        round_number (int): Race round number
        session_code (str): Session code ('R' or 'S')
    
    Returns:
        dict: Complete replay payload with frames, colors, metadata
    """
    enable_cache()
    session = load_session(year, round_number, session_code)
    replay_data = get_race_telemetry(session, session_type=session_code)

    return {
        "event_name": session.event.get("EventName", f"Round {round_number}"),
        "year": year,
        "round": round_number,
        "session_code": session_code,
        "frames": replay_data["frames"],
        "driver_colors": replay_data.get("driver_colors", {}),
        "total_laps": replay_data.get("total_laps"),
    }


def simulate_lap_by_lap_race(weather="DRY", circuit="STANDARD", seed=None):
    """
    Run the Formula-1-prediction lap-by-lap race simulation.

    Args:
        weather (str): DRY | LIGHT_RAIN | HEAVY_RAIN
        circuit (str): Circuit profile name
        seed (int | None): Optional random seed

    Returns:
        dict: Race simulation payload from race_engine.simulate_race
    """
    engine = _load_prediction_race_engine()
    if not hasattr(engine, "simulate_race"):
        raise AttributeError("race_engine.py does not expose simulate_race()")
    return engine.simulate_race(weather=weather, circuit=circuit, seed=seed)


# ========================
# Data Processing Helpers
# ========================

def collect_driver_window(frames, frame_index, driver_code, window_frames):
    """
    Collect telemetry data for a driver within a time window.
    
    Args:
        frames (list): List of frame dictionaries
        frame_index (int): Current frame index
        driver_code (str): Driver abbreviation code
        window_frames (int): Number of frames to look back
    
    Returns:
        dict or None: Telemetry window data with time, speed, throttle, brake, gear
    """
    start_idx = max(0, frame_index - window_frames + 1)

    time_vals = []
    speed_vals = []
    throttle_vals = []
    brake_vals = []
    gear_vals = []

    for idx in range(start_idx, frame_index + 1):
        frame = frames[idx]
        driver = frame.get("drivers", {}).get(driver_code)
        if not driver:
            continue

        time_vals.append(float(frame.get("t", 0.0)))
        speed_vals.append(float(driver.get("speed", 0.0)))
        throttle_vals.append(float(driver.get("throttle", 0.0)))
        brake_vals.append(float(driver.get("brake", 0.0)) * 100.0)
        gear_vals.append(int(driver.get("gear", 0)))

    if not time_vals:
        return None

    t_end = time_vals[-1]
    rel_time = [t - t_end for t in time_vals]

    return {
        "time": rel_time,
        "speed": speed_vals,
        "throttle": throttle_vals,
        "brake": brake_vals,
        "gear": gear_vals,
    }


def gear_change_count(gear_series):
    """Count gear changes in a series."""
    if len(gear_series) < 2:
        return 0
    return sum(1 for i in range(1, len(gear_series)) if gear_series[i] != gear_series[i - 1])


def speed_trend_label(speed_series):
    """Determine speed trend (Accelerating, Braking, Stable)."""
    if len(speed_series) < 2:
        return "Stable"

    delta = speed_series[-1] - speed_series[0]
    if delta > 5.0:
        return "Accelerating"
    if delta < -5.0:
        return "Braking"
    return "Stable"


def next_random_unique_color(used_colors):
    """Generate a unique random color not in used_colors."""
    import random
    
    for _ in range(200):
        color = f"#{random.randint(64, 255):02x}{random.randint(64, 255):02x}{random.randint(64, 255):02x}"
        if color not in used_colors:
            return color

    # Fallback
    return f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"
