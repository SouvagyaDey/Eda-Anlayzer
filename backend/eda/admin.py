from django.contrib import admin
from .models import EdaSession, EdaChart


@admin.register(EdaSession)
class EdaSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'filename', 'uploaded_at', 'row_count', 'column_count']
    list_filter = ['uploaded_at']
    search_fields = ['filename', 'session_id']
    readonly_fields = ['session_id', 'uploaded_at']


@admin.register(EdaChart)
class EdaChartAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'chart_type', 'column_name', 'created_at']
    list_filter = ['chart_type', 'created_at']
    search_fields = ['session__filename', 'column_name']
    readonly_fields = ['created_at']
