# 🏎️ Kinetic Pulse - F1 Analysis Dashboard

A comprehensive, interactive Formula 1 telemetry and performance analysis dashboard built with Streamlit. Analyze race data, compare driver performances, and explore detailed telemetry in real-time.

![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=flat&logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat&logo=python)
![FastF1](https://img.shields.io/badge/FastF1-3.0+-FF0000?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## ✨ Features

### 1. 🏠 Home: Season Overview
Get a high-level summary of the Formula 1 Championship season:
- **Driver Standings**: Current championship points for the top drivers
- **Points Progression**: Interactive line chart showing points evolution across the season
- **Race Calendar**: Visual display of completed and upcoming races with event details and dates

### 2. 🏁 Race Weekend Overview
Explore race weekend context and track characteristics:
- **Weekend Sessions**: Complete schedule and times for all sessions (FP1, FP2, FP3, Qualifying, Sprint, Race)
- **Dynamic Track Map**: Interactive telemetry-driven track layout with speed visualization (white → yellow → red gradient)
- **Event Selection**: Choose any event from the F1 calendar

### 3. 📊 Session Analysis
Deep dive into lap times and driver performance for specific sessions:
- **Fastest Laps Table**: Absolute fastest lap times for each driver in the session
- **Lap Time Distribution**: Interactive box plots showing consistency and variation by driver
- **Constructor Coloring**: Visual categorization by team colors
- **Multi-Session Support**: Analyze FP1, FP2, FP3, Qualifying, Sprint, or Race sessions

### 4. 🔬 Telemetry Lab: Pro Analysis
Professional-grade telemetry analysis with raw data visualization:
- **Multi-Driver Telemetry**: Compare up to multiple drivers simultaneously
- **Four Synchronized Traces**:
  - Speed (km/h)
  - Throttle (%)
  - Brake Application
  - Gear Selection
- **Distance-based Visualization**: All data plotted against track distance (meters)
- **Interactive Charts**: Zoom, pan, and hover for detailed inspection

### 5. 🆚 Driver Comparison
Head-to-head driver performance analysis:
- **Fastest Lap Metrics**: Raw lap times for both drivers
- **Time Delta**: Precise time difference between drivers (±seconds)
- **Delta Over Distance**: Filled area chart showing where drivers gain or lose time throughout the lap
- **Detailed Insights**: Identify specific track sections for performance differences

### 6. 🎬 Race Replay
Animated race visualization with live telemetry data:
- **Lap-by-Lap Replay**: Watch the race unfold with real-time position data
- **Interactive Playback**: Control speed and pause for detailed analysis
- **Telemetry Overlay**: View telemetry data alongside race positions
- **Track Visualization**: See all drivers' positions on the track in real-time

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **pip** or **conda**

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ds-f1-analysis-dashboard.git
cd ds-f1-analysis-dashboard
```

2. **Create a virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **(Optional) Install Race Replay feature**

The Race Replay feature requires an external module. To enable it:
```bash
# Clone the f1-race-replay module into the project root
git clone https://github.com/IAmTomShaw/f1-race-replay.git
```

**Without this module**: All other features work normally. Race Replay will show a message to install it if needed.

### Running the Dashboard

Start the Streamlit application:
```bash
streamlit run app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

---

## 📋 Requirements

```
streamlit>=1.30.0
fastf1>=3.0.0
pandas>=2.0.0
plotly>=5.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
```

---

## 📁 Project Structure

```
ds-f1-analysis-dashboard/
├── app.py                          # Main Streamlit application entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── guide.md                        # Detailed user guide
├── pages/
│   ├── 1_Home_Season_Overview.py  # Season summary and standings
│   ├── 2_Race_Weekend_Overview.py # Race weekend details
│   ├── 3_Session_Analysis.py      # Lap times and distribution
│   ├── 4_Telemetry_Lab.py         # Pro telemetry analysis
│   ├── 5_Driver_Comparison.py     # Head-to-head comparison
│   └── 6_Race_Replay.py           # Animated race replay
├── utils/
│   ├── data.py                     # Data fetching and processing
│   ├── style.py                    # UI theming and styling
│   └── ui.py                       # Shared UI components
├── cache/                          # Cached F1 session data
└── f1-race-replay/                 # Race replay engine module
    ├── src/
    ├── main.py
    └── README.md
```

---

## 🔄 Data Pipeline

This dashboard uses the **FastF1** library to fetch official Formula 1 telemetry data:

1. **Data Source**: [`fastf1` PyPI Package](https://github.com/theOehrly/Fast-F1)
2. **Cache Strategy**: Session data is cached locally to reduce API calls
3. **Real-time Updates**: New race weekends are automatically detected and cached
4. **Supported Seasons**: 2018 onwards (current season: 2025)

### Data Freshness
- Cache is automatically invalidated for new races
- Manual cache refresh available in the sidebar

---

## 🎯 Usage Guide

### Selecting a Season
Use the **Season Selector** in the sidebar to choose any available F1 season (2020+).

### Analyzing a Specific Race
1. Navigate to **Race Weekend Overview**
2. Select an event from the dropdown
3. View the track map and session schedule

### Comparing Drivers
1. Go to **Driver Comparison**
2. Select an event and session
3. Choose Driver 1 (reference) and Driver 2
4. View the time delta analysis

### Deep Telemetry Analysis
1. Open **Telemetry Lab: Pro Analysis**
2. Select event and session
3. Choose 2+ drivers to compare
4. Generate telemetry traces with 4 synchronized visualizations

---

## 🛠️ Technical Details

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly (interactive charts), Matplotlib, Seaborn
- **Data Source**: FastF1 Library (official F1 telemetry)

### Performance Optimizations
- **Caching**: Streamlit's `@st.cache_data` for expensive computations
- **Local Cache**: Session data stored locally to minimize API calls
- **Lazy Loading**: Data fetched on-demand per user selections

---

## 🔧 Configuration

### Custom Themes
Modify `utils/style.py` to customize:
- Color scheme
- Font styles
- Layout spacing
- Component styling

### Cache Location
Cached data is stored in `./cache/` directory organized by season:
```
cache/
├── 2024/
│   ├── 2024-03-02_Bahrain_Grand_Prix/
│   └── 2024-09-22_Singapore_Grand_Prix/
└── 2025/
    ├── 2025-03-16_Australian_Grand_Prix/
    └── ...
```

---

## 🐛 Troubleshooting

**Issue**: "Session data not loading"
- **Solution**: Check internet connection; data is fetched from FastF1 servers on first access

**Issue**: "Track map not displaying"
- **Solution**: Ensure the session has completed qualifying for track layout generation

**Issue**: "Slow performance with large sessions"
- **Solution**: Reduce the number of drivers compared or use a faster internet connection

**Issue**: Cache issues
- **Solution**: Delete the `cache/` directory and restart the app for a fresh cache

**Issue**: "Race Replay module not found" error
- **Solution**: Clone the f1-race-replay module as described in the [Installation](#installation) section:
  ```bash
  git clone https://github.com/IAmTomShaw/f1-race-replay.git
  ```
- **Alternative**: Other features work fine without this module. Race Replay will show an info message if not available.

---

## 📚 Documentation

For a detailed user guide with screenshots and feature walkthroughs, see [guide.md](guide.md).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to:
- Report bugs via GitHub Issues
- Suggest new features
- Submit pull requests with improvements

### Development Setup
```bash
git clone <repo-url>
cd ds-f1-analysis-dashboard
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastF1 Library**: Official F1 telemetry data fetching
  - [GitHub](https://github.com/theOehrly/Fast-F1)
  - [Documentation](https://docs.fastf1.dev/)
- **Formula 1**: Official race data and telemetry
- **Streamlit**: Interactive web framework
- **Plotly**: Interactive visualization library

---

## 📧 Support

For questions, issues, or suggestions:
- Open a GitHub Issue
- Check existing issues and discussions
- Review the detailed [guide.md](guide.md) for feature documentation

---

## 🏁 Roadmap

- [ ] Multi-season comparison tools
- [ ] Historical performance trends
- [ ] Weather impact analysis
- [ ] Pit stop strategy optimization
- [ ] Real-time race updates (when available)
- [ ] Export to PDF/CSV functionality
- [ ] Mobile app optimization

---

**Last Updated**: April 2026
**Current Season**: 2026 F1 Championship

Made with ❤️ for F1 enthusiasts and data analysts.
