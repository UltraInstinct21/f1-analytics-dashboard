import React, { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { Play, Pause, RotateCcw, ShieldAlert, Activity } from 'lucide-react';
import { DRIVER_STANDINGS_2025 } from '../data/mockF1Data';
import { MONZA_CIRCUIT, getInterpolatedTrackPoint } from '../data/circuitCoordinates';
import { fetchScheduleFromBackend, fetchReplayFromBackend, fetchWeekendOverviewFromBackend } from '../api/f1Api';

interface RaceReplayViewProps {
  selectedSeason: number;
  selectedRound: number;
  setSelectedRound: (round: number) => void;
}

export const RaceReplayView: React.FC<RaceReplayViewProps> = ({
  selectedSeason,
  selectedRound,
  setSelectedRound,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(120); // 0 to 1000 frames
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [safetyCarActive] = useState(false);
  const [replayData, setReplayData] = useState<any>(null);
  const [trackGeometry, setTrackGeometry] = useState<any>(null);

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

  // Load schedule events
  useEffect(() => {
    async function loadSchedule() {
      const sched = await fetchScheduleFromBackend(selectedSeason);
      if (sched && sched.length > 0) {
        const formatted = sched.map((evt: any, idx: number) => ({
          round: evt.RoundNumber || idx + 1,
          name: evt.EventName || `Round ${idx + 1}`,
          location: evt.Location || 'Circuit'
        }));
        setEvents(formatted);
      }
    }
    loadSchedule();
  }, [selectedSeason]);

  // Fetch track layout & replay telemetry frames from FastF1 backend
  useEffect(() => {
    async function loadReplay() {
      const wData = await fetchWeekendOverviewFromBackend(selectedSeason, selectedRound);
      if (wData && wData.trackGeometry) {
        setTrackGeometry(wData.trackGeometry);
      } else {
        setTrackGeometry(null);
      }

      const rep = await fetchReplayFromBackend(selectedSeason, selectedRound, 'R');
      if (rep && rep.frames && rep.frames.length > 0) {
        setReplayData(rep);
      } else {
        setReplayData(null);
      }
    }
    loadReplay();
  }, [selectedSeason, selectedRound]);

  // Animation Loop for Replay Simulation
  useEffect(() => {
    let timer: any;
    if (isPlaying) {
      const totalF = replayData?.total_frames || 600;
      timer = setInterval(() => {
        setCurrentFrame((prev) => {
          if (prev >= totalF - 1) return 0;
          return prev + 1;
        });
      }, 50 / playbackSpeed);
    }
    return () => clearInterval(timer);
  }, [isPlaying, playbackSpeed, replayData]);

  const currentEvent = events.find((e) => e.round === selectedRound) || events[0] || { round: selectedRound, name: 'Grand Prix', location: 'Circuit' };
  const totalLaps = replayData?.totalLaps || 57;
  const maxFrames = (replayData?.total_frames || 1000) - 1;

  const trackPath = trackGeometry?.pathD || replayData?.trackGeometry?.pathD || MONZA_CIRCUIT.pathD;
  const trackBox = trackGeometry?.viewBox || replayData?.trackGeometry?.viewBox || MONZA_CIRCUIT.viewBox;
  const trackStart = trackGeometry?.startLine || replayData?.trackGeometry?.startLine || MONZA_CIRCUIT.startLine;
  const trackPoints = trackGeometry?.points || replayData?.trackGeometry?.points || MONZA_CIRCUIT.points;

  // Extract current frame data from backend replay
  const currentBackendFrame = replayData?.frames?.[currentFrame];
  const isSC = currentBackendFrame ? currentBackendFrame.safetyCar : safetyCarActive;
  const isVSC = currentBackendFrame ? currentBackendFrame.vsc : false;
  const currentLap = currentBackendFrame ? currentBackendFrame.lap : Math.min(totalLaps, Math.floor((currentFrame / (maxFrames || 1)) * totalLaps) + 1);
  const raceTimeSeconds = currentBackendFrame ? currentBackendFrame.time : (currentFrame * 5.6).toFixed(1);
  const statusLabel = currentBackendFrame ? currentBackendFrame.statusText : (isSC ? 'SAFETY CAR DEPLOYED' : 'GREEN TRACK STATUS');

  const elapsedMins = Math.floor(Number(raceTimeSeconds) / 60);
  const elapsedSecs = Math.floor(Number(raceTimeSeconds) % 60);
  const timeFormatted = `${elapsedMins}m ${elapsedSecs < 10 ? '0' : ''}${elapsedSecs}s`;

  // Dynamic drivers on track
  let driversOnTrack: any[] = [];
  if (currentBackendFrame && currentBackendFrame.drivers) {
    driversOnTrack = Object.values(currentBackendFrame.drivers);
  } else {
    // Smooth fallback if loading
    driversOnTrack = DRIVER_STANDINGS_2025.slice(0, 8).map((drv, idx) => {
      const driverProgress = (((currentFrame * 0.002) + (10 - idx) * 0.02) % 1.0 + 1.0) % 1.0;
      const pos = getInterpolatedTrackPoint(trackPoints, driverProgress);
      return {
        code: drv.code,
        name: drv.name,
        color: drv.color,
        x: pos.x,
        y: pos.y,
        speed: Math.round(isSC ? 140 : 290 - idx * 5 + Math.sin(currentFrame / 10) * 20),
        lap: currentLap,
        tyre: 'MEDIUM',
        gap: idx === 0 ? 'Leader' : `+${(idx * 1.45).toFixed(1)}s`,
      };
    });
  }

  // Dynamic Leaderboard
  const liveLeaderboard = (currentBackendFrame && currentBackendFrame.leaderboard && currentBackendFrame.leaderboard.length > 0)
    ? currentBackendFrame.leaderboard
    : driversOnTrack.slice(0, 10);

  // Safety Car Position (ahead of leader)
  const leaderDrv = driversOnTrack[0];
  const scPos = leaderDrv ? { x: leaderDrv.x + 8, y: leaderDrv.y - 8 } : { x: 400, y: 250 };

  return (
    <div ref={containerRef} className="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 pt-28 pb-16 space-y-12">
      {/* Replay Control Bar Header */}
      <div className="gsap-fade flex flex-col md:flex-row md:items-center justify-between gap-6 mb-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-signal-blue)]">
            {selectedSeason} Season • Dynamic FastF1 Telemetry Engine
          </span>
          <h1 className="font-editorial text-3xl sm:text-4xl lg:text-5xl text-[var(--color-graphite)] tracking-tight">
            Round {selectedRound}: {currentEvent.name} Race Replay
          </h1>
          <p className="text-xs sm:text-sm text-[var(--color-ash)] mt-1.5">
            Synchronized 2D Telemetry Contour • Real Lap Progression ({totalLaps} Laps) & Dynamic Leaderboard
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 shrink-0">
          {events.length > 0 && (
            <div className="flex items-center gap-1.5 bg-[var(--color-paper)] px-3.5 py-2 rounded-xl border border-[var(--color-mist)] text-xs shadow-sm">
              <span className="text-[var(--color-ash)] font-medium">Event:</span>
              <select
                value={selectedRound}
                onChange={(e) => {
                  setSelectedRound(Number(e.target.value));
                  setCurrentFrame(0);
                }}
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

          <div
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-2 transition-all ${
              isSC
                ? 'bg-amber-50 border-amber-300 text-amber-800 animate-pulse'
                : isVSC
                ? 'bg-amber-50 border-amber-300 text-amber-800'
                : 'bg-emerald-50 border-emerald-300 text-emerald-800'
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            <span>{statusLabel}</span>
          </div>

          <div className="text-right text-xs font-mono font-bold text-[var(--color-graphite)] bg-[var(--color-paper)] px-3 py-1.5 rounded-lg border border-[var(--color-mist)]">
            Lap {currentLap} / {totalLaps} • {timeFormatted}
          </div>
        </div>
      </div>

      {/* Main Interactive Replay Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
        {/* Track Playback Canvas Card */}
        <div className="gsap-fade lg:col-span-8 card-mist p-6 sm:p-8 flex flex-col justify-between relative bg-gradient-to-b from-white to-[var(--color-linen)] overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-[var(--color-ash)] uppercase tracking-wider">
              {currentEvent.location} • Real 2D Telemetry Contour
            </span>
            <span className="text-xs text-[var(--color-ash)] font-mono">
              Frame {currentFrame} / {maxFrames}
            </span>
          </div>

          {/* Authentic 2D Canvas Track Map */}
          <div className="w-full h-[520px] my-3 relative flex items-center justify-center">
            <svg viewBox={trackBox} className="w-full h-full max-h-[380px]">
              {/* Outer Glow Track Path */}
              <path
                d={trackPath}
                fill="none"
                stroke="#dee2de"
                strokeWidth="16"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Main Authentic Circuit Contour */}
              <path
                d={trackPath}
                fill="none"
                stroke="#171717"
                strokeWidth="4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Start / Finish Line */}
              {trackStart && (
                <line
                  x1={trackStart.x1}
                  y1={trackStart.y1}
                  x2={trackStart.x2}
                  y2={trackStart.y2}
                  stroke="#41A1CF"
                  strokeWidth="4"
                />
              )}

              {/* Safety Car Marker (if active) */}
              {isSC && (
                <g transform={`translate(${scPos.x}, ${scPos.y})`}>
                  <circle r="12" fill="#F59E0B" opacity="0.4" className="animate-ping" />
                  <circle r="8" fill="#F59E0B" stroke="#ffffff" strokeWidth="2" />
                  <text x="12" y="4" fontSize="10" fontWeight="bold" fill="#B45309" className="font-mono">
                    SC
                  </text>
                </g>
              )}

              {/* Live Driver Position Dots along 2D Track Path */}
              {driversOnTrack.map((drv) => (
                <g key={drv.code} transform={`translate(${drv.x}, ${drv.y})`}>
                  <circle r="7" fill={drv.color || '#3671C6'} stroke="#ffffff" strokeWidth="2" />
                  <text
                    x="10"
                    y="4"
                    fontSize="10"
                    fontWeight="bold"
                    fill="#171717"
                    className="drop-shadow-sm font-mono"
                  >
                    {drv.code} ({Math.round(drv.speed)} km/h)
                  </text>
                </g>
              ))}
            </svg>
          </div>

          {/* Timeline Scrubber & Controls */}
          <div className="space-y-3 pt-4 border-t border-[var(--color-mist)]">
            <input
              type="range"
              min="0"
              max={maxFrames}
              value={currentFrame}
              onChange={(e) => setCurrentFrame(Number(e.target.value))}
              className="w-full h-1.5 bg-[var(--color-linen)] rounded-lg appearance-none cursor-pointer accent-[var(--color-signal-blue)]"
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-2.5 rounded-lg bg-[var(--color-twilight)] text-white hover:bg-black transition-colors"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                </button>
                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentFrame(0);
                  }}
                  className="p-2.5 rounded-lg bg-white border border-[var(--color-mist)] text-[var(--color-charcoal)] hover:bg-[var(--color-linen)] transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>

              {/* Speed Buttons */}
              <div className="flex items-center gap-1 bg-[var(--color-linen)] p-1 rounded-lg border border-[var(--color-mist)] text-xs">
                {[1, 2, 5, 10].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setPlaybackSpeed(spd)}
                    className={`px-2.5 py-1 rounded font-semibold transition-all ${
                      playbackSpeed === spd
                        ? 'bg-white text-[var(--color-twilight)] shadow-sm'
                        : 'text-[var(--color-ash)]'
                    }`}
                  >
                    {spd}x
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Live Race Leaderboard Panel */}
        <div className="gsap-fade lg:col-span-4 card-mist p-6">
          <h3 className="font-editorial text-xl text-[var(--color-graphite)] mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-[var(--color-signal-blue)]" />
            Live Race Leaderboard
          </h3>

          <div className="space-y-2 max-h-[460px] overflow-y-auto no-scrollbar pr-1">
            {liveLeaderboard.map((drv: any, idx: number) => (
              <div
                key={drv.code || idx}
                className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-linen)] hover:bg-white border border-transparent hover:border-[var(--color-mist)] transition-all text-xs"
              >
                <div className="flex items-center gap-2.5">
                  <span className="font-bold text-[var(--color-ash)] w-5 text-center">P{idx + 1}</span>
                  <span className="w-2 h-4 rounded-full" style={{ backgroundColor: drv.color || '#3671C6' }} />
                  <div>
                    <span className="font-semibold text-[var(--color-graphite)] block">{drv.name || drv.code}</span>
                    <span className="text-[10px] text-[var(--color-ash)]">
                      {Math.round(drv.speed || 0)} km/h • {drv.tyre || 'MED'}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="font-mono font-semibold text-[var(--color-graphite)] block">{drv.gap || (idx === 0 ? 'Leader' : `+${(idx * 1.5).toFixed(1)}s`)}</span>
                  <span className="text-[10px] text-[var(--color-ash)]">Lap {drv.lap || currentLap}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
