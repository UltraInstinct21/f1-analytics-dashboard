# 🏎️ Kinetic Pulse F1 Analysis Dashboard - User Guide

Welcome to the **Kinetic Pulse F1 Analysis Dashboard**! This comprehensive application provides live telemetry and performance analysis for Formula 1 races across multiple seasons.

## 📖 Quick Navigation
- [Getting Started](#getting-started)
- [Features Overview](#features-overview)
- [Tips & Tricks](#tips--tricks)
- [FAQ](#faq)

---

## Getting Started

### First Time Using the Dashboard?

1. **Launch the app**: The dashboard opens on the **Home: Season Overview** page by default
2. **Select a season**: Use the **Season Selector** in the sidebar to choose any available F1 season (2020+)
3. **Navigate tabs**: Use the left sidebar to switch between different analysis tools
4. **Interactive elements**: Most charts are interactive—hover for details, click to zoom, right-click to reset

### Dashboard Layout

```
┌─────────────────────────────────────────┐
│        Kinetic Pulse F1 Dashboard       │
├─────────┬─────────────────────────────┤
│         │                             │
│ Sidebar │    Main Content Area        │
│ (Tabs)  │   (Visualizations &        │
│         │    Data Tables)             │
│         │                             │
└─────────┴─────────────────────────────┘
```

---

## Features Overview

Here is a complete breakdown of all the features and selection options available across the different modules in the app.

---

## 1. Home: Season Overview (`pages/1_Home_Season_Overview.py`)

This page provides a high-level summary of the Formula 1 Championship.

**Features:**
*   **Driver Standings:** A data table displaying the current top drivers in the championship, their team, and total points.
*   **Points Progression:** an interactive line chart illustrating the championship points progression over the season's rounds for the top contenders.
*   **Race Calendar:** A visual display of the F1 calendar, split into two interactive tabs:
    *   **Completed:** Shows past races with their event names, locations, dates, and a "COMPLETED" badge.
    *   **Upcoming:** Outlines future races for the season with an "UPCOMING" badge.

**Selection Options:**
*   **Navigation Tabs:** Toggle between `Completed` and `Upcoming` races.

---

## 2. Race Weekend Overview (`pages/2_Race_Weekend_Overview.py`)

This module helps you understand the context, schedule, and track characteristics of a specific race weekend.

**Features:**
*   **Weekend Sessions:** A detailed list of all sessions for the selected event (Practice 1/2/3, Qualifying, Sprint, and Race) along with their localized UTC dates and times.
*   **Dynamic Track Map:** An interactive, telemetry-driven track layout generated from the fastest qualifying lap of that weekend. The track map is continuously colored to visualize car speeds (white to yellow to red) across the circuit.

**Selection Options:**
*   **Select Event (Sidebar):** A dropdown menu to choose any completed event from the race calendar. 

---

## 3. Session Analysis (`pages/3_Session_Analysis.py`)

A deeper dive into the specific lap times and performances of all drivers over the course of a chosen session.

**Features:**
*   **Fastest Laps Table:** A data table showing the absolute fastest lap time achieved by every active driver during the session.
*   **Lap Time Distribution:** An interactive box plot mapping the variation and consistency of lap times for each driver across their entire session, colored by constructor.

**Selection Options:**
*   **Select Event (Sidebar):** Choose any event from the calendar.
*   **Select Session (Sidebar):** Choose the specific session format (`FP1`, `FP2`, `FP3`, `Q`, `R`, `SQ`, `S`).
*   **Load Session Data (Button):** Executes the query to fetch and process data for your event/session combo.

---

## 4. Telemetry Lab (`pages/4_Telemetry_Lab.py`)

A pro-level tool that brings you straight into the cockpit, allowing you to plot raw telemetry components against distance alongside one another.

**Features:**
*   **Multi-Driver Telemetry Traces:** Generates four stacked, synchronized interactive line charts displaying:
    *   **Speed (km/h)**
    *   **Throttle (%)**
    *   **Brake**
    *   **Gear**
    All plotted dynamically against distance (in meters). Traces scale automatically based on selected drivers and colors.

**Selection Options:**
*   **Select Event (Dropdown):** Choose any event from the calendar.
*   **Select Session (Dropdown):** Choose the relevant session (`Q`, `R`, `FP1`, `FP2`, `FP3`, `SQ`, `S`).
*   **Select Drivers to Compare (Multi-select):** Once the session is fetched, pick two or more drivers from the active session grid.
*   **Generate Telemetry Traces (Button):** Processes the fastest laps for the selected drivers and updates the charts.

---

## 5. Driver Comparison (`pages/5_Driver_Comparison.py`)

A head-to-head comparison module designed to measure the raw time delta between two specific drivers over a single fastest lap.

**Features:**
*   **Metrics Dashboard:** Displays the raw fastest lap times for both selected drivers.
*   **Delta Metric:** Clearly highlights the time difference between the two drivers (`+` or `-` seconds) styled accordingly.
*   **Time Delta over Distance:** An interactive, filled area chart mapping the comparative time delta (seconds) against distance (meters) throughout the lap. It clearly demonstrates precisely where on track Driver 2 gained or lost time compared to Driver 1.

**Selection Options:**
*   **Select Event (Dropdown):** Choose any event from the calendar.
*   **Select Session (Dropdown):** Choose the relevant session (`Q`, `R`, `FP1`, `FP2`, `FP3`, `SQ`, `S`).
*   **Driver 1 / Reference (Dropdown):** Select the baseline driver for comparison.
*   **Driver 2 (Dropdown):** Select the challenger (the dropdown automatically excludes Driver 1).
*   **Compare Drivers (Button):** Processes the F1 telemetry deltas and generates the visualization.

---

## 6. Race Replay (`pages/6_Race_Replay.py`)

Experience the race as it unfolded with animated lap-by-lap visualization and live telemetry overlays.

**Features:**
*   **Animated Race Visualization:** Watch the race in real-time with live position tracking for all drivers on the track.
*   **Track Visualization:** See all drivers simultaneously positioned on the circuit, with colors representing their teams/constructors.
*   **Playback Controls:** Control animation speed, pause for detailed analysis, and rewind to critical moments.
*   **Telemetry Overlay:** View telemetry data (speed, throttle, brake) alongside race positions for deeper insights.
*   **Driver Highlighting:** Focus on specific drivers or compare multiple drivers throughout the race.

**Selection Options:**
*   **Select Event (Sidebar):** Choose any race event from the calendar.
*   **Select Session (Sidebar):** Choose the race session (`R` for main race or `SQ`/`S` for sprint).
*   **Play/Pause Controls (Button):** Start the race replay animation.
*   **Speed Control (Slider):** Adjust playback speed for detailed or fast-forward analysis.

---

## Tips & Tricks

### 🎯 Getting the Most Out of Each Feature

**Home: Season Overview**
- 📌 Hover over the points progression chart to see exact points at each round
- 📌 Use the race calendar tabs to quickly identify which races have concluded vs. upcoming
- 📌 Check standings to identify championship leaders before diving into specific races

**Race Weekend Overview**
- 📌 The track map updates based on the fastest qualifying lap, so it shows the actual racing line
- 📌 Session times are in UTC—check your local timezone for accurate race start times
- 📌 Use this page before analyzing specific sessions to understand track characteristics

**Session Analysis**
- 📌 Sort the fastest laps table by clicking column headers to find consistency outliers
- 📌 The lap time distribution shows which drivers struggled vs. thrived in that session
- 📌 Red flags or safety cars may affect data—check if laptimes seem unusual
- 📌 Compare FP1/FP2 with Qualifying to see driver/team pace improvement

**Telemetry Lab: Pro Analysis**
- 📌 Use this for comparing strategies—throttle/brake patterns reveal different driving styles
- 📌 Gear changes at the same distance indicate consistent corner handling
- 📌 Zoom into specific track sections (corners, straights) for detailed comparison
- 📌 Select drivers from different teams to spot performance gaps

**Driver Comparison**
- 📌 The time delta chart clearly shows which track sections each driver gains advantages
- 📌 Positive delta (blue) = Driver 2 gaining time; Negative (red) = Driver 2 losing time
- 📌 Compare drivers across different sessions to see consistency
- 📌 Compare qualifying vs. race laps for the same drivers to see tire strategy impact

**Race Replay**
- 📌 Slow down the replay to see pit stop strategy and timing
- 📌 Watch driver-to-driver battles in real-time for tactical insight
- 📌 Use to verify overtaking positions shown in telemetry data
- 📌 Great for understanding championship battles and position changes

### 🔄 Performance Tips

**Faster Loading**
- Load Qualifying or Race sessions—Free Practice sessions have more laps and take longer
- The dashboard caches data locally, so re-selecting events loads much faster
- Limit multi-driver comparisons to 2-3 drivers for smoother performance

**Better Analysis**
- Compare drivers from different teams for clear performance gaps
- Use multiple sessions (FP1 → FP2 → FP3 → Q) to see driver/team progression
- Combine Race Replay with Telemetry Lab for comprehensive race analysis

### 📊 Data Interpretation

**Lap Times**
- Session times vary due to fuel loads, tire age, and track conditions
- Fastest laps in Race sessions show ultimate car performance under racing conditions
- Compare drivers with similar pit stop strategies for fair comparison

**Telemetry Data**
- Speed varies based on fuel load—heavier fuel = slower speeds on same engine power
- Throttle % peaks and timing reveal driving aggression and precision
- Brake application patterns show corner-entry aggression and confidence

---

## FAQ

### How do I access historical seasons?

Use the **Season Selector** in the sidebar to choose seasons back to 2020. Select the year you want to analyze and browse all races from that season.

### Why is some session data missing?

- **Free Practice sessions** may be incomplete if weather red flags stopped the session
- **Historical data** (pre-2020) is not available in FastF1
- **Retired drivers** may have incomplete data if they crashed or had mechanical failure early

### Can I export the data?

Currently, the dashboard is read-only for viewing and analysis. You can screenshot charts or use browser developer tools to extract data from interactive charts.

### The track map looks wrong. What's the issue?

The track map is generated from the fastest qualifying lap. If qualifying was cancelled or delayed, the map may use practice data. This is normal behavior.

### How often is data updated?

- **Completed races**: Data is cached locally after first load and loads instantly on subsequent views
- **Live races**: Force-refresh by deleting local cache (see README for cache location)
- **Real-time telemetry**: Not available—data loads post-session completion

### What's the difference between Driver Comparison and Telemetry Lab?

- **Driver Comparison**: Shows lap time delta at each point on track (WHERE drivers lose/gain time)
- **Telemetry Lab**: Shows raw sensor data (speed, throttle, brake, gear) for deeper race strategy analysis

Use both together for complete understanding.

### Can I compare drivers across different races?

Not directly in a single visualization. However, you can:
1. Analyze Driver A at Race 1
2. Analyze Driver B at Race 2
3. Look at standings to infer performance differences

### Why does my selection reset when I switch tabs?

This is intentional to prevent loading incorrect data. Simply re-select your event/session/drivers when switching between features.

### How do I understand the telemetry traces?

- **Speed**: Raw car velocity in km/h
- **Throttle**: % of full throttle (0-100%)
- **Brake**: Binary on/off (0 = not braking, 1 = braking)
- **Gear**: Current gear (1-8, with -1 for reverse if visible)

All traces are synchronized to **distance**, so identical distance = identical track location for all drivers.

### What's "SQ" vs "S" vs "R"?

- **SQ**: Sprint Qualifying (determines sprint race grid)
- **S**: Sprint Race (shorter race on Friday/Saturday)
- **R**: Main Race (Sunday's primary race)
- **Q**: Qualifying (determines Sunday race grid)
- **FP1/FP2/FP3**: Free Practice sessions

---

## Troubleshooting

**Charts not loading?**
- Check your internet connection (data is fetched on first load)
- Try refreshing the page (Ctrl+R or Cmd+R)
- Clear browser cache and reload

**Slow performance?**
- Close other browser tabs to free up memory
- Reduce number of drivers in comparisons
- Reload the page to restart the dashboard

**Data looks incorrect?**
- Verify you've selected the correct season and event
- Check if the session completed (not cancelled due to weather)
- Try a different event to confirm dashboard functionality

---

**Last Updated**: April 2025  
**Need help?** Check the [README.md](README.md) or open an issue on GitHub.

Happy analyzing! 🏁
