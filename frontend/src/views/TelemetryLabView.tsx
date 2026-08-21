import React, { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { ALL_GRID_DRIVERS } from '../data/mockF1Data';
import { fetchScheduleFromBackend, fetchStandingsFromBackend, fetchTelemetryFromBackend } from '../api/f1Api';
import { Gauge, Zap, Disc, Search, X, Shield, Plus, Check } from 'lucide-react';

interface TelemetryLabViewProps {
  selectedSeason: number;
  selectedRound: number;
  setSelectedRound: (round: number) => void;
}

const CONTRAST_PALETTE = ['#3671C6', '#FF8000', '#E8002D', '#27F4D2', '#A855F7', '#EAB308', '#22C55E', '#EC4899'];

export const TelemetryLabView: React.FC<TelemetryLabViewProps> = ({
  selectedSeason,
  selectedRound,
  setSelectedRound,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [gridDrivers, setGridDrivers] = useState<any[]>(ALL_GRID_DRIVERS);
  const [selectedSession, setSelectedSession] = useState<string>('Q');
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>(['VER', 'NOR']);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [telemetryData, setTelemetryData] = useState<any[]>([]);
  const [driverInfoMap, setDriverInfoMap] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);

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
  }, [selectedRound, selectedSession, selectedSeason]);

  // Load schedule & standings for active season
  useEffect(() => {
    async function loadMetadata() {
      const [sched, standings] = await Promise.all([
        fetchScheduleFromBackend(selectedSeason),
        fetchStandingsFromBackend(selectedSeason),
      ]);

      if (sched && sched.length > 0) {
        const formatted = sched.map((evt: any, idx: number) => ({
          round: evt.RoundNumber || idx + 1,
          name: evt.EventName || `Round ${idx + 1}`
        }));
        setEvents(formatted);
      }

      if (standings && standings.length > 0) {
        const formattedDrv = standings.map((s: any) => ({
          code: s.Abbreviation || s.code,
          name: s.DriverName || s.name,
          team: s.TeamName || s.team,
          color: s.Color || s.color || '#3671C6',
        }));
        setGridDrivers(formattedDrv);
      } else {
        setGridDrivers(ALL_GRID_DRIVERS);
      }
    }
    loadMetadata();
  }, [selectedSeason]);

  // Fetch real distance-synchronized micro-telemetry from FastF1 backend
  useEffect(() => {
    async function loadTelemetry() {
      setIsLoading(true);
      const res = await fetchTelemetryFromBackend(selectedSeason, selectedRound, selectedSession, selectedDrivers);
      if (res && res.mergedData && res.mergedData.length > 0) {
        setTelemetryData(res.mergedData);
        setDriverInfoMap(res.driverInfo || {});
      } else {
        // Fallback smooth multi-driver telemetry generator
        const sampleDistances = Array.from({ length: 180 }, (_, i) => i * 30);
        const generated = sampleDistances.map((d) => {
          const row: any = { distance: d };
          selectedDrivers.forEach((code, idx) => {
            const shift = idx * 12;
            const spd = Math.round(180 + 110 * Math.sin((d + shift) / 380) + 30 * Math.cos((d * 2) / 600));
            const thr = spd > 220 ? 100 : Math.max(0, Math.round(100 * Math.sin((d + shift) / 250)));
            const brk = thr === 0 ? Math.min(100, Math.round(80 + 20 * Math.cos(d / 150))) : 0;
            const gear = spd < 120 ? 3 : spd < 170 ? 4 : spd < 220 ? 5 : spd < 270 ? 7 : 8;
            row[`speed_${code}`] = spd;
            row[`throttle_${code}`] = thr;
            row[`brake_${code}`] = brk;
            row[`gear_${code}`] = gear;
            row[`drs_${code}`] = spd > 280 ? 12 : 0;
          });
          return row;
        });
        setTelemetryData(generated);
      }
      setIsLoading(false);
    }
    loadTelemetry();
  }, [selectedSeason, selectedRound, selectedSession, selectedDrivers]);

  const addDriver = (code: string) => {
    if (!selectedDrivers.includes(code) && selectedDrivers.length < 5) {
      setSelectedDrivers((prev) => [...prev, code]);
    }
    setIsSearchOpen(false);
    setSearchQuery('');
  };

  const removeDriver = (code: string) => {
    if (selectedDrivers.length > 1) {
      setSelectedDrivers((prev) => prev.filter((c) => c !== code));
    }
  };

  const toggleDriver = (code: string) => {
    if (selectedDrivers.includes(code)) {
      removeDriver(code);
    } else {
      addDriver(code);
    }
  };

  const getDriverColor = (code: string, index: number) => {
    return driverInfoMap[code]?.color || gridDrivers.find((d) => d.code === code)?.color || CONTRAST_PALETTE[index % CONTRAST_PALETTE.length];
  };

  const availableToAdd = gridDrivers.filter(
    (d) =>
      !selectedDrivers.includes(d.code) &&
      (d.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.code?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.team?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div ref={containerRef} className="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 pt-28 pb-16 space-y-12">
      {/* Header & Controls */}
      <div className="gsap-fade flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-signal-blue)]">
            {selectedSeason} Season • Round {selectedRound} Distance Telemetry
          </span>
          <h1 className="font-editorial text-3xl sm:text-4xl lg:text-5xl text-[var(--color-graphite)] tracking-tight">
            Telemetry Lab: Multi-Driver Analysis
          </h1>
          <p className="text-xs sm:text-sm text-[var(--color-ash)] mt-1.5">
            Compare synchronized Speed, Throttle, Brake, and Gear traces over exact circuit distance.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {events.length > 0 && (
            <div className="flex items-center gap-1.5 bg-[var(--color-paper)] px-3 py-1.5 rounded-xl border border-[var(--color-mist)] text-xs">
              <span className="text-[var(--color-ash)] font-medium">Event:</span>
              <select
                value={selectedRound}
                onChange={(e) => setSelectedRound(Number(e.target.value))}
                className="bg-transparent font-semibold text-[var(--color-graphite)] focus:outline-none cursor-pointer"
              >
                {events.map((evt) => (
                  <option key={evt.round} value={evt.round}>
                    R{evt.round}: {evt.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center gap-1 bg-[var(--color-paper)] p-1 rounded-xl border border-[var(--color-mist)]">
            {[
              { id: 'Q', label: 'Qualifying' },
              { id: 'R', label: 'Race' },
              { id: 'FP3', label: 'FP3' },
              { id: 'FP2', label: 'FP2' },
              { id: 'FP1', label: 'FP1' },
            ].map((s) => (
              <button
                key={s.id}
                onClick={() => setSelectedSession(s.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  selectedSession === s.id
                    ? 'bg-[var(--color-twilight)] text-white'
                    : 'text-[var(--color-charcoal)] hover:bg-[var(--color-linen)]'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Driver Chip Manager & Quick Pick Bar */}
      <div className="gsap-fade card-mist p-5 mb-8 space-y-4">
        {/* Active Traces Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[var(--color-mist)]">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold text-[var(--color-graphite)] mr-1 flex items-center gap-2">
              Active Traces ({selectedDrivers.length}/5)
              {isLoading && <span className="text-[10px] text-[var(--color-signal-blue)] font-normal animate-pulse">Loading telemetry...</span>}
            </span>
            {selectedDrivers.map((code, idx) => {
              const drv = gridDrivers.find((d) => d.code === code);
              const info = driverInfoMap[code] || {};
              const color = getDriverColor(code, idx);
              const lapTimeStr = info.lapTime ? ` (${info.lapTime})` : '';

              return (
                <div
                  key={code}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-twilight)] text-white text-xs font-semibold shadow-sm"
                >
                  <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: color }} />
                  <span>
                    {drv?.name || code} ({code}){lapTimeStr}
                  </span>
                  {selectedDrivers.length > 1 && (
                    <button
                      onClick={() => removeDriver(code)}
                      className="hover:text-rose-400 ml-1 p-0.5 rounded transition-colors"
                      title={`Remove ${code}`}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Search & Add Driver Bar */}
          <div className="relative w-full sm:w-72">
            <div className="flex items-center gap-2 bg-[var(--color-linen)] px-3 py-1.5 rounded-lg border border-[var(--color-mist)]">
              <Search className="w-3.5 h-3.5 text-[var(--color-ash)] shrink-0" />
              <input
                type="text"
                placeholder="Search to add driver (e.g. HAM, ALO)..."
                value={searchQuery}
                onFocus={() => setIsSearchOpen(true)}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchOpen(true);
                }}
                className="w-full text-xs bg-transparent text-[var(--color-graphite)] focus:outline-none placeholder-[var(--color-ash)]"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="text-[var(--color-ash)] hover:text-[var(--color-graphite)]">
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Search Dropdown Popup */}
            {isSearchOpen && (
              <div
                className="absolute left-0 right-0 top-11 bg-white border border-[var(--color-mist)] rounded-xl shadow-2xl z-50 max-h-64 overflow-y-auto no-scrollbar p-1.5"
                onMouseDown={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between p-2 border-b border-[var(--color-linen)] text-[10px] uppercase text-[var(--color-ash)] font-bold">
                  <span>Select Grid Driver</span>
                  <button onClick={() => setIsSearchOpen(false)} className="hover:text-[var(--color-graphite)] p-1">
                    <X className="w-3 h-3" />
                  </button>
                </div>

                {availableToAdd.length === 0 ? (
                  <div className="p-3 text-xs text-center text-[var(--color-ash)]">No matching drivers to add</div>
                ) : (
                  availableToAdd.map((drv) => (
                    <div
                      key={drv.code}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        addDriver(drv.code);
                      }}
                      className="flex items-center justify-between p-2.5 rounded-lg hover:bg-[var(--color-linen)] cursor-pointer text-xs transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: drv.color || '#3671C6' }} />
                        <span className="font-bold text-[var(--color-graphite)]">{drv.code}</span>
                        <span className="text-[var(--color-ash)] text-[11px]">{drv.name}</span>
                      </div>
                      <span className="text-[10px] text-[var(--color-ash)]">{drv.team}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Quick Driver Toggle Pills */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] text-[var(--color-ash)] mr-1">Quick Select:</span>
          {gridDrivers.slice(0, 10).map((drv) => {
            const isSelected = selectedDrivers.includes(drv.code);
            return (
              <button
                key={drv.code}
                onClick={() => toggleDriver(drv.code)}
                className={`px-2.5 py-1 text-xs rounded-lg border transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-slate-900 border-slate-900 text-white font-bold'
                    : 'bg-white border-[var(--color-mist)] text-[var(--color-charcoal)] hover:bg-[var(--color-linen)]'
                }`}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: drv.color || '#3671C6' }} />
                <span>{drv.code}</span>
                {isSelected ? <Check className="w-3 h-3 text-emerald-400" /> : <Plus className="w-3 h-3 text-[var(--color-ash)]" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Synchronized Traces Stack */}
      <div className="space-y-6">
        {/* 1. Speed Trace */}
        <div className="gsap-fade card-mist p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-editorial text-lg text-[var(--color-graphite)] flex items-center gap-2">
              <Gauge className="w-4 h-4 text-sky-500" />
              1. Speed Profile (km/h)
            </h3>
            <span className="text-xs text-[var(--color-ash)] font-mono">FastF1 Distance Axis</span>
          </div>

          <div className="h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="distance" stroke="#888" fontSize={10} tickFormatter={(v) => `${v}m`} />
                <YAxis stroke="#888" fontSize={10} domain={['auto', 'auto']} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', borderColor: '#dee2de', borderRadius: '8px', fontSize: '11px' }}
                  formatter={(value: any, name: any) => [`${value} km/h`, name]}
                />
                <Legend />
                {selectedDrivers.map((code, idx) => {
                  const color = getDriverColor(code, idx);
                  return (
                    <Line
                      key={code}
                      type="monotone"
                      dataKey={`speed_${code}`}
                      stroke={color}
                      strokeWidth={2.5}
                      dot={false}
                      name={`${code} Speed`}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 2. Throttle Input Trace */}
        <div className="gsap-fade card-mist p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-editorial text-lg text-[var(--color-graphite)] flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-500" />
              2. Throttle Input (%)
            </h3>
            <span className="text-xs text-[var(--color-ash)] font-mono">0% - 100% Throttle</span>
          </div>

          <div className="h-[170px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="distance" stroke="#888" fontSize={10} tickFormatter={(v) => `${v}m`} />
                <YAxis stroke="#888" fontSize={10} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', borderColor: '#dee2de', borderRadius: '8px', fontSize: '11px' }}
                  formatter={(value: any, name: any) => [`${value}%`, name]}
                />
                <Legend />
                {selectedDrivers.map((code, idx) => {
                  const color = getDriverColor(code, idx);
                  return (
                    <Line
                      key={code}
                      type="stepAfter"
                      dataKey={`throttle_${code}`}
                      stroke={color}
                      strokeWidth={2}
                      dot={false}
                      name={`${code} Throttle`}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 3. Brake Application Trace */}
        <div className="gsap-fade card-mist p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-editorial text-lg text-[var(--color-graphite)] flex items-center gap-2">
              <Disc className="w-4 h-4 text-rose-500" />
              3. Brake Application (%)
            </h3>
            <span className="text-xs text-[var(--color-ash)] font-mono">Braking Zones & Apex Deceleration</span>
          </div>

          <div className="h-[170px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="distance" stroke="#888" fontSize={10} tickFormatter={(v) => `${v}m`} />
                <YAxis stroke="#888" fontSize={10} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', borderColor: '#dee2de', borderRadius: '8px', fontSize: '11px' }}
                  formatter={(value: any, name: any) => [`${value}%`, name]}
                />
                <Legend />
                {selectedDrivers.map((code, idx) => {
                  const color = getDriverColor(code, idx);
                  return (
                    <Line
                      key={code}
                      type="monotone"
                      dataKey={`brake_${code}`}
                      stroke={color}
                      strokeWidth={2}
                      dot={false}
                      name={`${code} Brake`}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 4. Gear Selection Trace */}
        <div className="gsap-fade card-mist p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-editorial text-lg text-[var(--color-graphite)] flex items-center gap-2">
              <Shield className="w-4 h-4 text-purple-500" />
              4. Gear Selection (nGear 1-8)
            </h3>
            <span className="text-xs text-[var(--color-ash)] font-mono">8-Speed Sequential Gearbox</span>
          </div>

          <div className="h-[160px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="distance" stroke="#888" fontSize={10} tickFormatter={(v) => `${v}m`} />
                <YAxis stroke="#888" fontSize={10} domain={[1, 8]} ticks={[1, 2, 3, 4, 5, 6, 7, 8]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', borderColor: '#dee2de', borderRadius: '8px', fontSize: '11px' }}
                  formatter={(value: any, name: any) => [`Gear ${value}`, name]}
                />
                <Legend />
                {selectedDrivers.map((code, idx) => {
                  const color = getDriverColor(code, idx);
                  return (
                    <Line
                      key={code}
                      type="stepAfter"
                      dataKey={`gear_${code}`}
                      stroke={color}
                      strokeWidth={2}
                      dot={false}
                      name={`${code} Gear`}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
