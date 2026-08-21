export interface DriverStanding {
  position: number;
  code: string;
  name: string;
  team: string;
  points: number;
  wins: number;
  podiums: number;
  color: string;
}

export interface EventInfo {
  round: number;
  name: string;
  location: string;
  date: string;
  country: string;
  completed: boolean;
  winner?: string;
}

export interface TelemetryPoint {
  distance: number;
  speed: number;
  throttle: number;
  brake: number;
  gear: number;
  drs: number;
}

export interface DriverTelemetry {
  code: string;
  name: string;
  team: string;
  color: string;
  lapTime: string;
  data: TelemetryPoint[];
}



export const ALL_GRID_DRIVERS: DriverStanding[] = [
  { position: 1, code: 'VER', name: 'Max Verstappen', team: 'Red Bull Racing', points: 437, wins: 9, podiums: 14, color: '#3671C6' },
  { position: 2, code: 'NOR', name: 'Lando Norris', team: 'McLaren', points: 374, wins: 4, podiums: 12, color: '#FF8000' },
  { position: 3, code: 'LEC', name: 'Charles Leclerc', team: 'Ferrari', points: 356, wins: 3, podiums: 11, color: '#E8002D' },
  { position: 4, code: 'PIA', name: 'Oscar Piastri', team: 'McLaren', points: 292, wins: 2, podiums: 8, color: '#FF8000' },
  { position: 5, code: 'SAI', name: 'Carlos Sainz', team: 'Ferrari', points: 290, wins: 2, podiums: 8, color: '#E8002D' },
  { position: 6, code: 'HAM', name: 'Lewis Hamilton', team: 'Mercedes', points: 223, wins: 2, podiums: 5, color: '#27F4D2' },
  { position: 7, code: 'RUS', name: 'George Russell', team: 'Mercedes', points: 215, wins: 1, podiums: 4, color: '#27F4D2' },
  { position: 8, code: 'PER', name: 'Sergio Perez', team: 'Red Bull Racing', points: 152, wins: 0, podiums: 4, color: '#3671C6' },
  { position: 9, code: 'ALO', name: 'Fernando Alonso', team: 'Aston Martin', points: 70, wins: 0, podiums: 0, color: '#229971' },
  { position: 10, code: 'GAS', name: 'Pierre Gasly', team: 'Alpine', points: 42, wins: 0, podiums: 1, color: '#0094DC' },
  { position: 11, code: 'STR', name: 'Lance Stroll', team: 'Aston Martin', points: 24, wins: 0, podiums: 0, color: '#229971' },
  { position: 12, code: 'OCO', name: 'Esteban Ocon', team: 'Alpine', points: 23, wins: 0, podiums: 0, color: '#0094DC' },
  { position: 13, code: 'ALB', name: 'Alexander Albon', team: 'Williams', points: 12, wins: 0, podiums: 0, color: '#64C4FF' },
  { position: 14, code: 'TSU', name: 'Yuki Tsunoda', team: 'Racing Bulls', points: 22, wins: 0, podiums: 0, color: '#6692FF' },
  { position: 15, code: 'RIC', name: 'Daniel Ricciardo', team: 'Racing Bulls', points: 12, wins: 0, podiums: 0, color: '#6692FF' },
  { position: 16, code: 'HUL', name: 'Nico Hulkenberg', team: 'Haas F1 Team', points: 31, wins: 0, podiums: 0, color: '#B6BABD' },
  { position: 17, code: 'MAG', name: 'Kevin Magnussen', team: 'Haas F1 Team', points: 14, wins: 0, podiums: 0, color: '#B6BABD' },
  { position: 18, code: 'BOT', name: 'Valtteri Bottas', team: 'Kick Sauber', points: 0, wins: 0, podiums: 0, color: '#52E252' },
  { position: 19, code: 'ZHO', name: 'Zhou Guanyu', team: 'Kick Sauber', points: 0, wins: 0, podiums: 0, color: '#52E252' },
  { position: 20, code: 'SAR', name: 'Logan Sargeant', team: 'Williams', points: 1, wins: 0, podiums: 0, color: '#64C4FF' },
];

export const DRIVER_STANDINGS_2025 = ALL_GRID_DRIVERS;

export const CALENDAR_2025: EventInfo[] = [
  { round: 1, name: 'Australian Grand Prix', location: 'Melbourne', date: '16 Mar 2025', country: '🇦🇺', completed: true, winner: 'Max Verstappen' },
  { round: 2, name: 'Chinese Grand Prix', location: 'Shanghai', date: '23 Mar 2025', country: '🇨🇳', completed: true, winner: 'Max Verstappen' },
  { round: 3, name: 'Japanese Grand Prix', location: 'Suzuka', date: '06 Apr 2025', country: '🇯🇵', completed: true, winner: 'Max Verstappen' },
  { round: 4, name: 'Bahrain Grand Prix', location: 'Sakhir', date: '13 Apr 2025', country: '🇧🇭', completed: true, winner: 'Lando Norris' },
  { round: 5, name: 'Saudi Arabian Grand Prix', location: 'Jeddah', date: '20 Apr 2025', country: '🇸🇦', completed: true, winner: 'Max Verstappen' },
  { round: 6, name: 'Miami Grand Prix', location: 'Miami', date: '04 May 2025', country: '🇺🇸', completed: true, winner: 'Lando Norris' },
  { round: 7, name: 'Emilia Romagna Grand Prix', location: 'Imola', date: '18 May 2025', country: '🇮🇹', completed: true, winner: 'Max Verstappen' },
  { round: 8, name: 'Monaco Grand Prix', location: 'Monte Carlo', date: '25 May 2025', country: '🇲🇨', completed: true, winner: 'Charles Leclerc' },
  { round: 9, name: 'Spanish Grand Prix', location: 'Barcelona', date: '01 Jun 2025', country: '🇪🇸', completed: true, winner: 'Max Verstappen' },
  { round: 10, name: 'Canadian Grand Prix', location: 'Montreal', date: '15 Jun 2025', country: '🇨🇦', completed: true, winner: 'Max Verstappen' },
  { round: 11, name: 'Austrian Grand Prix', location: 'Spielberg', date: '29 Jun 2025', country: '🇦🇹', completed: true, winner: 'George Russell' },
  { round: 12, name: 'British Grand Prix', location: 'Silverstone', date: '06 Jul 2025', country: '🇬🇧', completed: true, winner: 'Lewis Hamilton' },
  { round: 13, name: 'Hungarian Grand Prix', location: 'Budapest', date: '27 Jul 2025', country: '🇭🇺', completed: true, winner: 'Oscar Piastri' },
  { round: 14, name: 'Belgian Grand Prix', location: 'Spa-Francorchamps', date: '03 Aug 2025', country: '🇧🇪', completed: true, winner: 'Lewis Hamilton' },
  { round: 15, name: 'Dutch Grand Prix', location: 'Zandvoort', date: '31 Aug 2025', country: '🇳🇱', completed: true, winner: 'Lando Norris' },
  { round: 16, name: 'Italian Grand Prix', location: 'Monza', date: '07 Sep 2025', country: '🇮🇹', completed: true, winner: 'Charles Leclerc' },
  { round: 17, name: 'Azerbaijan Grand Prix', location: 'Baku', date: '21 Sep 2025', country: '🇦🇿', completed: true, winner: 'Oscar Piastri' },
  { round: 18, name: 'Singapore Grand Prix', location: 'Marina Bay', date: '05 Oct 2025', country: '🇸🇬', completed: true, winner: 'Lando Norris' },
  { round: 19, name: 'United States Grand Prix', location: 'Austin', date: '19 Oct 2025', country: '🇺🇸', completed: true, winner: 'Charles Leclerc' },
  { round: 20, name: 'Mexico City Grand Prix', location: 'Mexico City', date: '26 Oct 2025', country: '🇲🇽', completed: true, winner: 'Carlos Sainz' },
  { round: 21, name: 'São Paulo Grand Prix', location: 'Interlagos', date: '09 Nov 2025', country: '🇧🇷', completed: true, winner: 'Max Verstappen' },
  { round: 22, name: 'Las Vegas Grand Prix', location: 'Las Vegas', date: '22 Nov 2025', country: '🇺🇸', completed: true, winner: 'George Russell' },
  { round: 23, name: 'Qatar Grand Prix', location: 'Lusail', date: '30 Nov 2025', country: '🇶🇦', completed: true, winner: 'Max Verstappen' },
  { round: 24, name: 'Abu Dhabi Grand Prix', location: 'Yas Marina', date: '07 Dec 2025', country: '🇦🇪', completed: true, winner: 'Lando Norris' },
];

export const POINTS_PROGRESSION = [
  { round: 'R1', VER: 25, NOR: 18, LEC: 15, PIA: 12, HAM: 6, SAI: 10, RUS: 8, PER: 4 },
  { round: 'R3', VER: 76, NOR: 44, LEC: 47, PIA: 32, HAM: 18, SAI: 40, RUS: 24, PER: 46 },
  { round: 'R6', VER: 136, NOR: 101, LEC: 98, PIA: 81, HAM: 27, SAI: 85, RUS: 37, PER: 103 },
  { round: 'R9', VER: 194, NOR: 153, LEC: 138, PIA: 112, HAM: 55, SAI: 108, RUS: 69, PER: 107 },
  { round: 'R12', VER: 255, NOR: 171, LEC: 150, PIA: 124, HAM: 110, SAI: 146, RUS: 111, PER: 118 },
  { round: 'R15', VER: 303, NOR: 225, LEC: 192, PIA: 179, HAM: 154, SAI: 172, RUS: 128, PER: 139 },
  { round: 'R18', VER: 331, NOR: 279, LEC: 245, PIA: 237, HAM: 174, SAI: 190, RUS: 155, PER: 144 },
  { round: 'R21', VER: 393, NOR: 331, LEC: 307, PIA: 262, HAM: 190, SAI: 244, RUS: 192, PER: 151 },
  { round: 'R24', VER: 437, NOR: 374, LEC: 356, PIA: 292, HAM: 223, SAI: 290, RUS: 215, PER: 152 },
];

// Round x Driver Heatmap Dataset
export const HEATMAP_MATRIX = [
  { driver: 'VER', R1: 25, R2: 25, R3: 25, R4: 18, R5: 25, R6: 18, R7: 25, R8: 8, R9: 25, R10: 25 },
  { driver: 'NOR', R1: 18, R2: 6, R3: 10, R4: 25, R5: 12, R6: 25, R7: 18, R8: 12, R9: 18, R10: 18 },
  { driver: 'LEC', R1: 15, R2: 12, R3: 12, R4: 15, R5: 15, R6: 15, R7: 15, R8: 25, R9: 10, R10: 10 },
  { driver: 'PIA', R1: 12, R2: 4, R3: 4, R4: 4, R5: 4, R6: 4, R7: 12, R8: 18, R9: 6, R10: 12 },
  { driver: 'SAI', R1: 10, R2: 15, R3: 15, R4: 10, R5: 10, R6: 10, R7: 10, R8: 15, R9: 8, R10: 8 },
  { driver: 'HAM', R1: 6, R2: 2, R3: 2, R4: 2, R5: 2, R6: 8, R7: 8, R8: 6, R9: 12, R10: 15 },
  { driver: 'RUS', R1: 8, R2: 8, R3: 8, R4: 8, R5: 8, R6: 4, R7: 6, R8: 10, R9: 4, R10: 6 },
  { driver: 'PER', R1: 18, R2: 18, R3: 10, R4: 12, R5: 18, R6: 12, R7: 4, R8: 0, R9: 4, R10: 4 },
];

export const GENERATE_TELEMETRY = (driverCode: string, color: string, baseSpeed = 280): DriverTelemetry => {
  const driverInfo = ALL_GRID_DRIVERS.find((d) => d.code === driverCode) || ALL_GRID_DRIVERS[0];
  const points: TelemetryPoint[] = [];
  const totalDist = 5800; // 5.8 km lap length
  const steps = 120;

  for (let i = 0; i <= steps; i++) {
    const dist = Math.round((i / steps) * totalDist);
    let speed = baseSpeed;
    let throttle = 100;
    let brake = 0;
    let gear = 8;
    let drs = 0;

    // Corner 1: Turn 1-2 Chicane (700m - 1200m)
    if (dist >= 700 && dist <= 1200) {
      speed = 105 + Math.sin((dist - 700) / 500 * Math.PI) * 22;
      throttle = dist > 950 ? 65 : 0;
      brake = dist <= 950 ? 95 : 0;
      gear = 3;
    }
    // Main Straight DRS (2000m - 3200m)
    else if (dist >= 2000 && dist <= 3200) {
      speed = 315 + ((dist - 2000) / 1200) * 33;
      throttle = 100;
      brake = 0;
      gear = 8;
      drs = 1;
    }
    // High speed Lesmo sweepers (4000m - 4800m)
    else if (dist >= 4000 && dist <= 4800) {
      speed = 215 + Math.cos((dist - 4000) / 800 * Math.PI) * 38;
      throttle = 82;
      brake = 18;
      gear = 6;
    }

    // Driver pace variations
    const seedOffset = driverCode.charCodeAt(0) % 7;
    speed = Math.max(75, Math.round(speed + Math.sin(i / (4 + seedOffset)) * 8));

    points.push({
      distance: dist,
      speed,
      throttle: Math.round(throttle),
      brake: Math.round(brake),
      gear,
      drs,
    });
  }

  return {
    code: driverCode,
    name: driverInfo.name,
    team: driverInfo.team,
    color: color || driverInfo.color,
    lapTime: driverCode === 'VER' ? '1:21.046' : driverCode === 'NOR' ? '1:21.198' : '1:21.410',
    data: points,
  };
};



export const PREDICTION_PODIUM_PROBABILITY = [
  { position: 1, driver: 'Max Verstappen', team: 'Red Bull Racing', probability: '42.5%', color: '#3671C6' },
  { position: 2, driver: 'Lando Norris', team: 'McLaren', probability: '28.3%', color: '#FF8000' },
  { position: 3, driver: 'Charles Leclerc', team: 'Ferrari', probability: '18.1%', color: '#E8002D' },
  { position: 4, driver: 'Oscar Piastri', team: 'McLaren', probability: '6.8%', color: '#FF8000' },
  { position: 5, driver: 'Lewis Hamilton', team: 'Ferrari (2026)', probability: '4.3%', color: '#E8002D' },
];

export const FEATURE_IMPORTANCE = [
  { feature: 'Starting Grid Position', importance: 0.54 },
  { feature: 'Constructor Pace Delta', importance: 0.24 },
  { feature: 'Driver Historical Rank', importance: 0.14 },
  { feature: 'Track Elevation / Weather', importance: 0.08 },
];
