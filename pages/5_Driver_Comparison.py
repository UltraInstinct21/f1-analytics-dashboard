import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.style import apply_kinetic_pulse_theme
from utils.data import get_event_schedule, get_session
from utils.ui import sidebar_season_selector
from fastf1 import utils
import fastf1
from fastf1 import plotting
import matplotlib.pyplot as plt

st.set_page_config(page_title="Driver Comparison", layout="wide")
apply_kinetic_pulse_theme()

# Enable Matplotlib patches for plotting timedelta values and load FastF1's dark color scheme
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1')

st.title("Driver Analysis Comparison")

year = sidebar_season_selector()
schedule = get_event_schedule(year)
col1, col2 = st.columns(2)
with col1:
    event_name = st.selectbox("Select Event", schedule['EventName'].tolist(), key="event")
with col2:
    session_id = st.selectbox("Select Session", ['Q', 'R', 'FP1', 'FP2', 'FP3', 'SQ', 'S'], key="session")

session_loaded = False
try:
    with st.spinner("Loading telemetry..."):
        session = get_session(year, event_name, session_id)
        laps = session.laps
        drivers = laps['Driver'].dropna().unique().tolist()
        session_loaded = True
except Exception as e:
    st.error(f"Error loading session: {e}")

if session_loaded and len(drivers) >= 2:
    ccol1, ccol2 = st.columns(2)
    with ccol1:
        driver1 = st.selectbox("Driver 1 (Reference)", drivers, index=0)
    with ccol2:
        driver2_options = [d for d in drivers if d != driver1]
        driver2 = st.selectbox("Driver 2", driver2_options, index=0)
        
    if st.button("Compare Drivers"):
        with st.spinner("Calculating time delta..."):
            lap1 = laps.pick_drivers(driver1).pick_fastest()
            lap2 = laps.pick_drivers(driver2).pick_fastest()
            
            if pd.notna(lap1['LapTime']) and pd.notna(lap2['LapTime']):
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric(f"{driver1} Fastest", str(lap1['LapTime'])[10:19])
                col_m2.metric(f"{driver2} Fastest", str(lap2['LapTime'])[10:19])
                
                diff = lap2['LapTime'] - lap1['LapTime']
                diff_str = f"+{diff.total_seconds():.3f}s" if diff.total_seconds() > 0 else f"{diff.total_seconds():.3f}s"
                col_m3.metric("Delta", diff_str, delta=-diff.total_seconds() if diff.total_seconds() > 0 else abs(diff.total_seconds()), delta_color="inverse")
                
                tel1 = lap1.get_telemetry().add_distance()
                tel2 = lap2.get_telemetry().add_distance()
                
                delta_time, ref_tel, compare_tel = utils.delta_time(lap1, lap2)
                
                fig = go.Figure()
                # We plot Delta Time (driver 2 relative to driver 1)
                fig.add_trace(go.Scatter(x=ref_tel['Distance'], y=delta_time, 
                                         mode='lines', name=f"Delta ({driver2} - {driver1})",
                                         line=dict(color="#56fae5", width=2),
                                         fill='tozeroy', fillcolor="rgba(86,250,229,0.1)"))
                
                fig.update_layout(
                    title="Time Delta over Distance",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e1e2e7",
                    xaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Distance (m)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", title="Delta (s)")
                )
                
                st.plotly_chart(fig, width='stretch')
                
                st.markdown("---")
                st.subheader(f"Pace Comparison: {driver1} vs {driver2}")
                st.info("Pace overview over all quick laps using FastF1's native plotting styles.")
                
                fig_mpl, ax = plt.subplots(figsize=(8, 5))
                
                for driver in (driver1, driver2):
                    # Filter out slow laps as they distort the graph axis
                    driver_laps = laps.pick_drivers(driver).pick_quicklaps().reset_index()
                    style = plotting.get_driver_style(identifier=driver,
                                                      style=['color', 'linestyle'], # get custom style
                                                      session=session)
                    ax.plot(driver_laps['LapNumber'], driver_laps['LapTime'], **style, label=driver)

                # add axis labels and a legend
                ax.set_xlabel("Lap Number", color='white')
                ax.set_ylabel("Lap Time", color='white')
                plotting.add_sorted_driver_legend(ax, session)
                
                fig_mpl.patch.set_alpha(0.0)
                ax.patch.set_alpha(0.0)
                
                st.pyplot(fig_mpl)
                
            else:
                st.warning("One or both drivers do not have a valid fastest lap recorded in this session.")
