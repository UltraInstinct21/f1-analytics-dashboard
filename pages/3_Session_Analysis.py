import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import apply_kinetic_pulse_theme
from utils.data import get_event_schedule, load_session_minimal
from utils.ui import sidebar_season_selector

st.set_page_config(page_title="Session Analysis", layout="wide")
apply_kinetic_pulse_theme()

st.title("Session Analysis")

year = sidebar_season_selector()

schedule = get_event_schedule(year)
event_name = st.sidebar.selectbox("Select Event", schedule['EventName'].tolist())
session_id = st.sidebar.selectbox("Select Session", ['FP1', 'FP2', 'FP3', 'Q', 'R', 'SQ', 'S'])

if st.button("Load Session Data"):
    with st.spinner(f"Loading {session_id} for {event_name}..."):
        try:
            session = load_session_minimal(year, event_name, session_id)
            laps = session.laps
            
            st.markdown(f"### Extended Analytics for {event_name} - {session_id}")
            
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
                        st.plotly_chart(fig_team, width='stretch')
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
                        st.plotly_chart(fig_dist, width='stretch')
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
                        st.plotly_chart(fig_strat, width='stretch')
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
                        st.plotly_chart(fig_pos, width='stretch')
                    else:
                        st.info("No position tracking data available.")
                        
                with tab_driver:
                    st.subheader("Driver Laptime Scatterplot")
                    st.markdown("Deep dive into specific drivers' performance mapped by compound.")
                    drv_list = laps['Driver'].dropna().unique().tolist()
                    if drv_list:
                        sel_drivers = st.multiselect("Select Driver(s)", drv_list, default=[drv_list[0]], key="driver_lap_sel")
                        drv_laps = quicklaps[quicklaps['Driver'].isin(sel_drivers)] if not quicklaps.empty else pd.DataFrame()
                        
                        if not drv_laps.empty:
                            fig_drv = px.scatter(drv_laps, x="LapNumber", y="LapTime (s)", color="Driver", symbol="Compound")
                            fig_drv.update_traces(marker=dict(size=10, line=dict(width=1, color='DarkSlateGrey')))
                            fig_drv.update_layout(
                                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e1e2e7",
                                xaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap Number"),
                                yaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Lap Time (s)")
                            )
                            st.plotly_chart(fig_drv, width='stretch')
                        else:
                            st.warning(f"No quicklaps mapped for selected drivers")
                    else:
                        st.info("No drivers found.")

            else:
                st.warning("No laps data available.")
                
        except Exception as e:
            st.error(f"Failed to load session: {e}")
