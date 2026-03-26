from typing import List, Optional
from sqlmodel import Session, select
from app.models.base import LayerSource

class LayerCatalogService:
    @staticmethod
    def get_default_layer_sources(db: Session) -> List[LayerSource]:
        # 這裡之後可以改從資料庫讀取，目前回傳預設清單
        return [
            LayerSource(name="Roads", layer_type="road"),
            LayerSource(name="Buildings", layer_type="building"),
            LayerSource(name="Parks", layer_type="park"),
            LayerSource(name="Land Use", layer_type="landuse"),
        ]

    @staticmethod
    def get_layer_sources(db: Session) -> List[LayerSource]:
        statement = select(LayerSource).where(LayerSource.is_active == True)
        return db.exec(statement).all()
