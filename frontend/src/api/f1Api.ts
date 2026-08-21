const API_BASE_URL = typeof window !== 'undefined' 
  ? `http://${window.location.hostname || 'localhost'}:8001/api`
  : 'http://localhost:8001/api';

export async function fetchSeasonsFromBackend(): Promise<number[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/seasons`);
    if (!res.ok) throw new Error('Seasons API error');
    const data = await res.json();
    return data.seasons || [2021, 2022, 2023, 2024, 2025, 2026];
  } catch (err) {
    console.warn('Falling back to local seasons:', err);
    return [2021, 2022, 2023, 2024, 2025, 2026];
  }
}

export async function fetchScheduleFromBackend(year: number) {
  try {
    const res = await fetch(`${API_BASE_URL}/schedule/${year}`);
    if (!res.ok) throw new Error('Schedule API error');
    const data = await res.json();
    return data.events || [];
  } catch (err) {
    console.warn('Schedule API error:', err);
    return null;
  }
}

export async function fetchStandingsFromBackend(year: number) {
  try {
    const res = await fetch(`${API_BASE_URL}/standings/${year}`);
    if (!res.ok) throw new Error('Standings API error');
    const data = await res.json();
    return data.standings || [];
  } catch (err) {
    console.warn('Standings API error:', err);
    return null;
  }
}

export async function fetchProgressionFromBackend(year: number) {
  try {
    const res = await fetch(`${API_BASE_URL}/progression/${year}`);
    if (!res.ok) throw new Error('Progression API error');
    const data = await res.json();
    return data.progression || [];
  } catch (err) {
    console.warn('Progression API error:', err);
    return null;
  }
}

export async function fetchMatrixFromBackend(year: number) {
  try {
    const res = await fetch(`${API_BASE_URL}/matrix/${year}`);
    if (!res.ok) throw new Error('Matrix API error');
    const data = await res.json();
    return data.matrix || [];
  } catch (err) {
    console.warn('Matrix API error:', err);
    return null;
  }
}

export async function fetchWeekendOverviewFromBackend(year: number, eventRef: string | number) {
  try {
    const res = await fetch(`${API_BASE_URL}/weekend/${year}/${eventRef}`);
    if (!res.ok) throw new Error('Weekend API error');
    return await res.json();
  } catch (err) {
    console.warn('Weekend API error:', err);
    return null;
  }
}

export async function fetchSessionPaceFromBackend(year: number, eventRef: string | number, sessionId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/session/${year}/${eventRef}/${sessionId}/pace`);
    if (!res.ok) throw new Error('Session Pace API error');
    return await res.json();
  } catch (err) {
    console.warn('Pace API error:', err);
    return null;
  }
}

export async function fetchTelemetryFromBackend(year: number, eventRef: string | number, sessionId: string, drivers: string[]) {
  try {
    const drvQuery = encodeURIComponent(drivers.join(','));
    const res = await fetch(`${API_BASE_URL}/session/${year}/${eventRef}/${sessionId}/telemetry?drivers=${drvQuery}`);
    if (!res.ok) throw new Error('Telemetry API error');
    return await res.json();
  } catch (err) {
    console.warn('Telemetry API error:', err);
    return null;
  }
}

export async function fetchComparisonFromBackend(year: number, eventRef: string | number, sessionId: string, driverA: string, driverB: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/session/${year}/${eventRef}/${sessionId}/comparison?driver_a=${driverA}&driver_b=${driverB}`);
    if (!res.ok) throw new Error('Comparison API error');
    return await res.json();
  } catch (err) {
    console.warn('Comparison API error:', err);
    return null;
  }
}

export async function fetchReplayFromBackend(year: number, eventRef: string | number, sessionId: string) {
  try {
    const res = await fetch(`${API_BASE_URL}/session/${year}/${eventRef}/${sessionId}/replay`);
    if (!res.ok) throw new Error('Replay API error');
    return await res.json();
  } catch (err) {
    console.warn('Replay API error:', err);
    return null;
  }
}

export async function fetchPredictionsFromBackend(year: number, eventRef: string | number) {
  try {
    const res = await fetch(`${API_BASE_URL}/predictions/${year}/${eventRef}`);
    if (!res.ok) throw new Error('Predictions API error');
    return await res.json();
  } catch (err) {
    console.warn('Predictions API error:', err);
    return null;
  }
}

export async function retrainPredictorFromBackend(seasons = '2022,2023,2024') {
  try {
    const res = await fetch(`${API_BASE_URL}/train-predictor?seasons=${encodeURIComponent(seasons)}`);
    if (!res.ok) throw new Error('Retrain API error');
    return await res.json();
  } catch (err) {
    console.warn('Retrain API error:', err);
    return null;
  }
}

export async function fetchRaceSimulation(weather = 'DRY', circuit = 'MONACO') {
  try {
    const res = await fetch(`${API_BASE_URL}/simulate-race?weather=${weather}&circuit=${circuit}`);
    if (!res.ok) throw new Error('Simulation endpoint error');
    return await res.json();
  } catch (err) {
    console.warn('Simulation error:', err);
    return null;
  }
}

export async function fetch2026SeasonProjection() {
  try {
    const res = await fetch(`${API_BASE_URL}/season-2026`);
    if (!res.ok) throw new Error('2026 Projection endpoint error');
    return await res.json();
  } catch (err) {
    console.warn('Projection error:', err);
    return null;
  }
}
