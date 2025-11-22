import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
from datetime import datetime

class ChartGenerator:
    def __init__(self, df, session_id, output_dir, theme='light'):
        self.df = df
        self.session_id = session_id
        self.output_dir = output_dir
        self.theme = theme
        self.charts = []
        
        # Create output directory
        self.session_dir = os.path.join(output_dir, str(session_id))
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Simple color palette
        self.colors = {
            'primary': '#3b82f6',
            'secondary': '#8b5cf6',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444'
        }
    
    def _get_layout(self, title):
        """Simple, clean layout for all charts"""
        return go.Layout(
            title=title,
            title_font=dict(size=16),
            showlegend=True,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    
    def _save_chart(self, fig, chart_type, column_name=None):
        """Save chart as PNG image and record metadata"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{chart_type}_{column_name}_{timestamp}.png" if column_name else f"{chart_type}_{timestamp}.png"
        filepath = os.path.join(self.session_dir, filename)
        
        # Save as static PNG image
        fig.write_image(filepath, width=1200, height=700)
        
        # Include eda_outputs/ prefix for Django to serve correctly
        relative_path = os.path.join('eda_outputs', str(self.session_id), filename)
        self.charts.append({
            'type': chart_type,
            'path': relative_path,
            'column': column_name or ''
        })
        
        return filepath
    
    # Individual Column Charts
    
    def _generate_histogram(self, column):
        """Simple histogram"""
        fig = px.histogram(
            self.df,
            x=column,
            title=f'Distribution of {column}',
            color_discrete_sequence=[self.colors['primary']]
        )
        fig.update_layout(self._get_layout(f'Histogram: {column}'))
        self._save_chart(fig, 'histogram', column)
    
    def _generate_boxplot(self, column):
        """Simple boxplot"""
        fig = px.box(
            self.df,
            y=column,
            title=f'Boxplot of {column}',
            color_discrete_sequence=[self.colors['secondary']]
        )
        fig.update_layout(self._get_layout(f'Boxplot: {column}'))
        self._save_chart(fig, 'boxplot', column)
    
    def _generate_distribution_plot(self, column):
        """Simple distribution plot with histogram and KDE"""
        fig = go.Figure()
        
        # Histogram
        fig.add_trace(go.Histogram(
            x=self.df[column],
            name='Distribution',
            marker_color=self.colors['primary'],
            opacity=0.7
        ))
        
        fig.update_layout(self._get_layout(f'Distribution: {column}'))
        self._save_chart(fig, 'distribution', column)
    
    def _generate_bar_chart(self, column):
        """Simple bar chart for categorical data"""
        value_counts = self.df[column].value_counts().head(20)
        
        fig = px.bar(
            x=value_counts.index,
            y=value_counts.values,
            title=f'Bar Chart: {column}',
            labels={'x': column, 'y': 'Count'},
            color_discrete_sequence=[self.colors['success']]
        )
        fig.update_layout(self._get_layout(f'Bar Chart: {column}'))
        self._save_chart(fig, 'bar_chart', column)
    
    # Relationship Charts
    
    def _generate_scatter_plot(self, x_col, y_col):
        """Simple scatter plot"""
        fig = px.scatter(
            self.df,
            x=x_col,
            y=y_col,
            title=f'{y_col} vs {x_col}',
            color_discrete_sequence=[self.colors['primary']]
        )
        fig.update_layout(self._get_layout(f'Scatter: {x_col} vs {y_col}'))
        self._save_chart(fig, 'scatter', f'{x_col}_vs_{y_col}')
    
    def _generate_line_plot(self, x_col, y_col):
        """Simple line plot"""
        fig = px.line(
            self.df,
            x=x_col,
            y=y_col,
            title=f'{y_col} over {x_col}',
            color_discrete_sequence=[self.colors['secondary']]
        )
        fig.update_layout(self._get_layout(f'Line: {x_col} vs {y_col}'))
        self._save_chart(fig, 'line', f'{x_col}_vs_{y_col}')
    
    def _generate_correlation_heatmap(self, numeric_cols=None):
        """Simple correlation heatmap"""
        if numeric_cols is None:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return
        
        corr_matrix = self.df[numeric_cols].corr()
        
        fig = px.imshow(
            corr_matrix,
            title='Correlation Heatmap',
            labels=dict(color="Correlation"),
            color_continuous_scale='RdBu_r',
            aspect='auto'
        )
        fig.update_layout(self._get_layout('Correlation Heatmap'))
        self._save_chart(fig, 'correlation_heatmap')
    
    def _generate_pairplot(self, numeric_cols=None):
        """Simple pairplot (scatter matrix)"""
        if numeric_cols is None:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return
        
        # Limit to first 5 columns for performance
        numeric_cols = numeric_cols[:5]
        
        fig = px.scatter_matrix(
            self.df,
            dimensions=numeric_cols,
            title='Pairplot',
            color_discrete_sequence=[self.colors['primary']]
        )
        fig.update_layout(self._get_layout('Pairplot'))
        self._save_chart(fig, 'pairplot')
    
    def _generate_missing_values_chart(self):
        """Simple missing values chart"""
        missing = self.df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=False)
        
        if len(missing) == 0:
            return
        
        fig = px.bar(
            x=missing.values,
            y=missing.index,
            orientation='h',
            title='Missing Values',
            labels={'x': 'Count', 'y': 'Column'},
            color_discrete_sequence=[self.colors['danger']]
        )
        fig.update_layout(self._get_layout('Missing Values'))
        self._save_chart(fig, 'missing_values')
    
    # Chart Generation Methods
    
    def generate_all_charts(self):
        """Generate all available charts"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Individual column charts
        for col in numeric_cols:
            self._generate_histogram(col)
            self._generate_boxplot(col)
            self._generate_distribution_plot(col)
        
        for col in categorical_cols:
            self._generate_bar_chart(col)
        
        # Relationship charts
        if len(numeric_cols) >= 2:
            self._generate_correlation_heatmap(numeric_cols)
            self._generate_pairplot(numeric_cols)
        
        # Missing values
        self._generate_missing_values_chart()
        
        return self.charts
    
    def generate_essential_charts_for_ai(self, chart_types):
        """Generate essential charts for AI analysis"""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        for chart_type in chart_types:
            if chart_type == 'missing_values':
                self._generate_missing_values_chart()
            elif chart_type == 'correlation_heatmap' and len(numeric_cols) >= 2:
                self._generate_correlation_heatmap(numeric_cols)
            elif chart_type == 'distribution' and len(numeric_cols) > 0:
                self._generate_distribution_plot(numeric_cols[0])
            elif chart_type == 'pairplot' and len(numeric_cols) >= 2:
                self._generate_pairplot(numeric_cols)
        
        return self.charts
    
    def generate_on_demand_charts(self, x_axis=None, y_axis=None, chart_types=None):
        """Generate charts based on user selection
        
        Args:
            x_axis: X-axis column name
            y_axis: Y-axis column name
            chart_types: List of specific chart types to generate, or None to generate all possible charts
                        Options: 'scatter', 'line', 'bar_chart', 'histogram', 'boxplot', 'distribution'
                        Special value: ['all'] to generate all possible charts for the given axes
        """
        if not chart_types or chart_types == ['all']:
            # Generate ALL possible chart types based on column types
            chart_types = self._get_all_possible_chart_types(x_axis, y_axis)
        
        for chart_type in chart_types:
            if chart_type == 'scatter' and x_axis and y_axis:
                self._generate_scatter_plot(x_axis, y_axis)
            elif chart_type == 'line' and x_axis and y_axis:
                self._generate_line_plot(x_axis, y_axis)
            elif chart_type == 'histogram' and (x_axis or y_axis):
                col = x_axis or y_axis
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    self._generate_histogram(col)
            elif chart_type == 'boxplot' and (x_axis or y_axis):
                col = x_axis or y_axis
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    self._generate_boxplot(col)
            elif chart_type == 'distribution' and (x_axis or y_axis):
                col = x_axis or y_axis
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    self._generate_distribution_plot(col)
            elif chart_type == 'bar_chart' and (x_axis or y_axis):
                col = x_axis or y_axis
                self._generate_bar_chart(col)
        
        return self.charts
    
    def _get_all_possible_chart_types(self, x_axis, y_axis):
        """Get ALL possible chart types for given axes"""
        chart_types = []
        
        if x_axis and y_axis:
            # Two columns selected
            x_numeric = pd.api.types.is_numeric_dtype(self.df[x_axis])
            y_numeric = pd.api.types.is_numeric_dtype(self.df[y_axis])
            
            if x_numeric and y_numeric:
                # Both numeric: scatter and line plots
                chart_types = ['scatter', 'line']
            elif x_numeric or y_numeric:
                # One numeric, one categorical: bar chart
                chart_types = ['bar_chart']
            else:
                # Both categorical: grouped bar chart
                chart_types = ['bar_chart']
                
        elif x_axis or y_axis:
            # Single column selected
            col = x_axis or y_axis
            
            if pd.api.types.is_numeric_dtype(self.df[col]):
                # Numeric column: ALL univariate plots
                chart_types = ['histogram', 'boxplot', 'distribution']
            else:
                # Categorical column: bar chart only
                chart_types = ['bar_chart']
        
        return chart_types
    
    def get_available_chart_types(self, x_axis=None, y_axis=None):
        """Get list of available chart types for given axes (for frontend to display options)
        
        Returns:
            dict with 'chart_types' list and 'descriptions' dict
        """
        chart_types = self._get_all_possible_chart_types(x_axis, y_axis)
        
        descriptions = {
            'scatter': 'Scatter Plot - Shows relationship between two numeric variables',
            'line': 'Line Plot - Shows trend between two numeric variables',
            'bar_chart': 'Bar Chart - Shows distribution of categorical data or comparison',
            'histogram': 'Histogram - Shows frequency distribution of numeric data',
            'boxplot': 'Box Plot - Shows quartiles and outliers of numeric data',
            'distribution': 'Distribution Plot - Shows probability distribution with histogram'
        }
        
        return {
            'chart_types': chart_types,
            'descriptions': {ct: descriptions[ct] for ct in chart_types if ct in descriptions}
        }