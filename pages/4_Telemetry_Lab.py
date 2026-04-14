import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.style import apply_kinetic_pulse_theme
from utils.data import get_event_schedule, get_session
from utils.ui import sidebar_season_selector

st.set_page_config(page_title="Telemetry Lab", layout="wide")
apply_kinetic_pulse_theme()

st.title("Telemetry Lab: Pro Analysis")

year = sidebar_season_selector()
schedule = get_event_schedule(year)
col1, col2 = st.columns(2)
with col1:
    event_name = st.selectbox("Select Event", schedule['EventName'].tolist())
with col2:
    session_id = st.selectbox("Select Session", ['Q', 'R', 'FP1', 'FP2', 'FP3', 'SQ', 'S'])

session_loaded = False
try:
    with st.spinner("Loading telemetry..."):
        session = get_session(year, event_name, session_id)
        laps = session.laps
        drivers = laps['Driver'].dropna().unique().tolist()
        session_loaded = True
except Exception as e:
    st.error(f"Error loading session: {e}")

if session_loaded and drivers:
    selected_drivers = st.multiselect("Select Drivers to Compare", drivers, default=drivers[:2])
    
    if st.button("Generate Telemetry Traces") and selected_drivers:
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                            subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake", "Gear"))
        
        # Color palette for traces
        colors = ["#47efda", "#ffcbc2", "#ffe168", "#01d2be", "#dbb900"]
        
        with st.spinner("Plotting telemetry..."):
            for i, driver in enumerate(selected_drivers):
                color = colors[i % len(colors)]
                driver_lap = laps.pick_drivers(driver).pick_fastest()
                
                if pd.notna(driver_lap['LapTime']):
                    tel = driver_lap.get_telemetry().add_distance()
                    
                    # Speed
                    fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Speed'], 
                                             mode='lines', name=f"{driver} Speed",
                                             line=dict(color=color)), row=1, col=1)
                    # Throttle
                    fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Throttle'], 
                                             mode='lines', name=f"{driver} Throttle",
                                             line=dict(color=color)), row=2, col=1)
                    # Brake
                    fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['Brake'], 
                                             mode='lines', name=f"{driver} Brake",
                                             line=dict(color=color)), row=3, col=1)
                    # Gear
                    fig.add_trace(go.Scatter(x=tel['Distance'], y=tel['nGear'], 
                                             mode='lines', name=f"{driver} Gear",
                                             line=dict(color=color)), row=4, col=1)
            
            fig.update_layout(
                height=800,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e1e2e7",
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            # Grid lines
            for i in range(1, 5):
                fig.update_yaxes(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", row=i, col=1)
            fig.update_xaxes(showgrid=True, gridcolor="rgba(59, 74, 71, 0.15)", row=4, col=1, title_text="Distance (m)")
            
            st.plotly_chart(fig, width='stretch')
