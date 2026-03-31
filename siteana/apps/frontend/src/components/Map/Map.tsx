import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useStore, DEFAULT_STYLES } from '../../store/useStore';
import { useMapPaintStore } from '../../store/useMapPaintStore';
import { MapPaintEngine } from '../../engine/MapPaintEngine';
import NorthArrow from './NorthArrow';
import Legend from './Legend';
import SearchBar from './SearchBar';
import * as turf from '@turf/turf';

const INITIAL_STYLE = 'https://tiles.openfreemap.org/styles/liberty';

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
  const { selectedSite, selectedStyle, setSelectedStyle, setMapRef, bufferGeometry, showSiteMarker, siteMarkerText, drawnGeometry, isDrawingMode } = useStore();
  const paintState = useMapPaintStore();
  const prevStyleId = useRef<string>('ofm-liberty');

  // --- Map Init ---
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: INITIAL_STYLE,
      center: [121.5135, 25.042],
      zoom: 15,
      attributionControl: false,
      preserveDrawingBuffer: true,
    });

    // Scale control setup
    const scale = new maplibregl.ScaleControl({ maxWidth: 80, unit: 'metric' });
    map.current.addControl(scale, 'top-left');

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
      }
    });

    map.current.on('load', () => {
      console.log('[SiteANA] Map loaded.');
      setMapRef(map.current); // Expose map ref to store
      if (map.current) MapPaintEngine.applyAll(map.current, useMapPaintStore.getState());
    });

    return () => {
      map.current?.remove();
      map.current = null;
      setMapRef(null);
    };
  }, []);

  // --- Style Switch ---
  useEffect(() => {
    if (!map.current || !selectedStyle) return;
    if (prevStyleId.current === selectedStyle.id) return;
    prevStyleId.current = selectedStyle.id;
    map.current.setStyle(selectedStyle.mapStyle as any);
  }, [selectedStyle]);

  // --- Paint Overrides ---
  useEffect(() => {
    if (map.current && map.current.isStyleLoaded()) {
      MapPaintEngine.applyAll(map.current, paintState);
    }
  }, [paintState]);

  // --- Site Fly-to ---
  useEffect(() => {
    if (!map.current || !selectedSite) return;
    // TODO: flyTo when spatial data is available
  }, [selectedSite]);

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
            'text-field': ['get', 'label'],
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

  // --- 2D / 3D Toggle Controller ---
  const toggle3D = () => {
    if (!map.current) return;
    const next3D = !paintState.building3D;
    paintState.setBuildingStyles({ building3D: next3D });
    map.current.easeTo({ pitch: next3D ? 60 : 0, duration: 800 });
  };

  const zoomIn = () => map.current?.zoomIn({ duration: 200 });
  const zoomOut = () => map.current?.zoomOut({ duration: 200 });

  return (
    <div id="map-export-target" className="relative w-full h-full bg-slate-900">
      <div ref={mapContainer} className="absolute inset-0" />

      {/* --- TOP LEFT: Context Group --- */}
      <div className="absolute top-6 left-6 z-20 flex flex-col gap-3 pointer-events-none">
        <NorthArrow />
        {/* Scale Backdrop Integration via CSS hack to select maplibregl-ctrl-scale */}
        <div className="scale-control-wrapper ml-1">
          {/* Native scale control will be rendered here by maplibre */}
        </div>
      </div>

      {/* --- TOP CENTER: Search Group --- */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 w-96" data-html2canvas-ignore="true">
        <SearchBar mapRef={map} />
      </div>

      {/* --- BOTTOM RIGHT: Navigation & Legend Group --- */}
      <div className="absolute bottom-10 right-6 z-20 flex flex-col items-end gap-3">
        {/* Control Cluster (Zoom + 3D) */}
        <div className="flex flex-col gap-0 shadow-2xl rounded-2xl overflow-hidden border border-white/40 ring-1 ring-slate-900/5" data-html2canvas-ignore="true">
          <button
            onClick={toggle3D}
            title={paintState.building3D ? '切換2D' : '切換3D'}
            className={`w-11 h-11 flex flex-col items-center justify-center border-b border-white/20 transition-all ${
              paintState.building3D ? 'bg-brand-500 text-white' : 'bg-white/90 backdrop-blur text-slate-600 hover:bg-white'
            }`}
          >
            <span className="text-[10px] font-black leading-none">{paintState.building3D ? '2D' : '3D'}</span>
            <span className="text-[7px] leading-none mt-0.5 opacity-60 uppercase">{paintState.building3D ? 'Flat' : 'Tilt'}</span>
          </button>
          
          <button onClick={zoomIn} title="放大" className="w-11 h-11 flex items-center justify-center bg-white/90 backdrop-blur text-slate-600 hover:bg-white border-b border-white/20 text-xl font-light">
            +
          </button>
          
          <button onClick={zoomOut} title="縮小" className="w-11 h-11 flex items-center justify-center bg-white/90 backdrop-blur text-slate-600 hover:bg-white text-xl font-light">
            −
          </button>
        </div>

        {/* Legend Panel */}
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
