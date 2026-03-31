from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

from app.services.analysis import AnalysisService

router = APIRouter()

class GeoJSONInput(BaseModel):
    geojson: Dict[str, Any]

class BufferInput(BaseModel):
    geojson: Dict[str, Any]
    radius_m: float = 50.0


@router.post("/stats")
def get_spatial_stats(data: GeoJSONInput):
    """
    回傳基地的面積 (m²/坪)、周長 (m)、重心座標。
    """
    try:
        result = AnalysisService.compute_stats(data.geojson)
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/buffer")
def get_buffer(data: BufferInput):
    """
    回傳以 radius_m (公尺) 進行緩衝的 GeoJSON Feature。
    """
    try:
        result = AnalysisService.compute_buffer(data.geojson, data.radius_m)
        return {"status": "ok", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ping")
def ping():
    """確認 Analysis 服務是否正常運作"""
    return {"status": "ok", "message": "Spatial analysis engine ready (Shapely mode)"}
