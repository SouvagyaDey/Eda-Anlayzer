from django.db import models
import uuid


class EdaSession(models.Model):
    """Model to store EDA session information"""
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500)
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    insights = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.filename} - {self.session_id}"


class EdaChart(models.Model):
    """Model to store generated EDA charts"""
    CHART_TYPES = [
        ('histogram', 'Histogram'),
        ('bar', 'Bar Chart'),
        ('correlation', 'Correlation Heatmap'),
        ('pairplot', 'Pair Plot'),
        ('boxplot', 'Box Plot'),
        ('missing', 'Missing Value Matrix'),
        ('scatter', 'Scatter Plot'),
        ('distribution', 'Distribution Plot'),
    ]
    
    session = models.ForeignKey(EdaSession, on_delete=models.CASCADE, related_name='charts')
    chart_type = models.CharField(max_length=50, choices=CHART_TYPES)
    chart_path = models.CharField(max_length=500)
    column_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.chart_type} - {self.session.session_id}"
