import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import fastf1 as ff1
from utils.style import apply_kinetic_pulse_theme
from utils.data import get_event_schedule
from utils.ui import sidebar_season_selector
import concurrent.futures

st.set_page_config(page_title="Season Overview", layout="wide")
apply_kinetic_pulse_theme()

year = sidebar_season_selector()

st.title(f"F1 Season {year}")

def utc_now():
    return pd.Timestamp.now(tz="UTC")

def session_start_utc(event, session_number):
    session_date = event.get(f"Session{session_number}DateUtc")
    return pd.to_datetime(session_date, utc=True, errors="coerce")

def session_is_complete(event, session_number, now=None):
    if now is None:
        now = utc_now()
    start = session_start_utc(event, session_number)
    if pd.isna(start):
        return False

    session_name = str(event.get(f"Session{session_number}", "")).lower()
    duration = pd.Timedelta(hours=2 if "sprint" in session_name else 4)
    return start + duration < now

def event_has_completed_points(event, now=None):
    if now is None:
        now = utc_now()

    sprint_complete = (
        str(event.get("Session3", "")).lower() == "sprint"
        and session_is_complete(event, 3, now)
    )
    race_complete = session_is_complete(event, 5, now)
    return sprint_complete or race_complete

def load_points_session(selected_year, round_number, session_code):
    session = ff1.get_session(selected_year, round_number, session_code)
    session.load(laps=False, telemetry=False, weather=False, messages=False)

    results = session.results.copy()
    if results.empty or "Points" not in results:
        return pd.DataFrame()

    return results[[
        "Abbreviation",
        "FullName",
        "TeamName",
        "Position",
        "Points",
    ]].copy()

@st.cache_data(ttl=3600)
def get_season_data(selected_year):
    schedule = get_event_schedule(selected_year)
    # Filter out pre-season testing if needed, keeping only proper rounds
    rounds = schedule[schedule['EventFormat'] != 'testing'].copy()
    now = utc_now()
    race_complete = rounds.apply(lambda row: session_is_complete(row, 5, now), axis=1)
    completed = rounds[race_complete]
    upcoming = rounds[~race_complete]
    return rounds, completed, upcoming

rounds, completed, upcoming = get_season_data(year)

st.markdown(f"**{len(rounds)} Races | Round {len(completed)} of {len(rounds)}**")
st.markdown("---")

@st.cache_data(ttl=3600)
def get_standings_and_progression(selected_year):
    schedule = get_event_schedule(selected_year)
    rounds = schedule[schedule['EventFormat'] != 'testing'].copy()
    now = utc_now()

    points_by_driver = {}
    names_by_driver = {}
    teams_by_driver = {}
    progression_snapshots = []

    def fetch_event_points(event):
        round_number = int(event["RoundNumber"])
        event_points = []

        if session_is_complete(event, 3, now) and str(event.get("Session3", "")).lower() == "sprint":
            try:
                event_points.append(load_points_session(selected_year, round_number, "S"))
            except Exception:
                pass

        if session_is_complete(event, 5, now):
            try:
                event_points.append(load_points_session(selected_year, round_number, "R"))
            except Exception:
                pass

        event_points = [df for df in event_points if not df.empty]
        if not event_points:
            return round_number, pd.DataFrame()

        df = pd.concat(event_points, ignore_index=True)
        return round_number, df

    eligible_events = [
        row for _, row in rounds.iterrows()
        if event_has_completed_points(row, now)
    ]

    if not eligible_events:
        return pd.DataFrame(), pd.DataFrame(), [], []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_event_points, eligible_events)

    for round_number, event_df in sorted(results, key=lambda item: item[0]):
        if event_df.empty:
            continue

        round_points = event_df.groupby("Abbreviation", as_index=False).agg({
            "Points": "sum",
            "FullName": "last",
            "TeamName": "last",
        })

        for _, row in round_points.iterrows():
            driver = row["Abbreviation"]
            points_by_driver[driver] = points_by_driver.get(driver, 0) + float(row["Points"])
            names_by_driver[driver] = row["FullName"]
            teams_by_driver[driver] = row["TeamName"]

        progression_snapshots.append({
            "Round": round_number,
            **points_by_driver,
        })

    if not points_by_driver:
        return pd.DataFrame(), pd.DataFrame(), [], []

    standings_df = pd.DataFrame([
        {
            "DriverCode": driver,
            "Driver": names_by_driver.get(driver, driver),
            "Team": teams_by_driver.get(driver, ""),
            "Points": points,
        }
        for driver, points in points_by_driver.items()
    ]).sort_values(by=["Points", "Driver"], ascending=[False, True]).reset_index(drop=True)

    top_5 = standings_df.head(5).copy()
    top_5["Pos"] = [f"{i:02d}" for i in range(1, len(top_5) + 1)]

    standings_table = top_5[["Pos", "Driver", "Team", "Points"]].copy()
    standings_table["Points"] = standings_table["Points"].map(lambda points: f"{points:g}")

    driver_ids = top_5["DriverCode"].tolist()
    last_names = top_5["Driver"].str.split().str[-1].tolist()
    colors = ["#47efda", "#ffcbc2", "#859490", "#ffe168", "#01d2be"]

    prog_df = pd.DataFrame(progression_snapshots).fillna(0)
    progression_data = {"Round": prog_df["Round"]}
    for driver_code, name in zip(driver_ids, last_names):
        progression_data[name] = prog_df.get(driver_code, 0)

    prog_df = pd.DataFrame(progression_data)
        
    return standings_table, prog_df, last_names, colors

standings, progression_df, top_drivers, plot_colors = get_standings_and_progression(year)

if not standings.empty:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Driver Standings (Top 5)")
        st.dataframe(standings, hide_index=True, width='stretch')

    with col2:
        st.subheader("Points Progression")
        if not progression_df.empty:
            fig = px.line(
                progression_df, x="Round", y=top_drivers,
                color_discrete_sequence=plot_colors,
                markers=True
            )
            
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e1e2e7",
                font_family="Space Grotesk",
                legend_title_text="Drivers",
                xaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)")
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Progression data not available.")
else:
    st.info(f"Live standings data for {year} is not available yet. Completed race or sprint results are required.")

st.markdown("---")
st.subheader("Race Calendar")

# Navigation Tabs for Races
tab1, tab2 = st.tabs(["Completed", "Upcoming"])

with tab1:
    cols = st.columns(4)
    for idx, row in completed.iterrows():
        with cols[idx % 4]:
            st.markdown(f"""
            <div style='background-color: var(--surface-container); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid var(--outline-variant)'>
                <h4 style='margin:0'>{row['EventName']}</h4>
                <p style='color: var(--on-surface-variant); font-size: 0.8rem'>{row['Location']} • {pd.to_datetime(row['EventDate']).strftime('%d %b')}</p>
                <span style='background: var(--secondary); color: black; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;'>COMPLETED</span>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    cols = st.columns(4)
    valid_idx = 0
    for idx, row in upcoming.iterrows():
        with cols[valid_idx % 4]:
            st.markdown(f"""
            <div style='background-color: var(--surface-container-low); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px dashed var(--outline-variant)'>
                <h4 style='margin:0'>{row['EventName']}</h4>
                <p style='color: var(--on-surface-variant); font-size: 0.8rem'>{row['Location']} • {pd.to_datetime(row['EventDate']).strftime('%d %b')}</p>
                <span style='background: var(--surface-bright); color: var(--on-surface); padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;'>UPCOMING</span>
            </div>
            """, unsafe_allow_html=True)
        valid_idx += 1

st.markdown("---")
st.subheader("Full Season Visual Summary")

st.markdown("Generates an interactive heatmap displaying points scored per driver at each round. *(Note: Sourcing raw results may take a while if unloaded)*")

@st.cache_data(ttl=3600, show_spinner=False)
def get_heatmap_data(selected_year):
    schedule = ff1.get_event_schedule(selected_year, include_testing=False)
    now = utc_now()
    heatmap_schedule = schedule[
        schedule.apply(lambda row: event_has_completed_points(row, now), axis=1)
    ]
    
    completed_rounds = heatmap_schedule['RoundNumber'].dropna().astype(int).tolist()
    short_event_names = [name.replace("Grand Prix", "").strip() for name in heatmap_schedule['EventName'].tolist()]
    
    if not completed_rounds:
        return None, None, None, None, None
        
    def fetch_round(event):
        r = int(event["RoundNumber"])
        points_sessions = []

        if session_is_complete(event, 3, now) and str(event.get("Session3", "")).lower() == "sprint":
            try:
                points_sessions.append(load_points_session(selected_year, r, "S"))
            except Exception:
                pass

        if session_is_complete(event, 5, now):
            try:
                points_sessions.append(load_points_session(selected_year, r, "R"))
            except Exception:
                pass

        points_sessions = [df for df in points_sessions if not df.empty]
        if points_sessions:
            return r, pd.concat(points_sessions, ignore_index=True)

        return r, pd.DataFrame()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_round, [row for _, row in heatmap_schedule.iterrows()])
        
    standings = []
    cumulative_points = {}
    for r, result_df in sorted(results, key=lambda item: item[0]):
        if result_df.empty:
            continue

        round_points = result_df.groupby("Abbreviation", as_index=False).agg({
            "Points": "sum",
            "Position": "last",
        })

        for _, row in round_points.iterrows():
            driver = row["Abbreviation"]
            cumulative_points[driver] = cumulative_points.get(driver, 0) + float(row["Points"])
            standings.append({
                "RoundNumber": r,
                "Driver": driver,
                "PointsCumulative": cumulative_points[driver],
                "Position": row.get("Position", "N/A"),
            })

    if not standings:
        return None, None, None, None, None

    df_st = pd.DataFrame(standings)
    cum_points = df_st.pivot(index="Driver", columns="RoundNumber", values="PointsCumulative").fillna(0)
    cum_points = cum_points.ffill(axis=1).fillna(0)

    heatmap_data = cum_points.diff(axis=1).fillna(cum_points) 
    heatmap_data = heatmap_data.round(1)
    heatmap_data = heatmap_data.clip(lower=0)

    heatmap_data["total_points"] = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data.sort_values(by="total_points", ascending=True)
    total_points = heatmap_data["total_points"].values
    heatmap_data = heatmap_data.drop(columns=["total_points"])

    position_data = df_st.pivot(index="Driver", columns="RoundNumber", values="Position").fillna("N/A")

    hover_info = [
        [{"position": position_data.at[driver, race] if driver in position_data.index and race in position_data.columns else "N/A"} for race in heatmap_data.columns]
        for driver in heatmap_data.index
    ]

    return heatmap_data, total_points, position_data, short_event_names, hover_info


if st.button("Generate Season Heatmap"):
    with st.spinner(f"Aggregating points matrix for {year} (Optimized)..."):
        try:
            heatmap_data, total_points, position_data, short_event_names, hover_info = get_heatmap_data(year)
            
            if heatmap_data is not None:
                fig = make_subplots(
                    rows=1, cols=2, column_widths=[0.85, 0.15],
                    subplot_titles=(f"F1 {year} Season Summary", "Total Points"),
                )
                
                fig.add_trace(go.Heatmap(
                    x=short_event_names, y=heatmap_data.index, z=heatmap_data.values,
                    text=heatmap_data.values, texttemplate="%{text}", textfont={"size": 12},
                    customdata=hover_info,
                    hovertemplate="Driver: %{y}<br>Race: %{x}<br>Points: %{z}<br>Position: %{customdata.position}<extra></extra>",
                    colorscale="YlGnBu", showscale=False, zmin=0, zmax=heatmap_data.values.max() if heatmap_data.size > 0 else 100
                ), row=1, col=1)
                
                fig.add_trace(go.Heatmap(
                    x=["Total Points"] * len(total_points), y=heatmap_data.index, z=total_points,
                    text=total_points, texttemplate="%{text}", textfont={"size": 12},
                    colorscale="YlGnBu", showscale=False, zmin=0, zmax=total_points.max() if len(total_points) > 0 else 100
                ), row=1, col=2)
                
                fig.update_layout(
                    height=800,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e1e2e7"
                )
                
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning("Could not build heatmap. Make sure the season has completed rounds.")
                
        except Exception as e:
            st.error(f"Failed to generate heatmap: {str(e)}")
