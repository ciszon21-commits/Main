import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type maplibregl from 'maplibre-gl';

interface GeoJSONFeature {
  type: 'Feature';
  geometry: { type: string; coordinates: any };
  properties: Record<string, any>;
}

interface AnalysisResult {
  area_m2: number;
  area_ping: number;
  perimeter_m: number;
  centroid: { lon: number; lat: number };
  bbox?: number[];
}

interface LocalProject {
  id: string;
  name: string;
  updatedAt: string;
  snapshot: any;
}

interface StylePreset {
  id: string;
  name: string;
  type: 'presentation' | 'report';
  mapStyle: string; // URL or JSON string
}

interface AppState {
  localProjects: LocalProject[];
  saveAsProject: (name: string) => void;
  loadProject: (id: string) => void;
  deleteProject: (id: string) => void;

  // Phase 4: Style System
  stylePresets: StylePreset[];
  selectedStyle: StylePreset | null;
  setSelectedStyle: (style: StylePreset | null) => void;

  // Phase 4: Templates & Themes
  selectedTemplate: 'presentation' | 'report' | 'a3-print' | 'a4-print';
  setSelectedTemplate: (template: 'presentation' | 'report' | 'a3-print' | 'a4-print') => void;
  
  themeColor: 'brand' | 'slate' | 'emerald';
  setThemeColor: (color: 'brand' | 'slate' | 'emerald') => void;

  fontFamily: 'sans' | 'serif' | 'mono';
  setFontFamily: (font: 'sans' | 'serif' | 'mono') => void;

  // Phase 5: Spatial Analysis
  drawnGeometry: GeoJSONFeature | null;
  setDrawnGeometry: (g: GeoJSONFeature | null) => void;
  bufferGeometry: GeoJSONFeature | null;
  setBufferGeometry: (g: GeoJSONFeature | null) => void;
  analysisResult: AnalysisResult | null;
  setAnalysisResult: (r: AnalysisResult | null) => void;

  // Phase 10: Site Marking
  showSiteMarker: boolean;
  setShowSiteMarker: (v: boolean) => void;
  siteMarkerText: string;
  setSiteMarkerText: (t: string) => void;

  // Phase 5: Export
  isExporting: boolean;
  setIsExporting: (v: boolean) => void;
  mapRef: maplibregl.Map | null;
  setMapRef: (m: maplibregl.Map | null) => void;

  // Phase 11: Export Options
  circularMask: boolean;
  setCircularMask: (v: boolean) => void;

  // Phase 11: Drawing Mode
  isDrawingMode: boolean;
  setIsDrawingMode: (v: boolean) => void;

  // Phase 8: Export Metadata
  exportTitle: string;
  setExportTitle: (t: string) => void;
  exportAuthor: string;
  setExportAuthor: (a: string) => void;
  showLegendInExport: boolean;
  setShowLegendInExport: (v: boolean) => void;
}

export const DEFAULT_STYLES: StylePreset[] = [
  { id: 'ofm-liberty', name: 'Liberty (標準彩色)', type: 'report', mapStyle: 'https://tiles.openfreemap.org/styles/liberty' },
  { id: 'carto-positron', name: 'Positron (淺色極簡)', type: 'report', mapStyle: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json' },
  { id: 'carto-dark', name: 'Dark Matter (極簡暗黑)', type: 'presentation', mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json' },
  { id: 'carto-voyager', name: 'Voyager (旅行者)', type: 'report', mapStyle: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json' },
  { id: 'ofm-bright', name: 'Bright (明亮彩色)', type: 'presentation', mapStyle: 'https://tiles.openfreemap.org/styles/bright' },
  { id: 'osm-taiwan', name: 'Taiwan OSM (台灣中文)', type: 'report', mapStyle: {
    version: 8,
    sources: {
      'osm-raster': {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap contributors'
      }
    },
    layers: [
      { id: 'osm-raster-layer', type: 'raster', source: 'osm-raster', minzoom: 0, maxzoom: 19 }
    ]
  } as any },
  { id: 'esri-satellite', name: 'Satellite (衛星影像)', type: 'report', mapStyle: {
    version: 8,
    sources: {
      'esri-satellite': {
        type: 'raster',
        tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
        tileSize: 256,
        attribution: 'Tiles &copy; Esri'
      }
    },
    layers: [
      { id: 'satellite-layer', type: 'raster', source: 'esri-satellite', minzoom: 0, maxzoom: 19 }
    ]
  } as any },
  { id: 'osm-terrain', name: 'Terrain (地形圖層)', type: 'report', mapStyle: {
    version: 8,
    sources: {
      'osm-topo': {
        type: 'raster',
        tiles: ['https://tile.opentopomap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '&copy; OpenTopoMap'
      }
    },
    layers: [
      { id: 'topo-layer', type: 'raster', source: 'osm-topo', minzoom: 0, maxzoom: 17 }
    ]
  } as any }
];

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
  localProjects: [],
  saveAsProject: (name: string) => {
    const state = get();
    // Snapshot the crucial geometry and analysis data
    const snapshot = {
      drawnGeometry: state.drawnGeometry,
      bufferGeometry: state.bufferGeometry,
      analysisResult: state.analysisResult,
      siteMarkerText: state.siteMarkerText,
      showSiteMarker: state.showSiteMarker,
      selectedStyle: state.selectedStyle,
      exportTitle: state.exportTitle,
      exportAuthor: state.exportAuthor
    };

    const newProject: LocalProject = {
      id: Date.now().toString(),
      name,
      updatedAt: new Date().toISOString(),
      snapshot
    };

    set({ localProjects: [newProject, ...state.localProjects] });
  },
  loadProject: (id: string) => {
    const state = get();
    const proj = state.localProjects.find(p => p.id === id);
    if (proj && proj.snapshot) {
      set({
        ...proj.snapshot,
      });
    }
  },
  deleteProject: (id: string) => {
    set(state => ({ localProjects: state.localProjects.filter(p => p.id !== id) }));
  },

  stylePresets: DEFAULT_STYLES,
  selectedStyle: DEFAULT_STYLES[0],
  setSelectedStyle: (selectedStyle) => set({ selectedStyle }),

  selectedTemplate: 'report',
  setSelectedTemplate: (selectedTemplate) => set({ selectedTemplate }),

  themeColor: 'brand',
  setThemeColor: (themeColor) => set({ themeColor }),

  fontFamily: 'sans',
  setFontFamily: (fontFamily) => set({ fontFamily }),

  drawnGeometry: null,
  setDrawnGeometry: (drawnGeometry) => set({ drawnGeometry }),
  bufferGeometry: null,
  setBufferGeometry: (bufferGeometry) => set({ bufferGeometry }),
  analysisResult: null,
  setAnalysisResult: (analysisResult) => set({ analysisResult }),

  showSiteMarker: false,
  setShowSiteMarker: (showSiteMarker) => set({ showSiteMarker }),
  siteMarkerText: 'SITE',
  setSiteMarkerText: (siteMarkerText) => set({ siteMarkerText }),

  isExporting: false,
  setIsExporting: (isExporting) => set({ isExporting }),
  mapRef: null,
  setMapRef: (mapRef) => set({ mapRef }),

  circularMask: false,
  setCircularMask: (circularMask) => set({ circularMask }),

  isDrawingMode: false,
  setIsDrawingMode: (isDrawingMode) => set({ isDrawingMode }),

  exportTitle: 'SiteANA 基地分析圖書',
  setExportTitle: (exportTitle) => set({ exportTitle }),
  exportAuthor: 'SiteANA Studio / Designer',
  setExportAuthor: (exportAuthor) => set({ exportAuthor }),
  showLegendInExport: true,
  setShowLegendInExport: (showLegendInExport) => set({ showLegendInExport }),
    }),
    {
      name: 'siteana-local-storage',
      partialize: (state) => Object.fromEntries(
        Object.entries(state).filter(([key]) => !['mapRef', 'isExporting', 'isDrawingMode'].includes(key))
      ),
    }
  )
);
