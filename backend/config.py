"""
Backend Configuration Module
=============================
Provides global path, caching, and runtime settings for the F1 Analytics backend.
"""

import os
from pathlib import Path

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parents[1]

# Caching directories
FASTF1_CACHE_DIR = ROOT_DIR / ".fastf1-cache"
FASTF1_CACHE_DIR.mkdir(exist_ok=True)

# Computed data & model outputs
COMPUTED_DATA_DIR = ROOT_DIR / "computed_data"
COMPUTED_DATA_DIR.mkdir(exist_ok=True)

# Replay settings
REPLAY_FPS = 25
REPLAY_DT = 1.0 / REPLAY_FPS

# Default prediction seed
PREDICTION_SEED = 2026
