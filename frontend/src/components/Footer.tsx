import React from 'react';
import { Cpu, Zap, Activity, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-28 border-t border-[var(--color-mist)] bg-[var(--color-paper)] py-16 px-4 sm:px-6 lg:px-10 xl:px-12 text-[var(--color-charcoal)]">
      <div className="max-w-[1720px] w-full mx-auto grid grid-cols-1 md:grid-cols-12 gap-10 lg:gap-16 items-start">
        {/* Brand & Manifesto */}
        <div className="md:col-span-5 lg:col-span-5 space-y-4">
          <div className="flex items-center gap-2 font-editorial text-2xl text-[var(--color-ink-black)] tracking-tight">
            <span className="inline-block w-3 h-3 rounded-full bg-[var(--color-signal-blue)] animate-pulse" />
            Kinetic Pulse
          </div>
          <h2 className="font-editorial text-2xl sm:text-3xl lg:text-4xl text-[var(--color-graphite)] leading-snug tracking-tight">
            Formula 1 Telemetry, Generative Predictions & Spatial Analytics.
          </h2>
          <p className="text-sm text-[var(--color-ash)] max-w-xl leading-relaxed">
            Built with FastF1, Scikit-Learn Gradient Boosting, and fixed 25 FPS telemetry interpolation engines. Designed for precision motor racing insights.
          </p>
        </div>

        {/* Analytics Engine */}
        <div className="md:col-span-3 lg:col-span-2 space-y-3 text-xs font-medium">
          <div className="flex items-center gap-1.5 text-[var(--color-graphite)] font-bold uppercase tracking-wider text-[11px]">
            <Activity className="w-3.5 h-3.5 text-sky-500" />
            <span>Analytics Engine</span>
          </div>
          <ul className="space-y-2.5 text-[var(--color-ash)]">
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-sky-400" /> FastF1 PyPI Core
            </li>
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-sky-400" /> 25 FPS Replay Interpolation
            </li>
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-sky-400" /> Safety Car Distance KD-Tree
            </li>
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-sky-400" /> Ergast API Data Layer
            </li>
          </ul>
        </div>

        {/* ML Pipelines */}
        <div className="md:col-span-4 lg:col-span-2 space-y-3 text-xs font-medium">
          <div className="flex items-center gap-1.5 text-[var(--color-graphite)] font-bold uppercase tracking-wider text-[11px]">
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span>ML Pipelines</span>
          </div>
          <ul className="space-y-2.5 text-[var(--color-ash)]">
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-amber-400" /> Podium Probability Model
            </li>
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-amber-400" /> Grid Position Predictor
            </li>
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-amber-400" /> 2026 Season Projection
            </li>
            <li className="hover:text-[var(--color-signal-blue)] cursor-pointer transition-colors flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-amber-400" /> Feature Importance Suite
            </li>
          </ul>
        </div>

        {/* Architecture & Telemetry Specs */}
        <div className="md:col-span-12 lg:col-span-3 space-y-3 text-xs">
          <div className="flex items-center gap-1.5 text-[var(--color-graphite)] font-bold uppercase tracking-wider text-[11px]">
            <Cpu className="w-3.5 h-3.5 text-emerald-500" />
            <span>Architecture & Performance</span>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-linen)] border border-[var(--color-mist)] space-y-2 text-[11px] text-[var(--color-ash)]">
            <div className="flex justify-between items-center">
              <span>FastF1 Session Cache:</span>
              <span className="font-mono font-bold text-emerald-600">Active (v3.8)</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Telemetry Delta Axis:</span>
              <span className="font-mono font-bold text-[var(--color-graphite)]">25m Distance Grid</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Frame Replay Engine:</span>
              <span className="font-mono font-bold text-[var(--color-graphite)]">25 FPS Vectorized</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Horizontal Bar */}
      <div className="max-w-[1720px] w-full mx-auto mt-12 pt-6 border-t border-[var(--color-mist)] flex flex-col sm:flex-row justify-between items-center text-xs text-[var(--color-ash)] gap-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>© 2026 Kinetic Pulse • Literary F1 Intelligence</span>
        </div>
        <span className="font-mono text-[11px] bg-[var(--color-linen)] px-3 py-1 rounded-full border border-[var(--color-mist)] text-[var(--color-charcoal)]">
          Backend v1.0.0 • Decoupled React Engine
        </span>
      </div>
    </footer>
  );
};
