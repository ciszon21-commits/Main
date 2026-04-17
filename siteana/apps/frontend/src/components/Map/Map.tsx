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

interface MapProps {
  onReady?: () => void;
  startIntro?: boolean;
}

const Map: React.FC<MapProps> = ({ onReady, startIntro }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const scaleControl = useRef<maplibregl.ScaleControl | null>(null);
  const hasLoadError = useRef(false);
  const { 
    hasHydrated,
    activeProjectId, 
    selectedStyle, 
    setSelectedStyle, 
    setMapRef, 
    bufferGeometry, 
    showSiteMarker, 
    siteMarkerText, 
    drawnGeometry, 
    isDrawingMode, 
    analysisResult 
  } = useStore();
  const paintState = useMapPaintStore();
  const prevStyleId = useRef<string>('ofm-liberty');
  const lastProjectFlewTo = useRef<string | null>(null);

  // --- Fly to Site when Project changes ---
  useEffect(() => {
    if (!map.current || !activeProjectId || !drawnGeometry) return;
    if (lastProjectFlewTo.current === activeProjectId) return;
    
    try {
      const centroid = turf.centroid(drawnGeometry as any);
      map.current.flyTo({
        center: centroid.geometry.coordinates as [number, number],
        zoom: 16,
        duration: 2500,
        essential: true
      });
      lastProjectFlewTo.current = activeProjectId;
    } catch(e) {
      console.warn('[SiteANA] FlyTo failed:', e);
    }
  }, [activeProjectId, drawnGeometry]);

  // --- Intro Sequence (Asia -> Taiwan -> Taipei) ---
  const hasPlayedIntro = useRef(false);
  useEffect(() => {
    if (startIntro && map.current && !hasPlayedIntro.current && !activeProjectId) {
      hasPlayedIntro.current = true;

      // Smooth zoom into North Taiwan (Taipei area)
      map.current.flyTo({
        center: [121.5, 25.05], // Centered on Taipei / New Taipei
        zoom: 10.5,             // Wider view to see whole metropolitan area
        pitch: 0, 
        duration: 5000,         // Match loading duration
        curve: 1.4,
        essential: true
      });
    }
  }, [startIntro, activeProjectId]);

  // --- Map Init ---
  useEffect(() => {
    // [HYDRATION GUARD] Wait until store is hydrated before initializing map instance
    const store = useStore.getState();
    if (map.current || !mapContainer.current || !store.hasHydrated) return;

    // Use current selectedStyle from store for initialization
    const { selectedStyle } = store;
    const initialStyleUrl = (typeof selectedStyle?.mapStyle === 'string') 
      ? selectedStyle.mapStyle 
      : INITIAL_STYLE_URL;

    // [STYLE CLEANING & PRE-INJECTION] 
    // We inject the preset BEFORE initialization to ensure zero-latency visual consistency
    let isCancelled = false;
    
    StyleInterceptor.fetchAndCleanStyle(initialStyleUrl).then(cleaned => {
      if (isCancelled) return;
      
      const currentPaint = useMapPaintStore.getState();
      const preInjected = MapPaintEngine.applyToStyleJSON(cleaned, currentPaint);

      const m = new maplibregl.Map({
        container: mapContainer.current!,
        style: preInjected,
        center: [121.0, 23.7], // Center on Taiwan, global view
        zoom: 4,               // Asia-wide view during loading
        pitch: 0,
        bearing: 0,
        antialias: true,
        attributionControl: false,
        preserveDrawingBuffer: true
      });

      map.current = m;
      setMapRef(m);
      (window as any).map = m; // Expose for App.tsx sync

      map.current.on('load', () => {
        const m = map.current!;
        console.log('[Map] load event fired. Initializing UI and injecting paint.');
        
        // Scale control setup - Move to bottom-left to avoid legend overlap
        if (scaleControl.current) {
          try { m.removeControl(scaleControl.current); } catch(e) {}
        }
        scaleControl.current = new maplibregl.ScaleControl({ maxWidth: 80, unit: 'metric' });
        m.addControl(scaleControl.current, 'bottom-left');

        m.once('error', () => {
          if (!hasLoadError.current) {
            hasLoadError.current = true;
            console.warn('[SiteANA] Initial style failed. Switching to OSM Raster fallback.');
            m.setStyle(OSM_RASTER_STYLE);
            const osmPreset = DEFAULT_STYLES.find(s => s.id === 'osm-raster');
            if (osmPreset) setSelectedStyle(osmPreset);
          }
        });

        // [PAINT + READY] Inject preset immediately and unblock loader.
        // applyAll has built-in retry if style isn't loaded yet.
        setTimeout(() => {
          const paintState = useMapPaintStore.getState();
          console.log('[Map] First paint injection. Preset:', paintState.activePresetId);
          MapPaintEngine.applyAll(m, paintState);
          
          // Unblock loader regardless of paint result — applyAll will retry internally
          console.log('[Map] Signalling readiness to unblock loader.');
          if (onReady) onReady();
        }, 250);

        // [FALLBACK] Second injection at 1.5s to guarantee visual consistency
        setTimeout(() => {
          if (!m.isStyleLoaded()) return;
          const paintState = useMapPaintStore.getState();
          console.log('[Map] Fallback paint injection. Preset:', paintState.activePresetId);
          MapPaintEngine.applyAll(m, paintState);

          // Sunlight
          const s = useStore.getState();
          if (s.sunlightEnabled) {
            MapPaintEngine.applySunlight(m, {
              enabled: s.sunlightEnabled,
              date:    s.sunlightDate,
              time:    s.sunlightTime,
              opacity: s.sunlightShadowOpacity,
            });
          }
        }, 1500);

        // [STYLE SWITCH] style.load is used only for subsequent basemap switches
        m.on('style.load', () => {
          console.log('[Map] style.load — re-applying paint for basemap switch.');
          setTimeout(() => {
            MapPaintEngine.applyAll(m, useMapPaintStore.getState());
            MapPaintEngine.refreshBuildingCache(m);
          }, 250);
        });
      });
    });

    return () => {
      isCancelled = true;
      if (scaleControl.current && map.current) {
        try { map.current.removeControl(scaleControl.current); } catch(e) {}
        scaleControl.current = null;
      }
      map.current?.remove();
      map.current = null;
      setMapRef(null);
      (window as any).map = null;
    };
  }, [hasHydrated]);

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

  // --- Paint Synchronizer (PERMANENT SYNC) ---
  // We use both an effect and a map event listener to guarantee 
  // that style overrides are applied whenever the map or store changes.
  useEffect(() => {
    const m = map.current;
    if (!m) return;

    // 1. Initial/Store change application
    const reapply = () => {
      if (m.isStyleLoaded()) {
        MapPaintEngine.applyAll(m, paintState);
      }
    };
    
    reapply();

    // 2. Map Style Switch listener: 
    // Triggers whenever setStyle() finishes or data changes
    const onStyleData = () => reapply();
    
    m.on('styledata', onStyleData);
    return () => { m.off('styledata', onStyleData); };
  }, [paintState]);

  // --- Sunlight & Shadows ---
  const sunEnabled = useStore(state => state.sunlightEnabled);
  const sunDate    = useStore(state => state.sunlightDate);
  const sunTime    = useStore(state => state.sunlightTime);
  const sunOpacity = useStore(state => state.sunlightShadowOpacity);

  const triggerSunlight = () => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    const s = useStore.getState();
    MapPaintEngine.applySunlight(map.current, {
      enabled: s.sunlightEnabled,
      date:    s.sunlightDate,
      time:    s.sunlightTime,
      opacity: s.sunlightShadowOpacity,
    });
  };

  useEffect(() => {
    if (sunEnabled && map.current) {
        MapPaintEngine.refreshBuildingCache(map.current);
    }
    triggerSunlight();
  }, [sunEnabled, sunDate, sunTime, sunOpacity]);

  // Handle View Settle (Idle)
  useEffect(() => {
    const m = map.current;
    if (!m) return;

    const onIdle = () => {
      if (!m.isStyleLoaded()) return;
      MapPaintEngine.refreshBuildingCache(m);
      const s = useStore.getState();
      if (s.sunlightEnabled) {
        triggerSunlight();
      }
    };

    m.on('idle', onIdle);
    return () => { m.off('idle', onIdle); };
  }, []); // Mount once


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
    const RANGE_SOURCE_ID = 'site-range-source';

    if (!showSiteMarker || !drawnGeometry) {
      ['site-marker-line', 'site-marker-label', 'range-300-line', 'range-500-line', 'range-800-line', 'range-label-300', 'range-label-500', 'range-label-800'].forEach(id => {
        if (m.getLayer(id)) m.removeLayer(id);
      });
      if (m.getSource(SOURCE_ID)) m.removeSource(SOURCE_ID);
      if (m.getSource(RANGE_SOURCE_ID)) m.removeSource(RANGE_SOURCE_ID);
      return;
    }

    try {
      const centroid = turf.centroid(drawnGeometry as any);
      
      // Data for Marker & Label
      const markerData: GeoJSON.FeatureCollection = {
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

      // Data for Range Circles (300, 500, 800m)
      const rangeCircles: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: [300, 500, 800].map(dist => ({
          type: 'Feature',
          geometry: turf.buffer(centroid, dist, { units: 'meters' }).geometry,
          id: `range-${dist}`,
          properties: { distance: dist, label: `${dist}m` }
        }))
      };

      // Update or Add Sources
      if (m.getSource(SOURCE_ID)) {
        (m.getSource(SOURCE_ID) as maplibregl.GeoJSONSource).setData(markerData as any);
      } else {
        m.addSource(SOURCE_ID, { type: 'geojson', data: markerData as any });
      }

      if (m.getSource(RANGE_SOURCE_ID)) {
        (m.getSource(RANGE_SOURCE_ID) as maplibregl.GeoJSONSource).setData(rangeCircles as any);
      } else {
        m.addSource(RANGE_SOURCE_ID, { type: 'geojson', data: rangeCircles as any });
      }
      
      // --- Range Circles Layers ---
      [300, 500, 800].forEach(dist => {
        const layerId = `range-${dist}-line`;
        if (!m.getLayer(layerId)) {
          m.addLayer({
            id: layerId,
            type: 'line',
            source: RANGE_SOURCE_ID,
            filter: ['==', ['id'], `range-${dist}`],
            paint: {
              'line-color': '#94a3b8',
              'line-width': 1.5,
              'line-dasharray': [2, 2],
              'line-opacity': 0.6
            }
          });
        }
        
        // Range Labels
        const labelId = `range-label-${dist}`;
        if (!m.getLayer(labelId)) {
          m.addLayer({
            id: labelId,
            type: 'symbol',
            source: RANGE_SOURCE_ID,
            filter: ['==', ['id'], `range-${dist}`],
            layout: {
              'text-field': ['get', 'label'],
              'text-font': ['Open Sans Regular', 'Noto Sans Regular', 'Roboto Regular', 'Arial Unicode MS Regular'],
              'text-size': 10,
              'symbol-placement': 'line',
              'text-offset': [0, -1],
              'text-allow-overlap': true
            },
            paint: {
              'text-color': '#64748b',
              'text-halo-color': '#ffffff',
              'text-halo-width': 1
            }
          });
        }
      });

      // --- Marker Layers ---
      if (!m.getLayer('site-marker-line')) {
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
      }

      if (!m.getLayer('site-marker-label')) {
        m.addLayer({
          id: 'site-marker-label',
          type: 'symbol',
          source: SOURCE_ID,
          filter: ['==', ['id'], 'site-label'],
          layout: {
            'text-field': siteMarkerText,
            'text-font': ['Open Sans Bold', 'Noto Sans Regular', 'Roboto Medium', 'Arial Unicode MS Regular'],
            'text-size': 16,
            'text-anchor': 'center',
            'text-allow-overlap': true,
            'text-ignore-placement': true
          },
          paint: {
            'text-color': '#ffffff',
            'text-halo-color': '#ef4444',
            'text-halo-width': 4,
            'text-halo-blur': 0.5
          }
        });
      } else {
        m.setLayoutProperty('site-marker-label', 'text-field', siteMarkerText);
      }

      // Always move label to top
      m.moveLayer('site-marker-label');
      
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
    // Synchronize the 3D buildings toggle with the tilt button
    useMapPaintStore.getState().setBuilding3D(targetPitch > 10);
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
