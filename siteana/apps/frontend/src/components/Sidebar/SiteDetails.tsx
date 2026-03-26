import React from 'react';
import { useStore } from '../../store/useStore';
import { MapPin, Info, Ruler } from 'lucide-react';

const SiteDetails: React.FC = () => {
  const { selectedSite } = useStore();

  if (!selectedSite) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-6 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
        <MapPin size={32} className="text-slate-300 mb-3" />
        <p className="text-sm text-slate-500 font-medium whitespace-pre-wrap">Select a site on the map or from the list to see details.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-brand-100 flex items-center justify-center text-brand-600">
          <MapPin size={22} />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900 leading-tight">{selectedSite.name}</h3>
          <p className="text-xs text-slate-400 font-medium">Site ID: #{selectedSite.id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <Ruler size={16} className="text-brand-500" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Estimated Area</span>
          </div>
          <p className="text-xl font-bold text-slate-800">1,245 <span className="text-sm font-medium text-slate-400">m²</span></p>
        </div>

        <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
          <div className="flex items-center gap-2 mb-2">
            <Info size={16} className="text-brand-500" />
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Description</span>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">
            This is a sample site description. Visual analysis will be performed based on this boundary.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SiteDetails;
