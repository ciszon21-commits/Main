import * as turf from '@turf/turf';

/**
 * SunlightEngine v3.0
 *
 * 天文計算核心參考：suncalc.js (Vladimir Agafonkin / mourner)
 * https://github.com/mourner/suncalc
 *
 * Julian Day 計算：直接用 date.getTime()（UTC ms since epoch）
 * 注意：絕對不能把 getTimezoneOffset 加回去，那會造成二次偏移！
 * getTimezoneOffset 回傳的是「本地時 - UTC」的分鐘數（正西、負東）
 * 對於東八區台灣：getTimezoneOffset() = -480，加回去反而把時間延遲了！
 *
 * 角度換算：
 *   NOAA 慣例 azimuth:   0 = South, 正西 (+PI) = West  （-PI to +PI）
 *   羅盤方位 (compass):  0 = North, 順時針                (0 to 360)
 *   換算：compassDeg = (azimuthNOAA_deg + 180 + 360) % 360
 *   陰影方位：shadowDeg = (compassDeg + 180) % 360
 */

const PI  = Math.PI;
const rad = PI / 180;
const E   = rad * 23.4397; // Earth obliquity

// ── Julian Day ───────────────────────────────────────────────────────────────
/**
 * Days since J2000.0 (2000-01-01 12:00:00 UTC)
 * 直接使用 UTC ms，不加任何 timezone offset
 */
function toJulianDays(date: Date): number {
  return date.getTime() / 86400000 - 0.5 + 2440588 - 2451545.0;
}

// ── Astronomical helpers ──────────────────────────────────────────────────────
function rightAscension(l: number, b: number): number {
  return Math.atan2(Math.sin(l) * Math.cos(E) - Math.tan(b) * Math.sin(E), Math.cos(l));
}
function declination(l: number, b: number): number {
  return Math.asin(Math.sin(b) * Math.cos(E) + Math.cos(b) * Math.sin(E) * Math.sin(l));
}
function azimuthFn(H: number, phi: number, dec: number): number {
  return Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(dec) * Math.cos(phi));
}
function altitudeFn(H: number, phi: number, dec: number): number {
  return Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H));
}
function siderealTime(d: number, lw: number): number {
  return rad * (280.16 + 360.9856235 * d) - lw;
}
function solarMeanAnomaly(d: number): number {
  return rad * (357.5291 + 0.98560028 * d);
}
function eclipticLongitude(M: number): number {
  const C = rad * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
  const P = rad * 102.9372;
  return M + C + P + PI;
}
function sunCoords(d: number) {
  const M = solarMeanAnomaly(d);
  const L = eclipticLongitude(M);
  return { dec: declination(L, 0), ra: rightAscension(L, 0) };
}

// ── Public types ──────────────────────────────────────────────────────────────
export interface SunPosition {
  /** NOAA raw azimuth in radians (0=South, +W) */
  azimuth: number;
  /** Altitude above horizon in radians */
  altitude: number;
  /** Compass bearing 0-360 (0=N, 90=E, 180=S, 270=W) */
  azimuthDeg: number;
  /** Elevation angle in degrees above horizon */
  altitudeDeg: number;
  /** Direction shadows FALL (opposite to sun compass), 0-360 */
  shadowBearingDeg: number;
  /** True if sun is above horizon */
  isDay: boolean;
}

export interface SunTimes {
  sunrise:    Date | null;
  sunset:     Date | null;
  solarNoon:  Date | null;
  sunriseHour: number | null;
  sunsetHour:  number | null;
}

// ── Main Engine ───────────────────────────────────────────────────────────────
export class SunlightEngine {
  /**
   * Compute sun position for a given Date (should be built with local time constructor
   * so it represents the observer's local clock).
   *
   * @param date   A Date object — use: new Date(yr, mo-1, da, h, m, 0)
   * @param lat    Observer latitude  (degrees)
   * @param lng    Observer longitude (degrees, positive East)
   */
  static getSunPosition(date: Date, lat: number, lng: number): SunPosition {
    const lw  = rad * -lng;          // West-positive longitude in radians
    const phi = rad * lat;
    const d   = toJulianDays(date);  // Julian days from J2000
    const c   = sunCoords(d);
    const H   = siderealTime(d, lw) - c.ra;

    const az  = azimuthFn(H, phi, c.dec);   // radians, 0=S +W
    const alt = altitudeFn(H, phi, c.dec);  // radians, >0 = above horizon

    // Convert NOAA azimuth → compass bearing (0=N, CW)
    // azimuth in deg: -180..+180 (0=South, +W)
    // compass = (azDeg + 180) gives 0-360 with 0=North
    const azDeg        = az * 180 / PI;
    const compassDeg   = ((azDeg + 180) + 360) % 360;   // 0=N, CW
    const shadowBearingDeg = (compassDeg + 180) % 360;   // opposite to sun

    return {
      azimuth:          az,
      altitude:         alt,
      azimuthDeg:       compassDeg,
      altitudeDeg:      alt * 180 / PI,
      shadowBearingDeg,
      isDay:            alt > 0.0,
    };
  }

  /**
   * Compute sunrise, solar noon, and sunset for a given DATE (ignoring time component).
   */
  static getSunTimes(date: Date, lat: number, lng: number): SunTimes {
    const yr = date.getFullYear();
    const mo = date.getMonth();       // 0-indexed
    const da = date.getDate();

    // Helper: get altitude at local decimal hour h
    const altAt = (h: number): number => {
      const hh = Math.floor(h);
      const mm = Math.round((h - hh) * 60);
      const d  = new Date(yr, mo, da, hh, mm, 0, 0);
      return this.getSunPosition(d, lat, lng).altitude;
    };

    // Binary search for altitude crossing zero
    const bisect = (lo: number, hi: number, rising: boolean): number => {
      for (let i = 0; i < 48; i++) {
        const mid = (lo + hi) / 2;
        if (rising ? altAt(mid) > 0 : altAt(mid) < 0) hi = mid; else lo = mid;
      }
      return (lo + hi) / 2;
    };

    // Solar noon: peak altitude between 10h-14h
    let noonH = 12, maxAlt = -Infinity;
    for (let h = 10; h <= 14; h += 0.05) {
      const a = altAt(h);
      if (a > maxAlt) { maxAlt = a; noonH = h; }
    }

    // Sunrise: search 4h→noonH for rising zero crossing
    let sunriseH: number | null = null;
    for (let h = 4; h < noonH; h += 0.5) {
      if (altAt(h) <= 0 && altAt(h + 0.5) > 0) {
        sunriseH = bisect(h, h + 0.5, true);
        break;
      }
    }

    // Sunset: search noonH→22h for falling zero crossing
    let sunsetH: number | null = null;
    for (let h = noonH; h < 22; h += 0.5) {
      if (altAt(h) > 0 && altAt(h + 0.5) <= 0) {
        sunsetH = bisect(h, h + 0.5, false);
        break;
      }
    }

    const toDate = (h: number | null) => {
      if (h === null) return null;
      const hh = Math.floor(h);
      const mm = Math.round((h - hh) * 60);
      return new Date(yr, mo, da, hh, mm, 0, 0);
    };

    return {
      sunrise:     toDate(sunriseH),
      sunset:      toDate(sunsetH),
      solarNoon:   toDate(noonH),
      sunriseHour: sunriseH,
      sunsetHour:  sunsetH,
    };
  }

  /**
   * Project a shadow polygon for one building feature.
   *
   * Strategy (shademap-style):
   *   1. Translate the building footprint along shadowBearingDeg by shadowLength.
   *   2. Compute convex hull of original + translated footprints.
   *   This gives a 2D ground shadow polygon.
   *
   * @param feature          Building GeoJSON feature (Polygon or MultiPolygon)
   * @param altitudeRad      Sun altitude in RADIANS (must be > 0)
   * @param shadowBearingDeg Direction shadows fall, compass 0-360
   */
  static generateShadowPolygon(
    feature: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>,
    altitudeRad: number,
    shadowBearingDeg: number
  ): GeoJSON.Feature<GeoJSON.Polygon> | null {
    // Ignore sun below ~1° (avoids infinite shadows at sunrise/sunset)
    if (altitudeRad <= 0.01745) return null;   // 1° in radians

    // Building height (fallback 3m if no data)
    const height = Math.max(
      Number(feature.properties?.render_height) || 0,
      Number(feature.properties?.height) || 0,
      3
    );

    // Shadow length in km
    const shadowM   = height / Math.tan(altitudeRad);
    // Cap: ignore absurdly long shadows near horizon (>300m)
    if (shadowM > 300) return null;
    const shadowKm  = shadowM / 1000;

    try {
      // Translate the building footprint to shadow end position
      const translated = turf.transformTranslate(
        feature, shadowKm, shadowBearingDeg, { units: 'kilometers' }
      );

      // Collect all coordinate points from original + translated
      const pts: number[][] = [];
      turf.coordEach(feature,    c => pts.push([...c]));
      turf.coordEach(translated, c => pts.push([...c]));

      if (pts.length < 3) return null;

      // Convex hull of all points = shadow polygon on ground
      const fc   = turf.featureCollection(pts.map(p => turf.point(p)));
      const hull = turf.convex(fc as any);
      if (!hull) return null;

      hull.properties = { type: 'shadow', height };
      return hull;
    } catch {
      return null;
    }
  }

  /**
   * Compute all shadow polygons for a set of building features.
   * Called with a pre-CACHED building list (not from queryRenderedFeatures directly).
   */
  static computeShadows(
    buildings: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>[],
    date: Date,
    lat: number,
    lng: number
  ): GeoJSON.FeatureCollection {
    const pos = this.getSunPosition(date, lat, lng);

    // No shadows if sun is below horizon
    if (!pos.isDay) return turf.featureCollection([]);

    const shadows: GeoJSON.Feature[] = [];
    for (const bldg of buildings) {
      const shadow = this.generateShadowPolygon(bldg, pos.altitude, pos.shadowBearingDeg);
      if (shadow) shadows.push(shadow);
    }

    return turf.featureCollection(shadows);
  }
}
