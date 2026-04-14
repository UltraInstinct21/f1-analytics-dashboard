import fastf1
import streamlit as st

# Setup fastf1 cache globally
import os
os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

@st.cache_data(ttl=3600)
def get_event_schedule(year):
    return fastf1.get_event_schedule(year)

@st.cache_resource(ttl=3600)
def get_session(year, event, session_id):
    session = fastf1.get_session(year, event, session_id)
    session.load(telemetry=True, laps=True, weather=True)
    return session

@st.cache_resource(ttl=3600)
def load_session_minimal(year, event, session_id):
    session = fastf1.get_session(year, event, session_id)
    session.load(telemetry=False, laps=True, weather=False)
    return session
