import streamlit as st

def apply_kinetic_pulse_theme():
    
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Kinetic Pulse Theme Variables */
        :root {
            --surface: #111417;
            --surface-container-low: #191c1f;
            --surface-container: #1d2023;
            --surface-bright: #37393d;
            --primary: #ffcbc2;
            --primary-container: #ffa494;
            --secondary: #47efda;
            --secondary-fixed: #56fae5;
            --tertiary: #fbd502;
            --on-surface: #e1e2e7;
            --on-surface-variant: #bacac6;
            --outline-variant: rgba(59, 74, 71, 0.15);
        }

        /* Streamlit Override */
        .stApp {
            background-color: var(--surface);
            color: var(--on-surface);
            font-family: 'Inter', sans-serif;
        }

        .stSidebar {
            background-color: var(--surface-container-low) !important;
        }

        /* Headers with Space Grotesk */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--on-surface) !important;
        }
        
        h1 {
            font-weight: 900 !important;
            font-style: italic;
            letter-spacing: -0.05em;
        }

        /* Monospace mandate */
        pre, code, .stDataFrame td {
            font-family: monospace !important;
            font-variant-numeric: tabular-nums;
            color: var(--on-surface);
        }
        </style>
    """, unsafe_allow_html=True)
