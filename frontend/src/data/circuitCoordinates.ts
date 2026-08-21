export interface TrackPoint {
  x: number;
  y: number;
}

export interface CircuitShape {
  name: string;
  location: string;
  pathD: string;
  points: TrackPoint[];
  viewBox: string;
  turns: { number: number; name: string; x: number; y: number }[];
  drsZones: { name: string; x: number; y: number }[];
  startLine: { x1: number; y1: number; x2: number; y2: number };
}

// High-fidelity Monza Circuit Layout Coordinates
const MONZA_POINTS: TrackPoint[] = [
  { x: 120, y: 380 }, // Start/Finish Straight
  { x: 260, y: 380 },
  { x: 340, y: 380 }, // Heading to T1
  { x: 380, y: 380 },
  { x: 395, y: 350 }, // T1 Chicane (Prima Variante)
  { x: 410, y: 375 }, // T2 Exit
  { x: 480, y: 350 }, // Curva Grande (T3)
  { x: 550, y: 290 },
  { x: 620, y: 220 },
  { x: 660, y: 160 },
  { x: 645, y: 140 }, // T4-5 Variante della Roggia
  { x: 625, y: 155 },
  { x: 570, y: 130 }, // Lesmo 1 (T6)
  { x: 530, y: 100 }, // Lesmo 2 (T7)
  { x: 470, y: 90 },
  { x: 390, y: 110 }, // Serraglio Straight
  { x: 310, y: 130 },
  { x: 250, y: 150 },
  { x: 230, y: 135 }, // T8-10 Variante Ascari Chicane
  { x: 210, y: 165 },
  { x: 190, y: 180 }, // Exit Ascari
  { x: 160, y: 230 }, // Heading to Parabolica
  { x: 140, y: 280 },
  { x: 110, y: 330 }, // Curva Parabolica / Alboreto (T11)
  { x: 100, y: 360 },
  { x: 120, y: 380 }, // Return to Main Straight
];

// Helper to convert TrackPoints array to smooth SVG cubic bezier path string
export const pointsToPathString = (pts: TrackPoint[]): string => {
  if (pts.length === 0) return '';
  let d = `M ${pts[0].x},${pts[0].y}`;
  for (let i = 1; i < pts.length; i++) {
    const prev = pts[i - 1];
    const curr = pts[i];
    const xc = (prev.x + curr.x) / 2;
    const yc = (prev.y + curr.y) / 2;
    d += ` Q ${prev.x},${prev.y} ${xc},${yc}`;
  }
  d += ` Z`;
  return d;
};

// Monza Real Circuit Model
export const MONZA_CIRCUIT: CircuitShape = {
  name: 'Autodromo Nazionale Monza',
  location: 'Monaco / Monza, Italy',
  pathD: pointsToPathString(MONZA_POINTS),
  points: MONZA_POINTS,
  viewBox: '0 0 800 480',
  turns: [
    { number: 1, name: 'Prima Variante (T1-2)', x: 405, y: 395 },
    { number: 3, name: 'Curva Grande (T3)', x: 575, y: 270 },
    { number: 4, name: 'Variante della Roggia (T4-5)', x: 655, y: 130 },
    { number: 6, name: 'Lesmo 1 & 2 (T6-7)', x: 530, y: 75 },
    { number: 8, name: 'Variante Ascari (T8-10)', x: 210, y: 125 },
    { number: 11, name: 'Curva Parabolica (T11)', x: 80, y: 340 },
  ],
  drsZones: [
    { name: 'DRS Zone 1 (Main Straight)', x: 230, y: 400 },
    { name: 'DRS Zone 2 (Serraglio)', x: 380, y: 140 },
  ],
  startLine: { x1: 170, y1: 365, x2: 170, y2: 395 },
};

// Silverstone Circuit Model
const SILVERSTONE_POINTS: TrackPoint[] = [
  { x: 180, y: 360 }, // Hamilton Straight / Start
  { x: 300, y: 360 },
  { x: 350, y: 370 }, // T1 Abbey
  { x: 390, y: 330 }, // T2 Farm Curve
  { x: 420, y: 390 }, // T3 Village Heavy Braking
  { x: 400, y: 430 }, // T4 The Loop
  { x: 450, y: 440 }, // T5 Aintree
  { x: 560, y: 380 }, // Wellington Straight
  { x: 640, y: 320 }, // T6 Brooklands
  { x: 670, y: 250 }, // T7 Luffield
  { x: 650, y: 190 }, // Woodcote
  { x: 580, y: 180 }, // Copse Straight
  { x: 520, y: 150 }, // T9 Copse High Speed Entry
  { x: 450, y: 130 }, // Maggotts (T10)
  { x: 390, y: 110 }, // Becketts (T11-12)
  { x: 340, y: 140 }, // Chapel (T13)
  { x: 240, y: 200 }, // Hangar Straight
  { x: 160, y: 260 }, // T15 Stowe
  { x: 130, y: 310 }, // Vale & Club (T16-18)
  { x: 180, y: 360 },
];

export const SILVERSTONE_CIRCUIT: CircuitShape = {
  name: 'Silverstone Circuit',
  location: 'Silverstone, United Kingdom',
  pathD: pointsToPathString(SILVERSTONE_POINTS),
  points: SILVERSTONE_POINTS,
  viewBox: '0 0 800 480',
  turns: [
    { number: 1, name: 'Abbey & Village (T1-3)', x: 380, y: 405 },
    { number: 6, name: 'Brooklands & Luffield (T6-7)', x: 685, y: 245 },
    { number: 9, name: 'Copse (T9)', x: 520, y: 125 },
    { number: 10, name: 'Maggotts & Becketts (T10-12)', x: 390, y: 90 },
    { number: 15, name: 'Stowe (T15)', x: 135, y: 250 },
    { number: 18, name: 'Club (T18)', x: 110, y: 325 },
  ],
  drsZones: [
    { name: 'DRS Zone 1 (Wellington Straight)', x: 500, y: 410 },
    { name: 'DRS Zone 2 (Hangar Straight)', x: 280, y: 180 },
  ],
  startLine: { x1: 220, y1: 345, x2: 220, y2: 375 },
};

// Monaco Circuit Model
const MONACO_POINTS: TrackPoint[] = [
  { x: 220, y: 410 }, // Pit Straight
  { x: 360, y: 410 },
  { x: 420, y: 390 }, // Sainte Devote (T1)
  { x: 510, y: 290 }, // Beau Rivage Uphill
  { x: 570, y: 210 }, // Massenet (T2)
  { x: 620, y: 160 }, // Casino Square (T3)
  { x: 640, y: 190 }, // Mirabeau Haute (T4)
  { x: 610, y: 220 }, // Grand Hotel Hairpin (T5)
  { x: 580, y: 240 }, // Mirabeau Bas (T6)
  { x: 630, y: 270 }, // Portier (T7)
  { x: 590, y: 330 }, // Tunnel Entry
  { x: 510, y: 370 }, // Nouvelle Chicane (T10-11)
  { x: 440, y: 340 }, // Tabac (T12)
  { x: 360, y: 310 }, // Swimming Pool (T13-16)
  { x: 280, y: 330 },
  { x: 240, y: 370 }, // Rascasse (T17-18)
  { x: 200, y: 390 }, // Anthony Noghes (T19)
  { x: 220, y: 410 },
];

export const MONACO_CIRCUIT: CircuitShape = {
  name: 'Circuit de Monaco',
  location: 'Monte Carlo, Monaco',
  pathD: pointsToPathString(MONACO_POINTS),
  points: MONACO_POINTS,
  viewBox: '0 0 800 480',
  turns: [
    { number: 1, name: 'Sainte Devote (T1)', x: 445, y: 405 },
    { number: 3, name: 'Casino Square (T3)', x: 645, y: 145 },
    { number: 6, name: 'Hairpin (T6)', x: 585, y: 210 },
    { number: 10, name: 'Nouvelle Chicane (T10)', x: 510, y: 390 },
    { number: 17, name: 'La Rascasse (T17)', x: 235, y: 350 },
  ],
  drsZones: [
    { name: 'DRS Zone (Pit Straight)', x: 280, y: 430 },
  ],
  startLine: { x1: 270, y1: 395, x2: 270, y2: 425 },
};

export const GET_CIRCUIT_BY_ROUND = (round: number): CircuitShape => {
  if (round === 12) return SILVERSTONE_CIRCUIT;
  if (round === 8) return MONACO_CIRCUIT;
  return MONZA_CIRCUIT; // Default high fidelity track shape
};

// Interpolate position (x, y) along a TrackPoint polyline curve given a distance ratio (0.0 to 1.0)
export const getInterpolatedTrackPoint = (pts: TrackPoint[], progress: number): TrackPoint => {
  if (!pts || pts.length === 0) return { x: 400, y: 250 };
  const totalSegments = pts.length - 1;
  const scaled = progress * totalSegments;
  const idx = Math.floor(scaled);
  const frac = scaled - idx;

  const p1 = pts[idx % pts.length];
  const p2 = pts[(idx + 1) % pts.length];

  return {
    x: p1.x + (p2.x - p1.x) * frac,
    y: p1.y + (p2.y - p1.y) * frac,
  };
};
