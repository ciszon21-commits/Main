from rest_framework import serializers
from .models import FoundationExcavation


class FoundationExcavationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundationExcavation
        fields = '__all__'
