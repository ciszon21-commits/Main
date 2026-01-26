from rest_framework import serializers
from .models import County, Township, Village, GeoQuery


class CountySerializer(serializers.ModelSerializer):
    """縣市序列化器"""
    class Meta:
        model = County
        fields = ['id', 'name', 'latitude', 'longitude']


class TownshipSerializer(serializers.ModelSerializer):
    """鄉鎮區序列化器"""
    county_name = serializers.CharField(source='county.name', read_only=True)
    
    class Meta:
        model = Township
        fields = ['id', 'name', 'county', 'county_name', 'latitude', 'longitude']


class VillageSerializer(serializers.ModelSerializer):
    """村里序列化器"""
    township_name = serializers.CharField(source='township.name', read_only=True)
    county_name = serializers.CharField(source='township.county.name', read_only=True)
    
    class Meta:
        model = Village
        fields = ['id', 'name', 'township', 'township_name', 'county_name', 'latitude', 'longitude']


class GeocodeRequestSerializer(serializers.Serializer):
    """地理編碼請求序列化器"""
    query = serializers.CharField(
        max_length=500,
        help_text="要查詢的地名或地址 (支援模糊輸入)"
    )


class GeocodeResponseSerializer(serializers.Serializer):
    """地理編碼回應序列化器"""
    success = serializers.BooleanField()
    latitude = serializers.FloatField(allow_null=True)
    longitude = serializers.FloatField(allow_null=True)
    county = serializers.CharField(allow_null=True)
    township = serializers.CharField(allow_null=True)
    village = serializers.CharField(allow_null=True)
    full_address = serializers.CharField()
    confidence = serializers.FloatField()
    message = serializers.CharField()


class GeoQuerySerializer(serializers.ModelSerializer):
    """查詢紀錄序列化器"""
    county_name = serializers.CharField(
        source='matched_county.name', 
        read_only=True,
        allow_null=True
    )
    township_name = serializers.CharField(
        source='matched_township.name', 
        read_only=True,
        allow_null=True
    )
    village_name = serializers.CharField(
        source='matched_village.name',
        read_only=True,
        allow_null=True
    )
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = GeoQuery
        fields = [
            'id', 'query_text', 'county_name', 'township_name', 'village_name',
            'full_address', 'latitude', 'longitude', 'confidence', 'created_at'
        ]
    
    def get_full_address(self, obj):
        parts = []
        if obj.matched_county:
            parts.append(obj.matched_county.name)
        if obj.matched_township:
            parts.append(obj.matched_township.name)
        if obj.matched_village:
            parts.append(obj.matched_village.name)
        return ''.join(parts) if parts else None


class SuggestionSerializer(serializers.Serializer):
    """搜尋建議序列化器"""
    type = serializers.CharField()
    name = serializers.CharField()
    full_name = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
