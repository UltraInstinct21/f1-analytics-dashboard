import React, { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Navigation, type TabType } from './components/Navigation';
import { Footer } from './components/Footer';
import { ControlRoomView } from './views/ControlRoomView';
import { SeasonOverviewView } from './views/SeasonOverviewView';
import { WeekendOverviewView } from './views/WeekendOverviewView';
import { SessionAnalysisView } from './views/SessionAnalysisView';
import { TelemetryLabView } from './views/TelemetryLabView';
import { DriverComparisonView } from './views/DriverComparisonView';
import { RaceReplayView } from './views/RaceReplayView';
import { RacePredictionsView } from './views/RacePredictionsView';
import { fetchSeasonsFromBackend } from './api/f1Api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('control-room');
  const [selectedSeason, setSelectedSeason] = useState<number>(2025);
  const [selectedRound, setSelectedRound] = useState<number>(1);
  const [seasons, setSeasons] = useState<number[]>([2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]);
  const mainContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadSeasons() {
      const availSeasons = await fetchSeasonsFromBackend();
      if (availSeasons && availSeasons.length > 0) {
        setSeasons(availSeasons);
      }
    }
    loadSeasons();
  }, []);

  // GSAP Tab Switch Fade Transition
  useEffect(() => {
    if (!mainContentRef.current) return;
    gsap.fromTo(
      mainContentRef.current,
      { opacity: 0, y: 12 },
      { opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' }
    );
  }, [activeTab, selectedSeason]);

  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-parchment)] text-[var(--color-charcoal)] selection:bg-[var(--color-signal-blue)] selection:text-white">
      {/* Top Floating Glass Navigation Pill with Season Selector */}
      <Navigation
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedSeason={selectedSeason}
        setSelectedSeason={setSelectedSeason}
        seasons={seasons}
      />

      {/* Main Tab Content Container */}
      <main ref={mainContentRef} className="flex-1">
        {activeTab === 'control-room' && (
          <ControlRoomView
            setActiveTab={setActiveTab}
            selectedSeason={selectedSeason}
            setSelectedSeason={setSelectedSeason}
          />
        )}
        {activeTab === 'season' && (
          <SeasonOverviewView
            selectedSeason={selectedSeason}
            setSelectedSeason={setSelectedSeason}
            setSelectedRound={setSelectedRound}
            setActiveTab={setActiveTab}
          />
        )}
        {activeTab === 'weekend' && (
          <WeekendOverviewView
            selectedSeason={selectedSeason}
            selectedRound={selectedRound}
            setSelectedRound={setSelectedRound}
          />
        )}
        {activeTab === 'session' && (
          <SessionAnalysisView
            selectedSeason={selectedSeason}
            selectedRound={selectedRound}
            setSelectedRound={setSelectedRound}
          />
        )}
        {activeTab === 'telemetry' && (
          <TelemetryLabView
            selectedSeason={selectedSeason}
            selectedRound={selectedRound}
            setSelectedRound={setSelectedRound}
          />
        )}
        {activeTab === 'comparison' && (
          <DriverComparisonView
            selectedSeason={selectedSeason}
            selectedRound={selectedRound}
            setSelectedRound={setSelectedRound}
          />
        )}
        {activeTab === 'replay' && (
          <RaceReplayView
            selectedSeason={selectedSeason}
            selectedRound={selectedRound}
            setSelectedRound={setSelectedRound}
          />
        )}
        {activeTab === 'predictions' && (
          <RacePredictionsView
            selectedSeason={selectedSeason}
          />
        )}
      </main>

      {/* Literary Journal Footer */}
      <Footer />
    </div>
  );
};

export default App;
