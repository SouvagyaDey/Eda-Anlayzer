"""
URL configuration for EDA Analyzer project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('eda.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve EDA output files
    from django.conf import settings
    urlpatterns += static('/eda_outputs/', document_root=settings.EDA_OUTPUT_DIR)
