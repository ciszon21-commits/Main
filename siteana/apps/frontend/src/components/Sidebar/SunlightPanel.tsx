import React, { useState, useEffect, useRef } from 'react';
import { Sun, Moon, Play, Pause, Clock, Compass, SkipBack } from 'lucide-react';
import { useStore } from '../../store/useStore';
import { useMapPaintStore } from '../../store/useMapPaintStore';
import { SunlightEngine } from '../../engine/SunlightEngine';

// ──  PRESETS for sunlight mode ─────────────────────────────────────────────
const ECOLOGICAL_PRESET_ID = 'ecological_texture';
const ARCHITECTURAL_PRESET_ID = 'architectural_grey';

// Ecological Texture colours (from MapStyleStudio.tsx)
const ECOLOGICAL_PRESET = {
  roadColors: { highway: '#fcfcfc', primary: '#fcfcfc', secondary: '#ffffff', residential: '#ffffff', path: '#ffffff' },
  buildingColor: '#f1f5f2', buildingOutlineColor: '#e2e8e4', buildingOpacity: 0.85, building3D: false, buildingVisibility: true,
  landUseColors: { residential: '#ffffff', commercial: '#ffffff', park: '#c2dac1', water: '#aed1d6', industrial: '#ffffff' },
  backgroundColor: '#ffffff', labelVisibility: { road: false, park: false, water: false, poi: false },
};

// Architectural Grey preset
const ARCHITECTURAL_PRESET = {
  roadColors: { highway: '#4a5568', primary: '#718096', secondary: '#a0aec0', residential: '#cbd5e1', path: '#e2e8f0' },
  buildingColor: '#ffffff', buildingOutlineColor: '#000000', buildingOpacity: 1.0, building3D: false, buildingVisibility: true,
  landUseColors: { residential: '#e2e8f0', commercial: '#e2e8f0', park: '#cbd2d9', water: '#a0aec0', industrial: '#e2e8f0' },
  backgroundColor: '#f1f5f9', labelVisibility: { road: false, park: false, water: false, poi: false },
};

// ─────────────────────────────────────────────────────────────────────────────

const fmt2 = (n: number) => n.toString().padStart(2, '0');
const formatHour = (decimal: number) => {
  const h = Math.floor(decimal);
  const m = Math.floor((decimal - h) * 60);
  return `${fmt2(h)}:${fmt2(m)}`;
};

// Taiwan location default for sunrise calc
const DEFAULT_LAT = 25.04;
const DEFAULT_LNG = 121.51;

const SunlightPanel: React.FC = () => {
  const {
    sunlightEnabled, setSunlightEnabled,
    sunlightDate, setSunlightDate,
    sunlightTime, setSunlightTime,
    sunlightShadowOpacity, setSunlightShadowOpacity,
    stylePresets, setSelectedStyle, selectedStyle,
    mapRef
  } = useStore();

  const [isPlaying, setIsPlaying] = useState(false);
  const [activePreset, setActivePreset] = useState<'ecological' | 'architectural'>('ecological');
  const [sunTimes, setSunTimes] = useState<{ sunriseHour: number | null; sunsetHour: number | null } | null>(null);
  const [currentSunPos, setCurrentSunPos] = useState<{ altitudeDeg: number; azimuthDeg: number; isDay: boolean } | null>(null);
  const animRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Key: use map center for accurate sunrise/set ──────────────────────────
  const getLat = () => mapRef?.getCenter().lat ?? DEFAULT_LAT;
  const getLng = () => mapRef?.getCenter().lng ?? DEFAULT_LNG;

  // Compute sun times whenever date changes
  useEffect(() => {
    const d = new Date(sunlightDate);
    const times = SunlightEngine.getSunTimes(d, getLat(), getLng());
    setSunTimes({ sunriseHour: times.sunriseHour, sunsetHour: times.sunsetHour });
  }, [sunlightDate, sunlightEnabled]);

  // Update current sun position whenever time or date changes
  useEffect(() => {
    const d = new Date(sunlightDate);
    d.setHours(Math.floor(sunlightTime), Math.floor((sunlightTime % 1) * 60), 0, 0);
    const pos = SunlightEngine.getSunPosition(d, getLat(), getLng());
    setCurrentSunPos(pos);
  }, [sunlightTime, sunlightDate]);

  //  ── Playback animation ─────────────────────────────────────────────────
  useEffect(() => {
    if (!isPlaying) {
      if (animRef.current) clearInterval(animRef.current);
      return;
    }
    animRef.current = setInterval(() => {
      setSunlightTime((useStore.getState().sunlightTime + 0.25) % 24);
    }, 180);
    return () => { if (animRef.current) clearInterval(animRef.current); };
  }, [isPlaying]);

  // ── Toggle sunlight with auto-preset selection ─────────────────────────
  const handleToggle = (checked: boolean) => {
    setSunlightEnabled(checked);
    if (checked) {
      // Switch to Liberty basemap
      if (selectedStyle?.id !== 'ofm-liberty') {
        const liberty = stylePresets.find(p => p.id === 'ofm-liberty');
        if (liberty) setSelectedStyle(liberty);
      }
      // Apply matching preset
      applyModePreset(activePreset);
    } else {
      setIsPlaying(false);
    }
  };

  const applyModePreset = (mode: 'ecological' | 'architectural') => {
    const presetId  = mode === 'ecological' ? ECOLOGICAL_PRESET_ID : ARCHITECTURAL_PRESET_ID;
    const presetVal = mode === 'ecological' ? ECOLOGICAL_PRESET : ARCHITECTURAL_PRESET;
    useMapPaintStore.getState().applyPreset(presetId, presetVal);
  };

  const handlePresetSwitch = (mode: 'ecological' | 'architectural') => {
    setActivePreset(mode);
    if (sunlightEnabled) applyModePreset(mode);
  };

  const jumpToNow = () => {
    const now = new Date();
    const todayStr = now.toISOString().split('T')[0];
    setSunlightDate(todayStr);
    setSunlightTime(now.getHours() + now.getMinutes() / 60);
  };

  // ── Sunrise / Sunset positions on slider (0-100%) ──────────────────────
  const srPct = sunTimes?.sunriseHour != null ? (sunTimes.sunriseHour / 24) * 100 : null;
  const ssPct = sunTimes?.sunsetHour  != null ? (sunTimes.sunsetHour  / 24) * 100 : null;
  const timePct = (sunlightTime / 24) * 100;
  const isDay = currentSunPos?.isDay ?? false;

  // ── Compass bearing label ───────────────────────────────────────────────
  const compassLabel = (deg: number) => {
    const dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
    return dirs[Math.round(deg / 22.5) % 16];
  };

  return (
    <div className="space-y-3 animate-fade-in py-2">

      {/* ── Toggle Row ─────────────────────────────────────────────────── */}
      <label className="flex items-center justify-between cursor-pointer border border-slate-200 p-3 rounded-xl bg-white hover:border-amber-200 hover:bg-amber-50/40 transition-colors shadow-sm">
        <span className="text-xs font-bold text-slate-700 flex items-center gap-2">
          {isDay
            ? <Sun size={15} className="text-amber-500" />
            : <Moon size={14} className="text-slate-400" />
          }
          啟用建築日照陰影
        </span>
        <input
          type="checkbox"
          checked={sunlightEnabled}
          onChange={e => handleToggle(e.target.checked)}
          className="w-4 h-4 rounded accent-amber-500"
        />
      </label>

      {sunlightEnabled && (
        <div className="space-y-4">

          {/* ── Auto-Preset Selector ─────────────────────────────────── */}
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 space-y-2">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">底圖風格</p>
            <div className="grid grid-cols-2 gap-2">
              {([
                { id: 'ecological', label: '生態紋理', sub: 'Ecological' },
                { id: 'architectural', label: '建築灰階', sub: 'Arch Grey' }
              ] as const).map(({ id, label, sub }) => (
                <button
                  key={id}
                  onClick={() => handlePresetSwitch(id)}
                  className={`flex flex-col items-center py-2.5 px-2 rounded-lg border text-center transition-all text-[11px] font-bold ${
                    activePreset === id
                      ? 'bg-amber-500 border-amber-500 text-white shadow-md shadow-amber-100'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-amber-200'
                  }`}
                >
                  <span>{label}</span>
                  <span className={`text-[9px] font-normal ${activePreset === id ? 'text-amber-100' : 'text-slate-400'}`}>{sub}</span>
                </button>
              ))}
            </div>
          </div>

          {/* ── HUD: Sun Position ────────────────────────────────────── */}
          {currentSunPos && (
            <div className={`rounded-xl border p-3 flex gap-3 items-center ${
              isDay ? 'bg-amber-50 border-amber-100' : 'bg-slate-100 border-slate-200'
            }`}>
              <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${
                isDay ? 'bg-amber-400 text-white' : 'bg-slate-400 text-white'
              }`}>
                {isDay ? <Sun size={18} /> : <Moon size={16} />}
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 flex-1 text-[10px]">
                <div>
                  <div className="text-slate-400 font-bold uppercase tracking-wider">仰角 Alt</div>
                  <div className="font-mono font-bold text-slate-700 text-xs">
                    {currentSunPos.altitudeDeg.toFixed(1)}°
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 font-bold uppercase tracking-wider">方位 Az</div>
                  <div className="font-mono font-bold text-slate-700 text-xs">
                    {currentSunPos.azimuthDeg.toFixed(0)}° {compassLabel(currentSunPos.azimuthDeg)}
                  </div>
                </div>
                {sunTimes?.sunriseHour != null && (
                  <div>
                    <div className="text-slate-400 font-bold uppercase tracking-wider">🌅 日出</div>
                    <div className="font-mono font-bold text-slate-700 text-xs">{formatHour(sunTimes.sunriseHour)}</div>
                  </div>
                )}
                {sunTimes?.sunsetHour != null && (
                  <div>
                    <div className="text-slate-400 font-bold uppercase tracking-wider">🌇 日落</div>
                    <div className="font-mono font-bold text-slate-700 text-xs">{formatHour(sunTimes.sunsetHour)}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Date + NOW button ─────────────────────────────────────── */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-bold text-slate-500">分析日期</label>
              <button
                onClick={jumpToNow}
                className="flex items-center gap-1 text-[10px] font-bold text-brand-600 bg-brand-50 hover:bg-brand-100 px-2 py-0.5 rounded-full transition-colors"
              >
                <Clock size={10} /> NOW
              </button>
            </div>
            <input
              type="date"
              value={sunlightDate}
              onChange={e => setSunlightDate(e.target.value)}
              className="w-full px-2 py-2 text-xs font-medium rounded-lg border border-slate-200 focus:outline-none focus:border-amber-400"
            />
          </div>

          {/* ── Time Slider with day/night gradient ───────────────────── */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
                <Clock size={10} /> 時刻
              </label>
              <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                isDay ? 'text-amber-700 bg-amber-50' : 'text-slate-500 bg-slate-100'
              }`}>{formatHour(sunlightTime)}</span>
            </div>

            {/* Gradient track with sunrise/sunset markers */}
            <div className="relative pt-3 pb-1">
              {/* Gradient bar */}
              <div
                className="w-full h-3 rounded-full relative overflow-hidden"
                style={{
                  background: 'linear-gradient(to right, #0f172a 0%, #1e3a5f 15%, #fb923c 28%, #fde68a 50%, #fb923c 72%, #1e3a5f 85%, #0f172a 100%)'
                }}
              >
                {/* Sunrise tick */}
                {srPct != null && (
                  <div className="absolute top-0 h-full w-0.5 bg-orange-300/80" style={{ left: `${srPct}%` }} />
                )}
                {/* Sunset tick */}
                {ssPct != null && (
                  <div className="absolute top-0 h-full w-0.5 bg-orange-300/80" style={{ left: `${ssPct}%` }} />
                )}
                {/* Current time thumb */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white border-2 border-amber-500 shadow-md shadow-amber-200 transition-left duration-100"
                  style={{ left: `${timePct}%` }}
                />
              </div>

              {/* Accessible range input overlay */}
              <input
                type="range" min="0" max="24" step="0.25"
                value={sunlightTime}
                onChange={e => { setSunlightTime(Number(e.target.value)); setIsPlaying(false); }}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              {/* Sunrise / sunset labels */}
              <div className="flex justify-between text-[9px] text-slate-400 mt-1 px-0.5">
                <span>00:00</span>
                {srPct != null && (
                  <span className="text-orange-500 font-bold" style={{ marginLeft: `${srPct - 8}%` }}>
                    🌅 {formatHour(sunTimes!.sunriseHour!)}
                  </span>
                )}
                <span className="ml-auto">24:00</span>
              </div>
              {ssPct != null && (
                <div className="relative h-3">
                  <span
                    className="absolute text-[9px] text-orange-500 font-bold -translate-x-1/2"
                    style={{ left: `${ssPct}%`, top: 0 }}
                  >
                    🌇 {formatHour(sunTimes!.sunsetHour!)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* ── Quick Time Presets ────────────────────────────────────── */}
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => { setSunlightTime(sunTimes?.sunriseHour ? sunTimes.sunriseHour + 1 : 7); setIsPlaying(false); }}
              className="py-1.5 rounded-lg bg-slate-50 border border-slate-100 text-[10px] font-bold text-slate-500 hover:bg-amber-50 hover:text-amber-600 hover:border-amber-200 transition-all flex flex-col items-center gap-1"
            >
              <Sun size={12} /> 早晨
            </button>
            <button
              onClick={() => { setSunlightTime(12); setIsPlaying(false); }}
              className="py-1.5 rounded-lg bg-slate-50 border border-slate-100 text-[10px] font-bold text-slate-500 hover:bg-amber-50 hover:text-amber-600 hover:border-amber-200 transition-all flex flex-col items-center gap-1"
            >
              <Sun size={12} className="text-amber-400" /> 正午
            </button>
            <button
              onClick={() => { setSunlightTime(sunTimes?.sunsetHour ? sunTimes.sunsetHour - 1 : 17); setIsPlaying(false); }}
              className="py-1.5 rounded-lg bg-slate-50 border border-slate-100 text-[10px] font-bold text-slate-500 hover:bg-orange-50 hover:text-orange-600 hover:border-orange-200 transition-all flex flex-col items-center gap-1"
            >
              <Moon size={12} className="text-orange-400" /> 黃昏
            </button>
          </div>

          {/* ── Playback Controls ─────────────────────────────────────── */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(p => !p)}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-bold transition-all ${
                isPlaying
                  ? 'bg-gradient-to-r from-orange-400 to-amber-500 text-white shadow-lg shadow-amber-500/30'
                  : 'bg-white border-2 border-slate-100 text-slate-600 hover:border-amber-400 hover:text-amber-600 shadow-sm'
              }`}
            >
              {isPlaying ? <><Pause size={13} className="animate-pulse" /> 暫停分析</> : <><Play size={13} /> 播放全天日照軌跡</>}
            </button>
          </div>

          {/* ── Opacity ──────────────────────────────────────────────── */}
          <div className="space-y-1.5 pt-1 border-t border-slate-100">
            <div className="flex items-center justify-between text-[10px] font-bold text-slate-500">
              <span>陰影深淺</span>
              <span className="text-slate-600">{(sunlightShadowOpacity * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range" min="0.1" max="1.0" step="0.05"
              value={sunlightShadowOpacity}
              onChange={e => setSunlightShadowOpacity(Number(e.target.value))}
              className="w-full accent-slate-600 h-1 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* ── Compass indicator note ────────────────────────────────── */}
          <div className="bg-slate-50 border border-slate-100 p-2.5 rounded-xl flex gap-2 items-start">
            <Compass size={13} className="text-amber-500 flex-shrink-0 mt-0.5" />
            <p className="text-[10px] text-slate-500 leading-relaxed">
              地圖中心已顯示 <b>太陽方位羅盤</b>，金色虛線圓圈與方向箭頭代表當前時刻的太陽方位。
            </p>
          </div>

        </div>
      )}
    </div>
  );
};

export default SunlightPanel;
