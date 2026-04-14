import time

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from utils.data import get_event_schedule
from utils.style import apply_kinetic_pulse_theme
from utils.ui import sidebar_season_selector
from utils.race_replay import (
    enable_cache,
    load_session,
    get_race_telemetry,
    rgb_to_hex,
    build_track_reference,
    load_replay_payload,
    collect_driver_window,
    gear_change_count,
    speed_trend_label,
    next_random_unique_color,
)


st.set_page_config(page_title="Race Replay", layout="wide")
apply_kinetic_pulse_theme()


def _render_frame_figure(payload, frame_index):
    frames = payload["frames"]
    frame = frames[frame_index]
    drivers = frame.get("drivers", {})
    driver_colors = payload.get("driver_colors", {})

    track_x, track_y = build_track_reference(frames)

    leaderboard = []
    for code, data in drivers.items():
        leaderboard.append(
            {
                "Driver": code,
                "Pos": int(data.get("position", 99)),
                "Lap": int(data.get("lap", 0)),
                "Speed": int(round(data.get("speed", 0))),
                "Gear": int(data.get("gear", 0)),
                "DRS": "ON" if int(data.get("drs", 0)) >= 10 else "OFF",
            }
        )
    leaderboard = sorted(leaderboard, key=lambda row: row["Pos"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=track_x,
            y=track_y,
            mode="lines",
            line=dict(color="rgba(225, 226, 231, 0.50)", width=2),
            name="Track",
            hoverinfo="skip",
        )
    )

    driver_x = []
    driver_y = []
    driver_text = []
    driver_marker_colors = []

    for row in leaderboard:
        code = row["Driver"]
        d = drivers[code]
        driver_x.append(d.get("x", 0.0))
        driver_y.append(d.get("y", 0.0))
        driver_text.append(code)
        driver_marker_colors.append(rgb_to_hex(driver_colors.get(code)))

    fig.add_trace(
        go.Scatter(
            x=driver_x,
            y=driver_y,
            mode="markers+text",
            text=driver_text,
            textposition="top center",
            marker=dict(color=driver_marker_colors, size=10, line=dict(width=1, color="#0b0f12")),
            name="Drivers",
        )
    )

    safety_car = frame.get("safety_car")
    if safety_car:
        fig.add_trace(
            go.Scatter(
                x=[safety_car.get("x", 0.0)],
                y=[safety_car.get("y", 0.0)],
                mode="markers+text",
                text=["SC"],
                textposition="top center",
                marker=dict(color="#ffb000", size=14, line=dict(color="#221a00", width=2)),
                name="Safety Car",
            )
        )

    fig.update_layout(
        title=f"{payload['event_name']} | Lap {frame.get('lap', 0)}",
        height=650,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e1e2e7",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    return fig, leaderboard, frame


# Note: Helper functions now imported from utils.race_replay module
# See utils/race_replay.py for implementations of:
# - collect_driver_window
# - gear_change_count
# - speed_trend_label
# - next_random_unique_color


def _render_telemetry_comparison(payload, frame_index, selected_drivers, window_frames, telemetry_colors):
    frames = payload.get("frames", [])

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake (%)", "Gear"),
    )

    summary_rows = []

    for code in selected_drivers:
        window = collect_driver_window(frames, frame_index, code, window_frames)
        if not window:
            continue

        color = telemetry_colors.get(code, "#9ca3af")

        fig.add_trace(
            go.Scatter(x=window["time"], y=window["speed"], mode="lines", name=f"{code} Speed", line=dict(color=color, width=2)),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=window["time"], y=window["throttle"], mode="lines", name=f"{code} Throttle", line=dict(color=color, width=2)),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=window["time"], y=window["brake"], mode="lines", name=f"{code} Brake", line=dict(color=color, width=2, dash="dot")),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=window["time"], y=window["gear"], mode="lines", name=f"{code} Gear", line=dict(color=color, width=2)),
            row=4,
            col=1,
        )

        current = frames[frame_index].get("drivers", {}).get(code, {})
        summary_rows.append(
            {
                "Driver": code,
                "Pos": int(current.get("position", 99)),
                "Speed": int(round(current.get("speed", 0.0))),
                "Throttle": round(float(current.get("throttle", 0.0)), 1),
                "Brake": round(float(current.get("brake", 0.0)) * 100.0, 1),
                "Gear": int(current.get("gear", 0)),
                "Gear Changes": gear_change_count(window["gear"]),
                "Trend": speed_trend_label(window["speed"]),
            }
        )

    fig.update_layout(
        height=820,
        margin=dict(l=10, r=10, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e1e2e7",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    fig.update_xaxes(title_text="Time Relative To Current Frame (s)", row=4, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", range=[0, 100], row=2, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", range=[0, 100], row=3, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", row=4, col=1)

    summary_rows = sorted(summary_rows, key=lambda row: row["Pos"])
    return fig, summary_rows


if "race_replay_payload" not in st.session_state:
    st.session_state.race_replay_payload = None
if "race_replay_selection_key" not in st.session_state:
    st.session_state.race_replay_selection_key = None
if "race_replay_frame_idx" not in st.session_state:
    st.session_state.race_replay_frame_idx = 0
if "race_replay_auto_play" not in st.session_state:
    st.session_state.race_replay_auto_play = False
if "race_replay_telemetry_colors" not in st.session_state:
    st.session_state.race_replay_telemetry_colors = {}
if "race_replay_selected_drivers" not in st.session_state:
    st.session_state.race_replay_selected_drivers = []
if "race_replay_selected_drivers_key" not in st.session_state:
    st.session_state.race_replay_selected_drivers_key = None


st.title("Race Replay")
st.caption("Core replay view powered by the f1-race-replay telemetry pipeline.")

year = sidebar_season_selector()
schedule = get_event_schedule(year)
race_events = schedule[schedule["EventFormat"] != "testing"].copy()

if race_events.empty:
    st.warning("No race events found for this season.")
    st.stop()

event_map = {
    f"R{int(row['RoundNumber']):02d} - {row['EventName']}": int(row["RoundNumber"])
    for _, row in race_events.iterrows()
}
event_label = st.selectbox("Select Event", list(event_map.keys()))
round_number = event_map[event_label]
session_label = st.selectbox("Session Type", ["Race", "Sprint"])
session_code = "R" if session_label == "Race" else "S"

selection_key = f"{year}-{round_number}-{session_code}"

load_clicked = st.button("Load Replay", type="primary")

if load_clicked:
    with st.spinner("Loading replay frames... this can take a while on first run"):
        try:
            payload = load_replay_payload(year, round_number, session_code)
            st.session_state.race_replay_payload = payload
            st.session_state.race_replay_selection_key = selection_key
            st.session_state.race_replay_frame_idx = 0
            st.session_state.race_replay_auto_play = False
            st.session_state.race_replay_telemetry_colors = {}
            st.session_state.race_replay_selected_drivers = []
            st.session_state.race_replay_selected_drivers_key = None
        except Exception as exc:
            st.error(f"Replay could not be loaded: {exc}")

payload = st.session_state.race_replay_payload

if payload and st.session_state.race_replay_selection_key == selection_key:
    frames = payload.get("frames", [])

    if not frames:
        st.warning("Replay data is empty for this selection.")
        st.stop()

    total_frames = len(frames)

    play_col, pause_col, restart_col = st.columns([1, 1, 1])
    with play_col:
        if st.button("Play", use_container_width=True):
            st.session_state.race_replay_auto_play = True
    with pause_col:
        if st.button("Pause", use_container_width=True):
            st.session_state.race_replay_auto_play = False
    with restart_col:
        if st.button("Restart", use_container_width=True):
            st.session_state.race_replay_auto_play = False
            st.session_state.race_replay_frame_idx = 0

    col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
    with col_a:
        frame_idx = st.slider(
            "Frame",
            min_value=0,
            max_value=total_frames - 1,
            value=min(st.session_state.race_replay_frame_idx, total_frames - 1),
        )
    with col_b:
        playback_speed = st.select_slider("Speed", options=[0.5, 1.0, 2.0, 4.0], value=1.0)
    with col_c:
        if st.button("Prev"):
            st.session_state.race_replay_auto_play = False
            frame_idx = max(0, frame_idx - 1)
    with col_d:
        if st.button("Next"):
            st.session_state.race_replay_auto_play = False
            frame_idx = min(total_frames - 1, frame_idx + 1)

    st.session_state.race_replay_frame_idx = frame_idx

    info_col = st.columns([1])[0]
    with info_col:
        st.caption("Tip: lower speed improves smoothness on slower machines.")

    fig, leaderboard, active_frame = _render_frame_figure(payload, st.session_state.race_replay_frame_idx)

    left, right = st.columns([3, 1])
    with left:
        st.plotly_chart(fig, width="stretch")
    with right:
        st.subheader("Live Leaderboard")
        st.dataframe(pd.DataFrame(leaderboard), hide_index=True, width="stretch")

        t_seconds = float(active_frame.get("t", 0.0))
        mm = int(t_seconds // 60)
        ss = int(t_seconds % 60)
        st.metric("Race Clock", f"{mm:02d}:{ss:02d}")

        total_laps = payload.get("total_laps")
        if total_laps:
            st.metric("Lap", f"{active_frame.get('lap', 0)} / {int(total_laps)}")
        else:
            st.metric("Lap", str(active_frame.get("lap", 0)))

    st.markdown("---")
    st.subheader("Driver Telemetry Comparison")

    # Keep options in a stable order so widget identity does not reset during playback.
    driver_options = sorted([row["Driver"] for row in leaderboard])

    # Initialize selection once per loaded replay/session selection.
    if st.session_state.race_replay_selected_drivers_key != selection_key:
        st.session_state.race_replay_selected_drivers = driver_options[: min(3, len(driver_options))]
        st.session_state.race_replay_selected_drivers_key = selection_key
    else:
        # Drop selections that are no longer present in current options.
        st.session_state.race_replay_selected_drivers = [
            code for code in st.session_state.race_replay_selected_drivers if code in driver_options
        ]

    compare_col, window_col = st.columns([3, 1])
    with compare_col:
        selected_drivers = st.multiselect(
            "Select drivers for comparison",
            options=driver_options,
            key="race_replay_selected_drivers",
        )
    with window_col:
        lookback_seconds = st.slider("Lookback (s)", min_value=5, max_value=60, value=20, step=5)

    if selected_drivers:
        telemetry_color_map = dict(st.session_state.race_replay_telemetry_colors)
        used_colors = set(telemetry_color_map.values())

        for code in selected_drivers:
            if code not in telemetry_color_map:
                new_color = next_random_unique_color(used_colors)
                telemetry_color_map[code] = new_color
                used_colors.add(new_color)

        st.session_state.race_replay_telemetry_colors = telemetry_color_map

        window_frames = int(lookback_seconds * 25)
        telemetry_fig, summary_rows = _render_telemetry_comparison(
            payload,
            st.session_state.race_replay_frame_idx,
            selected_drivers,
            window_frames,
            telemetry_color_map,
        )

        if summary_rows:
            st.dataframe(pd.DataFrame(summary_rows), hide_index=True, width="stretch")
            st.plotly_chart(telemetry_fig, width="stretch")
        else:
            st.info("No telemetry samples were available for the selected drivers at this frame.")
    else:
        st.info("Select at least one driver to show braking, acceleration, and gear-change comparisons.")

    # Advance playback only after rendering all sections so telemetry stays in sync.
    if st.session_state.race_replay_auto_play:
        step = max(1, int(playback_speed * 2))
        next_idx = st.session_state.race_replay_frame_idx + step
        if next_idx >= total_frames:
            st.session_state.race_replay_frame_idx = total_frames - 1
            st.session_state.race_replay_auto_play = False
        else:
            st.session_state.race_replay_frame_idx = next_idx

        time.sleep(max(0.02, 0.10 / playback_speed))
        st.rerun()

else:
    st.info("Select an event and click Load Replay to start the in-app race replay.")