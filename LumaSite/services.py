import pandas as pd
from pvlib import solarposition
from django.utils import timezone
import trimesh
import numpy as np
import os

class SunPositionService:
    """
    太陽位置計算服務：提供指定經緯度與時間的太陽方位角與高度角。
    """
    @staticmethod
    def get_sun_position(lat, lng, dt=None):
        if dt is None:
            dt = timezone.now()
        times = pd.DatetimeIndex([dt])
        solpos = solarposition.get_solarposition(times, lat, lng)
        azimuth = float(solpos['azimuth'].iloc[0])
        elevation = float(solpos['apparent_elevation'].iloc[0])
        return azimuth, elevation

    @staticmethod
    def get_sun_path_day(lat, lng, date_str):
        times = pd.date_range(start=f"{date_str} 00:00:00", 
                            end=f"{date_str} 23:59:59", 
                            freq='h', 
                            tz='Asia/Taipei')
        solpos = solarposition.get_solarposition(times, lat, lng)
        results = []
        for i, time in enumerate(times):
            results.append({
                'time': time.isoformat(),
                'azimuth': float(solpos['azimuth'].iloc[i]),
                'elevation': float(solpos['apparent_elevation'].iloc[i])
            })
        return results

class ShadowSimulationService:
    """
    陰影模擬服務：基於 Mesh 的幾何運算。
    """
    @staticmethod
    def load_scene_from_scenario(scenario):
        scene = trimesh.Scene()
        for asset in scenario.assets.all():
            if asset.file:
                file_path = asset.file.path
                if os.path.exists(file_path):
                    mesh = trimesh.load(file_path)
                    matrix = asset.transform_json.get('matrix', np.eye(4))
                    if isinstance(mesh, trimesh.Scene):
                        for name, geometry in mesh.geometry.items():
                            scene.add_geometry(geometry, transform=matrix)
                    else:
                        scene.add_geometry(mesh, transform=matrix)
        return scene

    @staticmethod
    def check_shadow(scene, point, sun_vector):
        origins = np.array([point])
        directions = np.array([sun_vector])
        origins = origins + directions * 0.001
        locations, index_ray, index_tri = scene.ray.intersects_location(
            ray_origins=origins,
            ray_directions=directions
        )
        return len(locations) > 0

    @staticmethod
    def calculate_sun_vector(azimuth, elevation):
        phi = np.deg2rad(90 - elevation)
        theta = np.deg2rad(180 - azimuth)
        x = np.sin(phi) * np.sin(theta)
        y = np.cos(phi)
        z = np.sin(phi) * np.cos(theta)
        return np.array([x, y, z])
