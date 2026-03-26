import React from 'react';
import { Compass } from 'lucide-react';

const NorthArrow: React.FC = () => {
  return (
    <div className="absolute top-6 left-6 flex flex-col items-center gap-1 pointer-events-none group">
      <div className="w-10 h-10 rounded-full bg-white/80 backdrop-blur-sm border border-slate-200/50 shadow-lg flex items-center justify-center text-slate-900 transition-transform group-hover:scale-110">
        <Compass size={24} strokeWidth={1.5} className="text-brand-600" />
      </div>
      <span className="text-[10px] font-black text-slate-900 tracking-tighter bg-white/80 backdrop-blur-sm px-1.5 rounded border border-slate-200/20 shadow-sm">N</span>
    </div>
  );
};

export default NorthArrow;
