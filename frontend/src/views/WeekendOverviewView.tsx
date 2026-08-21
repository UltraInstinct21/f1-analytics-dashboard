import React, { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { Clock } from 'lucide-react';
import { CALENDAR_2025 } from '../data/mockF1Data';
import { GET_CIRCUIT_BY_ROUND } from '../data/circuitCoordinates';
import { fetchScheduleFromBackend, fetchWeekendOverviewFromBackend } from '../api/f1Api';

interface WeekendOverviewViewProps {
  selectedSeason: number;
  selectedRound: number;
  setSelectedRound: (round: number) => void;
}

export const WeekendOverviewView: React.FC<WeekendOverviewViewProps> = ({
  selectedSeason,
  selectedRound,
  setSelectedRound,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [events, setEvents] = useState<any[]>(CALENDAR_2025);
  const [weekendData, setWeekendData] = useState<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const ctx = gsap.context(() => {
      gsap.from('.gsap-fade', {
        opacity: 0,
        y: 16,
        duration: 0.6,
        stagger: 0.1,
        ease: 'power2.out',
      });
    }, containerRef);

    return () => ctx.revert();
  }, [selectedRound, selectedSeason]);

  // Load schedule for selected season
  useEffect(() => {
    async function loadSchedule() {
      const realSched = await fetchScheduleFromBackend(selectedSeason);
      if (realSched && realSched.length > 0) {
        const formatted = realSched.map((evt: any, idx: number) => ({
          round: evt.RoundNumber || idx + 1,
          name: evt.EventName || `Round ${idx + 1}`,
          country: evt.Country || evt.Location || 'Grand Prix',
          location: evt.Location || 'Circuit',
          date: evt.EventDate ? evt.EventDate.substring(0, 10) : ''
        }));
        setEvents(formatted);
      }
    }
    loadSchedule();
  }, [selectedSeason]);

  // Fetch weekend overview & dynamic track geometry for selected event
  useEffect(() => {
    async function loadWeekendDetails() {
      const data = await fetchWeekendOverviewFromBackend(selectedSeason, selectedRound);
      if (data && !data.error) {
        setWeekendData(data);
      } else {
        setWeekendData(null);
      }
    }
    loadWeekendDetails();
  }, [selectedSeason, selectedRound]);

  const currentEvent = events.find((e) => e.round === selectedRound) || events[0] || CALENDAR_2025[0];
  const fallbackCircuit = GET_CIRCUIT_BY_ROUND(selectedRound);

  const trackGeo = weekendData?.trackGeometry || {
    pathD: fallbackCircuit.pathD,
    viewBox: fallbackCircuit.viewBox,
    startLine: fallbackCircuit.startLine,
    turns: fallbackCircuit.turns,
    drsZones: fallbackCircuit.drsZones
  };

  const sessions = weekendData?.sessions || [
    { name: 'Free Practice 1', date: '05 Sep', time: '13:30 - 14:30 UTC', status: 'Completed' },
    { name: 'Free Practice 2', date: '05 Sep', time: '17:00 - 18:00 UTC', status: 'Completed' },
    { name: 'Free Practice 3', date: '06 Sep', time: '12:30 - 13:30 UTC', status: 'Completed' },
    { name: 'Qualifying', date: '06 Sep', time: '16:00 - 17:00 UTC', status: 'Completed' },
    { name: 'Grand Prix Race', date: '07 Sep', time: '13:00 UTC', status: 'Completed' },
  ];

  return (
    <div ref={containerRef} className="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 pt-28 pb-16 space-y-12">
      {/* Selector Header */}
      <div className="gsap-fade flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-signal-blue)]">
            {selectedSeason} Season • Round {currentEvent.round} of {events.length}
          </span>
          <h1 className="font-editorial text-3xl sm:text-4xl lg:text-5xl text-[var(--color-graphite)] tracking-tight">
            {currentEvent.country} {currentEvent.name}
          </h1>
          <p className="text-xs sm:text-sm text-[var(--color-ash)] mt-1.5">
            {currentEvent.location} Circuit • Dynamic FastF1 2D Telemetry Contour & Weekend Schedule.
          </p>
        </div>

        {/* Round Selector Dropdown */}
        <div className="flex items-center gap-2 bg-[var(--color-paper)] p-2 rounded-xl border border-[var(--color-mist)] shrink-0 shadow-sm">
          <label className="text-xs text-[var(--color-ash)] pl-2 font-medium">Select Event:</label>
          <select
            value={selectedRound}
            onChange={(e) => setSelectedRound(Number(e.target.value))}
            className="text-xs bg-[var(--color-linen)] font-medium text-[var(--color-graphite)] px-3.5 py-2 rounded-lg border border-[var(--color-mist)] focus:outline-none cursor-pointer"
          >
            {events.map((evt) => (
              <option key={evt.round} value={evt.round}>
                R{evt.round}: {evt.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Track Map + Specs Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
        {/* Dynamic Authentic Track Map Canvas Card */}
        <div className="gsap-fade lg:col-span-8 card-mist p-6 sm:p-8 flex flex-col justify-between relative overflow-hidden bg-gradient-to-b from-white to-[var(--color-linen)]">
          <div className="flex items-center justify-between z-10">
            <div>
              <span className="text-[10px] font-mono text-[var(--color-ash)] uppercase tracking-widest">
                FastF1 2D Telemetry Circuit Contour
              </span>
              <h3 className="font-editorial text-xl text-[var(--color-graphite)]">
                {currentEvent.location} Circuit ({selectedSeason})
              </h3>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-medium text-[var(--color-ash)]">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Full Throttle</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Apexes</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-sky-500" /> DRS Zones</span>
            </div>
          </div>

          {/* Authentic SVG Circuit Contour */}
          <div className="w-full h-[440px] my-4 flex items-center justify-center relative">
            <svg viewBox={trackGeo.viewBox || "0 0 800 500"} className="w-full h-full max-h-[360px]">
              <defs>
                <linearGradient id="circuitSpeedGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#10B981" />
                  <stop offset="35%" stopColor="#F59E0B" />
                  <stop offset="70%" stopColor="#EF4444" />
                  <stop offset="100%" stopColor="#41A1CF" />
                </linearGradient>
              </defs>

              {/* Outer Glow Path */}
              <path
                d={trackGeo.pathD}
                fill="none"
                stroke="url(#circuitSpeedGradient)"
                strokeWidth="14"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.2"
              />

              {/* Main Circuit Path */}
              <path
                d={trackGeo.pathD}
                fill="none"
                stroke="url(#circuitSpeedGradient)"
                strokeWidth="5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Start / Finish Line */}
              {trackGeo.startLine && (
                <line
                  x1={trackGeo.startLine.x1}
                  y1={trackGeo.startLine.y1}
                  x2={trackGeo.startLine.x2}
                  y2={trackGeo.startLine.y2}
                  stroke="#171717"
                  strokeWidth="4"
                  strokeLinecap="square"
                />
              )}

              {/* Corner Annotations */}
              {trackGeo.turns && trackGeo.turns.map((turn: any) => (
                <g key={turn.number} transform={`translate(${turn.x}, ${turn.y})`}>
                  <circle r="4" fill="#171717" />
                  <text
                    fontSize="10"
                    fontWeight="bold"
                    fill="#444141"
                    className="font-mono drop-shadow-sm"
                    dy="-6"
                    dx="-10"
                  >
                    {turn.name}
                  </text>
                </g>
              ))}

              {/* DRS Zone Labels */}
              {trackGeo.drsZones && trackGeo.drsZones.map((drs: any, i: number) => (
                <text
                  key={i}
                  x={drs.x}
                  y={drs.y}
                  fontSize="10"
                  fontWeight="bold"
                  fill="#41A1CF"
                  className="font-mono tracking-wide"
                >
                  ▶ {drs.name}
                </text>
              ))}
            </svg>
          </div>

          <div className="flex items-center justify-between text-xs text-[var(--color-ash)] pt-3 border-t border-[var(--color-mist)] z-10">
            <span>Location: {currentEvent.location}</span>
            <span>Turns: {trackGeo.turns ? trackGeo.turns.length : 11} Annotated Apexes</span>
            <span>DRS Zones: {trackGeo.drsZones ? trackGeo.drsZones.length : 2}</span>
          </div>
        </div>

        {/* Circuit Technical Specs */}
        <div className="gsap-fade lg:col-span-4 space-y-4">
          <div className="card-mist p-5">
            <span className="text-xs text-[var(--color-ash)] uppercase tracking-wider font-medium">Race Distance</span>
            <div className="text-2xl font-editorial text-[var(--color-graphite)] mt-1">306.72 km</div>
            <span className="text-xs text-[var(--color-ash)]">53 Laps Total</span>
          </div>

          <div className="card-mist p-5">
            <span className="text-xs text-[var(--color-ash)] uppercase tracking-wider font-medium">Lap Record</span>
            <div className="text-2xl font-editorial text-[var(--color-signal-blue)] mt-1">1:21.046</div>
            <span className="text-xs text-[var(--color-ash)]">Rubens Barrichello (2004)</span>
          </div>

          <div className="card-mist p-5">
            <span className="text-xs text-[var(--color-ash)] uppercase tracking-wider font-medium">Full Throttle %</span>
            <div className="text-2xl font-editorial text-[var(--color-graphite)] mt-1">76% of Lap</div>
            <span className="text-xs text-[var(--color-ash)]">High Speed Telemetry Profile</span>
          </div>
        </div>
      </div>

      {/* Weekend Sessions Schedule */}
      <div className="gsap-fade card-mist p-6">
        <h3 className="font-editorial text-xl text-[var(--color-graphite)] mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-[var(--color-signal-blue)]" />
          Weekend Session Schedule & Status ({selectedSeason})
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
          {sessions.map((sess: any, idx: number) => (
            <div
              key={idx}
              className="p-4 rounded-xl border border-[var(--color-mist)] bg-[var(--color-linen)] flex flex-col justify-between"
            >
              <div>
                <span className="text-[10px] uppercase font-mono text-[var(--color-ash)]">Session {idx + 1}</span>
                <h4 className="font-semibold text-sm text-[var(--color-graphite)] mt-1 mb-2">
                  {sess.name}
                </h4>
              </div>

              <div className="space-y-1 text-xs text-[var(--color-ash)]">
                <div>{sess.date}</div>
                <div className="font-mono text-[11px] text-[var(--color-charcoal)]">{sess.time || 'Scheduled'}</div>
                <div className="pt-2">
                  <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-100 text-emerald-800">
                    {sess.status || 'Completed'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
