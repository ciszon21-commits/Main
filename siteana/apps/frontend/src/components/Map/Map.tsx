import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useStore } from '../../store/useStore';
import { Plus } from 'lucide-react';

const Map: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const { selectedSite, setSelectedSite } = useStore();

  useEffect(() => {
    if (map.current) return;
    if (!mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [121.5, 25.0],
      zoom: 12
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.current.on('click', (e) => {
      // 這裡未來會加入點擊地圖物件或選取基地的邏輯
      console.log('Map clicked at:', e.lngLat);
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  // 當選中基地時，在地圖上標示（範例邏輯）
  useEffect(() => {
    if (!map.current || !selectedSite) return;
    
    // 範例：移動到基地中心
    // map.current.flyTo({ center: [longitude, latitude], zoom: 16 });
  }, [selectedSite]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />
      {/* Map Overlay Controls */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2">
        <button className="p-3 bg-white rounded-full shadow-lg hover:bg-slate-50 transition-all text-slate-600">
          <Plus size={20} />
        </button>
      </div>
    </div>
  );
};

export default Map;
