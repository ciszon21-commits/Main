import maplibregl from 'maplibre-gl';
import { MapPaintState } from '../store/useMapPaintStore';
import { SunlightEngine } from './SunlightEngine';

export interface SunlightState {
  enabled: boolean;
  date: string;
  time: number;
  opacity: number;
}

export class MapPaintEngine {
  /**
   * 套用所有儲存的視覺設定到地圖實例
   */
  static applyAll(map: maplibregl.Map, state: MapPaintState) {
    if (!map.isStyleLoaded()) return;

    console.log('[MapPaintEngine] Applying all visual overrides...');
    this.applyRoads(map, state);
    this.applyBuildings(map, state);
    this.applyLandUse(map, state);
    this.applyLabels(map, state);
    this.applyEnvironment(map, state);
  }

  /**
   * 道路顏色控制 — 全面重構版
   * - 新增 expressway (快速道路/trunk) 獨立分類
   * - pedestrian_flow: 天橋/地下道(overpass)紫色，斑馬線(crossing)黃色
   * - 強制 line-opacity: 1.0 確保 Preset 顏色蓋過底圖 expression
   * - Z-index: path→residential→secondary→expressway→highway（所有道路在 fill 之上、symbol 之下）
   */
  static applyRoads(map: maplibregl.Map, state: MapPaintState) {
    const { roadColors } = state;
    const preset = state.activePresetId || '';

    // ── Layer keyword mappings ───────────────────────────────────────────────
    // ORDER MATTERS: more specific entries first (overpass before path)
    const mappings: Record<string, string[]> = {
      highway:    ['motorway', 'road_motorway'],
      expressway: ['trunk', 'expressway', 'freeway', 'road_trunk'],
      primary:    ['primary', 'major_road', 'road_primary'],
      secondary:  ['secondary', 'medium_road', 'road_secondary'],
      residential:['residential', 'tertiary', 'minor_road', 'street', 'road_tertiary', 'road_major_residential', 'road_minor', 'road_street'],
      path:       ['footway', 'cycleway', 'track', 'service', 'road_service', 'road_path', 'road_pedestrian'],
      overpass:   ['bridge_foot', 'pedestrian_bridge', 'steps', 'escalator', 'tunnel_foot'],
      crossing:   ['crossing', 'zebra'],
      transit_rail: ['rail', 'railway', 'roads-rail', 'transportation-rail', 'major_rail', 'bridge_major_rail', 'tunnel_major_rail'],
      transit_mrt:  ['subway', 'tram', 'transit', 'light_rail', 'busway'],
    };

    const layers = map.getStyle()?.layers || [];
    const firstLabel   = layers.find(l => l.type === 'symbol');
    const firstFill    = layers.find(l => l.type === 'fill' || l.type === 'background');

    // ── Line width table by road type ────────────────────────────────────────
    const widthTable: Record<string, [number, number, number]> = {
      // type:         [zoom12, zoom16, zoom19]
      highway:     [3.0, 10, 22],
      expressway:  [2.0,  8, 18],
      primary:     [1.5,  6, 14],
      secondary:   [1.0,  4,  9],
      residential: [0.5,  2.5, 6],
      path:        [0.2,  1.5, 4],
      overpass:    [0.5,  2,   5],
      crossing:    [0.3,  1.5, 4],
    };

    // ── Apply each category ──────────────────────────────────────────────────
    Object.entries(mappings).forEach(([type, keywords]) => {
      const color = (roadColors as any)[type];

      const targetIds = layers.filter(l =>
        l.type === 'line' &&
        keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetIds.forEach(id => {
        try {
          // ── TRANSIT special handling ──────────────────────────────────────
          if (type === 'transit_rail' || type === 'transit_mrt') {
            if (preset === 'transit_network') {
              map.setLayoutProperty(id, 'visibility', 'visible');
              map.setPaintProperty(id, 'line-opacity', 1.0);

              if (type === 'transit_rail') {
                map.setPaintProperty(id, 'line-width', ['interpolate', ['linear'], ['zoom'], 12, 2, 16, 4, 19, 6]);
                map.setPaintProperty(id, 'line-color', [
                  'case',
                  ['>=', ['index-of', '高鐵', ['coalesce', ['get', 'name:zh'], ['get', 'name'], '']], 0], '#ea580c',
                  ['>=', ['index-of', 'THSR', ['coalesce', ['get', 'network'], ['get', 'ref'], '']], 0], '#ea580c',
                  '#374151' // TRA gray
                ]);
              } else {
                map.setPaintProperty(id, 'line-width', ['interpolate', ['linear'], ['zoom'], 12, 2.5, 16, 5, 19, 8]);
                const nameF = ['coalesce', ['get', 'name:zh'], ['get', 'name'], ''];
                const refF  = ['coalesce', ['get', 'ref'], ''];
                map.setPaintProperty(id, 'line-color', [
                  'case',
                  ['>=', ['index-of', '紅', nameF], 0], '#e3002c',
                  ['>=', ['index-of', 'R',   refF], 0], '#e3002c',
                  ['>=', ['index-of', '藍', nameF], 0], '#0070bd',
                  ['>=', ['index-of', 'BL',  refF], 0], '#0070bd',
                  ['>=', ['index-of', '綠', nameF], 0], '#008659',
                  ['>=', ['index-of', 'G',   refF], 0], '#008659',
                  ['>=', ['index-of', '橘', nameF], 0], '#f39800',
                  ['>=', ['index-of', 'O',   refF], 0], '#f39800',
                  ['>=', ['index-of', '黃', nameF], 0], '#fddb00',
                  ['>=', ['index-of', 'Y',   refF], 0], '#fddb00',
                  ['>=', ['index-of', '棕', nameF], 0], '#c48c31',
                  ['>=', ['index-of', 'BR',  refF], 0], '#c48c31',
                  ['>=', ['index-of', '機', nameF], 0], '#834e98',
                  ['>=', ['index-of', 'A',   refF], 0], '#834e98',
                  color || '#9ca3af'
                ]);
              }
              // Transit lines should display inside minzoom 11 only
              map.setLayerZoomRange(id, 11, 24);
              map.moveLayer(id); // push to top
            } else {
              // Non-transit preset: hide transit lines completely
              map.setLayoutProperty(id, 'visibility', 'none');
            }
            return;
          }

          // ── No color defined → hide/reset ────────────────────────────────
          if (!color) {
            map.setLayoutProperty(id, 'visibility', 'none');
            return;
          }

          // ── Pedestrian Flow special handling ─────────────────────────────
          const isPedPreset = preset === 'pedestrian_flow';

          if (isPedPreset) {
            if (type === 'overpass') {
              // 天橋/地下道 — 紫色，強調顯示
              map.setLayoutProperty(id, 'visibility', 'visible');
              map.setPaintProperty(id, 'line-color', roadColors.overpass || '#a855f7');
              map.setPaintProperty(id, 'line-opacity', 1.0);
              map.setPaintProperty(id, 'line-width', ['interpolate', ['linear'], ['zoom'], 13, 1, 16, 3, 19, 7]);
              return;
            } else if (type === 'crossing') {
              // 斑馬線 — 亮黃
              map.setLayoutProperty(id, 'visibility', 'visible');
              map.setPaintProperty(id, 'line-color', roadColors.crossing || '#facc15');
              map.setPaintProperty(id, 'line-opacity', 1.0);
              map.setPaintProperty(id, 'line-width', ['interpolate', ['linear'], ['zoom'], 14, 0.5, 17, 2, 19, 4]);
              return;
            } else if (type === 'path') {
              // 人行道 — 橘黃色，比平常更粗
              map.setLayoutProperty(id, 'visibility', 'visible');
              map.setPaintProperty(id, 'line-color', roadColors.path || '#f97316');
              map.setPaintProperty(id, 'line-opacity', 1.0);
              map.setPaintProperty(id, 'line-width', ['interpolate', ['linear'], ['zoom'], 13, 1, 16, 4, 19, 10]);
              return;
            }
          }

          // ── Analysis presets: hide link/minor clutter ─────────────────────
          const isAnalysisPreset = ['urban_density', 'figure_ground', 'architectural_line', 'architectural_grey'].includes(preset);
          const isMinorClutter   = id.includes('casing') || id.includes('hatching') || id.includes('link');
          if (isAnalysisPreset && isMinorClutter) {
            map.setLayoutProperty(id, 'visibility', 'none');
            return;
          }

          // ── Standard road styling ─────────────────────────────────────────
          map.setLayoutProperty(id, 'visibility', 'visible');

          // CRITICAL (Problem 3): Force opacity=1 to override basemap zoom expressions
          map.setPaintProperty(id, 'line-opacity', 1.0);
          map.setPaintProperty(id, 'line-color', color);
          try { map.setPaintProperty(id, 'line-gap-width', 0); } catch(e) {}

          // Width table
          const [wMin, wMid, wMax] = widthTable[type] || [0.5, 2, 5];
          map.setPaintProperty(id, 'line-width', [
            'interpolate', ['linear'], ['zoom'],
            12, wMin,
            16, wMid,
            19, wMax
          ]);

        } catch (e) {}
      });
    });

    // ── Z-INDEX RESTACKING ───────────────────────────────────────────────────
    // Order: path → residential → secondary → primary → expressway → highway
    // All roads must sit ABOVE fills (land use) and BELOW symbols (labels)
    const zOrder = ['path', 'crossing', 'overpass', 'residential', 'secondary', 'primary', 'expressway', 'highway'];
    zOrder.forEach(type => {
      const keywords = mappings[type];
      const ids = layers.filter(l =>
        l.type === 'line' && keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      ids.forEach(id => {
        try {
          // Insert before first symbol to stay under labels
          if (firstLabel) map.moveLayer(id, firstLabel.id);
          else map.moveLayer(id);
        } catch(e) {}
      });
    });

    // Transit (if active) goes above roads but below labels
    if (preset === 'transit_network') {
      const transitIds = layers.filter(l =>
        l.type === 'line' && (
          mappings.transit_rail.some(k => l.id.toLowerCase().includes(k)) ||
          mappings.transit_mrt.some(k  => l.id.toLowerCase().includes(k))
        )
      ).map(l => l.id);

      transitIds.forEach(id => {
        try { map.moveLayer(id); } catch(e) {}
      });

      // Station fills (platform/station areas) pushed above transit lines
      const stationFills = layers.filter(l =>
        l.type === 'fill' && (
          l.id.toLowerCase().includes('station') ||
          l.id.toLowerCase().includes('platform') ||
          l.id.toLowerCase().includes('transit_stop')
        )
      ).map(l => l.id);
      stationFills.forEach(id => {
        try {
          map.setPaintProperty(id, 'fill-color', '#ffffff');
          map.setPaintProperty(id, 'fill-opacity', 1.0);
          map.moveLayer(id); // push station above transit lines
        } catch(e) {}
      });
    }

    // ── Ecological Texture: waterway line coloring ───────────────────────────
    // (Problem 4) waterway/stream/drain are LINE layers — applyLandUse misses them
    if (preset === 'ecological_texture') {
      const waterLineIds = layers.filter(l =>
        l.type === 'line' && (
          l.id.toLowerCase().includes('waterway') ||
          l.id.toLowerCase().includes('stream') ||
          l.id.toLowerCase().includes('drain') ||
          l.id.toLowerCase().includes('ditch') ||
          l.id.toLowerCase().includes('canal')
        )
      ).map(l => l.id);

      waterLineIds.forEach(id => {
        try {
          const isSmall = id.includes('stream') || id.includes('drain') || id.includes('ditch');
          map.setLayoutProperty(id, 'visibility', 'visible');
          map.setPaintProperty(id, 'line-color', isSmall ? '#93c5fd' : '#3b82f6');
          map.setPaintProperty(id, 'line-opacity', 1.0);
          map.setPaintProperty(id, 'line-width', [
            'interpolate', ['linear'], ['zoom'],
            12, isSmall ? 0.5 : 1.5,
            16, isSmall ? 2 : 4,
            19, isSmall ? 4 : 8,
          ]);
        } catch(e) {}
      });
    }
  }

  /**
   * 建築物與 3D 視覺
   */
  static applyBuildings(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    // RELAXED FILTER: Find all layers that look like buildings
    const buildingLayers = layers.filter(l => 
      (l.id.toLowerCase().includes('building') || l.id.toLowerCase().includes('structure') || l.id.toLowerCase().includes('architecture')) && 
      (l.type === 'fill' || l.type === 'fill-extrusion')
    ).map(l => ({ id: l.id, type: l.type, source: (l as any).source, sourceLayer: (l as any)['source-layer'] }));

    // --- Dynamic 3D Injection for styles that only have 2D building layers (like Carto) ---
    if (state.building3D) {
      const hasExtrusion = buildingLayers.some(l => l.type === 'fill-extrusion');
      if (!hasExtrusion) {
        // Try to inject based on source layer info
        const baseLayer = buildingLayers.find(l => l.type === 'fill');
        if (baseLayer && baseLayer.source && baseLayer.sourceLayer) {
           const INJECTED_ID = `injected-3d-${baseLayer.id}`;
           if (!map.getLayer(INJECTED_ID)) {
              console.log('[MapPaintEngine] Injecting 3D building layer:', INJECTED_ID);
              // Move it above the 2D fill but before labels
              const firstLabel = layers.find(l => l.type === 'symbol');
              map.addLayer({
                id: INJECTED_ID,
                type: 'fill-extrusion',
                source: baseLayer.source,
                'source-layer': baseLayer.sourceLayer,
              }, firstLabel?.id);
           }
           // Add to our list to be styled below
           buildingLayers.push({ id: INJECTED_ID, type: 'fill-extrusion', source: baseLayer.source, sourceLayer: baseLayer.sourceLayer });
        }
      }
    }

    // --- Robust Outline Logic (Fixes Arch Line/Gray Issues) ---
    const OUTLINE_LAYER = 'injected-building-outline';
    if (!state.building3D && state.buildingOutlineColor && state.buildingVisibility) {
       const baseLayer = buildingLayers.find(l => l.type === 'fill');
       if (baseLayer) {
         if (!map.getLayer(OUTLINE_LAYER)) {
           map.addLayer({
              id: OUTLINE_LAYER,
              type: 'line',
              source: baseLayer.source,
              'source-layer': baseLayer.sourceLayer,
              paint: {
                'line-color': state.buildingOutlineColor,
                'line-width': ['interpolate', ['linear'], ['zoom'], 15, 0.5, 18, 2]
              }
           });
         }
         // Zoom-dependent visibility for line presets (Fixes issue #3 and #4)
         map.setPaintProperty(OUTLINE_LAYER, 'line-opacity', [
            'interpolate', ['linear'], ['zoom'],
            13, state.activePresetId === 'architectural_grey' ? 0.0 : 0.8, // Hide gray outlines when zoomed out
            15, 1.0
         ]);
         map.setPaintProperty(OUTLINE_LAYER, 'line-color', state.buildingOutlineColor);
       }
    } else {
       if (map.getLayer(OUTLINE_LAYER)) try { map.removeLayer(OUTLINE_LAYER); } catch(e) {}
    }

    // 依據樓層設定漸層色 (低層: 淺灰, 中層: 橘色, 高層: 深紅)
    const gradientExpression = [
      'interpolate', ['linear'], ['get', 'render_height'],
      0, '#e2e8f0',   // 平房/低矮 (0m)
      15, '#fcd34d',  // 低層 (5樓左右, ~15m)
      36, '#f97316',  // 中層 (12樓左右, ~36m)
      80, '#b91c1c'   // 高層 (25樓以上, 80m+)
    ];

    const isGradient = state.activePresetId === 'urban_density';
    const colorProp = isGradient ? gradientExpression : state.buildingColor;

    buildingLayers.forEach(l => {
      const { id, type } = l;
      try {
        // --- Visibility ---
        map.setLayoutProperty(id, 'visibility', state.buildingVisibility ? 'visible' : 'none');
        if (!state.buildingVisibility) return;

        if (type === 'fill') {
          map.setPaintProperty(id, 'fill-color', colorProp);
          map.setPaintProperty(id, 'fill-opacity', state.buildingOpacity);
          // If we have our injected line layer, hide the native fuzzy outline
          map.setPaintProperty(id, 'fill-outline-color', 'rgba(0,0,0,0)');
        } else if (type === 'fill-extrusion') {
          const extrusionOpacity = isGradient ? [
            'interpolate', ['linear'], ['zoom'],
            12, 0.2, 15, state.buildingOpacity
          ] : state.buildingOpacity;

          if (!state.building3D) {
             map.setPaintProperty(id, 'fill-extrusion-height', 0);
             map.setPaintProperty(id, 'fill-extrusion-base', 0);
             map.setPaintProperty(id, 'fill-extrusion-opacity', extrusionOpacity); 
             map.setPaintProperty(id, 'fill-extrusion-color', colorProp);
          } else {
             map.setPaintProperty(id, 'fill-extrusion-color', colorProp);
             map.setPaintProperty(id, 'fill-extrusion-opacity', extrusionOpacity);
             map.setPaintProperty(id, 'fill-extrusion-height', [
               'coalesce', ['get', 'render_height'], ['get', 'height'], 10
             ]);
             map.setPaintProperty(id, 'fill-extrusion-base', [
               'coalesce', ['get', 'render_min_height'], ['get', 'min_height'], 0
             ]);
          }
        }
      } catch (e) {}
    });
  }

  /**
   * 土地利用分區
   */
  static applyLandUse(map: maplibregl.Map, state: MapPaintState) {
    const { landUseColors } = state;
    const layers = map.getStyle()?.layers || [];

    const apply = (keywords: string[], color: string) => {
      if (!color) return;
      const targetLayers = layers.filter(l =>
        l.type === 'fill' &&
        keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetLayers.forEach(id => {
        try {
          // Problem 3: ALWAYS force fill-color and fill-opacity=1.0 to override
          // basemap's native zoom-based expressions. This ensures Presets fully dominate.
          map.setPaintProperty(id, 'fill-color', color);
          map.setPaintProperty(id, 'fill-opacity', 1.0);
          // Remove native fill-patterns to prevent black fallback rendering
          try { map.setPaintProperty(id, 'fill-pattern', undefined); } catch(e) {}
        } catch (e) {}
      });
    };

    apply(
      ['park', 'garden', 'recreation', 'leisure', 'green', 'grass', 'forest', 'wood',
       'landcover', 'landuse_park', 'landuse_grass', 'natural', 'wetland', 'scrub',
       'allotment', 'orchard', 'vineyard', 'cemetery', 'pitch', 'area_park', 'area_grass', 'golf', 'meadow'],
      landUseColors.park
    );
    apply(['water', 'river', 'lake', 'stream', 'ocean', 'sea', 'canal', 'waterway', 'basin'], landUseColors.water);
    
    // Aggressively capture all plaza/pedestrian areas to kill black patterns
    // Also captures bridges and piers to fix yellow line artifacts (Problem 5)
    apply(['parking', 'area_parking', 'landuse_parking'], landUseColors.parking || landUseColors.residential);
    apply(['square', 'plaza', 'pedestrian', 'footway_area', 'path_area', 'area_pedestrian', 'landuse_pedestrian', 'monument', 'bridge', 'pier', 'transportation'], landUseColors.pedestrian || landUseColors.residential);

    apply(
      ['residential', 'neighborhood', 'urban', 'landuse_residential', 'school', 'hospital', 'aeroway', 'building-area'], 
      landUseColors.residential
    );
    apply(['commercial', 'retail', 'business', 'office', 'landuse_commercial'], landUseColors.commercial);
    apply(['industrial', 'quarry', 'factory', 'landuse_industrial'], landUseColors.industrial);
  }

  /**
   * 標籤文字 (Categorized toggle)
   */
  static applyLabels(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    
    // Categorize keywords to match layer IDs to the 4 categories
    const labelMapping = {
      road: ['road-label', 'highway-name', 'street', 'shield'],
      park: ['park', 'garden', 'recreation', 'square', 'memorial'],
      water: ['water', 'stream', 'ocean', 'sea', 'lake'],
      poi: ['poi', 'place', 'railway', 'airport', 'hospital', 'school', 'station', 'transit', 'label', 'name'] // fallback for all other symbols
    };

    const targetLayers = layers.filter(l => l.type === 'symbol');
    
    targetLayers.forEach(layer => {
      const id = layer.id.toLowerCase();
      
      // Determine which category this layer belongs to
      let category: keyof typeof state.labelVisibility = 'poi'; // default to poi if unmatched
      if (labelMapping.road.some(k => id.includes(k))) category = 'road';
      else if (labelMapping.park.some(k => id.includes(k))) category = 'park';
      else if (labelMapping.water.some(k => id.includes(k))) category = 'water';
      
      const isVisible = state.labelVisibility[category];

      try {
        // Completely remove bus station markers by universally filtering out 'bus' class and 'bus_stop' subclass
        if (layer.id.includes('poi') || layer.id.includes('transit')) {
           try {
             // We inject a filter dynamically
             const currentFilter = map.getFilter(layer.id) || ['has', '$type'];
             // Avoid infinitely wrapping filters if already applied
             if (JSON.stringify(currentFilter).indexOf('bus_stop') === -1) {
                map.setFilter(layer.id, [
                  'all', 
                  currentFilter, 
                  ['!=', ['get', 'subclass'], 'bus_stop'],
                  ['!=', ['get', 'class'], 'bus']
                ] as any);
             }
           } catch(e) {}
        }
        
        // Fix for Issue #9: Keep labels visible longer when zooming out
        map.setLayerZoomRange(layer.id, 0, 24); 
        
        map.setLayoutProperty(layer.id, 'visibility', isVisible ? 'visible' : 'none');
      } catch (e) {}
    });
  }

  /**
   * 全局環境 (背景色)
   */
  static applyEnvironment(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    
    // 尋找背景圖層
    const bgLayers = layers.filter(l => l.type === 'background' || l.id === 'background').map(l => l.id);
    bgLayers.forEach(id => {
      try {
        map.setPaintProperty(id, 'background-color', state.backgroundColor);
      } catch (e) {}
    });
  }

  // ── Building geometry cache ────────────────────────────────────────────────
  // Populated by refreshBuildingCache() when the map idles.
  // applySunlight() reads from this cache for smooth, flicker-free animation.
  private static _buildingCache: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>[] = [];

  /**
   * Scan the current viewport for building features and store them in cache.
   * Call this on map 'idle' (after pan/zoom settles), NOT on every time-slider tick.
   */
  static refreshBuildingCache(map: maplibregl.Map): void {
    if (!map.isStyleLoaded()) return;
    const layers = map.getStyle()?.layers || [];
    
    // RELAXED FILTER: Catch anything that looks like a building or is a 3D extrusion
    const bldgIds = layers
      .filter(l => 
        (l.id.toLowerCase().includes('building') || l.type === 'fill-extrusion') &&
        !l.id.includes('sunlight') // Don't cache our own shadows
      )
      .map(l => l.id);

    if (bldgIds.length === 0) {
      console.warn('[SiteANA] No building layers found in current style.');
      this._buildingCache = [];
      return;
    }

    // Deduplicate logic: use standard id, fallback to properties.id, fallback to coordinate-based UID
    this._buildingCache = rawFeatures
      .filter(f => f.geometry && (f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon'))
      .filter((f, i, arr) => {
        const getUid = (feat: any) => {
          if (feat.id !== undefined && feat.id !== null) return String(feat.id);
          if (feat.properties?.id) return String(feat.properties.id);
          if (feat.properties?.osm_id) return String(feat.properties.osm_id);
          // Fallback to coordinates string + index to ensure uniqueness for ID-less features
          const coords = feat.geometry.coordinates?.[0]?.[0];
          return coords ? `${coords[0]},${coords[1]}` : `idx-${i}`;
        };

        const uid = getUid(f);
        return arr.findIndex(x => getUid(x) === uid) === i;
      });

    console.log(`[SiteANA] Building cache refreshed: ${this._buildingCache.length} features (from ${bldgIds.length} layers)`);
    // Expose for browser debugging
    (window as any).MapPaintEngine = MapPaintEngine;
  }

  /**
   * Apply sunlight shadows + sun compass to the map.
   * Reads building geometry from the static cache — call refreshBuildingCache() on
   * map idle to keep the cache fresh when the viewport changes.
   *
   * Shadow visual style inspired by shademap.app:
   *   - Deep blue-grey semi-transparent fill (multiply effect)
   *   - Layer sits ABOVE building fill but BELOW fill-extrusion and labels
   */
  static applySunlight(map: maplibregl.Map, state: SunlightState) {
    const SHADOW_SOURCE  = 'sunlight-shadow-source';
    const SHADOW_LAYER   = 'sunlight-shadow-layer';
    const COMPASS_SOURCE = 'sunlight-compass-source';
    const COMPASS_RING   = 'sunlight-compass-ring';
    const COMPASS_DOT    = 'sunlight-compass-dot';

    // ── Cleanup helper ───────────────────────────────────────────────────────
    const cleanup = () => {
      for (const l of [COMPASS_DOT, COMPASS_RING, SHADOW_LAYER]) {
        try { if (map.getLayer(l)) map.removeLayer(l); } catch {}
      }
      for (const s of [COMPASS_SOURCE, SHADOW_SOURCE]) {
        try { if (map.getSource(s)) map.removeSource(s); } catch {}
      }
    };

    if (!state.enabled) { cleanup(); return; }
    if (!map.isStyleLoaded()) return;

    try {
      // ── Build time in LOCAL time (no UTC/timezone tricks) ─────────────────
      const [yr, mo, da] = state.date.split('-').map(Number);
      const hh = Math.floor(state.time);
      const mm = Math.floor((state.time - hh) * 60);
      const baseDate = new Date(yr, mo - 1, da, hh, mm, 0, 0);

      const center = map.getCenter();
      const lat    = center.lat;
      const lng    = center.lng;
      const allLayers = map.getStyle()?.layers || [];

      // ── 1. Shadow layer (uses building cache) ─────────────────────────────
      if (this._buildingCache.length > 0) {
        // Use cached buildings — this is the KEY change for smooth animation
        const shadows = SunlightEngine.computeShadows(this._buildingCache, baseDate, lat, lng);

        // Shadow color: distinguishable blue-grey (distinct from pure black basemaps)
        const SHADOW_COLOR = 'rgba(71, 85, 105, 1)'; // Slate-600 質感，比純黑明顯且專業

        if (map.getSource(SHADOW_SOURCE)) {
          (map.getSource(SHADOW_SOURCE) as maplibregl.GeoJSONSource).setData(shadows);
          if (map.getLayer(SHADOW_LAYER)) {
            map.setPaintProperty(SHADOW_LAYER, 'fill-opacity', state.opacity);
          }
        } else {
          map.addSource(SHADOW_SOURCE, { type: 'geojson', data: shadows });
          map.addLayer({
            id: SHADOW_LAYER,
            type: 'fill',
            source: SHADOW_SOURCE,
            paint: {
              'fill-color':   SHADOW_COLOR,
              'fill-opacity': state.opacity,
            }
          });
        }

        // Layer ordering:
        // We want: ground → shadow → building fill → fill-extrusion → labels
        // So insert shadow ABOVE fill layers but BELOW fill-extrusion & symbols
        const firstExtrusionOrSymbol = allLayers.find(l =>
          (l.type === 'fill-extrusion' || l.type === 'symbol')
        );
        if (firstExtrusionOrSymbol && map.getLayer(SHADOW_LAYER)) {
          try { map.moveLayer(SHADOW_LAYER, firstExtrusionOrSymbol.id); } catch {}
        }
      }

      // ── 2. Sun compass indicator ──────────────────────────────────────────
      const sunPos  = SunlightEngine.getSunPosition(baseDate, lat, lng);
      const zoom    = map.getZoom();
      // Ring radius: larger at lower zoom (city scale), smaller at high zoom (block scale)
      const radiusKm = Math.max(0.05, Math.min(0.45, 0.45 / Math.pow(2, zoom - 14)));

      // Build ring as 64-segment closed linestring
      const ring: number[][] = [];
      for (let i = 0; i <= 64; i++) {
        ring.push(moveAlongBearing(lng, lat, radiusKm, (i / 64) * 360));
      }
      // Ray tip goes slightly beyond ring
      const rayEnd = moveAlongBearing(lng, lat, radiusKm * 1.45, sunPos.azimuthDeg);
      // Sun dot sits on the ring at sun's bearing
      const sunDot = moveAlongBearing(lng, lat, radiusKm, sunPos.azimuthDeg);

      const compassData: GeoJSON.FeatureCollection = {
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            properties: { kind: 'ring' },
            geometry: { type: 'Polygon', coordinates: [ring] }
          },
          {
            type: 'Feature',
            properties: { kind: 'ray' },
            geometry: { type: 'LineString', coordinates: [[lng, lat], rayEnd] }
          },
          {
            type: 'Feature',
            properties: { kind: 'dot' },
            geometry: { type: 'Point', coordinates: sunDot }
          }
        ]
      };

      const ringColor = sunPos.isDay ? 'rgba(251,191,36,0.8)' : 'rgba(148,163,184,0.5)';
      const rayColor  = sunPos.isDay ? '#f59e0b' : '#94a3b8';
      const dotColor  = sunPos.isDay ? '#fbbf24' : '#64748b';

      if (map.getSource(COMPASS_SOURCE)) {
        (map.getSource(COMPASS_SOURCE) as maplibregl.GeoJSONSource).setData(compassData);
        // Update colors live (sun might cross horizon)
        if (map.getLayer(COMPASS_RING)) {
          map.setPaintProperty(COMPASS_RING, 'line-color',
            ['match', ['get', 'kind'], 'ray', rayColor, ringColor] as any
          );
          map.setPaintProperty(COMPASS_RING, 'line-width',
            ['match', ['get', 'kind'], 'ray', 2.5, 1.5] as any
          );
        }
        if (map.getLayer(COMPASS_DOT)) {
          map.setPaintProperty(COMPASS_DOT, 'circle-color', dotColor);
        }
      } else {
        map.addSource(COMPASS_SOURCE, { type: 'geojson', data: compassData });

        // Ring + ray (line layer)
        // Note: line-dasharray does NOT support expressions — must be static
        map.addLayer({
          id: COMPASS_RING,
          type: 'line',
          source: COMPASS_SOURCE,
          filter: ['any',
            ['==', ['get', 'kind'], 'ring'],
            ['==', ['get', 'kind'], 'ray']
          ] as any,
          paint: {
            'line-color': ['match', ['get', 'kind'], 'ray', rayColor, ringColor] as any,
            'line-width': ['match', ['get', 'kind'], 'ray', 2.5, 1.5] as any,
            'line-dasharray': [4, 3],
          }
        });

        // Sun dot (circle layer)
        map.addLayer({
          id: COMPASS_DOT,
          type: 'circle',
          source: COMPASS_SOURCE,
          filter: ['==', ['get', 'kind'], 'dot'] as any,
          paint: {
            'circle-radius':       7,
            'circle-color':        dotColor,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff',
          }
        });
      }

      // Compass always on top
      try {
        if (map.getLayer(COMPASS_RING)) map.moveLayer(COMPASS_RING);
        if (map.getLayer(COMPASS_DOT))  map.moveLayer(COMPASS_DOT);
      } catch {}

    } catch (err) {
      console.error('[SiteANA] Sunlight Error:', err);
    }
  }
}

// ── Geo utility ───────────────────────────────────────────────────────────────
/**
 * Haversine displacement: move [lng, lat] by distKm along bearingDeg (0=North, CW).
 */
function moveAlongBearing(
  lng: number, lat: number,
  distKm: number, bearingDeg: number
): [number, number] {
  const R  = 6371;
  const d  = distKm / R;
  const b  = bearingDeg * Math.PI / 180;
  const φ1 = lat * Math.PI / 180;
  const λ1 = lng * Math.PI / 180;
  const φ2 = Math.asin(Math.sin(φ1) * Math.cos(d) + Math.cos(φ1) * Math.sin(d) * Math.cos(b));
  const λ2 = λ1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(φ1), Math.cos(d) - Math.sin(φ1) * Math.sin(φ2));
  return [λ2 * 180 / Math.PI, φ2 * 180 / Math.PI];
}
