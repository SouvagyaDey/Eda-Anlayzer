from rest_framework import serializers
from .models import EdaSession, EdaChart


class EdaChartSerializer(serializers.ModelSerializer):
    chart_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EdaChart
        fields = ['id', 'chart_type', 'column_name', 'chart_url', 'created_at']
    
    def get_chart_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri('/' + obj.chart_path)
        return obj.chart_path


class EdaSessionSerializer(serializers.ModelSerializer):
    charts = EdaChartSerializer(many=True, read_only=True)
    
    class Meta:
        model = EdaSession
        fields = ['session_id', 'filename', 'uploaded_at', 'row_count', 
                  'column_count', 'insights', 'charts']


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value
