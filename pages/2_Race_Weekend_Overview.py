import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import apply_kinetic_pulse_theme
from utils.data import get_event_schedule, get_session
from utils.ui import sidebar_season_selector

st.set_page_config(page_title="Race Weekend Overview", layout="wide")
apply_kinetic_pulse_theme()

st.title("Race Weekend Overview")

year = sidebar_season_selector()

schedule = get_event_schedule(year)
completed_rounds = schedule[schedule['EventDate'] < pd.Timestamp.now()]
if completed_rounds.empty:
    completed_rounds = schedule # fallback

event_name = st.sidebar.selectbox("Select Event", completed_rounds['EventName'].tolist())

if event_name:
    event_data = schedule[schedule['EventName'] == event_name].iloc[0]
    st.markdown(f"### {event_data['EventName']} - {event_data['Location']}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Weekend Sessions")
        sessions = [
            ("Session 1", event_data['Session1'], event_data['Session1DateUtc']),
            ("Session 2", event_data['Session2'], event_data['Session2DateUtc']),
            ("Session 3", event_data['Session3'], event_data['Session3DateUtc']),
            ("Session 4", event_data['Session4'], event_data['Session4DateUtc']),
            ("Session 5", event_data['Session5'], event_data['Session5DateUtc']),
        ]
        for s_idx, s_name, s_date in sessions:
            if pd.notna(s_name):
                st.markdown(f"""
                <div style='background-color: var(--surface-container-low); padding: 10px; margin-bottom: 5px; border-radius: 5px; border-left: 3px solid var(--primary)'>
                    <strong>{s_name}</strong><br>
                    <small style='color: var(--on-surface-variant)'>{s_date}</small>
                </div>
                """, unsafe_allow_html=True)
                
    with col2:
        st.subheader("Track Map")
        with st.spinner("Loading Track Data..."):
            try:
                # To draw track, we need telemetry from a session. We'll load Q or Race.
                session = get_session(year, event_name, 'Q')
                lap = session.laps.pick_fastest()
                tel = lap.get_telemetry()
                
                # Plotly line for track map
                fig = px.scatter(tel, x='X', y='Y', color='Speed', 
                                 color_continuous_scale=[(0, "white"), (0.5, "yellow"), (1.0, "red")])
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e1e2e7",
                    xaxis=dict(showgrid=False, zeroline=False, visible=False),
                    yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
                    coloraxis_colorbar=dict(title="Speed (km/h)", thicknessmode="pixels", thickness=15)
                )
                st.plotly_chart(fig, width='stretch')
            except Exception as e:
                st.error(f"Could not load telemetry for track map: {e}")
