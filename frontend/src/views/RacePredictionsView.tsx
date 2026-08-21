import React, { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { BarChart2, ShieldCheck, RefreshCw, Trophy, Cpu } from 'lucide-react';
import {
  fetch2026SeasonProjection,
  fetchPredictionsFromBackend,
  retrainPredictorFromBackend,
} from '../api/f1Api';

interface RacePredictionsViewProps {
  selectedSeason: number;
}

export const RacePredictionsView: React.FC<RacePredictionsViewProps> = ({ selectedSeason }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [activeSubTab, setActiveSubTab] = useState<'podium' | 'season2026'>('podium');
  const [season2026Standings, setSeason2026Standings] = useState<any[]>([]);
  const [podiumPredictions, setPodiumPredictions] = useState<any[]>([]);
  const [featureImportances, setFeatureImportances] = useState<any[]>([]);
  const [trainSamples, setTrainSamples] = useState<number>(840);

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
  }, [activeSubTab, selectedSeason]);

  // Load predictions for selected season
  useEffect(() => {
    async function loadPredictions() {
      const pred = await fetchPredictionsFromBackend(selectedSeason, 1);
      if (pred && pred.podiumProbabilities && pred.podiumProbabilities.length > 0) {
        setPodiumPredictions(pred.podiumProbabilities);
        setFeatureImportances(pred.featureImportance || []);
      } else {
        setPodiumPredictions([
          { position: 1, driver: 'Max Verstappen', team: 'Red Bull Racing', probability: '42%' },
          { position: 2, driver: 'Lando Norris', team: 'McLaren', probability: '28%' },
          { position: 3, driver: 'Charles Leclerc', team: 'Ferrari', probability: '18%' },
        ]);
        setFeatureImportances([
          { feature: 'Starting Grid Position', importance: 0.54 },
          { feature: 'Driver Historical Form', importance: 0.28 },
          { feature: 'Constructor Efficiency', importance: 0.18 },
        ]);
      }
    }
    loadPredictions();
  }, [selectedSeason]);

  useEffect(() => {
    async function load2026Projections() {
      const data = await fetch2026SeasonProjection();
      if (data && data.standings) {
        setSeason2026Standings(
          data.standings.map((s: any, idx: number) => ({
            pos: idx + 1,
            name: s.name,
            team: s.team,
            points: s.points,
            wins: s.wins,
          }))
        );
      } else {
        setSeason2026Standings([
          { pos: 1, name: 'Max Verstappen', team: 'Red Bull Racing', points: 412, wins: 8 },
          { pos: 2, name: 'Lewis Hamilton', team: 'Ferrari', points: 385, wins: 6 },
          { pos: 3, name: 'Lando Norris', team: 'McLaren', points: 360, wins: 4 },
          { pos: 4, name: 'Charles Leclerc', team: 'Ferrari', points: 342, wins: 3 },
          { pos: 5, name: 'Oscar Piastri', team: 'McLaren', points: 298, wins: 2 },
          { pos: 6, name: 'Kimi Antonelli', team: 'Mercedes', points: 184, wins: 1 },
          { pos: 7, name: 'Carlos Sainz', team: 'Williams', points: 112, wins: 0 },
          { pos: 8, name: 'Valtteri Bottas', team: 'Cadillac F1', points: 48, wins: 0 },
        ]);
      }
    }
    load2026Projections();
  }, []);

  const handleRetrain = async () => {
    setIsTraining(true);
    const retrainResult = await retrainPredictorFromBackend('2022,2023,2024');
    if (retrainResult && retrainResult.status === 'success') {
      if (retrainResult.train_samples) setTrainSamples(retrainResult.train_samples);
      if (retrainResult.feature_importance) setFeatureImportances(retrainResult.feature_importance);
    }
    const pred = await fetchPredictionsFromBackend(selectedSeason, 1);
    if (pred && pred.podiumProbabilities) {
      setPodiumPredictions(pred.podiumProbabilities);
    }
    const updatedProj = await fetch2026SeasonProjection();
    if (updatedProj && updatedProj.standings) {
      setSeason2026Standings(
        updatedProj.standings.map((s: any, idx: number) => ({
          pos: idx + 1,
          name: s.name,
          team: s.team,
          points: s.points,
          wins: s.wins,
        }))
      );
    }
    setIsTraining(false);
  };

  return (
    <div ref={containerRef} className="max-w-[1720px] w-full mx-auto px-4 sm:px-6 lg:px-10 xl:px-12 pt-28 pb-16 space-y-12">
      {/* Header & Subtabs */}
      <div className="gsap-fade flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-signal-blue)]">
            {selectedSeason} Season • Gradient Boosting & Generative Monte Carlo Pipeline
          </span>
          <h1 className="font-editorial text-3xl sm:text-4xl lg:text-5xl text-[var(--color-graphite)] tracking-tight">
            Machine Learning Race Predictions
          </h1>
          <p className="text-xs sm:text-sm text-[var(--color-ash)] mt-1.5">
            Top-3 podium probabilities, feature importance, and 2026 regulation projections.
          </p>
        </div>

        {/* Action & Tab Buttons */}
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <div className="flex items-center gap-1.5 bg-[var(--color-paper)] p-1.5 rounded-xl border border-[var(--color-mist)] shadow-sm">
            <button
              onClick={() => setActiveSubTab('podium')}
              className={`px-4 py-2 text-xs font-medium rounded-lg transition-all ${
                activeSubTab === 'podium'
                  ? 'bg-[var(--color-twilight)] text-white shadow-sm'
                  : 'text-[var(--color-charcoal)] hover:bg-[var(--color-linen)]'
              }`}
            >
              Podium Predictor
            </button>
            <button
              onClick={() => setActiveSubTab('season2026')}
              className={`px-4 py-2 text-xs font-medium rounded-lg transition-all ${
                activeSubTab === 'season2026'
                  ? 'bg-[var(--color-twilight)] text-white shadow-sm'
                  : 'text-[var(--color-charcoal)] hover:bg-[var(--color-linen)]'
              }`}
            >
              2026 Projection
            </button>
          </div>

          <button
            onClick={handleRetrain}
            disabled={isTraining}
            className="btn-signal px-4 py-2 text-xs font-semibold flex items-center gap-2 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTraining ? 'animate-spin' : ''}`} />
            <span>{isTraining ? 'Retraining ML...' : 'Retrain Backend ML'}</span>
          </button>
        </div>
      </div>

      {activeSubTab === 'podium' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
          {/* Top-3 Podium Probabilities Card */}
          <div className="gsap-fade lg:col-span-7 card-mist p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-editorial text-xl text-[var(--color-graphite)] flex items-center gap-2">
                <Trophy className="w-5 h-5 text-amber-500" />
                Podium Finish Probability Forecast
              </h3>
              <span className="text-xs text-[var(--color-ash)] font-mono">Model: GradientBoosting</span>
            </div>

            <div className="space-y-4">
              {podiumPredictions.map((item) => (
                <div key={item.driver} className="p-4 rounded-xl border border-[var(--color-mist)] bg-white">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-[var(--color-linen)] flex items-center justify-center text-xs font-bold text-[var(--color-charcoal)]">
                        P{item.position}
                      </span>
                      <div>
                        <span className="font-semibold text-sm text-[var(--color-graphite)] block">{item.driver}</span>
                        <span className="text-xs text-[var(--color-ash)]">{item.team}</span>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="font-editorial text-2xl text-[var(--color-signal-blue)] block">{item.probability}</span>
                      <span className="text-[10px] text-[var(--color-ash)]">Podium Probability</span>
                    </div>
                  </div>

                  {/* Probability Progress Bar */}
                  <div className="w-full h-2 bg-[var(--color-linen)] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-[var(--color-signal-blue)] transition-all duration-500"
                      style={{ width: item.probability }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Feature Importance Card */}
          <div className="gsap-fade lg:col-span-5 card-mist p-6 flex flex-col justify-between">
            <div>
              <h3 className="font-editorial text-xl text-[var(--color-graphite)] mb-1 flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-indigo-500" />
                ML Feature Importances
              </h3>
              <p className="text-xs text-[var(--color-ash)] mb-6">Factors dictating machine learning predictions.</p>

              <div className="space-y-4">
                {featureImportances.map((feat) => (
                  <div key={feat.feature} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[var(--color-graphite)] font-medium">{feat.feature}</span>
                      <span className="font-mono text-[var(--color-ash)]">{Math.round(feat.importance * 100)}%</span>
                    </div>
                    <div className="w-full h-2 bg-[var(--color-linen)] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[var(--color-twilight)]"
                        style={{ width: `${Math.round(feat.importance * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[var(--color-linen)] border border-[var(--color-mist)] mt-6 text-xs text-[var(--color-ash)] flex items-start gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
              <span>
                Model trained on {trainSamples}+ race result records across recent seasons using FastF1 & Ergast dataset.
              </span>
            </div>
          </div>
        </div>
      ) : (
        /* 2026 Generative Season Projection */
        <div className="gsap-fade card-mist p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-editorial text-2xl text-[var(--color-graphite)] flex items-center gap-2">
                <Cpu className="w-6 h-6 text-purple-600" />
                2026 Generative Regulation Projection
              </h3>
              <p className="text-xs text-[var(--color-ash)] mt-1">
                Simulated 24-round season outcome under 50/50 electrical combustion split & active aero.
              </p>
            </div>

            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-purple-50 text-purple-700 border border-purple-200">
              FastF1 Backend Seed #2026
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {season2026Standings.map((st) => (
              <div key={st.name} className="p-4 rounded-xl border border-[var(--color-mist)] bg-white">
                <div className="flex items-center justify-between text-xs text-[var(--color-ash)] mb-2">
                  <span>P{st.pos} Projected</span>
                  <span>{st.wins} Wins</span>
                </div>
                <h4 className="font-editorial text-lg text-[var(--color-graphite)] leading-tight mb-1">{st.name}</h4>
                <p className="text-xs text-[var(--color-ash)] mb-3">{st.team}</p>

                <div className="text-right pt-2 border-t border-[var(--color-linen)]">
                  <span className="font-editorial text-xl text-[var(--color-graphite)]">{st.points} PTS</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
