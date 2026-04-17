import React, { useEffect, useState, useCallback } from 'react';
import { useStore } from '../../store/useStore';
import { Square, Video, Aperture, Compass, Film, RotateCcw, Zap } from 'lucide-react';
import { MapAnimationEngine } from '../../engine/MapAnimationEngine';
import { useVideoRecorder } from '../../hooks/useVideoRecorder';

type VideoQuality = '1080p' | '4K' | '8K';

const QUALITY_CONFIG: Record<VideoQuality, { label: string; bps: number; desc: string }> = {
  '1080p': { label: '1080p', bps: 8_000_000,  desc: '8 Mbps — 標準品質' },
  '4K':    { label: '4K',    bps: 25_000_000, desc: '25 Mbps — 高畫質 推薦' },
  '8K':    { label: '8K',    bps: 80_000_000, desc: '80 Mbps — 極致畫質' },
};

type AnimMode = 'orbit' | 'spiral' | 'flyin' | null;

export const AnimationStudioPanel: React.FC = () => {
  const mapRef = useStore(state => state.mapRef);
  const { isRecording, recordingSeconds, startRecording, stopRecording } = useVideoRecorder();

  const [activeAnim, setActiveAnim] = useState<AnimMode>(null);
  const [speed, setSpeed] = useState<number>(1.0);
  const [quality, setQuality] = useState<VideoQuality>('4K');
  const [autoRecord, setAutoRecord] = useState<boolean>(false);

  // Sync state with Animation Engine
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveAnim(MapAnimationEngine.getActiveMode() as AnimMode);
    }, 200);
    return () => clearInterval(interval);
  }, []);

  const startAnim = useCallback((mode: AnimMode) => {
    if (!mapRef || !mode) return;
    if (mode === 'orbit') MapAnimationEngine.startOrbit(mapRef, speed);
    else if (mode === 'spiral') MapAnimationEngine.startSpiral(mapRef, speed);
    else if (mode === 'flyin') MapAnimationEngine.startFlyIn(mapRef, speed);

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

  const modes: { id: AnimMode; icon: React.ReactNode; label: string; sub: string; color: string }[] = [
    {
      id: 'orbit',
      icon: <Aperture size={18} className={activeAnim === 'orbit' ? 'text-brand-500 animate-spin' : 'text-slate-400'} />,
      label: 'Orbit', sub: '360° 環繞', color: 'brand',
    },
    {
      id: 'spiral',
      icon: <RotateCcw size={18} className={activeAnim === 'spiral' ? 'text-violet-500 animate-spin' : 'text-slate-400'} />,
      label: 'Spiral', sub: '螺旋上升', color: 'violet',
    },
    {
      id: 'flyin',
      icon: <Zap size={18} className={activeAnim === 'flyin' ? 'text-amber-500 animate-pulse' : 'text-slate-400'} />,
      label: 'Fly-In', sub: '電影入鏡', color: 'amber',
    },
  ];

  const colorMap: Record<string, string> = {
    brand:  'border-brand-400 bg-brand-50 ring-brand-200',
    violet: 'border-violet-400 bg-violet-50 ring-violet-200',
    amber:  'border-amber-400 bg-amber-50 ring-amber-200',
  };

  return (
    <div className="flex flex-col bg-slate-50 text-slate-800 rounded-2xl overflow-hidden border border-slate-100 shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 flex items-center gap-2 border-b border-slate-100 bg-white">
        <Film size={14} className="text-brand-500" />
        <div>
          <div className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">Animation Studio</div>
          <div className="text-sm font-bold text-slate-800">動態運鏡中心</div>
        </div>
        {isRecording && (
          <div className="ml-auto flex items-center gap-1.5 px-2 py-1 bg-rose-500 rounded-full animate-pulse">
            <div className="w-1.5 h-1.5 rounded-full bg-white" />
            <span className="text-[10px] font-black text-white tracking-wider">{formatTime(recordingSeconds)}</span>
          </div>
        )}
      </div>

      <div className="p-4 space-y-5">
        {/* Camera Modes */}
        <div className="space-y-2">
          <label className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">1 · Camera Path</label>
          <div className="grid grid-cols-3 gap-1.5">
            {modes.map(m => (
              <button
                key={m.id}
                onClick={() => startAnim(m.id)}
                className={`p-2.5 rounded-xl border-2 text-center transition-all ${
                  activeAnim === m.id
                    ? `${colorMap[m.color]} ring-2 shadow-inner`
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="flex justify-center mb-1">{m.icon}</div>
                <div className="text-[11px] font-bold text-slate-700">{m.label}</div>
                <div className="text-[9px] text-slate-400">{m.sub}</div>
              </button>
            ))}
          </div>

          {activeAnim && (
            <button
              onClick={handleStop}
              className="w-full flex items-center justify-center gap-2 py-2 border border-rose-200 bg-rose-50 text-rose-600 rounded-xl hover:bg-rose-100 transition-colors text-xs font-bold"
            >
              <Square size={12} /> STOP  ·  {activeAnim?.toUpperCase()}
            </button>
          )}
        </div>

        {/* Speed Control */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">2 · Speed</label>
            <span className="text-[10px] font-mono font-bold text-brand-600">{speed.toFixed(1)}×</span>
          </div>
          <input
            type="range" min="0.2" max="3" step="0.1" value={speed}
            onChange={e => setSpeed(parseFloat(e.target.value))}
            className="w-full h-1.5 accent-brand-500"
          />
          <div className="flex justify-between text-[9px] text-slate-400">
            <span>Slow</span><span>Fast</span>
          </div>
        </div>

        <div className="h-px bg-slate-200" />

        {/* Video Quality */}
        <div className="space-y-2">
          <label className="text-[9px] font-bold tracking-widest text-slate-400 uppercase">3 · Recording Quality</label>
          <div className="grid grid-cols-3 gap-1.5">
            {(Object.keys(QUALITY_CONFIG) as VideoQuality[]).map(q => (
              <button
                key={q}
                onClick={() => setQuality(q)}
                className={`py-2 rounded-xl text-center border-2 transition-all ${
                  quality === q
                    ? 'border-brand-400 bg-brand-50 text-brand-700 font-black'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <div className="text-xs font-bold">{QUALITY_CONFIG[q].label}</div>
              </button>
            ))}
          </div>
          <p className="text-[9px] text-slate-400 text-center">{QUALITY_CONFIG[quality].desc}</p>
        </div>

        {/* Auto Record Toggle */}
        <div className="flex items-center justify-between px-3 py-2 bg-white rounded-xl border border-slate-100">
          <div>
            <div className="text-[11px] font-bold text-slate-700">啟動即錄影</div>
            <div className="text-[9px] text-slate-400">點擊鏡頭模式時自動開始錄製</div>
          </div>
          <button
            onClick={() => setAutoRecord(v => !v)}
            className={`w-10 h-5 rounded-full transition-all relative flex items-center ${autoRecord ? 'bg-brand-500' : 'bg-slate-200'}`}
          >
            <div className={`w-4 h-4 bg-white rounded-full shadow absolute transition-all ${autoRecord ? 'left-5.5' : 'left-0.5'}`} />
          </button>
        </div>

        {/* Record Button */}
        <button
          onClick={handleToggleRecord}
          className={`w-full py-3.5 rounded-xl font-black text-xs tracking-widest uppercase transition-all flex items-center justify-center gap-2 ${
            isRecording
              ? 'bg-rose-600 text-white hover:bg-rose-700 animate-pulse'
              : 'bg-slate-900 text-white hover:bg-brand-600'
          }`}
        >
          {isRecording ? <Square size={14} className="fill-current" /> : <Video size={14} />}
          {isRecording ? `STOP REC · ${formatTime(recordingSeconds)}` : `REC · ${quality} WebM`}
        </button>
      </div>
    </div>
  );
};

