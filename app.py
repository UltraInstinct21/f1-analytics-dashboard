import streamlit as st
import pandas as pd
import fastf1 as ff1
from utils.style import apply_kinetic_pulse_theme
from utils.data import get_event_schedule
from utils.ui import sidebar_season_selector

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="KINETIC PULSE | F1 Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_kinetic_pulse_theme()
year = sidebar_season_selector()


def utc_now():
    return pd.Timestamp.now(tz="UTC")


def session_start_utc(event, session_number):
    return pd.to_datetime(
        event.get(f"Session{session_number}DateUtc"),
        utc=True,
        errors="coerce",
    )


def session_is_complete(event, session_number, now=None):
    if now is None:
        now = utc_now()

    start = session_start_utc(event, session_number)
    if pd.isna(start):
        return False

    session_name = str(event.get(f"Session{session_number}", "")).lower()
    duration = pd.Timedelta(hours=2 if "sprint" in session_name else 4)
    return start + duration < now


@st.cache_data(ttl=1800)
def get_dashboard_summary(selected_year):
    schedule = get_event_schedule(selected_year)
    races = schedule[schedule["EventFormat"] != "testing"].copy()
    now = utc_now()

    races["RaceComplete"] = races.apply(
        lambda row: session_is_complete(row, 5, now),
        axis=1,
    )

    completed = races[races["RaceComplete"]]
    upcoming = races[~races["RaceComplete"]]

    latest_event = completed.iloc[-1].to_dict() if not completed.empty else None
    next_event = upcoming.iloc[0].to_dict() if not upcoming.empty else None

    active_drivers = "TBD"
    leader = "TBD"

    if latest_event is not None:
        try:
            session = ff1.get_session(selected_year, int(latest_event["RoundNumber"]), "R")
            session.load(laps=False, telemetry=False, weather=False, messages=False)
            results = session.results.copy()
            active_drivers = len(results) if not results.empty else "TBD"
            if not results.empty and "Position" in results:
                winner = results.sort_values("Position").iloc[0]
                leader = winner.get("FullName", winner.get("Abbreviation", "TBD"))
        except Exception:
            active_drivers = "TBD"
            leader = "TBD"

    return {
        "total_races": len(races),
        "completed_races": len(completed),
        "upcoming_races": len(upcoming),
        "active_drivers": active_drivers,
        "leader": leader,
        "latest_event": latest_event,
        "next_event": next_event,
    }


def format_event_date(event):
    if event is None:
        return "No scheduled race"
    return pd.to_datetime(event["EventDate"]).strftime("%d %b %Y")


def event_name(event, fallback="TBD"):
    if event is None:
        return fallback
    return event.get("EventName", fallback)


summary = get_dashboard_summary(year)

st.markdown("""
<style>
.main .block-container {
    padding-top: 2rem;
    max-width: 1220px;
}

.kp-hero {
    position: relative;
    overflow: hidden;
    padding: 2.25rem;
    border: 1px solid rgba(71, 239, 218, 0.18);
    border-radius: 8px;
    background:
        linear-gradient(135deg, rgba(255, 203, 194, 0.14), rgba(71, 239, 218, 0.06) 45%, rgba(251, 213, 2, 0.10)),
        repeating-linear-gradient(110deg, rgba(225, 226, 231, 0.05) 0 1px, transparent 1px 18px),
        var(--surface-container-low);
}

.kp-hero::after {
    content: "";
    position: absolute;
    inset: auto 0 0 0;
    height: 5px;
    background: linear-gradient(90deg, var(--secondary), var(--primary), var(--tertiary));
}

.kp-eyebrow {
    color: var(--secondary);
    font: 700 0.78rem 'Space Grotesk', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0;
    margin-bottom: 0.65rem;
}

.kp-hero h1 {
    margin: 0;
    font-size: clamp(2.75rem, 6vw, 5.75rem);
    line-height: 0.9;
}

.kp-hero p {
    max-width: 760px;
    margin: 1rem 0 0;
    color: var(--on-surface-variant);
    font-size: 1.05rem;
}

.kp-status-row {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 1.35rem;
}

.kp-status {
    padding: 1rem;
    border: 1px solid var(--outline-variant);
    border-radius: 8px;
    background: rgba(17, 20, 23, 0.55);
}

.kp-status span,
.kp-module span {
    display: block;
    color: var(--on-surface-variant);
    font-size: 0.78rem;
    text-transform: uppercase;
    font-weight: 700;
}

.kp-status strong {
    display: block;
    margin-top: 0.35rem;
    color: var(--on-surface);
    font: 800 1.15rem 'Space Grotesk', sans-serif;
}

.kp-section-title {
    margin: 1.75rem 0 0.75rem;
    font: 800 1.35rem 'Space Grotesk', sans-serif;
}

.kp-module-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
}

.kp-module {
    min-height: 150px;
    padding: 1.15rem;
    border: 1px solid rgba(186, 202, 198, 0.14);
    border-radius: 8px;
    background: linear-gradient(180deg, rgba(55, 57, 61, 0.52), rgba(25, 28, 31, 0.82));
}

.kp-module h3 {
    margin: 0.35rem 0 0.55rem;
    font-size: 1.15rem;
}

.kp-module p {
    margin: 0;
    color: var(--on-surface-variant);
}

.kp-tag {
    display: inline-block !important;
    margin-top: 0.95rem;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    background: rgba(71, 239, 218, 0.12);
    color: var(--secondary) !important;
}

.kp-guide {
    padding: 1.1rem;
    border-left: 4px solid var(--secondary);
    border-radius: 8px;
    background: var(--surface-container-low);
    color: var(--on-surface-variant);
}

.kp-guide strong {
    color: var(--on-surface);
}

.kp-footer {
    margin-top: 2rem;
    padding: 1rem 0;
    color: var(--on-surface-variant);
    border-top: 1px solid var(--outline-variant);
    font-size: 0.9rem;
}

@media (max-width: 760px) {
    .kp-hero {
        padding: 1.35rem;
    }

    .kp-status-row,
    .kp-module-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
st.markdown(f"""
<div class="kp-hero">
    <div class="kp-eyebrow">Season {year} Control Room</div>
    <h1>KINETIC PULSE</h1>
    <p>Live Formula 1 telemetry, championship context, race-weekend analysis, and driver comparison for the selected season.</p>
    <div class="kp-status-row">
        <div class="kp-status">
            <span>Calendar</span>
            <strong>{summary["completed_races"]} of {summary["total_races"]} rounds complete</strong>
        </div>
        <div class="kp-status">
            <span>Next Race</span>
            <strong>{event_name(summary["next_event"], "Season complete")}</strong>
        </div>
        <div class="kp-status">
            <span>Latest Winner</span>
            <strong>{summary["leader"]}</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Selected Season", str(year))
col2.metric("Total Races", summary["total_races"])
col3.metric("Upcoming Races", summary["upcoming_races"])
col4.metric("Active Drivers", summary["active_drivers"])

next_event = summary["next_event"]
latest_event = summary["latest_event"]
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"""
<div class="kp-status">
    <span>Latest Completed Event</span>
    <strong>{event_name(latest_event, "No completed race yet")}</strong>
    <p style="margin:0.45rem 0 0;color:var(--on-surface-variant);">{format_event_date(latest_event)}</p>
</div>
""", unsafe_allow_html=True)
with col_b:
    st.markdown(f"""
<div class="kp-status">
    <span>Next Scheduled Event</span>
    <strong>{event_name(next_event, "No upcoming race")}</strong>
    <p style="margin:0.45rem 0 0;color:var(--on-surface-variant);">{format_event_date(next_event)}</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="kp-section-title">Analysis Modules</div>', unsafe_allow_html=True)


def module_card(title, desc, tag):
    return f"""<div class="kp-module">
    <span>{tag}</span>
    <h3>{title}</h3>
    <p>{desc}</p>
    <span class="kp-tag">Season {year}</span>
</div>"""


modules = [
    (
        "Season Overview",
        "Championship standings, points progression, completed rounds, and upcoming races.",
        "Macro Analysis",
    ),
    (
        "Race Weekend Overview",
        "Track layouts, event schedules, and race-weekend context for each Grand Prix.",
        "Event Context",
    ),
    (
        "Session Analysis",
        "Lap distributions, fastest laps, tyre strategy, and session-level pace trends.",
        "Performance",
    ),
    (
        "Telemetry Lab",
        "Speed, throttle, brake, and gear traces for detailed driver comparison.",
        "Telemetry",
    ),
    (
        "Driver Comparison",
        "Head-to-head lap deltas that show where time is gained or lost.",
        "Comparison",
    ),
]

module_html = '<div class="kp-module-grid">'
for title, desc, tag in modules:
    module_html += module_card(title, desc, tag)
module_html += "</div>"
st.markdown(module_html, unsafe_allow_html=True)

st.markdown('<div class="kp-section-title">How To Use</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="kp-guide">
    <p><strong>1.</strong> Use the sidebar to choose a season. Current selection: <strong>{year}</strong>.</p>
    <p><strong>2.</strong> Open a module from the navigation sidebar and choose the event or session you want to inspect.</p>
    <p><strong>3.</strong> Load the relevant FastF1 data and interact with the charts to compare pace, strategy, and telemetry.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="kp-footer">
FastF1 powered analysis with cached live data.
</div>
""", unsafe_allow_html=True)
