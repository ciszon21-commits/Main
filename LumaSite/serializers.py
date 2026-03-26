from rest_framework import serializers
from .models import Project, Scenario, SceneAsset, AnalysisRun, AnalysisResult

class SceneAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SceneAsset
        fields = '__all__'

class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = '__all__'

class AnalysisRunSerializer(serializers.ModelSerializer):
    result = AnalysisResultSerializer(read_only=True)
    
    class Meta:
        model = AnalysisRun
        fields = '__all__'

class ScenarioSerializer(serializers.ModelSerializer):
    assets = SceneAssetSerializer(many=True, read_only=True)
    analysis_runs = AnalysisRunSerializer(many=True, read_only=True)
    
    class Meta:
        model = Scenario
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    scenarios = ScenarioSerializer(many=True, read_only=True)
    owner_name = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('owner',)
