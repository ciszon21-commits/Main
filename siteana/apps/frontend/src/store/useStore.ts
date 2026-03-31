import { create } from 'zustand';

interface Project {
  id: number;
  name: string;
}

interface Site {
  id: number;
  name: string;
  projectId: number;
}

interface StylePreset {
  id: string;
  name: string;
  type: 'presentation' | 'report';
  mapStyle: string; // URL or JSON string
}

interface AppState {
  projects: Project[];
  setProjects: (projects: Project[]) => void;
  selectedProject: Project | null;
  setSelectedProject: (project: Project | null) => void;
  
  sites: Site[];
  setSites: (sites: Site[]) => void;
  selectedSite: Site | null;
  setSelectedSite: (site: Site | null) => void;

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
}

export const DEFAULT_STYLES: StylePreset[] = [
  { id: 'ofm-liberty', name: 'Liberty (Default)', type: 'report', mapStyle: 'https://tiles.openfreemap.org/styles/liberty' },
  { id: 'osm-raster', name: 'OSM Raster (Fallback)', type: 'report', mapStyle: {
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
      {
        id: 'osm-raster-layer',
        type: 'raster',
        source: 'osm-raster',
        minzoom: 0,
        maxzoom: 19
      }
    ]
  } as any },
  { id: 'ofm-bright', name: 'Bright Mode', type: 'presentation', mapStyle: 'https://tiles.openfreemap.org/styles/bright' },
  { id: 'minimal-dark', name: 'Minimal Dark', type: 'presentation', mapStyle: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json' },
  { id: 'blueprint', name: 'Blueprint Mode', type: 'presentation', mapStyle: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json' }
];

export const useStore = create<AppState>((set) => ({
  projects: [],
  setProjects: (projects) => set({ projects }),
  selectedProject: null,
  setSelectedProject: (selectedProject) => set({ selectedProject }),
  
  sites: [],
  setSites: (sites) => set({ sites }),
  selectedSite: null,
  setSelectedSite: (selectedSite) => set({ selectedSite }),

  stylePresets: DEFAULT_STYLES,
  selectedStyle: DEFAULT_STYLES[0],
  setSelectedStyle: (selectedStyle) => set({ selectedStyle }),

  selectedTemplate: 'report',
  setSelectedTemplate: (selectedTemplate) => set({ selectedTemplate }),

  themeColor: 'brand',
  setThemeColor: (themeColor) => set({ themeColor }),

  fontFamily: 'sans',
  setFontFamily: (fontFamily) => set({ fontFamily }),
}));
