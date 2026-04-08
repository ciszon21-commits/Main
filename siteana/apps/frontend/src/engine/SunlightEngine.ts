import * as turf from '@turf/turf';

/**
 * SunlightEngine v2.1 - Fixed shadow bearing & timezone handling
 *
 * Key fix: getSunPosition returns azimuth where 0=South, positive=West (NOAA convention)
 * Converting to compass bearing (0=North clockwise): compassBearing = (azimuthRad_in_deg + 180) % 360
 * Shadow falls OPPOSITE to sun: shadowBearing = (compassBearing + 180) % 360
 * Net: shadowBearing = (azimuthRad_in_deg + 360) % 360 = azimuthRad_in_deg (since +180+180=+360)
 * BUT azimuthRad_in_deg ranges -180..+180, so we must normalize properly.
 */

const PI = Math.PI;
const rad = PI / 180;
const e = rad * 23.4397; // obliquity of the Earth

function getJulianDays(date: Date) {
  // Use UTC to avoid timezone issues
  const utcMs = date.getTime() + date.getTimezoneOffset() * 60000;
  return utcMs / 86400000 - 0.5 + 2440588 - 2451545.0;
}

function getRightAscension(l: number, b: number) {
  return Math.atan2(Math.sin(l) * Math.cos(e) - Math.tan(b) * Math.sin(e), Math.cos(l));
}

function getDeclination(l: number, b: number) {
  return Math.asin(Math.sin(b) * Math.cos(e) + Math.cos(b) * Math.sin(e) * Math.sin(l));
}

function getAzimuth(H: number, phi: number, dec: number) {
  return Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(phi) - Math.tan(dec) * Math.cos(phi));
}

function getAltitude(H: number, phi: number, dec: number) {
  return Math.asin(Math.sin(phi) * Math.sin(dec) + Math.cos(phi) * Math.cos(dec) * Math.cos(H));
}

function getSiderealTime(d: number, lw: number) {
  return rad * (280.16 + 360.9856235 * d) - lw;
}

function getSolarMeanAnomaly(d: number) {
  return rad * (357.5291 + 0.98560028 * d);
}

function getEclipticLongitude(M: number) {
  const C = rad * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
  const P = rad * 102.9372; // perihelion of the Earth
  return M + C + P + PI;
}

function getSunCoords(d: number) {
  const M = getSolarMeanAnomaly(d);
  const L = getEclipticLongitude(M);
  return {
    dec: getDeclination(L, 0),
    ra: getRightAscension(L, 0)
  };
}

/**
 * Build a Date from a YYYY-MM-DD string + fractional hour, treating it as LOCAL time.
 */
export function buildLocalDate(dateStr: string, decimalHour: number): Date {
  const [yr, mo, da] = dateStr.split('-').map(Number);
  const h = Math.floor(decimalHour);
  const m = Math.floor((decimalHour - h) * 60);
  const s = Math.floor(((decimalHour - h) * 60 - m) * 60);
  return new Date(yr, mo - 1, da, h, m, s, 0); // local constructor
}

export interface SunPosition {
  azimuth: number;      // radians, NOAA: 0 = South, positive = West
  altitude: number;     // radians, 0 = horizon, PI/2 = zenith
  azimuthDeg: number;   // compass bearing 0-360 (0=North, 90=East, 180=South, 270=West)
  altitudeDeg: number;  // elevation angle in degrees
  shadowBearingDeg: number; // direction shadows fall (opposite to sun), 0-360
  isDay: boolean;
}

export interface SunTimes {
  sunrise: Date | null;
  sunset: Date | null;
  solarNoon: Date | null;
  sunriseHour: number | null;
  sunsetHour: number | null;
}

export class SunlightEngine {
  /**
   * Calculate sun position for given date/location.
   */
  static getSunPosition(date: Date, lat: number, lng: number): SunPosition {
    const lw = rad * -lng;
    const phi = rad * lat;
    const d = getJulianDays(date);
    const c = getSunCoords(d);
    const H = getSiderealTime(d, lw) - c.ra;

    const azimuth = getAzimuth(H, phi, c.dec);  // 0=South, +W
    const altitude = getAltitude(H, phi, c.dec);

    // Convert NOAA azimuth (0=South, +W) → compass bearing (0=North, CW)
    // azimuth in degrees from NOAA convention: measured from south going west
    // Compass = azimuth_deg + 180 to rotate to North reference
    const azimuthNOAA_deg = azimuth * 180 / PI;            // -180..+180
    const compassBearing = ((azimuthNOAA_deg + 180) + 360) % 360;  // 0-360, 0=N
    // Shadow falls directly opposite to sun
    const shadowBearingDeg = (compassBearing + 180) % 360;

    return {
      azimuth,
      altitude,
      azimuthDeg: compassBearing,
      altitudeDeg: altitude * 180 / PI,
      shadowBearingDeg,
      isDay: altitude > 0.0
    };
  }

  /**
   * Calculate sunrise, sunset for given date/location.
   * Uses binary search on the altitude function.
   */
  static getSunTimes(date: Date, lat: number, lng: number): SunTimes {
    const yr  = date.getFullYear();
    const mo  = date.getMonth();
    const da  = date.getDate();

    // Sample altitude at a given LOCAL hour
    const altAt = (h: number) => {
      const d = new Date(yr, mo, da, Math.floor(h), Math.round((h % 1) * 60), 0, 0);
      return this.getSunPosition(d, lat, lng).altitude;
    };

    const binarySearch = (lo: number, hi: number, rising: boolean): number => {
      for (let i = 0; i < 40; i++) {
        const mid = (lo + hi) / 2;
        const a = altAt(mid);
        if (rising ? a > 0 : a < 0) hi = mid; else lo = mid;
      }
      return (lo + hi) / 2;
    };

    // Solar noon: scan 10-14h for maximum altitude
    let noonH = 12;
    let maxAlt = -Infinity;
    for (let h = 10; h <= 14; h += 0.1) {
      const a = altAt(h);
      if (a > maxAlt) { maxAlt = a; noonH = h; }
    }

    // Sunrise: search 4-10 for altitude crossing 0 upward
    let sunriseH: number | null = null;
    for (let h = 4; h < 10; h += 0.5) {
      if (altAt(h) < 0 && altAt(h + 0.5) > 0) {
        sunriseH = binarySearch(h, h + 0.5, true);
        break;
      }
    }

    // Sunset: search 14-22 for altitude crossing 0 downward
    let sunsetH: number | null = null;
    for (let h = 14; h < 22; h += 0.5) {
      if (altAt(h) > 0 && altAt(h + 0.5) < 0) {
        sunsetH = binarySearch(h, h + 0.5, false);
        break;
      }
    }

    const makeDate = (h: number | null) => {
      if (h === null) return null;
      return new Date(yr, mo, da, Math.floor(h), Math.round((h % 1) * 60), 0, 0);
    };

    return {
      sunrise:    makeDate(sunriseH),
      sunset:     makeDate(sunsetH),
      solarNoon:  makeDate(noonH),
      sunriseHour: sunriseH,
      sunsetHour:  sunsetH,
    };
  }

  /**
   * Projects a shadow polygon for a single building feature.
   * @param altitudeRad  Sun altitude in radians
   * @param shadowBearingDeg  Direction shadows fall (0=N, 90=E, ...), NOT sun azimuth
   */
  static generateShadowPolygon(
    feature: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>,
    altitudeRad: number,
    shadowBearingDeg: number
  ): GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon> | null {
    if (altitudeRad <= 0.017) return null; // below ~1° — no shadow

    const height = feature.properties?.render_height || feature.properties?.height || 3;
    const shadowLengthMeters = height / Math.tan(altitudeRad);

    // Hard cap to avoid degenerate polygons near sunrise/sunset
    if (shadowLengthMeters > 250) return null;

    try {
      const shadowEnd = turf.transformTranslate(
        feature,
        shadowLengthMeters / 1000,
        shadowBearingDeg,
        { units: 'kilometers' }
      );

      const points: number[][] = [];
      turf.coordEach(feature, coord => points.push(coord));
      turf.coordEach(shadowEnd, coord => points.push(coord));

      if (points.length < 3) return null;

      const hullFC = turf.featureCollection(points.map(p => turf.point(p)));
      const hull = turf.convex(hullFC as any);
      if (!hull) return null;

      hull.properties = { type: 'shadow' };
      return hull as any;
    } catch {
      return null;
    }
  }

  /**
   * Compute shadows for all buildings in viewport.
   */
  static computeShadowsForBuildings(
    buildings: GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>[],
    date: Date,
    lat: number,
    lng: number
  ): GeoJSON.FeatureCollection {
    const pos = this.getSunPosition(date, lat, lng);

    if (!pos.isDay) {
      return turf.featureCollection([]);
    }

    const shadows: any[] = [];
    for (const bldg of buildings) {
      // Use the pre-computed shadowBearingDeg (opposite to sun compass bearing)
      const shadow = this.generateShadowPolygon(bldg, pos.altitude, pos.shadowBearingDeg);
      if (shadow) shadows.push(shadow);
    }

    return turf.featureCollection(shadows);
  }
}
