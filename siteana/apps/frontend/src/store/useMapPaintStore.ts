import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface MapPaintState {
  // 🛣️ ROADS
  roadColors: {
    highway: string;       // 高速公路 motorway
    expressway: string;    // 快速道路 trunk
    primary: string;       // 省道/連外 primary
    secondary: string;     // 主要幹道 secondary
    residential: string;   // 市區道路 residential/tertiary
    path: string;          // 步道/人行道 path/footway
    transit_rail?: string; // 台鐵/高鐵
    transit_mrt?: string;  // 捷運/輕軌
    overpass?: string;     // 天橋/地下道/地下街 (pedestrian_flow 用)
    crossing?: string;     // 斑馬線/路口 (pedestrian_flow 用)
  };
  
  // 🏢 BUILDINGS
  buildingColor: string;       // 建築填色 (預設 #d4c9b0)
  buildingOutlineColor?: string; // 建築外框色
  buildingOpacity: number;     // 建築透明度 0-1
  building3D: boolean;         // 是否開啟 3D/陰影視覺感
  buildingVisibility: boolean; // 建築物顯示開關
  
  // 🌿 LAND USE
  landUseColors: {
    residential: string;  // 住宅 (預設 #f5e6c8)
    commercial: string;   // 商業 (預設 #f9d4a0)
    park: string;         // 公園 (預設 #b5d4a0)
    water: string;        // 水體 (預設 #aad3df)
    industrial: string;   // 工業 (預設 #eef1ec)
    parking?: string;     // 停車空間 (台灣標準: P字深藍)
    pedestrian?: string;  // 人行廣場 (台灣標準: 特殊鋪面包裝綠)
  };
  
  // 🔤 LABELS
  labelVisibility: {
    road: boolean;
    park: boolean;
    water: boolean;
    poi: boolean;
  };
  labelLanguage: 'zh-Hant' | 'en' | 'none';
  labelSizeEmoji: 'small' | 'medium' | 'large'; // 比例 0.8, 1, 1.2

  // ☁️ GLOBAL
  backgroundColor: string;
  globalBrightness: number; // 0.5 - 1.5
  
  // 🎨 THEME TRACKING
  activePresetId: string | null;

  // 💎 ACTIONS
  setRoadColor: (type: keyof MapPaintState['roadColors'], color: string) => void;
  setBuildingStyles: (styles: Partial<Pick<MapPaintState, 'buildingColor' | 'buildingOutlineColor' | 'buildingOpacity' | 'building3D' | 'buildingVisibility'>>) => void;
  setLandUseColor: (type: keyof MapPaintState['landUseColors'], color: string) => void;
  setLabelStyles: (styles: Partial<Pick<MapPaintState, 'labelVisibility' | 'labelLanguage' | 'labelSizeEmoji'>>) => void;
  resetToDefault: () => void;
  applyPreset: (presetId: string, preset: Partial<Omit<MapPaintState, 'setRoadColor' | 'setBuildingStyles' | 'setLandUseColor' | 'setLabelStyles' | 'resetToDefault' | 'applyPreset' | 'restoreState'>>) => void;
  restoreState: (snapshot: Partial<MapPaintState>) => void;
}

const DEFAULT_PAINT: Omit<MapPaintState, 'setRoadColor' | 'setBuildingStyles' | 'setLandUseColor' | 'setLabelStyles' | 'resetToDefault' | 'applyPreset' | 'restoreState'> = {
  roadColors: {
    highway:    '#f0c040',
    expressway: '#f4a261',
    primary:    '#ffd080',
    secondary:  '#ffffff',
    residential:'#f5f5f5',
    path:       '#d8d8d8',
  },
  buildingColor: '#d4c9b0',
  buildingOutlineColor: '#bdc3c7',
  buildingOpacity: 0.8,
  building3D: false,
  buildingVisibility: true,
  landUseColors: {
    residential: '#f5e6c8',
    commercial: '#f9d4a0',
    park: '#b5d4a0',
    water: '#aad3df',
    industrial: '#eef1ec',
    parking: '#d6ebd3', // Light green
    pedestrian: '#e0ebd3', // Light green
  },
  labelVisibility: {
    road: true,
    park: true,
    water: true,
    poi: true,
  },
  labelLanguage: 'zh-Hant',
  labelSizeEmoji: 'medium',
  backgroundColor: '#f8f4f0',
  globalBrightness: 1,
  activePresetId: null,
};

export const useMapPaintStore = create<MapPaintState>()(
  persist(
    (set) => ({
      ...DEFAULT_PAINT,

      setRoadColor: (type, color) => 
        set((state) => ({ roadColors: { ...state.roadColors, [type]: color } })),
        
      setBuildingStyles: (styles) => 
        set((state) => ({ ...state, ...styles })),

      setLandUseColor: (type, color) => 
        set((state) => ({ landUseColors: { ...state.landUseColors, [type]: color } })),

      setLabelStyles: (styles) => 
        set((state) => {
          if (styles.labelVisibility) {
            // merge labelVisibility carefully
            return {
              ...state,
              ...styles,
              labelVisibility: {
                ...state.labelVisibility,
                ...styles.labelVisibility as any
              }
            };
          }
          return { ...state, ...styles };
        }),

      resetToDefault: () => set(DEFAULT_PAINT),

      applyPreset: (presetId, preset) => set((state) => ({ ...state, ...preset, activePresetId: presetId })),
      
      restoreState: (snapshot: Partial<MapPaintState>) => set((state) => ({ ...state, ...snapshot })),
    }),
    {
      name: 'siteana-map-paint-storage',
    }
  )
);
