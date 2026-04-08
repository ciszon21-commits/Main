import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useStore, DEFAULT_STYLES } from '../../store/useStore';
import { useMapPaintStore } from '../../store/useMapPaintStore';
import { MapPaintEngine } from '../../engine/MapPaintEngine';
import { StyleInterceptor } from '../../engine/StyleInterceptor';
import NorthArrow from './NorthArrow';
import Legend from './Legend';
import SearchBar from './SearchBar';
import { Compass, Plus, Minus, Navigation } from 'lucide-react';
import * as turf from '@turf/turf';

const INITIAL_STYLE_URL = 'https://tiles.openfreemap.org/styles/liberty';

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
  const { selectedStyle, setSelectedStyle, setMapRef, bufferGeometry, showSiteMarker, siteMarkerText, drawnGeometry, isDrawingMode, analysisResult } = useStore();
  const paintState = useMapPaintStore();
  const prevStyleId = useRef<string>('ofm-liberty');

  // --- Map Init ---
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    // 先透過 StyleInterceptor 清洗 Liberty 底圖，移除草地符號與填充紋理
    StyleInterceptor.fetchAndCleanStyle(INITIAL_STYLE_URL).then(cleanedStyle => {
      if (!mapContainer.current) return;

      map.current = new maplibregl.Map({
        container: mapContainer.current,
        style: cleanedStyle,
        center: [121.5135, 25.042],
        zoom: 15,
        attributionControl: false,
        preserveDrawingBuffer: true,
      });

    // Scale control setup
    const scale = new maplibregl.ScaleControl({ maxWidth: 80, unit: 'metric' });
    map.current.addControl(scale, 'bottom-right');

      map.current.once('error', () => {
        if (!hasLoadError.current) {
          hasLoadError.current = true;
          console.warn('[SiteANA] Initial style failed. Switching to OSM Raster fallback.');
          map.current?.setStyle(OSM_RASTER_STYLE);
          const osmPreset = DEFAULT_STYLES.find(s => s.id === 'osm-raster');
          if (osmPreset) setSelectedStyle(osmPreset);
        }
      });

      // Re-apply paint when style finishes loading
      map.current.on('style.load', () => {
        if (map.current) {
          MapPaintEngine.applyAll(map.current, useMapPaintStore.getState());
          // Re-apply sunlight layers (they're wiped on style change)
          const s = useStore.getState();
          if (s.sunlightEnabled) {
            MapPaintEngine.applySunlight(map.current, {
              enabled: s.sunlightEnabled,
              date: s.sunlightDate,
              time: s.sunlightTime,
              opacity: s.sunlightShadowOpacity
            });
          }
        }
      });

      map.current.on('load', () => {
        console.log('[SiteANA] Map loaded.');
        setMapRef(map.current); // Expose map ref to store
        if (map.current) MapPaintEngine.applyAll(map.current, useMapPaintStore.getState());
      });
    });

    return () => {
      map.current?.remove();
      map.current = null;
      setMapRef(null);
    };
  }, []);

  // --- Style Switch (透過 StyleInterceptor 清洗後再切換) ---
  useEffect(() => {
    if (!map.current || !selectedStyle) return;
    if (prevStyleId.current === selectedStyle.id) return;
    prevStyleId.current = selectedStyle.id;

    const styleTarget = selectedStyle.mapStyle;
    if (typeof styleTarget === 'string' && styleTarget.startsWith('http')) {
      // 向量底圖：先清洗再切換
      StyleInterceptor.fetchAndCleanStyle(styleTarget).then(cleaned => {
        map.current?.setStyle(cleaned as any);
      });
    } else {
      // 非向量（如 OSM Raster）：直接切換
      map.current.setStyle(styleTarget as any);
    }
  }, [selectedStyle]);

  // --- Paint Overrides ---
  useEffect(() => {
    if (map.current && map.current.isStyleLoaded()) {
      MapPaintEngine.applyAll(map.current, paintState);
    }
  }, [paintState]);

  // --- Sunlight & Shadows ---
  const sunEnabled = useStore(state => state.sunlightEnabled);
  const sunDate = useStore(state => state.sunlightDate);
  const sunTime = useStore(state => state.sunlightTime);
  const sunOpacity = useStore(state => state.sunlightShadowOpacity);

  useEffect(() => {
    const updateSunlight = () => {
      if (map.current && map.current.isStyleLoaded()) {
         MapPaintEngine.applySunlight(map.current, {
           enabled: sunEnabled, date: sunDate, time: sunTime, opacity: sunOpacity
         });
      }
    };

    updateSunlight(); // Initial call
    
    // During pan/zoom, the visible buildings change, so we must recalculate
    if (map.current && sunEnabled) {
       map.current.on('moveend', updateSunlight);
       map.current.on('zoomend', updateSunlight);
    }

    return () => {
       if (map.current) {
          map.current.off('moveend', updateSunlight);
          map.current.off('zoomend', updateSunlight);
       }
    };
  }, [sunEnabled, sunDate, sunTime, sunOpacity]);

  // --- Buffer Display ---
  useEffect(() => {
    const m = map.current;
    if (!m || !m.isStyleLoaded()) return;

    const SOURCE_ID = 'buffer-polygon';

    if (!bufferGeometry) {
      if (m.getLayer('buffer-fill')) m.removeLayer('buffer-fill');
      if (m.getLayer('buffer-line')) m.removeLayer('buffer-line');
      if (m.getSource(SOURCE_ID)) m.removeSource(SOURCE_ID);
      return;
    }

    if (m.getSource(SOURCE_ID)) {
      (m.getSource(SOURCE_ID) as maplibregl.GeoJSONSource).setData(bufferGeometry as any);
    } else {
      m.addSource(SOURCE_ID, { type: 'geojson', data: bufferGeometry as any });
      m.addLayer({ id: 'buffer-fill', type: 'fill', source: SOURCE_ID, paint: { 'fill-color': '#f59e0b', 'fill-opacity': 0.15 } });
      m.addLayer({ id: 'buffer-line', type: 'line', source: SOURCE_ID, paint: { 'line-color': '#f59e0b', 'line-width': 2, 'line-dasharray': [4, 2] } });
    }
  }, [bufferGeometry]);
  // --- Site Marker ---
  useEffect(() => {
    const m = map.current;
    if (!m || !m.isStyleLoaded()) return;

    const SOURCE_ID = 'site-marker-source';

    if (!showSiteMarker || !drawnGeometry) {
      if (m.getLayer('site-marker-line')) m.removeLayer('site-marker-line');
      if (m.getLayer('site-marker-label')) m.removeLayer('site-marker-label');
      if (m.getSource(SOURCE_ID)) m.removeSource(SOURCE_ID);
      return;
    }

    try {
      const centroid = turf.centroid(drawnGeometry as any);
      const data: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: [
          { 
            type: 'Feature',
            geometry: (drawnGeometry as any).geometry,
            id: 'site-boundary',
            properties: { isSite: true }
          },
          {
            type: 'Feature',
            geometry: centroid.geometry,
            id: 'site-label',
            properties: { label: siteMarkerText, isSiteLabel: true }
          }
        ]
      };

      if (m.getSource(SOURCE_ID)) {
        (m.getSource(SOURCE_ID) as maplibregl.GeoJSONSource).setData(data as any);
        // Force layout property update for immediate text reaction
        if (m.getLayer('site-marker-label')) {
          m.setLayoutProperty('site-marker-label', 'text-field', siteMarkerText);
        }
        m.triggerRepaint();
      } else {
        m.addSource(SOURCE_ID, { type: 'geojson', data: data as any });
        
        m.addLayer({
          id: 'site-marker-line',
          type: 'line',
          source: SOURCE_ID,
          filter: ['==', ['id'], 'site-boundary'],
          paint: {
            'line-color': '#ef4444',
            'line-width': 4,
            'line-dasharray': [1.5, 1],
            'line-opacity': 0.9
          }
        });

        m.addLayer({
          id: 'site-marker-label',
          type: 'symbol',
          source: SOURCE_ID,
          filter: ['==', ['id'], 'site-label'],
          layout: {
            'text-field': siteMarkerText, // Bind directly for safety instead of reading properties
            'text-font': ['Open Sans Regular', 'Arial Unicode MS Regular'],
            'text-size': 14,
            'text-anchor': 'center',
            'text-allow-overlap': true,
            'text-ignore-placement': true
          },
          paint: {
            'text-color': '#ffffff',
            'text-halo-color': '#ef4444',
            'text-halo-width': 3,
            'text-halo-blur': 0.5
          }
        });
      }
    } catch(e) {
      console.warn('[SiteANA] Site Marker error:', e);
    }
  }, [showSiteMarker, siteMarkerText, drawnGeometry]);

  const resetNorth = () => {
    if (!map.current) return;
    map.current.easeTo({ bearing: 0, duration: 800 });
  };

  const toggle3D = () => {
    if (!map.current) return;
    const currentPitch = map.current.getPitch();
    const targetPitch = currentPitch > 10 ? 0 : 60;
    map.current.easeTo({ pitch: targetPitch, duration: 800 });
  };

  // --- Zoom logic ---
  const zoomIn = () => map.current?.zoomIn({ duration: 200 });
  const zoomOut = () => map.current?.zoomOut({ duration: 200 });

  return (
    <div id="map-export-target" className="relative w-full h-full bg-slate-900 overflow-hidden">
      <div ref={mapContainer} className="absolute inset-0" />

      {/* --- TOP LEFT: DEPRECATED Context (Moved to legend) --- */}
      <div className="absolute top-6 left-6 z-20 flex flex-col gap-3 pointer-events-none">
        {/* NorthArrow moved to Legend */}
      </div>

      {/* --- TOP RIGHT: Map Controls (Moved from bottom right) --- */}
      <div className="absolute top-20 right-6 z-20 flex flex-col items-end gap-3" data-html2canvas-ignore="true">
        <div className="flex flex-col gap-0 shadow-2xl rounded-2xl overflow-hidden border border-white/40 ring-1 ring-slate-900/5">
          <button
            onClick={resetNorth}
            title="重設為正北"
            className="w-11 h-11 flex items-center justify-center bg-white/90 backdrop-blur text-brand-600 hover:bg-white border-b border-white/20 transition-all group"
          >
            <Compass size={20} className="-rotate-45 group-hover:rotate-0 transition-transform" />
          </button>

          <button
            onClick={toggle3D}
            title={'切換視角 (Tilt / Flat View)'}
            className={`w-11 h-11 flex flex-col items-center justify-center bg-white/90 backdrop-blur text-slate-600 hover:bg-white border-b border-white/20 transition-all font-bold`}
          >
            <span className="text-[10px] font-black leading-none">View</span>
            <span className="text-[7px] leading-none mt-0.5 opacity-60 uppercase">Tilt</span>
          </button>
          
          <button onClick={zoomIn} title="放大" className="w-11 h-11 flex items-center justify-center bg-white/90 backdrop-blur text-slate-600 hover:bg-white border-b border-white/20">
            <Plus size={20} />
          </button>
          
          <button onClick={zoomOut} title="縮小" className="w-11 h-11 flex items-center justify-center bg-white/90 backdrop-blur text-slate-600 hover:bg-white">
            <Minus size={20} />
          </button>
        </div>
      </div>

      {/* --- TOP CENTER: Search Group --- */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 w-96" data-html2canvas-ignore="true">
        <SearchBar mapRef={map} />
      </div>

      {/* --- BOTTOM LEFT: DELETED --- */}

      {/* --- BOTTOM RIGHT: Navigation & Legend Group --- */}
      <div className="absolute bottom-10 right-6 z-20 flex flex-col items-end gap-3">
        {/* Legend Panel (Integrated North Arrow) */}
        <Legend />
      </div>

      {/* --- FLOATING: Mode Status --- */}
      {isDrawingMode && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-30 pointer-events-none" data-html2canvas-ignore="true">
          <div className="bg-brand-500/95 backdrop-blur text-white text-[10px] font-black uppercase tracking-[0.2em] px-5 py-2.5 rounded-full shadow-2xl ring-4 ring-brand-500/20 flex items-center gap-3 animate-slide-up">
            <span className="w-2 h-2 rounded-full bg-white animate-ping" />
            Drawing Mode Active
          </div>
        </div>
      )}

      {/* Style overrides for native components */}
      <style>{`
        .maplibregl-ctrl-top-left {
          top: 100px !important;
          left: 24px !important;
          margin: 0 !important;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .maplibregl-ctrl-scale {
          background-color: rgba(255, 255, 255, 0.85) !important;
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.5) !important;
          border-radius: 8px !important;
          padding: 6px 10px !important;
          color: #0f172a !important;
          font-weight: 900 !important;
          font-size: 10px !important;
          text-transform: uppercase;
          pointer-events: auto;
          box-shadow: 0 4px 15px rgba(0,0,0,0.1);
          margin: 0 !important;
          line-height: 1;
        }
        .maplibregl-ctrl-bottom-right { margin: 0 10px 10px 0; }
      `}</style>
    </div>
  );
};

export default Map;
