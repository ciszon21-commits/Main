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
   * 道路顏色控制 - 針對 OpenFreeMap Liberty 圖層優化
   */
  static applyRoads(map: maplibregl.Map, state: MapPaintState) {
    const { roadColors } = state;
    
    // 對應 Store 中的 key 與地圖 ID 中的關鍵字
    const mappings: Record<string, string[]> = {
      highway: ['motorway', 'trunk', 'highway', 'road_motorway', 'road_trunk'],
      primary: ['primary', 'major_road', 'road_primary'],
      secondary: ['secondary', 'medium_road', 'road_secondary'],
      residential: ['residential', 'tertiary', 'minor_road', 'street', 'road_tertiary', 'road_major_residential', 'road_minor'],
      path: ['path', 'pedestrian', 'footway', 'cycleway', 'track', 'service', 'road_service', 'road_path'],
      transit_rail: ['rail', 'railway'], // Matches general rail (TRA/THSR)
      transit_mrt: ['subway', 'tram', 'transit', 'light_rail', 'bus', 'busway'], // Matches MRT & Bus layers
    };

    const layers = map.getStyle()?.layers || [];

    Object.entries(mappings).forEach(([type, keywords]) => {
      const color = (roadColors as any)[type];
      
      const targetLayerIds = layers.filter(l => 
        (l.type === 'line') && 
        keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetLayerIds.forEach(id => {
        try {
          if (!color) {
            map.setPaintProperty(id, 'line-color', undefined);
            map.setPaintProperty(id, 'line-width', undefined);
            map.setPaintProperty(id, 'line-opacity', undefined);
            if (type === 'transit_rail' || type === 'transit_mrt') {
               map.setLayoutProperty(id, 'visibility', 'none'); // Ensure transit hides completely when preset doesn't define it
            }
            // Move back to a neutral position (before symbols/labels) if it was moved to top
            const firstSymbol = layers.find(l => l.type === 'symbol');
            if (firstSymbol) map.moveLayer(id, firstSymbol.id);
            return;
          }
          if (state.activePresetId === 'transit_network') {
            if (type === 'transit_rail' || type === 'transit_mrt') {
               map.setLayoutProperty(id, 'visibility', 'visible');
               map.setPaintProperty(id, 'line-opacity', 1.0);
               map.moveLayer(id); // push to top of everything
               
               if (type === 'transit_rail') {
                  map.setPaintProperty(id, 'line-width', 3);
                  map.setPaintProperty(id, 'line-color', [
                     'case',
                     ['>=', ['index-of', '高鐵', ['coalesce', ['get', 'name:zh'], ['get', 'name'], '']], 0], '#ea580c',
                     ['>=', ['index-of', 'THSR', ['coalesce', ['get', 'network'], ['get', 'ref'], '']], 0], '#ea580c',
                     '#003366' // TRA Blue Default
                  ]);
               } else {
                  map.setPaintProperty(id, 'line-width', 4);
                  const nameField = ['coalesce', ['get', 'name:zh'], ['get', 'name'], ''];
                  const refField = ['coalesce', ['get', 'ref'], ''];
                  map.setPaintProperty(id, 'line-color', [
                     'case',
                     ['>=', ['index-of', '紅', nameField], 0], '#e3002c',
                     ['>=', ['index-of', 'R', refField], 0], '#e3002c',
                     ['>=', ['index-of', '藍', nameField], 0], '#0070bd',
                     ['>=', ['index-of', 'BL', refField], 0], '#0070bd',
                     ['>=', ['index-of', '綠', nameField], 0], '#008659',
                     ['>=', ['index-of', 'G', refField], 0], '#008659',
                     ['>=', ['index-of', '橘', nameField], 0], '#f39800',
                     ['>=', ['index-of', 'O', refField], 0], '#f39800',
                     ['>=', ['index-of', '黃', nameField], 0], '#fddb00',
                     ['>=', ['index-of', 'Y', refField], 0], '#fddb00',
                     ['>=', ['index-of', '棕', nameField], 0], '#c48c31',
                     ['>=', ['index-of', 'BR', refField], 0], '#c48c31',
                     ['>=', ['index-of', '機', nameField], 0], '#834e98',
                     ['>=', ['index-of', 'A', refField], 0], '#834e98',
                     color // Fallback
                  ]);
               }
               return;
            }
          } else {
             // In other presets, ensure transit is BELOW roads and buildings
             // Find the first road or building layer to move transit behind it
             const refLayer = layers.find(l => l.id.includes('road') || l.id.includes('building'));
             if (refLayer) map.moveLayer(id, refLayer.id);
          }

          if (state.activePresetId === 'pedestrian_flow' && type === 'path') {
             map.setLayoutProperty(id, 'visibility', 'visible');
             map.setPaintProperty(id, 'line-opacity', 1.0);
             map.setPaintProperty(id, 'line-width', [
                'interpolate', ['linear'], ['zoom'],
                13, 1,
                16, 4,
                19, 10
             ]); 
          }

          // Custom thicknesses based on type to create visual hierarchy
          if (type !== 'transit_rail' && type !== 'transit_mrt') {
             let maxW = 10; let midW = 4; let minW = 1;
             if (type === 'highway') { maxW = 16; midW = 8; minW = 2; }
             else if (type === 'primary') { maxW = 12; midW = 6; minW = 1.5; }
             else if (type === 'secondary') { maxW = 10; midW = 5; minW = 1; }
             else if (type === 'residential') { maxW = 6; midW = 3; minW = 0.5; }
             else if (type === 'path') { maxW = 3; midW = 1.5; minW = 0.2; }

             map.setPaintProperty(id, 'line-width', [
                'interpolate', ['linear'], ['zoom'],
                13, minW,
                16, midW,
                19, maxW
             ]); 
          }

          map.setPaintProperty(id, 'line-color', color);
        } catch (e) {}
      });
    });

    // --- Z-INDEX RESTACKING: Ensure Highway > Primary > Secondary > Residential > Path ---
    const layerOrder = ['path', 'residential', 'secondary', 'primary', 'highway'];
    const firstLabel = layers.find(l => l.type === 'symbol');

    layerOrder.forEach(type => {
      const keywords = mappings[type as keyof typeof mappings];
      const targetIds = layers.filter(l => 
        (l.type === 'line') && keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetIds.forEach(id => {
        try {
          if (firstLabel) {
            map.moveLayer(id, firstLabel.id);
          } else {
            map.moveLayer(id);
          }
        } catch (e) {}
      });
    });

    // Special case for transit: if transit_network preset is ON, rail/mrt should be at the absolute top
    if (state.activePresetId === 'transit_network') {
      const transitLayers = layers.filter(l => 
        (l.type === 'line') && 
        (mappings.transit_rail.some(k => l.id.toLowerCase().includes(k)) || 
         mappings.transit_mrt.some(k => l.id.toLowerCase().includes(k)))
      ).map(l => l.id);
      
      transitLayers.forEach(id => {
        try { map.moveLayer(id); } catch(e) {}
      });
    }
  }

  /**
   * 建築物與 3D 視覺
   */
  static applyBuildings(map: maplibregl.Map, state: MapPaintState) {
    const layers = map.getStyle()?.layers || [];
    const buildingLayers = layers.filter(l => 
      l.id.toLowerCase().includes('building') && 
      (l.type === 'fill' || l.type === 'fill-extrusion')
    ).map(l => l.id);

    // 依據樓層設定漸層色 (低層: 淺灰, 中層: 橘色, 高層: 深紅)
    const gradientExpression = [
      'interpolate', ['linear'], ['get', 'render_height'],
      0, '#e2e8f0',   // 平房/低矮 (0m)
      15, '#fcd34d',  // 低層 (5樓左右, ~15m)
      36, '#f97316',  // 中層 (12樓左右, ~36m)
      80, '#b91c1c'   // 高層 (25樓以上, 80m+)
    ];

    const isGradient = state.activePresetId === 'urban_density';

    buildingLayers.forEach(id => {
      try {
        const layer = map.getLayer(id);
        if (!layer) return;

        // --- Visibility ---
        map.setLayoutProperty(id, 'visibility', state.buildingVisibility ? 'visible' : 'none');
        if (!state.buildingVisibility) return;

        const colorProp = isGradient ? gradientExpression : state.buildingColor;

        if (layer.type === 'fill') {
          map.setPaintProperty(id, 'fill-color', colorProp);
          map.setPaintProperty(id, 'fill-opacity', state.buildingOpacity);
          
          if (state.buildingOutlineColor) {
            try {
              map.setPaintProperty(id, 'fill-outline-color', state.buildingOutlineColor);
            } catch (e) {}
          }
        } else if (layer.type === 'fill-extrusion') {
          // Prevent dense 3D buildings from turning black when zoomed out by lowering opacity
          const extrusionOpacity = isGradient ? [
            'interpolate', ['linear'], ['zoom'],
            12, 0.2, // very transparent when zoomed out
            15, state.buildingOpacity
          ] : state.buildingOpacity;

          // If in 2D mode, flatten extrusion layers but keep them visible
          if (!state.building3D) {
             map.setPaintProperty(id, 'fill-extrusion-height', 0);
             map.setPaintProperty(id, 'fill-extrusion-base', 0);
             map.setPaintProperty(id, 'fill-extrusion-opacity', extrusionOpacity); 
             map.setPaintProperty(id, 'fill-extrusion-color', colorProp);
          } else {
             map.setPaintProperty(id, 'fill-extrusion-color', colorProp);
             map.setPaintProperty(id, 'fill-extrusion-opacity', extrusionOpacity);
             map.setPaintProperty(id, 'fill-extrusion-height', ['get', 'render_height']);
             map.setPaintProperty(id, 'fill-extrusion-base', ['get', 'render_min_height']);
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
      const targetLayers = layers.filter(l => 
        (l.type === 'fill') &&
        keywords.some(k => l.id.toLowerCase().includes(k))
      ).map(l => l.id);

      targetLayers.forEach(id => {
        try {
          if (state.activePresetId === null) {
            // In Liberty (default) mode, we preserve native patterns
            map.setPaintProperty(id, 'fill-color', color);
            return;
          }

          map.setPaintProperty(id, 'fill-color', color);
          map.setPaintProperty(id, 'fill-opacity', 1.0); // 強制不透明，蓋過底圖預設值
          
          // Remove native fill-patterns to prevent them from turning black
          try { 
            // In MapLibre, the safest way to remove a pattern is setting it to undefined and resetting opacity/color
            map.setPaintProperty(id, 'fill-pattern', undefined);
          } catch (e) {}
        } catch (e) {}
      });
    };

    apply(
      ['park', 'garden', 'recreation', 'leisure', 'green', 'grass', 'forest', 'wood',
       'landcover', 'landuse_park', 'landuse_grass', 'natural', 'wetland', 'scrub',
       'allotment', 'orchard', 'vineyard', 'cemetery', 'pitch', 'area_park', 'area_grass'],
      landUseColors.park
    );
    apply(['water', 'river', 'lake', 'stream', 'ocean', 'sea', 'canal', 'waterway'], landUseColors.water);
    
    // Aggressively capture all plaza/pedestrian areas to kill black patterns
    apply(['parking', 'area_parking', 'landuse_parking'], landUseColors.parking || landUseColors.residential);
    apply(['square', 'plaza', 'pedestrian', 'footway_area', 'path_area', 'area_pedestrian', 'landuse_pedestrian', 'monument'], landUseColors.pedestrian || landUseColors.residential);

    apply(
      ['residential', 'neighborhood', 'urban', 'landuse_residential', 'school', 'hospital', 'aeroway'], 
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
    const layers  = map.getStyle()?.layers || [];
    const bldgIds = layers
      .filter(l => l.id.toLowerCase().includes('building') &&
                   (l.type === 'fill' || l.type === 'fill-extrusion'))
      .map(l => l.id);

    if (bldgIds.length === 0) { this._buildingCache = []; return; }

    this._buildingCache = (map.queryRenderedFeatures({ layers: bldgIds }) as any[])
      .filter(f => f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon')
      // deduplicate by id to avoid stacking polygons on the same footprint
      .filter((f, i, arr) => arr.findIndex(x => x.id === f.id) === i);

    console.log(`[SiteANA] Building cache refreshed: ${this._buildingCache.length} features`);
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

        // Shadow color: deep blue-grey, semi-transparent (shademap.app style)
        // This creates a "multiply" effect on light basemaps
        const SHADOW_COLOR = 'rgba(30, 41, 70, 1)';

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
