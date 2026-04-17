import React, { useEffect, useState, useCallback } from 'react';
import { useStore } from '../../store/useStore';
import { Square, Video, Aperture, RotateCcw, Zap, Play, Compass, ChevronRight } from 'lucide-react';
import { MapAnimationEngine } from '../../engine/MapAnimationEngine';
import { useVideoRecorder } from '../../hooks/useVideoRecorder';

type VideoQuality = '1080p' | '4K' | '8K';

const QUALITY_CONFIG: Record<VideoQuality, { label: string; bps: number; desc: string }> = {
  '1080p': { label: '1080p', bps: 8_000_000,  desc: '8 Mbps — 標準品質' },
  '4K':    { label: '4K',    bps: 25_000_000, desc: '25 Mbps — 高畫質  推薦' },
  '8K':    { label: '8K',    bps: 80_000_000, desc: '80 Mbps — 極致畫質' },
};

type AnimMode = 'orbit' | 'spiral' | 'flyin' | 'helicopter' | 'dolly' | null;

const MODES: { id: Exclude<AnimMode, null>; label: string; sub: string; icon: React.FC<{ active: boolean }> }[] = [
  {
    id: 'orbit',
    label: 'Orbit',
    sub: '360° 環繞',
    icon: ({ active }) => <Aperture size={16} className={active ? 'text-brand-500' : 'text-slate-400'} />,
  },
  {
    id: 'spiral',
    label: 'Spiral',
    sub: '螺旋上升',
    icon: ({ active }) => <RotateCcw size={16} className={active ? 'text-violet-500' : 'text-slate-400'} />,
  },
  {
    id: 'flyin',
    label: 'Fly-In',
    sub: '電影入鏡',
    icon: ({ active }) => <Zap size={16} className={active ? 'text-amber-500' : 'text-slate-400'} />,
  },
  {
    id: 'helicopter',
    label: 'Heli',
    sub: '空拍巡航',
    icon: ({ active }) => <Compass size={16} className={active ? 'text-emerald-500' : 'text-slate-400'} />,
  },
  {
    id: 'dolly',
    label: 'Dolly',
    sub: '滑軌平移',
    icon: ({ active }) => <Play size={16} className={active ? 'text-sky-500' : 'text-slate-400'} />,
  },
];

const ACTIVE_COLOR: Record<string, string> = {
  orbit:      'border-brand-400 bg-brand-50 ring-1 ring-brand-200',
  spiral:     'border-violet-400 bg-violet-50 ring-1 ring-violet-200',
  flyin:      'border-amber-400 bg-amber-50 ring-1 ring-amber-200',
  helicopter: 'border-emerald-400 bg-emerald-50 ring-1 ring-emerald-200',
  dolly:      'border-sky-400 bg-sky-50 ring-1 ring-sky-200',
};

export const AnimationStudioPanel: React.FC = () => {
  const mapRef = useStore(state => state.mapRef);
  const { isRecording, recordingSeconds, startRecording, stopRecording } = useVideoRecorder();

  const [activeAnim, setActiveAnim] = useState<AnimMode>(null);
  const [speed, setSpeed] = useState<number>(1.0);
  const [quality, setQuality] = useState<VideoQuality>('4K');
  const [autoRecord, setAutoRecord] = useState<boolean>(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveAnim(MapAnimationEngine.getActiveMode() as AnimMode);
    }, 200);
    return () => clearInterval(interval);
  }, []);

  const startAnim = useCallback((mode: Exclude<AnimMode, null>) => {
    if (!mapRef) return;
    if (mode === 'orbit')      MapAnimationEngine.startOrbit(mapRef, speed);
    else if (mode === 'spiral')     MapAnimationEngine.startSpiral(mapRef, speed);
    else if (mode === 'flyin')      MapAnimationEngine.startFlyIn(mapRef, speed);
    else if (mode === 'helicopter') MapAnimationEngine.startHelicopter(mapRef, speed);
    else if (mode === 'dolly')      MapAnimationEngine.startDollyPan(mapRef, speed);

    if (autoRecord && !isRecording) {
      setTimeout(() => startRecording(QUALITY_CONFIG[quality].bps), 400);
    }
  }, [mapRef, speed, autoRecord, isRecording, quality, startRecording]);

  const handleStop = useCallback(() => {
    MapAnimationEngine.stop();
    if (isRecording) stopRecording();
  }, [isRecording, stopRecording]);

  const handleToggleRecord = () => {
    if (isRecording) stopRecording();
    else startRecording(QUALITY_CONFIG[quality].bps);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="space-y-5 animate-fade-in">

      {/* ─── Section 1: Camera Path ─── */}
      <div className="space-y-3">
        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
          <ChevronRight size={10} /> 運鏡模式
        </h4>

        <div className="grid grid-cols-5 gap-1.5 pl-2">
          {MODES.map(m => {
            const active = activeAnim === m.id;
            return (
              <button
                key={m.id}
                onClick={() => startAnim(m.id)}
                className={`flex flex-col items-center justify-center gap-1 py-2.5 rounded-xl border transition-all text-center ${
                  active
                    ? ACTIVE_COLOR[m.id]
                    : 'border-slate-100 bg-slate-50 hover:bg-white hover:border-slate-200'
                }`}
              >
                <m.icon active={active} />
                <div className={`text-[9px] font-bold leading-tight ${active ? 'text-slate-800' : 'text-slate-500'}`}>
                  {m.label}
                </div>
              </button>
            );
          })}
        </div>

        {activeAnim && (
          <div className="pl-2">
            <button
              onClick={handleStop}
              className="w-full flex items-center justify-center gap-2 py-2 border border-rose-200 bg-rose-50 text-rose-600 rounded-xl hover:bg-rose-100 transition-colors text-[11px] font-bold"
            >
              <Square size={11} />
              STOP · {activeAnim.toUpperCase()}
            </button>
          </div>
        )}
      </div>

      {/* ─── Section 2: Speed ─── */}
      <div className="space-y-3">
        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
          <ChevronRight size={10} /> 速度控制
        </h4>
        <div className="pl-2 space-y-1.5">
          <div className="flex justify-between items-center">
            <span className="text-[11px] text-slate-600 font-medium">速度係數</span>
            <span className="text-[10px] font-mono font-black text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded-md">{speed.toFixed(1)}×</span>
          </div>
          <input
            type="range" min="0.2" max="3" step="0.1" value={speed}
            onChange={e => setSpeed(parseFloat(e.target.value))}
            className="w-full h-1.5 accent-brand-500"
          />
          <div className="flex justify-between text-[9px] text-slate-400">
            <span>Slow · 0.2×</span>
            <span>Fast · 3.0×</span>
          </div>
        </div>
      </div>

      {/* ─── Divider ─── */}
      <div className="h-px bg-slate-100 mx-1" />

      {/* ─── Section 3: Recording ─── */}
      <div className="space-y-3">
        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
          <ChevronRight size={10} /> 錄影輸出
        </h4>

        {/* Quality Selector */}
        <div className="pl-2 space-y-2">
          <span className="text-[11px] text-slate-600 font-medium">畫質</span>
          <div className="grid grid-cols-3 gap-1.5">
            {(Object.keys(QUALITY_CONFIG) as VideoQuality[]).map(q => (
              <button
                key={q}
                onClick={() => setQuality(q)}
                className={`py-2 rounded-xl border-2 text-center transition-all ${
                  quality === q
                    ? 'border-brand-400 bg-brand-50 text-brand-700 font-black'
                    : 'border-slate-100 bg-slate-50 text-slate-600 hover:bg-white hover:border-slate-200'
                }`}
              >
                <div className="text-xs font-bold">{QUALITY_CONFIG[q].label}</div>
              </button>
            ))}
          </div>
          <p className="text-[9px] text-slate-400">{QUALITY_CONFIG[quality].desc}</p>
        </div>

        {/* Auto Record Toggle */}
        <div className="pl-2">
          <div className="flex items-center justify-between px-3 py-2.5 bg-slate-50 rounded-xl border border-slate-100">
            <div>
              <div className="text-[11px] font-bold text-slate-700">啟動即錄影</div>
              <div className="text-[9px] text-slate-400">點擊鏡頭模式時自動開始錄製</div>
            </div>
            <button
              onClick={() => setAutoRecord(v => !v)}
              className={`w-9 h-5 rounded-full transition-all relative flex-shrink-0 ${autoRecord ? 'bg-brand-500' : 'bg-slate-200'}`}
            >
              <div className={`w-4 h-4 bg-white rounded-full shadow absolute top-0.5 transition-all ${autoRecord ? 'left-4' : 'left-0.5'}`} />
            </button>
          </div>
        </div>

        {/* Record Button */}
        <div className="pl-2">
          <button
            onClick={handleToggleRecord}
            className={`w-full py-3.5 rounded-xl font-black text-[11px] tracking-widest uppercase transition-all flex items-center justify-center gap-2 shadow-sm ${
              isRecording
                ? 'bg-rose-600 text-white hover:bg-rose-700'
                : 'bg-slate-800 text-white hover:bg-brand-600'
            }`}
          >
            {isRecording ? <Square size={13} className="fill-current" /> : <Video size={13} />}
            {isRecording ? `● REC ${formatTime(recordingSeconds)}` : `REC · ${quality} WebM`}
          </button>
        </div>
      </div>
    </div>
  );
};
