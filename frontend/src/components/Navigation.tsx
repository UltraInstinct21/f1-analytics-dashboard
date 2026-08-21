import React from 'react';
import { Compass, Trophy, Flag, Activity, Gauge, GitCompare, PlayCircle, Sparkles, Calendar } from 'lucide-react';

export type TabType = 
  | 'control-room'
  | 'season'
  | 'weekend'
  | 'session'
  | 'telemetry'
  | 'comparison'
  | 'replay'
  | 'predictions';

interface NavigationProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  selectedSeason: number;
  setSelectedSeason: (season: number) => void;
  seasons: number[];
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  setActiveTab,
  selectedSeason,
  setSelectedSeason,
  seasons,
}) => {
  const navItems: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'control-room', label: 'Control Room', icon: <Compass className="w-4 h-4" /> },
    { id: 'season', label: 'Season', icon: <Trophy className="w-4 h-4" /> },
    { id: 'weekend', label: 'Race Weekend', icon: <Flag className="w-4 h-4" /> },
    { id: 'session', label: 'Session', icon: <Activity className="w-4 h-4" /> },
    { id: 'telemetry', label: 'Telemetry', icon: <Gauge className="w-4 h-4" /> },
    { id: 'comparison', label: 'Compare', icon: <GitCompare className="w-4 h-4" /> },
    { id: 'replay', label: 'Replay 25FPS', icon: <PlayCircle className="w-4 h-4" /> },
    { id: 'predictions', label: 'ML Predictions', icon: <Sparkles className="w-4 h-4" /> },
  ];

  return (
    <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-[1720px] w-[96%] px-4 sm:px-6 py-2.5 nav-pill shadow-lg transition-all duration-300">
      <div className="flex items-center justify-between gap-2 overflow-x-auto no-scrollbar">
        {/* Brand glyph */}
        <div className="flex items-center gap-2 px-2 py-1 font-editorial text-lg text-[var(--color-ink-black)] tracking-tight whitespace-nowrap">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[var(--color-signal-blue)] animate-pulse" />
          Kinetic Pulse
        </div>

        {/* Global Season Selector */}
        <div className="flex items-center gap-1.5 px-2 py-1 bg-[var(--color-paper)] rounded-full border border-[var(--color-mist)] text-xs shrink-0">
          <Calendar className="w-3.5 h-3.5 text-[var(--color-signal-blue)]" />
          <select
            value={selectedSeason}
            onChange={(e) => setSelectedSeason(Number(e.target.value))}
            className="bg-transparent font-bold text-[var(--color-graphite)] focus:outline-none cursor-pointer pr-1"
          >
            {seasons.map((yr) => (
              <option key={yr} value={yr}>
                {yr} Season
              </option>
            ))}
          </select>
        </div>

        {/* Tab Links */}
        <div className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full transition-all duration-200 whitespace-nowrap ${
                  isActive
                    ? 'bg-[var(--color-twilight)] text-white shadow-sm'
                    : 'text-[var(--color-charcoal)] hover:text-[var(--color-ink-black)] hover:bg-[var(--color-linen)]'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* CTA Button */}
        <div className="hidden xl:block pl-1">
          <button 
            onClick={() => setActiveTab('replay')}
            className="btn-signal px-3 py-1 text-xs font-medium flex items-center gap-1.5 whitespace-nowrap"
          >
            <span>Live Replay</span>
            <span className="text-[10px]">→</span>
          </button>
        </div>
      </div>
    </nav>
  );
};
