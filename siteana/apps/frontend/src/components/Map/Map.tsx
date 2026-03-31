import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useStore, DEFAULT_STYLES } from '../../store/useStore';
import { Plus, Minus } from 'lucide-react';
import NorthArrow from './NorthArrow';
import Legend from './Legend';

// 這個 URL 是從 LumaSite 驗證可用的地圖來源
const INITIAL_STYLE = 'https://tiles.openfreemap.org/styles/liberty';

// OSM Raster 備案 - 不依賴外部向量地圖服務
const OSM_RASTER_STYLE = {
  version: 8 as const,
  sources: {
    'osm': {
      type: 'raster' as const,
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors'
    }
  },
  layers: [{
    id: 'osm-tiles',
    type: 'raster' as const,
    source: 'osm',
    minzoom: 0,
    maxzoom: 19
  }]
};

const Map: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const hasLoadError = useRef(false);
  const { selectedSite, selectedStyle, setSelectedStyle } = useStore();
  const prevStyleId = useRef<string>('ofm-liberty');

  // --- 地圖初始化 ---
  // 關鍵：style 直接使用常數字串，不從 React state 讀取
  // 這樣才能確保不受 React rendering 時序影響
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: INITIAL_STYLE,
      center: [121.5135, 25.042],
      zoom: 15,
      attributionControl: false
    });

    map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
    map.current.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    // 增加比例尺 (Scale Bar)
    map.current.addControl(new maplibregl.ScaleControl({ maxWidth: 100, unit: 'metric' }), 'bottom-left');

    // 若初始向量地圖載入失敗，自動降級為 OSM Raster
    map.current.once('error', () => {
      if (!hasLoadError.current) {
        hasLoadError.current = true;
        console.warn('[SiteANA] Initial style failed. Switching to OSM Raster fallback.');
        map.current?.setStyle(OSM_RASTER_STYLE);
        // 同步更新 UI 狀態
        const osmPreset = DEFAULT_STYLES.find(s => s.id === 'osm-raster');
        if (osmPreset) setSelectedStyle(osmPreset);
      }
    });

    map.current.on('load', () => {
      console.log('[SiteANA] Map loaded successfully.');
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);  // 空陣列 - 只在 mount 時執行一次，不依賴任何 state

  // --- 樣式切換 ---
  // 僅在使用者主動切換樣式時才更新地圖
  useEffect(() => {
    if (!map.current || !selectedStyle) return;
    if (prevStyleId.current === selectedStyle.id) return;

    prevStyleId.current = selectedStyle.id;
    map.current.setStyle(selectedStyle.mapStyle as any);
  }, [selectedStyle]);

  // --- 基地選取 ---
  useEffect(() => {
    if (!map.current || !selectedSite) return;
    // TODO: flyTo site location when spatial data is available
  }, [selectedSite]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />

      {/* 地圖裝飾組件 */}
      <NorthArrow />
      <Legend />
    </div>
  );
};

export default Map;
