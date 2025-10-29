from django.urls import path
from .views import (
    FileUploadView,
    EdaChartsView,
    AiInsightsView,
    SessionListView,
    SessionDetailView,
    ColumnInfoView,
    GenerateCustomChartsView,
    GenerateOnDemandChartsView,
)

urlpatterns = [
    path('upload_csv/', FileUploadView.as_view(), name='upload_csv'),
    path('eda_charts/<uuid:session_id>/', EdaChartsView.as_view(), name='eda_charts'),
    path('ai_insights/<uuid:session_id>/', AiInsightsView.as_view(), name='ai_insights'),
    path('sessions/', SessionListView.as_view(), name='session_list'),
    path('sessions/<uuid:session_id>/', SessionDetailView.as_view(), name='session_detail'),
    path('columns/<uuid:session_id>/', ColumnInfoView.as_view(), name='column_info'),
    path('generate_charts/<uuid:session_id>/', GenerateCustomChartsView.as_view(), name='generate_custom_charts'),
    path('generate_on_demand/<uuid:session_id>/', GenerateOnDemandChartsView.as_view(), name='generate_on_demand_charts'),
]
