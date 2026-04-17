import React, { useState, useEffect, useRef } from 'react';

// --- HIGH-PRECISION 3D ROTATION ENGINE ---
const ThreeDSphere: React.FC<{ size: number; isExiting: boolean; progress: number; mouseOffset: { x: number; y: number } }> = ({ size, isExiting, progress, mouseOffset }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const points = useRef<{ x: number; y: number; z: number; type: 'dot' | 'label' | 'particle'; label?: string }[]>([]);
  const lerpRotation = useRef({ x: 0, y: 0 });

  useEffect(() => {
    // Generate nodes
    const p: { x: number; y: number; z: number; type: 'dot' | 'label' | 'particle'; label?: string }[] = [];
    
    // Core Shell (550 dots)
    for (let i = 0; i < 550; i++) {
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = size * 0.42;
      p.push({ x: r * Math.sin(phi) * Math.cos(theta), y: r * Math.sin(phi) * Math.sin(theta), z: r * Math.cos(phi), type: 'dot' });
    }

    // Outer Particles (80 particles)
    for (let i = 0; i < 80; i++) {
        const theta = Math.random() * 2 * Math.PI;
        const phi = Math.acos(2 * Math.random() - 1);
        const r = size * (0.5 + Math.random() * 0.1);
        p.push({ x: r * Math.sin(phi) * Math.cos(theta), y: r * Math.sin(phi) * Math.sin(theta), z: r * Math.cos(phi), type: 'particle' });
    }

    // Interactive 3D Labels
    const labels = ["GEO_LOCKED", "OSM_SYNC", "GRID_READY", "V_0.14_PRO", "TPE_COORD"];
    labels.forEach((text, i) => {
        const theta = (i / labels.length) * 2 * Math.PI;
        const phi = Math.PI / 2;
        const r = size * 0.46; // Surface orbit
        p.push({ x: r * Math.sin(phi) * Math.cos(theta), y: r * Math.sin(phi) * Math.sin(theta), z: r * Math.cos(phi), type: 'label', label: text });
    });

    points.current = p;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const fov = 1000;

      // Mouse Lerp
      lerpRotation.current.y += (mouseOffset.x * 0.12 - lerpRotation.current.y) * 0.04;
      lerpRotation.current.x += (mouseOffset.y * 0.12 - lerpRotation.current.x) * 0.04;

      // [PRECISION] Rotation: exactly 360deg in 5s
      const rotationY = progress * Math.PI * 2 + lerpRotation.current.y;
      const rotationX = 0.15 + (Math.sin(progress * Math.PI) * 0.05) + lerpRotation.current.x;

      const cosY = Math.cos(rotationY);
      const sinY = Math.sin(rotationY);
      const cosX = Math.cos(rotationX);
      const sinX = Math.sin(rotationX);

      const items = points.current.map(p => {
        let x = p.x * cosY - p.z * sinY;
        let z = p.x * sinY + p.z * cosY;
        let y = p.y * cosX - z * sinX;
        z = p.y * sinX + z * cosX;
        const scale = fov / (fov + z + size);
        return { px: x * scale + centerX, py: y * scale + centerY, pz: z, scale, label: p.label, type: p.type };
      }).sort((a, b) => a.pz - b.pz);

      // Render Energy Trails
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(14, 165, 233, 0.04)';
      ctx.lineWidth = 0.5;
      for (let i = 0; i < 20; i++) {
          const it1 = items[i * 20 % items.length];
          const it2 = items[(i * 20 + 8) % items.length];
          if (it1.pz > 0) {
            ctx.moveTo(it1.px, it1.py);
            ctx.lineTo(it2.px, it2.py);
          }
      }
      ctx.stroke();

      // Render Batched Dots
      ctx.beginPath();
      items.forEach((p) => {
        if (p.type === 'label') return;
        const rad = (p.type === 'particle' ? 0.8 : 1.3) * p.scale;
        ctx.moveTo(p.px, p.py);
        ctx.arc(p.px, p.py, rad, 0, Math.PI * 2);
      });
      ctx.fillStyle = `rgba(14, 165, 233, 0.5)`;
      ctx.fill();

      // Labels and Highlights
      items.forEach((p, i) => {
        if (p.type === 'label' && p.pz > 0) {
            const opacity = (p.pz + size) / (size * 2);
            ctx.font = `8px Inter, monospace`;
            ctx.fillStyle = `rgba(255, 255, 255, ${opacity * 0.8})`;
            ctx.fillText(p.label!, p.px + 15, p.py);
            ctx.beginPath();
            ctx.strokeStyle = `rgba(14, 165, 233, ${opacity * 0.2})`;
            ctx.moveTo(p.px, p.py);
            ctx.lineTo(p.px + 10, p.py - 3);
            ctx.stroke();
        } else if (p.type === 'dot' && i % 40 === 0) {
            const opacity = (p.pz + size) / (size * 2);
            ctx.beginPath();
            ctx.arc(p.px, p.py, 1.8 * p.scale, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
            ctx.fill();
        }
      });

      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, [size, progress, mouseOffset]);

  return (
    <div className={`relative flex items-center justify-center transition-all duration-1000 ${isExiting ? 'scale-[15] opacity-0 blur-3xl' : 'scale-100 opacity-100'}`}>
       <canvas ref={canvasRef} width={size * 1.5} height={size * 1.5} className="relative z-10" />
       {/* Ambient Depth Glow - Enhanced for deeper contrast and vibration */}
       <div className={`absolute inset-x-0 inset-y-0 rounded-full bg-brand-500/10 blur-[100px] pointer-events-none transition-all duration-[3000ms] ${isExiting ? 'opacity-0 scale-150' : 'opacity-100 animate-pulse'}`} />
       {/* Center Accretion Lens Flare */}
       <div className="absolute w-[30vw] h-[2px] bg-brand-400/30 blur-[2px] rotate-[-15deg] pointer-events-none" />
       <div className="absolute w-[2px] h-[30vw] bg-brand-400/10 blur-[4px] rotate-[-15deg] pointer-events-none" />
    </div>
  );
};

interface LoadingScreenProps {
  onLoadingComplete?: () => void;
  isMapReady: boolean;
  isPaintHydrated: boolean;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ onLoadingComplete, isMapReady, isPaintHydrated }) => {
  const [progress, setProgress] = useState(0); 
  const [isExiting, setIsExiting] = useState(false);
  const [tipIndex, setTipIndex] = useState(0);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [techLogs, setTechLogs] = useState<string[]>([]);
  const startTime = useRef(performance.now());
  const finishedRef = useRef(false);

  const tips = [
    "Initializing Spatial Engine...",
    "Syncing Urban Geometry...",
    "Loading OpenStreetMap Data...",
    "Calibrating Sunlight Vectors...",
    "Finalizing Visual Layers...",
    "Ready for Design Analysis"
  ];

  const techSource = [
    "> Initialize Global Coordinate System...",
    "> Fetching North Taiwan GIS Fabric...",
    "> Configuring SiteANA_Analysis_Grid...",
    "> SYNC_REGION: TAIWAN_STRAIT / TPE",
    "> LAYER_LOAD: ROADS_PRIMARY_STABLE",
    "> AUTH_TOKEN: EXPIRED_FALLBACK_OSM",
    "> SYST_CHECK: PASS_60FPS_STABLE"
  ];

  useEffect(() => {
    let animationFrame: number;
    const duration = 1200; // Accelerated from 2500ms

    const tick = () => {
      const elapsed = performance.now() - startTime.current;
      const p = Math.min(elapsed / duration, 1);
      setProgress(p);

      // Sync Tips and Logs
      setTipIndex(Math.floor(p * tips.length) % tips.length);
      const activeLogs = Math.ceil(p * (techSource.length + 3));
      setTechLogs(techSource.slice(0, Math.min(activeLogs, techSource.length)));

      // DECISIVE EXIT: trigger exactly at 100% and map status
      if (p >= 1 && isMapReady && isPaintHydrated && !finishedRef.current) {
        finishedRef.current = true;
        setIsExiting(true);
        setTimeout(() => {
          if (onLoadingComplete) onLoadingComplete();
        }, 1200); // Accelerated from 1800ms
      } else {
        animationFrame = requestAnimationFrame(tick);
      }
    };

    animationFrame = requestAnimationFrame(tick);

    const handleMouseMove = (e: MouseEvent) => {
        setMousePos({ x: (e.clientX / window.innerWidth) - 0.5, y: (e.clientY / window.innerHeight) - 0.5 });
    };
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [isMapReady, isPaintHydrated, onLoadingComplete]);

  return (
    <div className={`fixed inset-0 z-[100] flex flex-col items-center justify-center overflow-hidden transition-all duration-[1200ms] cubic-bezier(0.4, 0, 0.2, 1) ${isExiting ? 'opacity-0 scale-[1.5] blur-xl' : 'opacity-100 scale-100 blur-0'}`}
         style={{ background: 'radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%)' }}>
      
      {/* 1. BACKGROUND GRID (Holographic projection feel) */}
      <div className="absolute inset-0 perspective-[1200px] opacity-[0.25]">
        <div 
          className="absolute inset-[-100%] border-[0.5px] border-brand-500/10 animate-[spin-slow_150s_linear_infinite]"
          style={{
             backgroundImage: 'linear-gradient(to right, rgba(14,165,233,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(14,165,233,0.04) 1px, transparent 1px)',
             backgroundSize: '100px 100px',
             transform: 'rotateX(75deg) translateZ(-400px)'
          }}
        />
        {/* Ground illumination sweep */}
        <div className="absolute inset-0 bg-gradient-to-t from-brand-500/5 via-transparent to-transparent opacity-50 pointer-events-none" />
      </div>

      {/* 2. CENTER PIECE: THE 360-ORBITAL CORE */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-[1200px]">
          <ThreeDSphere size={650} isExiting={isExiting} progress={progress} mouseOffset={mousePos} />
          
          {/* Orbital Mirror Rings */}
          <div className="absolute" style={{ transform: 'rotateX(65deg) translateZ(-100px)' }}>
            <div className="w-[160vw] h-[160vw] border-[1px] border-white/10 rounded-full shadow-[0_0_100px_rgba(255,255,255,0.02)] animate-[spin_6s_linear_infinite]"
                 style={{ backgroundImage: 'conic-gradient(from 0deg, transparent, rgba(14,165,233,0.15) 30deg, transparent 60deg, transparent 180deg, rgba(14,165,233,0.15) 210deg, transparent 240deg)' }} />
          </div>
          
          <div className="absolute" style={{ transform: 'rotateX(72deg) rotateY(15deg) translateZ(50px)' }}>
             <div className="w-[140vw] h-[140vw] border-[1.5px] border-brand-500/20 rounded-full shadow-[0_0_60px_rgba(14,165,233,0.2)_inset] animate-[spin_4s_linear_infinite_reverse]"
                  style={{ backgroundImage: 'conic-gradient(from 90deg, transparent, rgba(245,158,11,0.1) 45deg, transparent 90deg)' }} />
          </div>

          {/* High-speed targeting ring */}
          <div className="absolute" style={{ transform: 'rotateX(80deg) rotateY(-10deg) translateZ(-50px)' }}>
             <div className="w-[180vw] h-[180vw] border-[0.5px] border-amber-500/10 rounded-full animate-[spin_10s_linear_infinite] border-dashed" />
          </div>
      </div>

      {/* 3. SYMMETRICAL HUD LAYOUT */}
      
      {/* [LEFT] DIAGNOSTICS */}
      <div className="absolute left-16 top-1/2 -translate-y-1/2 w-[280px] space-y-4 transition-all duration-1000" style={{ transform: isExiting ? 'translateX(-50px)' : 'translateX(0)', opacity: isExiting ? 0 : 0.4 }}>
         <div className="flex items-center gap-2 mb-4">
            <div className="w-1.5 h-4 bg-brand-500 rounded-sm" />
            <span className="text-[10px] font-mono text-white tracking-[5px] uppercase">Engine_Logs</span>
         </div>
         <div className="flex flex-col gap-2.5 font-mono text-[7px] text-brand-300">
            {techLogs.map((log, i) => (
              <div key={i} className="flex gap-2">
                 <span className="text-white/20">{">"}</span>
                 <span className="truncate">{log}</span>
              </div>
            ))}
         </div>
      </div>

      {/* [RIGHT] TELEMETRY */}
      <div className="absolute right-16 top-1/2 -translate-y-1/2 text-right w-[280px] space-y-6 transition-all duration-1000" style={{ transform: isExiting ? 'translateX(50px)' : 'translateX(0)', opacity: isExiting ? 0 : 0.4 }}>
         <div className="space-y-1">
            <p className="text-[10px] font-mono text-brand-400 tracking-[5px] uppercase mb-2">Telemetry_Link</p>
            <p className="text-3xl font-light text-white tracking-widest leading-none">
                {Math.round((1 - progress) * 19500 + 500).toLocaleString()} <span className="text-xs opacity-40">KM</span>
            </p>
         </div>
         <div className="h-[1px] w-32 ml-auto bg-white/10" />
         <div className="space-y-2 font-mono text-[8px] text-white/30 uppercase tracking-[3px]">
            <p>LAT_25.04N / LON_121.51E</p>
            <p className="text-brand-500/50">Status: Orbital_Entry_Armed</p>
         </div>
      </div>

      {/* [BOTTOM] BRANDING CENTER */}
      <div className="absolute bottom-16 inset-x-0 flex flex-col items-center transition-all duration-1000" style={{ opacity: isExiting ? 0 : 1, transform: `translateY(${isExiting ? 20 : 0}px)` }}>
        <div className="w-64 h-[2px] bg-white/[0.05] mb-8 relative rounded-full">
           <div className="absolute left-0 top-0 h-full bg-brand-500 shadow-[0_0_15px_#0ea5e9]" style={{ width: `${progress * 100}%` }} />
        </div>
        <div className="flex flex-col items-center gap-3">
            <div className="w-16 h-16 rounded-2xl bg-slate-900/80 border border-white/10 flex items-center justify-center text-white font-black text-3xl shadow-2xl relative">
                S
                <div className="absolute -inset-1 border border-brand-500/20 rounded-2xl animate-pulse" />
            </div>
            <h1 className="text-3xl font-black text-white tracking-[0.5em] uppercase text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40">SiteANA</h1>
            <p className="text-[9px] text-brand-400 font-mono tracking-[5px] uppercase opacity-50">
               {tips[tipIndex]}
            </p>
        </div>
      </div>

      {/* OPTICAL EFFECTS */}
      <div className="absolute inset-0 bg-[radial-gradient(circle,transparent_20%,rgba(2,6,23,0.97)_100%)] pointer-events-none" />

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes spin-slow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}} />
    </div>
  );
};

export default LoadingScreen;
