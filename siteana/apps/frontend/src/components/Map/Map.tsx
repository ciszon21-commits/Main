import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useStore, DEFAULT_STYLES } from '../../store/useStore';
import { Plus } from 'lucide-react';
import NorthArrow from './NorthArrow';
import Legend from './Legend';

const Map: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const { selectedSite, selectedStyle } = useStore();

  useEffect(() => {
    if (map.current) return;
    if (!mapContainer.current) return;

    try {
      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: selectedStyle?.mapStyle || 'https://tiles.openfreemap.org/styles/liberty',
        center: [121.5135, 25.042],
        zoom: 15
      });

      map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

      map.current.on('error', (e) => {
        console.error('MapLibre error:', e);
        // 如果樣式載入失敗，且目前不是 OSM Raster，則自動切換到 OSM Raster 備案
        if (selectedStyle?.id !== 'osm-raster') {
          console.log('Switching to OSM Raster fallback due to error');
          const osmFallback = DEFAULT_STYLES.find(s => s.id === 'osm-raster');
          if (osmFallback) {
            map.current?.setStyle(osmFallback.mapStyle);
          }
        }
      });

      map.current.on('click', (e) => {
        console.log('Map clicked at:', e.lngLat);
      });
    } catch (err) {
      console.error('Failed to initialize map:', err);
    }

    return () => {
      map.current?.remove();
    };
  }, []);

  // Phase 4: Handle Style Switching
  const previousStyleId = useRef<string | undefined>(selectedStyle?.id);
  
  useEffect(() => {
    if (!map.current || !selectedStyle) return;
    if (previousStyleId.current === selectedStyle.id) return; // Skip initial mount
    
    previousStyleId.current = selectedStyle.id;
    
    if (map.current.isStyleLoaded()) {
      map.current.setStyle(selectedStyle.mapStyle);
    } else {
      map.current.once('load', () => {
        map.current?.setStyle(selectedStyle.mapStyle);
      });
    }
  }, [selectedStyle]);

  // 當選中基地時，在地圖上標示（範例邏輯）
  useEffect(() => {
    if (!map.current || !selectedSite) return;
    
    // 範例：移動到基地中心
    // map.current.flyTo({ center: [longitude, latitude], zoom: 16 });
  }, [selectedSite]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />
      
      {/* Map Decorations */}
      <NorthArrow />
      <Legend />
      
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
