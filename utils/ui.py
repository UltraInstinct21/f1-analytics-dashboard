import streamlit as st
import datetime

def sidebar_season_selector():
    current_year = datetime.datetime.now().year
    years = list(range(current_year, 2017, -1))
    
    # Render the selectbox in the sidebar and bind to session_state with key="global_season"
    selected_year = st.sidebar.selectbox("Select Season", years, index=0, key="global_season")
    return selected_year
