from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer
import math
from typing import Dict, Any, Optional

class AnalysisService:
    """
    Pure Python / Shapely-based spatial analysis.
    Does NOT require PostGIS or Docker.
    """

    @staticmethod
    def _get_local_crs_transformer(lon: float, lat: float):
        """Create a transformer to a local metric CRS centered on the geometry."""
        # Use UTM zone based on longitude
        zone = int((lon + 180) / 6) + 1
        hemisphere = 'north' if lat >= 0 else 'south'
        epsg = 32600 + zone if hemisphere == 'north' else 32700 + zone
        return (
            Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True),
            Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True),
        )

    @staticmethod
    def compute_stats(geojson: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute area (m²), area (ping), perimeter (m), and centroid.
        Input: GeoJSON Feature or Geometry dict
        """
        try:
            geometry = geojson.get('geometry') or geojson
            geom = shape(geometry)
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y

            to_metric, _ = AnalysisService._get_local_crs_transformer(lon, lat)

            def _proj(x, y, z=None):
                return to_metric.transform(x, y)

            projected = transform(_proj, geom)
            area_m2 = projected.area
            perimeter_m = projected.length
            area_ping = area_m2 / 3.305785  # 1 坪 = 3.305785 m²

            return {
                "area_m2": round(area_m2, 2),
                "area_ping": round(area_ping, 2),
                "perimeter_m": round(perimeter_m, 2),
                "centroid": {"lon": round(lon, 6), "lat": round(lat, 6)},
                "bbox": list(geom.bounds),
            }
        except Exception as e:
            raise ValueError(f"Stats computation failed: {str(e)}")

    @staticmethod
    def compute_buffer(geojson: Dict[str, Any], radius_m: float) -> Dict[str, Any]:
        """
        Compute a metric buffer around the geometry.
        Input: GeoJSON Feature/Geometry, radius in meters
        Output: GeoJSON Feature with buffer polygon
        """
        try:
            geometry = geojson.get('geometry') or geojson
            geom = shape(geometry)
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y

            to_metric, to_wgs84 = AnalysisService._get_local_crs_transformer(lon, lat)

            def _proj(x, y, z=None):
                return to_metric.transform(x, y)

            def _unproj(x, y, z=None):
                return to_wgs84.transform(x, y)

            projected = transform(_proj, geom)
            buffered = projected.buffer(radius_m)
            result_wgs84 = transform(_unproj, buffered)

            return {
                "type": "Feature",
                "properties": {"buffer_radius_m": radius_m},
                "geometry": mapping(result_wgs84),
            }
        except Exception as e:
            raise ValueError(f"Buffer computation failed: {str(e)}")
