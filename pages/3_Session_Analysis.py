import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import apply_kinetic_pulse_theme
from utils.data import get_event_schedule, load_session_minimal
from utils.ui import sidebar_season_selector

st.set_page_config(page_title="Session Analysis", layout="wide")
apply_kinetic_pulse_theme()

st.title("Session Analysis")

# Initialize session state variables
if "session_analysis_data" not in st.session_state:
    st.session_state.session_analysis_data = None
if "session_analysis_selection" not in st.session_state:
    st.session_state.session_analysis_selection = None
if "session_analysis_driver_sel" not in st.session_state:
    st.session_state.session_analysis_driver_sel = None

year = sidebar_season_selector()

schedule = get_event_schedule(year)
event_name = st.sidebar.selectbox("Select Event", schedule['EventName'].tolist())
session_id = st.sidebar.selectbox("Select Session", ['FP1', 'FP2', 'FP3', 'Q', 'R', 'SQ', 'S'])

current_selection = (year, event_name, session_id)

# Create two columns for Load and Reset buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    load_btn = st.button("Load Session Data", use_container_width=True)
with col2:
    reset_btn = st.button("Reset", use_container_width=True)

# Handle button presses
if load_btn:
    with st.spinner(f"Loading {session_id} for {event_name}..."):
        try:
            session = load_session_minimal(year, event_name, session_id)
            laps = session.laps
            
            if not laps.empty:
                import fastf1.plotting
                
                # Fetch F1 Styles dynamically into dictionaries
                team_colors = {}
                for team in laps['Team'].dropna().unique():
                    try:
                        team_colors[team] = fastf1.plotting.get_team_color(team, session=session)
                    except:
                        pass
                
                compound_colors = {
                    'SOFT': '#FF3333', 'MEDIUM': '#FFFF00', 'HARD': '#FFFFFF', 
                    'INTERMEDIATE': '#39B54A', 'WET': '#00AEEF', 'UNKNOWN': '#AAAAAA'
                }

                # Quicklaps strictly for Pace Evaluation (excludes VSC/Pit out laps)
                quicklaps = laps.pick_quicklaps()
                if not quicklaps.empty:
                    quicklaps['LapTime (s)'] = quicklaps['LapTime'].dt.total_seconds()
                
                # Store in session state
                st.session_state.session_analysis_data = {
                    'session': session,
                    'laps': laps,
                    'quicklaps': quicklaps,
                    'team_colors': team_colors,
                    'compound_colors': compound_colors,
                    'event_name': event_name,
                    'session_id': session_id,
                    'year': year
                }
                st.session_state.session_analysis_selection = current_selection
                st.success(f"Loaded {session_id} for {event_name}")
            else:
                st.error("No laps data available for this session.")
        except Exception as e:
            st.error(f"Failed to load session: {e}")

elif reset_btn:
    st.session_state.session_analysis_data = None
    st.session_state.session_analysis_selection = None
    st.session_state.session_analysis_driver_sel = None
    st.success("Data reset. Select a new event and click Load Session Data.")

# Display tabs if data is loaded
if st.session_state.session_analysis_data is not None:
    data = st.session_state.session_analysis_data
    session = data['session']
    laps = data['laps']
    quicklaps = data['quicklaps']
    team_colors = data['team_colors']
    compound_colors = data['compound_colors']
    event_name = data['event_name']
    session_id = data['session_id']
    
    st.markdown(f"### Extended Analytics for {event_name} - {session_id}")
    
    # Initialize Architecture Tabs
    tab_team, tab_dist, tab_strat, tab_pos, tab_driver = st.tabs([
        "Team Pace Ranking", 
        "Driver Pace Distribution", 
        "Tyre Strategy", 
        "Position Changes", 
        "Driver Deep Dive"
    ])
    
    with tab_team:
        st.subheader("Team Pace Ranking")
        st.markdown("Rank team's race pace from the fastest to the slowest.")
        if not quicklaps.empty and 'Team' in quicklaps.columns:
            team_order = quicklaps[["Team", "LapTime (s)"]].groupby("Team").median().sort_values(by="LapTime (s)").index
            
            fig_team = px.box(quicklaps, x="Team", y="LapTime (s)", color="Team", 
                         category_orders={"Team": team_order},
                         color_discrete_map=team_colors)
            fig_team.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e1e2e7",
                xaxis=dict(showgrid=False, title=None),
                yaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap Time (s)")
            )
            st.plotly_chart(fig_team, use_container_width=True)
        else:
            st.info("Insufficient lap data for pace ranking.")
    
    with tab_dist:
        st.subheader("Lap Time Distributions")
        st.markdown("Visualize all drivers' laptime distributions with internal swarm tracking.")
        if not quicklaps.empty:
            # Attempt finishing order sort
            if hasattr(session, 'results') and session.results is not None and not session.results.empty:
                finishers = session.results.sort_values(by="Position")['Abbreviation'].dropna().tolist()
            else:
                finishers = quicklaps.groupby("Driver")["LapTime (s)"].median().sort_values().index.tolist()
                
            fig_dist = px.violin(quicklaps, x="Driver", y="LapTime (s)", color="Driver", points="all",
                            category_orders={"Driver": finishers})
            fig_dist.update_layout(
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e1e2e7",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap Time (s)")
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Insufficient lap data for distribution.")
            
    with tab_strat:
        st.subheader("Tyre Strategies")
        st.markdown("All drivers' tyre strategies and pitstop timelines during the session.")
        if 'Stint' in laps.columns and 'Compound' in laps.columns:
            stints = laps[["Driver", "Stint", "Compound", "LapNumber"]].dropna()
        else:
            stints = pd.DataFrame()
            
        if not stints.empty:
            stints_grouped = stints.groupby(["Driver", "Stint", "Compound"]).count().reset_index()
            stints_grouped = stints_grouped.rename(columns={"LapNumber": "StintLength"})
            
            fig_strat = px.bar(stints_grouped, y="Driver", x="StintLength", color="Compound", 
                            orientation='h', color_discrete_map=compound_colors,
                            category_orders={"Driver": finishers if 'finishers' in locals() else []})
            
            fig_strat.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e1e2e7",
                xaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap Number"),
                yaxis=dict(autorange="reversed", title=None)
            )
            st.plotly_chart(fig_strat, use_container_width=True)
        else:
            st.info("No tyre strategies available.")
            
    with tab_pos:
        st.subheader("Position Changes")
        st.markdown("Track overtakes and position evolution lap-by-lap.")
        if 'Position' in laps.columns:
            pos_laps = laps[["Driver", "LapNumber", "Position"]].dropna()
        else:
            pos_laps = pd.DataFrame()
        
        if not pos_laps.empty:
            fig_pos = px.line(pos_laps, x="LapNumber", y="Position", color="Driver", markers=True)
            fig_pos.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e1e2e7",
                xaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap"),
                yaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Position", autorange="reversed", dtick=1)
            )
            st.plotly_chart(fig_pos, use_container_width=True)
        else:
            st.info("No position tracking data available.")
            
    with tab_driver:
        st.subheader("Driver Laptime Scatterplot")
        st.markdown("Deep dive into specific drivers' performance mapped by compound.")
        drv_list = sorted(laps['Driver'].dropna().unique().tolist())
        if drv_list:
            # Use default of first driver to avoid empty selection
            default_drivers = [drv_list[0]] if drv_list else []
            sel_drivers = st.multiselect(
                "Select Driver(s)", 
                options=drv_list, 
                default=default_drivers,
                key="driver_lap_sel"
            )
            
            if sel_drivers:
                # Filter laps for the selected drivers
                drv_laps = laps[laps['Driver'].isin(sel_drivers)].copy()
                
                # Ensure LapTime column is in seconds
                if 'LapTime' in drv_laps.columns:
                    drv_laps['LapTime (s)'] = drv_laps['LapTime'].dt.total_seconds()
                
                # Clean the data - remove NaN lap times
                if 'LapTime (s)' in drv_laps.columns:
                    drv_laps = drv_laps[drv_laps['LapTime (s)'].notna()].copy()
                
                if not drv_laps.empty and 'LapNumber' in drv_laps.columns:
                    # Build title based on number of drivers
                    title = f"{', '.join(sel_drivers)} - Lap Time Analysis"
                    if len(sel_drivers) > 2:
                        title = f"{len(sel_drivers)} Drivers - Lap Time Analysis"
                    
                    fig_drv = px.scatter(
                        drv_laps, 
                        x="LapNumber", 
                        y="LapTime (s)", 
                        color="Driver",
                        symbol="Compound",
                        hover_data={'Driver': True, 'Compound': True, 'LapNumber': True, 'LapTime (s)': ':.2f'},
                        title=title
                    )
                    fig_drv.update_traces(marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey')))
                    fig_drv.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", 
                        paper_bgcolor="rgba(0,0,0,0)", 
                        font_color="#e1e2e7",
                        xaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap Number"),
                        yaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap Time (s)"),
                        height=500
                    )
                    st.plotly_chart(fig_drv, use_container_width=True)
                else:
                    st.warning(f"No valid lap data available for selected drivers: {', '.join(sel_drivers)}")
            else:
                st.info("Please select at least one driver.")
        else:
            st.info("No drivers found.")

else:
    st.info("Select an event, session, and click 'Load Session Data' to begin analysis.")
