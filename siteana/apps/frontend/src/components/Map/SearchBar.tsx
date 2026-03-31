import React, { useState, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import { Search, MapPin, X, Loader2 } from 'lucide-react';

interface SearchResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type: string;
  addresstype: string;
}

interface SearchBarProps {
  mapRef: React.RefObject<maplibregl.Map | null>;
}

const SearchBar: React.FC<SearchBarProps> = ({ mapRef }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const search = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=6&addressdetails=1&accept-language=zh-TW,en`,
        { signal: AbortSignal.timeout(5000) }
      );
      if (!res.ok) throw new Error('Search failed');
      const data: SearchResult[] = await res.json();
      setResults(data);
      setIsOpen(true);
    } catch (e: any) {
      if (e?.name === 'TimeoutError') {
        setError('搜尋逾時，請確認網路連線。');
      } else {
        setError('搜尋服務暫時無法使用（可能受公司內網限制）。');
      }
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleInput = (v: string) => {
    setQuery(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(v), 600);
  };

  const handleSelect = (result: SearchResult) => {
    const map = mapRef.current;
    if (!map) return;

    const lng = parseFloat(result.lon);
    const lat = parseFloat(result.lat);

    markerRef.current?.remove();
    markerRef.current = new maplibregl.Marker({ color: '#f59e0b' })
      .setLngLat([lng, lat])
      .setPopup(new maplibregl.Popup({ offset: 25 }).setText(result.display_name))
      .addTo(map);

    map.flyTo({ center: [lng, lat], zoom: 16, duration: 1200, essential: true });

    setQuery(result.display_name.split(',')[0]);
    setIsOpen(false);
  };

  const clear = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setError(null);
    markerRef.current?.remove();
    markerRef.current = null;
  };

  return (
    <div className="relative w-full max-w-lg mx-auto">
      {/* Input */}
      <div className="relative flex items-center">
        <Search size={15} className="absolute left-3 text-slate-400 pointer-events-none z-10" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleInput(e.target.value)}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          placeholder="搜尋地址或地標 (Nominatim)..."
          className="w-full pl-9 pr-8 py-2 text-sm bg-white/95 backdrop-blur-md rounded-xl border border-slate-200 shadow-lg focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent transition-all placeholder-slate-400"
        />
        {(query || isLoading) && (
          <button
            onClick={clear}
            className="absolute right-2.5 text-slate-400 hover:text-slate-600 transition-colors"
          >
            {isLoading ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />}
          </button>
        )}
      </div>

      {/* Results Dropdown */}
      {isOpen && results.length > 0 && (
        <div className="absolute top-full mt-1.5 w-full bg-white/98 backdrop-blur-md rounded-xl shadow-xl border border-slate-100 z-50 overflow-hidden">
          {results.map((r) => (
            <button
              key={r.place_id}
              onClick={() => handleSelect(r)}
              className="w-full flex items-start gap-2.5 px-3 py-2.5 hover:bg-brand-50 transition-colors text-left group"
            >
              <MapPin size={14} className="text-brand-400 mt-0.5 flex-shrink-0 group-hover:text-brand-600" />
              <div className="min-w-0">
                <div className="text-xs font-medium text-slate-800 truncate">
                  {r.display_name.split(',')[0]}
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  {r.display_name.split(',').slice(1, 4).join(',')}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="absolute top-full mt-1.5 w-full bg-amber-50 border border-amber-200 rounded-xl px-3 py-2.5 text-[11px] text-amber-700 shadow-lg z-50">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
