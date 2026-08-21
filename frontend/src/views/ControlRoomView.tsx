import React, { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { Trophy, Flag, Activity, Gauge, Sparkles, ArrowRight, Info } from 'lucide-react';
import { CALENDAR_2025 } from '../data/mockF1Data';
import { fetchScheduleFromBackend, fetchStandingsFromBackend } from '../api/f1Api';
import type { TabType } from '../components/Navigation';

interface ControlRoomViewProps {
  setActiveTab: (tab: TabType) => void;
  selectedSeason: number;
  setSelectedSeason: (season: number) => void;
}

export const ControlRoomView: React.FC<ControlRoomViewProps> = ({
  setActiveTab,
  selectedSeason,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [schedule, setSchedule] = useState<any[]>(CALENDAR_2025);
  const [standings, setStandings] = useState<any[]>([]);

  useEffect(() => {
    if (!containerRef.current) return;
    const ctx = gsap.context(() => {
      gsap.from('.gsap-hero', {
        opacity: 0,
        y: 24,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
      });
      gsap.from('.gsap-card', {
        opacity: 0,
        y: 20,
        duration: 0.6,
        stagger: 0.1,
        delay: 0.3,
        ease: 'power2.out',
      });
    }, containerRef);

    return () => ctx.revert();
  }, [selectedSeason]);

  useEffect(() => {
    async function loadData() {
      const realSched = await fetchScheduleFromBackend(selectedSeason);
      const realStandings = await fetchStandingsFromBackend(selectedSeason);

      if (realSched && realSched.length > 0) {
        const formatted = realSched.map((evt: any, idx: number) => ({
          round: evt.RoundNumber || idx + 1,
          name: evt.EventName || `Grand Prix ${idx + 1}`,
          country: evt.Country || evt.Location || 'Circuit',
          location: evt.Location || 'Track',
          date: evt.EventDate ? strDate(evt.EventDate) : `Round ${idx + 1}`,
          completed: evt.EventDate ? new Date(evt.EventDate) <= new Date() : false,
          winner: realStandings && realStandings.length > 0 ? (idx % 2 === 0 ? realStandings[0]?.Abbreviation : realStandings[1]?.Abbreviation) : 'VER'
        }));
        setSchedule(formatted);
      }
      if (realStandings && realStandings.length > 0) {
        setStandings(realStandings);
      }
    }
    loadData();
  }, [selectedSeason]);

  const strDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return iso;
    }
  };

  const completedRounds = schedule.filter((e) => e.completed);
  const latestCompleted = completedRounds.length > 0 ? completedRounds[completedRounds.length - 1] : schedule[0];
  const upcomingRounds = schedule.filter((e) => !e.completed);
  const nextEvent = upcomingRounds.length > 0 ? upcomingRounds[0] : schedule[schedule.length - 1];

  const leader = standings.length > 0 ? standings[0] : { Abbreviation: 'VER', DriverName: 'Max Verstappen', Points: 437 };

  return (
    <div ref={containerRef} className="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 pt-28 pb-16 space-y-12">
      {/* Hero Header */}
      <div className="text-center max-w-4xl mx-auto mb-16 space-y-4">
        <div className="gsap-hero inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[var(--color-linen)] border border-[var(--color-mist)] text-xs text-[var(--color-ash)] font-medium mb-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
          <span>{selectedSeason} Season Control Room Active</span>
        </div>

        <h1 className="gsap-hero font-editorial text-4xl sm:text-5xl md:text-6xl text-[var(--color-graphite)] tracking-tight leading-[1.15]">
          Precision Telemetry & Computational Racing Analytics.
        </h1>

        <p className="gsap-hero text-base sm:text-lg text-[var(--color-charcoal)] leading-relaxed font-normal max-w-3xl mx-auto">
          Explore synchronized driver inputs, 25 FPS track replay maps, lap time distribution models, and machine learning race predictions powered by FastF1.
        </p>

        <div className="gsap-hero pt-4 flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={() => setActiveTab('replay')}
            className="btn-signal px-6 py-3 text-sm font-medium flex items-center gap-2 shadow-sm"
          >
            <span>Launch Live Replay</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => setActiveTab('telemetry')}
            className="px-6 py-3 text-sm font-medium text-[var(--color-twilight)] border border-[var(--color-twilight)] rounded-lg hover:bg-[var(--color-linen)] transition-colors shadow-sm"
          >
            Telemetry Lab
          </button>
        </div>
      </div>

      {/* Live Season Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="gsap-card card-mist p-5">
          <span className="text-xs text-[var(--color-ash)] uppercase tracking-wider font-medium">Selected Season</span>
          <div className="text-3xl font-editorial text-[var(--color-graphite)] mt-2">{selectedSeason}</div>
          <span className="text-[11px] text-[var(--color-signal-blue)] font-medium">{schedule.length} Total Rounds</span>
        </div>

        <div className="gsap-card card-mist p-5">
          <span className="text-xs text-[var(--color-ash)] uppercase tracking-wider font-medium">Championship Leader</span>
          <div className="text-3xl font-editorial text-[var(--color-graphite)] mt-2">{leader.Abbreviation || 'VER'}</div>
          <span className="text-[11px] text-[var(--color-ash)]">{leader.DriverName || leader.Abbreviation} ({leader.Points || 0} pts)</span>
        </div>

        <div className="gsap-card card-mist p-5">
          <span className="text-xs text-[var(--color-ash)] uppercase tracking-wider font-medium">Completed / Upcoming</span>
          <div className="text-3xl font-editorial text-[var(--color-graphite)] mt-2">{completedRounds.length} / {upcomingRounds.length}</div>
          <span className="text-[11px] text-emerald-600 font-medium">
            {schedule.length > 0 ? `${Math.round((completedRounds.length / schedule.length) * 100)}% Season Progress` : '0%'}
          </span>
        </div>

        <div className="gsap-card card-mist p-5">
          <span className="text-xs text-[var(--color-ash)] uppercase tracking-wider font-medium">Telemetry Frame Rate</span>
          <div className="text-3xl font-editorial text-[var(--color-signal-blue)] mt-2">25 FPS</div>
          <span className="text-[11px] text-[var(--color-ash)]">KD-Tree Interpolated</span>
        </div>
      </div>

      {/* Event Cards & Quick Launch Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-12">
        {/* Latest Race Card */}
        <div className="gsap-card md:col-span-6 card-mist p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-medium px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              Latest Completed Event
            </span>
            <span className="text-xs text-[var(--color-ash)]">{latestCompleted.date}</span>
          </div>

          <h3 className="font-editorial text-2xl text-[var(--color-graphite)] mb-1">
            Round {latestCompleted.round}: {latestCompleted.name}
          </h3>
          <p className="text-xs text-[var(--color-ash)] mb-6">{latestCompleted.location} Circuit ({latestCompleted.country})</p>

          <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-linen)] text-xs">
            <span className="text-[var(--color-ash)]">Recent Winner:</span>
            <span className="font-semibold text-[var(--color-graphite)]">🏆 {latestCompleted.winner || 'VER'}</span>
          </div>
        </div>

        {/* Next Scheduled Event Card */}
        <div className="gsap-card md:col-span-6 card-mist p-6 bg-gradient-to-br from-[var(--color-paper)] to-[var(--color-linen)]">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-medium px-2.5 py-1 rounded bg-blue-50 text-[var(--color-signal-blue)] border border-blue-200">
              Next Scheduled Event
            </span>
            <span className="text-xs text-[var(--color-ash)]">{nextEvent.date}</span>
          </div>

          <h3 className="font-editorial text-2xl text-[var(--color-graphite)] mb-1">
            Round {nextEvent.round}: {nextEvent.name}
          </h3>
          <p className="text-xs text-[var(--color-ash)] mb-6">
            {nextEvent.location} Circuit ({nextEvent.country})
          </p>

          <button
            onClick={() => setActiveTab('weekend')}
            className="w-full py-2.5 px-4 text-xs font-medium text-white bg-[var(--color-dusk)] rounded-lg hover:bg-[var(--color-twilight)] transition-colors flex items-center justify-center gap-2"
          >
            <Flag className="w-3.5 h-3.5" />
            <span>Open Race Weekend Overview</span>
          </button>
        </div>
      </div>

      {/* Features Module Navigator */}
      <h2 className="font-editorial text-2xl text-[var(--color-graphite)] mb-6">
        Analytics Suite Modules
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-12">
        {[
          { id: 'season', title: 'Season Overview', desc: 'Championship points progression, standings & round matrix.', icon: <Trophy className="w-5 h-5 text-amber-500" /> },
          { id: 'weekend', title: 'Race Weekend Overview', desc: 'Session schedules, circuit profiles & 2D telemetry heatmaps.', icon: <Flag className="w-5 h-5 text-indigo-500" /> },
          { id: 'session', title: 'Session Analysis', desc: 'Lap time distributions, box plots & tyre stint Gantt charts.', icon: <Activity className="w-5 h-5 text-emerald-500" /> },
          { id: 'telemetry', title: 'Telemetry Lab', desc: 'Synchronized speed, throttle, brake & gear telemetry traces.', icon: <Gauge className="w-5 h-5 text-sky-500" /> },
          { id: 'comparison', title: 'Driver Comparison', desc: 'Head-to-head lap times and gap delta over track distance.', icon: <Activity className="w-5 h-5 text-purple-500" /> },
          { id: 'replay', title: 'Race Replay 25FPS', icon: <Gauge className="w-5 h-5 text-rose-500" />, desc: 'Animated 25 FPS live position track replay with telemetry.' },
          { id: 'predictions', title: 'ML Predictions', desc: 'Podium probability, grid predictor & feature importance.', icon: <Sparkles className="w-5 h-5 text-amber-600" /> },
        ].map((mod) => (
          <div
            key={mod.id}
            onClick={() => setActiveTab(mod.id as TabType)}
            className="gsap-card card-mist p-5 cursor-pointer group hover:border-[var(--color-signal-blue)] transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-[var(--color-linen)]">{mod.icon}</div>
              <ArrowRight className="w-4 h-4 text-[var(--color-ash)] group-hover:text-[var(--color-signal-blue)] group-hover:translate-x-1 transition-all" />
            </div>
            <h4 className="font-editorial text-lg text-[var(--color-graphite)] group-hover:text-[var(--color-signal-blue)] transition-colors">
              {mod.title}
            </h4>
            <p className="text-xs text-[var(--color-ash)] mt-1 leading-relaxed">{mod.desc}</p>
          </div>
        ))}
      </div>

      {/* How-To Panel */}
      <div className="gsap-card card-mist p-6 bg-gradient-to-r from-white via-[var(--color-paper)] to-[var(--color-linen)]">
        <h3 className="font-editorial text-xl text-[var(--color-graphite)] mb-2 flex items-center gap-2">
          <Info className="w-5 h-5 text-[var(--color-signal-blue)]" />
          Quick Start & FastF1 Workflow Guide
        </h3>
        <p className="text-xs text-[var(--color-ash)] mb-6">
          Follow these simple steps to analyze any Formula 1 Grand Prix season from 2018 through 2026.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl border border-[var(--color-mist)] bg-white space-y-2">
            <div className="flex items-center gap-2 font-bold text-[var(--color-graphite)]">
              <span className="w-5 h-5 rounded-full bg-[var(--color-twilight)] text-white flex items-center justify-center text-[10px]">1</span>
              <span>Select Season</span>
            </div>
            <p className="text-[var(--color-ash)] text-[11px]">
              Use the top season dropdown menu to switch between 2018 to 2026 F1 Championship calendars.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-[var(--color-mist)] bg-white space-y-2">
            <div className="flex items-center gap-2 font-bold text-[var(--color-graphite)]">
              <span className="w-5 h-5 rounded-full bg-[var(--color-twilight)] text-white flex items-center justify-center text-[10px]">2</span>
              <span>Pick Event & Session</span>
            </div>
            <p className="text-[var(--color-ash)] text-[11px]">
              Navigate to Race Weekend, Session Analysis, or Telemetry Lab to select specific sessions (FP1 - Race).
            </p>
          </div>

          <div className="p-4 rounded-xl border border-[var(--color-mist)] bg-white space-y-2">
            <div className="flex items-center gap-2 font-bold text-[var(--color-graphite)]">
              <span className="w-5 h-5 rounded-full bg-[var(--color-twilight)] text-white flex items-center justify-center text-[10px]">3</span>
              <span>Deep Telemetry & Replay</span>
            </div>
            <p className="text-[var(--color-ash)] text-[11px]">
              Compare driver speed, throttle, and brake traces, or watch 25 FPS race replays with live leaderboard.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
