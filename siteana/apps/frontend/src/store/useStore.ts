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
  category: 'Vector (向量可調)' | 'Raster (像素底圖)' | 'Historic (歷史圖繪)';
  supportsPresets: boolean;
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
  // --- Vector Tiles (Supports 3D, Style Overrides) ---
  { id: 'ofm-liberty', name: 'Liberty (圖紙)', type: 'report', category: 'Vector (向量可調)', supportsPresets: true, mapStyle: 'https://tiles.openfreemap.org/styles/liberty' },
  { id: 'carto-positron', name: 'Positron (極白)', type: 'report', category: 'Vector (向量可調)', supportsPresets: true, mapStyle: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json' },
  { id: 'carto-dark', name: 'Midnight (黑夜)', type: 'presentation', category: 'Vector (向量可調)', supportsPresets: true, mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json' },
  { id: 'carto-voyager', name: 'Voyager (文脈)', type: 'report', category: 'Vector (向量可調)', supportsPresets: true, mapStyle: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json' },
  { id: 'ofm-bright', name: 'Bright (亮彩)', type: 'presentation', category: 'Vector (向量可調)', supportsPresets: true, mapStyle: 'https://tiles.openfreemap.org/styles/bright' },

  // --- Raster Tiles (No Overrides) ---
  { id: 'esri-satellite', name: 'Hybrid (衛星地籍)', type: 'report', category: 'Raster (像素底圖)', supportsPresets: false, mapStyle: {
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
  { id: 'osm-terrain', name: 'Topography (高程)', type: 'report', category: 'Raster (像素底圖)', supportsPresets: false, mapStyle: {
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
  } as any },
  { id: 'nlsc-emap', name: 'Gov Map (國土測繪)', type: 'report', category: 'Raster (像素底圖)', supportsPresets: false, mapStyle: {
    version: 8,
    sources: {
      'nlsc': {
        type: 'raster',
        tiles: ['https://wmts.nlsc.gov.tw/wmts/EMAP/default/GoogleMapsCompatible/{z}/{x}/{y}'],
        tileSize: 256,
        attribution: '&copy; 內政部國土測繪中心'
      }
    },
    layers: [
      { id: 'nlsc-layer', type: 'raster', source: 'nlsc', minzoom: 0, maxzoom: 20 }
    ]
  } as any },
  
  // --- Historic Maps ---
  { id: 'historic-taiwan', name: '1904 台灣堡圖', type: 'report', category: 'Historic (歷史圖繪)', supportsPresets: false, mapStyle: {
    version: 8,
    sources: {
      'historic': {
        type: 'raster',
        tiles: ['https://gis.sinica.edu.tw/tileserver/file-exists.php?img=JM20K_1904-png-{z}-{x}-{y}'],
        tileSize: 256,
        attribution: '&copy; 中央研究院 GIS 中心'
      }
    },
    layers: [
      { id: 'historic-layer', type: 'raster', source: 'historic', minzoom: 0, maxzoom: 16 }
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
        Object.entries(state).filter(([key]) => !['mapRef', 'isExporting', 'isDrawingMode', 'stylePresets'].includes(key))
      ),
    }
  )
);
