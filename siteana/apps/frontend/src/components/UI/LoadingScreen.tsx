import React, { useState, useEffect } from 'react';

interface LoadingScreenProps {
  onLoadingComplete?: () => void;
  isMapReady: boolean;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ onLoadingComplete, isMapReady }) => {
  const [isExiting, setIsExiting] = useState(false);
  const [tipIndex, setTipIndex] = useState(0);

  const tips = [
    "Initializing Spatial Engine...",
    "Syncing Urban Geometry...",
    "Loading OpenStreetMap Data...",
    "Calibrating Sunlight Vectors...",
    "Finalizing Visual Layers...",
    "Ready for Design Analysis"
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setTipIndex((prev) => (prev + 1) % tips.length);
    }, 1200);
    return () => clearInterval(interval);
  }, [tips.length]);

  const [altitude, setAltitude] = useState(20000);
  const [techLogs, setTechLogs] = useState<string[]>([]);
  
  const techSource = [
    "> Initialize Global Coordinate System (WGS84)...",
    "> Fetching North Taiwan Urban Fabric Data...",
    "> Establishing WebGL Geometric Shader Core...",
    "> Configuring SiteANA Analysis Presets...",
    "> LOCK_REGION: TAIWAN_STRAIT / TPE"
  ];

  useEffect(() => {
    let logIdx = 0;
    let charIdx = 0;
    let currentLogs: string[] = [];

    const typeTimer = setInterval(() => {
      if (logIdx < techSource.length) {
        const line = techSource[logIdx];
        if (charIdx === 0) {
          currentLogs.push("");
        }
        
        currentLogs[logIdx] = line.substring(0, charIdx + 1);
        setTechLogs([...currentLogs]);
        
        charIdx++;
        if (charIdx >= line.length) {
          logIdx++;
          charIdx = 0;
        }
      } else {
        clearInterval(typeTimer);
      }
    }, 40);

    return () => clearInterval(typeTimer);
  }, []);

  useEffect(() => {
    if (isMapReady) {
      // Small delay to ensure map tiles are partially visible behind
      const timer = setTimeout(() => {
        setIsExiting(true);
        
        // Altitude drop animation
        const altInterval = setInterval(() => {
          setAltitude((prev) => {
            const next = prev - (prev * 0.15); // exponentially decrease
            return next < 500 ? 500 : next;
          });
        }, 50);

        if (onLoadingComplete) {
          setTimeout(() => {
            clearInterval(altInterval);
            onLoadingComplete();
          }, 2000); // 2 seconds for the dramatic zoom
        }
      }, 2500); // Extended slightly to show more typewriter logs
      return () => clearTimeout(timer);
    }
  }, [isMapReady, onLoadingComplete]);

  return (
    <div className={`fixed inset-0 z-[100] bg-slate-900 flex flex-col items-center justify-center overflow-hidden pointer-events-none transition-opacity duration-1000 ${isExiting ? 'opacity-0' : 'opacity-100'}`}>
      
      {/* PLANETARY WARD ZOOM BACKGROUND */}
      <div 
        className="absolute inset-0 flex items-center justify-center pointer-events-none"
        style={{
          transition: 'transform 2s cubic-bezier(0.85, 0, 0.15, 1), filter 2s ease-in',
          transform: isExiting ? 'scale(50) translateZ(0)' : 'scale(1) translateZ(0)',
          filter: isExiting ? 'blur(4px)' : 'blur(0)',
        }}
      >
        {/* Outer Orbit Rings */}
        <div className="absolute w-[200vw] h-[200vw] md:w-[140vw] md:h-[140vw] border-[1px] border-slate-700/30 rounded-full animate-[spin_120s_linear_infinite]">
          <div className="absolute inset-0 border-[1px] border-brand-500/10 rounded-full rotate-45" />
          <div className="absolute inset-0 border-[1px] border-brand-500/10 rounded-full -rotate-45" />
        </div>
        
        <div className="absolute w-[160vw] h-[160vw] md:w-[110vw] md:h-[110vw] border-[1px] border-slate-700/50 rounded-full animate-[spin_80s_linear_infinite_reverse]">
          <div className="absolute inset-0 border-[1px] border-brand-500/5 rounded-full rotate-12" />
        </div>

        {/* Core Planet Sphere */}
        <div 
          className="relative w-[120vw] h-[120vw] md:w-[80vw] md:h-[80vw] rounded-full overflow-hidden shadow-[inset_-40px_-40px_80px_rgba(0,0,0,0.9)] animate-[spin_240s_linear_infinite]"
          style={{ background: 'radial-gradient(circle at 35% 35%, #1e293b, #0f172a 50%, #020617 90%)' }}
        >
          {/* Surface texture grid */}
          <div className="absolute inset-0 opacity-[0.15]" style={{ backgroundImage: 'linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)', backgroundSize: 'clamp(20px, 3vw, 40px) clamp(20px, 3vw, 40px)' }} />
          
          {/* Faux Atmospheric Glow */}
          <div className="absolute inset-0 rounded-full shadow-[inset_0_0_120px_rgba(var(--brand-500-rgb),0.2)] pointer-events-none" />
        </div>

        {/* Equatorial Grid */}
        <div className="absolute w-[120vw] h-[120vw] md:w-[80vw] md:h-[80vw] border-[1px] border-brand-500/20 rounded-full flex items-center justify-center">
           <div className="w-full h-[1px] bg-brand-500/20" />
           <div className="absolute w-[1px] h-full bg-brand-500/20" />
        </div>
      </div>

      {/* FOREGROUND HUD UI */}
      <div className="absolute inset-x-0 flex items-center justify-center pointer-events-none">
        <div 
          className="relative z-10 flex items-center gap-16"
          style={{
             transition: 'transform 1s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.8s ease',
             transform: isExiting ? 'scale(1.5) translateY(20px)' : 'scale(1) translateY(0)',
             opacity: isExiting ? 0 : 1,
          }}
        >
          {/* Tech Typewriter Area */}
          <div className="hidden lg:flex flex-col gap-2 min-w-[300px] text-left opacity-80">
            <div className="text-[10px] font-black text-brand-500 mb-2 border-b border-brand-500/30 pb-1 tracking-[0.2em] uppercase">System Initialization Logs</div>
            <div className="flex flex-col gap-1.5 font-mono text-[10px] text-slate-400">
              {techLogs.map((log, i) => (
                <div key={i} className="flex gap-2">
                   <span className={i === techLogs.length - 1 ? 'animate-pulse' : ''}>{log}</span>
                   {i === techLogs.length - 1 && log.length < (techSource[i]?.length || 0) && <span className="w-1.5 h-3 bg-brand-500 animate-pulse" />}
                </div>
              ))}
            </div>
          </div>

          {/* Core Logo Transition */}
          <div className="relative">
             <div className="w-24 h-24 rounded-2xl bg-brand-500 flex items-center justify-center text-white font-bold text-4xl shadow-[0_0_50px_rgba(var(--brand-500-rgb),0.3)] animate-pulse">
               S
             </div>
             {/* Progress Ring */}
             <div className="absolute -inset-4 border-2 border-slate-800 rounded-[2rem]" />
             <div className="absolute -inset-4 border-2 border-brand-500 rounded-[2rem] border-t-transparent animate-spin" />
          </div>

          {/* Stats Description */}
          <div className="hidden lg:flex flex-col gap-1 text-left">
            <h2 className="text-2xl font-black text-white tracking-[0.2em] uppercase">SiteANA</h2>
            <div className="h-6 flex flex-col overflow-hidden">
              <p className="text-brand-400 font-mono text-[10px] tracking-widest uppercase">
                 {tips[tipIndex]}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Decorative HUD Info (Corners) */}
      <div 
        className="absolute bottom-12 left-12 font-mono text-[9px] text-slate-500 space-y-1 hidden md:block transition-all duration-700"
        style={{ opacity: isExiting ? 0 : 0.6, transform: isExiting ? 'translateX(-20px)' : 'translateX(0)' }}
      >
        <p className="text-brand-400 animate-pulse">SYSTEM: SPATIAL_LOCK_ENGAGED</p>
        <p>TARGET: NORTH_TAIWAN_URBAN_FABRIC</p>
        <p>ENGINE: WEBGL_2.0_ENABLED</p>
      </div>

      <div 
        className="absolute bottom-12 right-12 font-mono text-[9px] text-slate-500 text-right space-y-1 hidden md:block transition-all duration-700"
        style={{ opacity: isExiting ? 0 : 0.6, transform: isExiting ? 'translateX(20px)' : 'translateX(0)' }}
      >
        <p>LAT: 25.0421 | LON: 121.5135</p>
        <p>COORD_SYS: WGS84 / EPSG:4326</p>
        <p className="text-white">ALTITUDE: {Math.round(altitude).toLocaleString()} M</p>
      </div>

      {/* Bottom Progress Bar */}
      <div className="absolute bottom-0 left-0 w-full h-1 bg-slate-800">
        <div className={`h-full bg-brand-500 transition-all duration-[2000ms] ${isMapReady ? 'w-full' : 'w-1/3 animate-pulse'}`} />
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}} />
    </div>
  );
};

export default LoadingScreen;
