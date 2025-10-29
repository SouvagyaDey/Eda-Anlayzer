import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import List, Dict
import warnings
import time
warnings.filterwarnings('ignore')


class ChartGenerator:
    """Generate interactive EDA charts using Plotly and save them"""
    
    def __init__(self, dataframe: pd.DataFrame, session_id: str, output_dir: Path, theme: str = 'light'):
        self.df = dataframe
        self.session_id = session_id
        self.output_dir = Path(output_dir) / str(session_id)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.charts = []
        self.theme = theme
        self.generation_timestamp = str(int(time.time() * 1000))  # millisecond timestamp for unique filenames


        self.label_color = "#ffffff"  # bright blue for dark mode
        self.bg_color = "#111827"   # dark gray
        self.template = "plotly_dark"
        print(f"ChartGenerator initialized with theme: {theme}, label_color: {self.label_color}")
        
        # Plotly theme colors
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#7c3aed',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
        }
    
    def generate_all_charts(self) -> List[Dict[str, str]]:
        """Generate ALL possible EDA charts (for initial upload - shown to users via filters)"""
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Always generate overview charts
        self._generate_missing_value_chart()
        
        if numeric_cols:
            self._generate_correlation_heatmap(numeric_cols)
            
            # Generate ALL individual charts for ALL numeric columns (no limit)
            for col in numeric_cols:
                self._generate_histogram(col)
                self._generate_boxplot(col)
                self._generate_distribution_plot(col)
            
            # Generate pairplot if we have multiple numeric columns
            if len(numeric_cols) >= 2:
                self._generate_pairplot(numeric_cols[:6])  # Limit pairplot to 6 for performance
        
        if categorical_cols:
            # Generate bar charts for ALL categorical columns (no limit)
            for col in categorical_cols:
                self._generate_bar_chart(col)
        
        return self.charts
    
    def generate_essential_charts_for_ai(self) -> List[Dict[str, str]]:
        """Generate only essential charts for AI analysis (sent to Gemini)"""
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 1. Missing values - crucial for data quality insights
        self._generate_missing_value_chart()
        
        # 2. Correlation heatmap - shows relationships between variables
        if len(numeric_cols) >= 2:
            self._generate_correlation_heatmap(numeric_cols)
        
        # 3. One distribution plot for the first numeric column - shows data distribution
        if numeric_cols:
            self._generate_distribution_plot(numeric_cols[0])
        
        # 4. One bar chart for the first categorical column - shows category distribution
        if categorical_cols:
            self._generate_bar_chart(categorical_cols[0])
        
        # 5. Pairplot if multiple numeric columns exist - shows multivariate relationships
        if len(numeric_cols) >= 2:
            self._generate_pairplot(numeric_cols[:3])  # Limit to 3 for faster processing
        
        return self.charts
    
    def _save_chart(self, fig, chart_type: str, column: str = None) -> str:
        """Save Plotly chart as static image and return relative path"""
        filename = f"{chart_type}"
        if column:
            safe_column = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in str(column))
            filename += f"_{safe_column}"
        
        # Add timestamp to make each generation unique and prevent overwriting
        filename += f"_{self.generation_timestamp}"
        filename += ".png"
        
        filepath = self.output_dir / filename
        
        # ✅ Adaptive background colors
        fig.update_layout(
            paper_bgcolor=self.bg_color,
            plot_bgcolor=self.bg_color,
        )
        
        fig.write_image(str(filepath), width=1000, height=600, scale=2)
        
        relative_path = f"eda_outputs/{self.session_id}/{filename}"
        
        self.charts.append({
            'type': chart_type,
            'path': relative_path,
            'column': column
        })
        
        return relative_path
    
    def _generate_histogram(self, column: str):
        """Generate interactive histogram for numeric column"""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=self.df[column],
                nbinsx=30,
                marker=dict(
                    color=self.colors['primary'],
                    line=dict(color='white', width=1)
                ),
                name=column
            ))
            
            fig.update_layout(
                title=dict(
                    text=f'Histogram of {column}',
                    font=dict(size=18, color=self.label_color)
                ),
                xaxis_title=column,
                yaxis_title='Frequency',
                template=self.template,
                hovermode='x',
                showlegend=False,
                height=600,
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                font=dict(color=self.label_color)
            )
            
            self._save_chart(fig, 'histogram', column)
        except Exception as e:
            print(f"Error generating histogram for {column}: {e}")
    
    def _generate_boxplot(self, column: str):
        """Generate interactive boxplot for numeric column"""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Box(
                y=self.df[column],
                name=column,
                marker=dict(color=self.colors['secondary']),
                boxmean='sd'
            ))
            
            fig.update_layout(
                title=dict(
                    text=f'Box Plot of {column}',
                    font=dict(size=18, color=self.label_color)
                ),
                yaxis_title=column,
                template=self.template,
                showlegend=False,
                height=600,
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                font=dict(color=self.label_color)
            )
            
            self._save_chart(fig, 'boxplot', column)
        except Exception as e:
            print(f"Error generating boxplot for {column}: {e}")
    
    def _generate_bar_chart(self, column: str):
        """Generate interactive bar chart for categorical column"""
        try:
            value_counts = self.df[column].value_counts().head(10)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=value_counts.index,
                y=value_counts.values,
                marker=dict(
                    color=self.colors['success'],
                    line=dict(color='white', width=1)
                ),
                text=value_counts.values,
                textposition='outside'
            ))
            
            fig.update_layout(
                title=dict(
                    text=f'Bar Chart of {column} (Top 10)',
                    font=dict(size=18, color=self.label_color)
                ),
                xaxis_title=column,
                yaxis_title='Count',
                template=self.template,
                showlegend=False,
                height=600,
                xaxis=dict(
                    tickangle=-45, 
                    showgrid=False,
                    color=self.label_color
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                font=dict(color=self.label_color)
            )
            
            self._save_chart(fig, 'bar', column)
        except Exception as e:
            print(f"Error generating bar chart for {column}: {e}")
    
    def _generate_correlation_heatmap(self, numeric_cols: List[str]):
        """Generate interactive correlation heatmap"""
        try:
            if len(numeric_cols) < 2:
                return
            
            corr_matrix = self.df[numeric_cols].corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0,
                text=corr_matrix.values.round(2),
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(title="Correlation")
            ))
            
            fig.update_layout(
                title=dict(
                    text='Correlation Heatmap',
                    font=dict(size=18, color=self.label_color)
                ),
                template=self.template,
                height=max(600, len(numeric_cols) * 50),
                xaxis=dict(
                    tickangle=-45,
                    color=self.label_color
                ),
                yaxis=dict(
                    tickangle=0,
                    color=self.label_color
                ),
                font=dict(color=self.label_color)
            )
            
            self._save_chart(fig, 'correlation')
        except Exception as e:
            print(f"Error generating correlation heatmap: {e}")
    
    def _generate_pairplot(self, numeric_cols: List[str]):
        """Generate scatter matrix (pairplot) for numeric columns"""
        try:
            if len(numeric_cols) < 2:
                return
            
            sample_size = min(1000, len(self.df))
            df_sample = self.df[numeric_cols].sample(n=sample_size, random_state=42)
            
            fig = px.scatter_matrix(
                df_sample,
                dimensions=numeric_cols,
                title='Pairplot of Numeric Variables',
                height=max(800, len(numeric_cols) * 200),
                color_discrete_sequence=[self.colors['primary']]
            )
            
            fig.update_traces(diagonal_visible=False, showupperhalf=False, marker=dict(size=3))
            fig.update_layout(
                template=self.template,
                font=dict(color=self.label_color)
            )
            
            self._save_chart(fig, 'pairplot')
        except Exception as e:
            print(f"Error generating pairplot: {e}")
    
    def _generate_missing_value_chart(self):
        """Generate missing value visualization"""
        try:
            missing_data = self.df.isnull().sum()
            missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
            
            if len(missing_data) == 0:
                fig = go.Figure()
                fig.add_annotation(
                    text="No Missing Values Found ✓",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=24, color=self.colors['success'])
                )
                fig.update_layout(
                    template=self.template,
                    height=600,
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    font=dict(color=self.label_color)
                )
                self._save_chart(fig, 'missing')
                return
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=missing_data.index,
                y=missing_data.values,
                marker=dict(
                    color=self.colors['warning'],
                    line=dict(color='white', width=1)
                ),
                text=missing_data.values,
                textposition='outside'
            ))
            
            fig.update_layout(
                title=dict(
                    text='Missing Values by Column',
                    font=dict(size=18, color=self.label_color)
                ),
                xaxis_title='Column',
                yaxis_title='Number of Missing Values',
                template=self.template,
                showlegend=False,
                height=600,
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                font=dict(color=self.label_color)
            )
            
            self._save_chart(fig, 'missing')
        except Exception as e:
            print(f"Error generating missing value chart: {e}")
    
    def _generate_distribution_plot(self, column: str):
        """Generate distribution plot with KDE overlay"""
        try:
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=self.df[column],
                nbinsx=30,
                name='Distribution',
                marker=dict(
                    color=self.colors['primary'],
                    line=dict(color='white', width=1)
                ),
                opacity=0.7,
                histnorm='probability density'
            ))
            
            from scipy import stats
            data = self.df[column].dropna()
            kde = stats.gaussian_kde(data)
            x_range = np.linspace(data.min(), data.max(), 100)
            
            fig.add_trace(go.Scatter(
                x=x_range,
                y=kde(x_range),
                mode='lines',
                name='KDE',
                line=dict(color=self.colors['danger'], width=3)
            ))
            
            fig.update_layout(
                title=dict(
                    text=f'Distribution of {column}',
                    font=dict(size=18, color=self.label_color)
                ),
                xaxis_title=column,
                yaxis_title='Density',
                template=self.template,
                height=600,
                showlegend=True,
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(148, 163, 184, 0.2)',
                    color=self.label_color
                ),
                font=dict(color=self.label_color),
                legend=dict(
                    bgcolor='rgba(0,0,0,0)',
                    bordercolor='rgba(148, 163, 184, 0.3)',
                    borderwidth=1,
                    font=dict(color=self.label_color)
                )
            )
            
            self._save_chart(fig, 'distribution', column)
        except Exception as e:
            print(f"Error generating distribution plot for {column}: {e}")

    def _generate_scatter(self, x: str, y: str):
        """Generate scatter plot for two numeric columns"""
        try:
            fig = px.scatter(
                self.df,
                x=x,
                y=y,
                title=f'Scatter: {x} vs {y}',
                color_discrete_sequence=[self.colors['primary']],
                height=600
            )

            fig.update_layout(
                template=self.template,
                xaxis=dict(color=self.label_color),
                yaxis=dict(color=self.label_color),
                title=dict(font=dict(size=18, color=self.label_color)),
                font=dict(color=self.label_color)
            )

            self._save_chart(fig, 'scatter', f"{x}_vs_{y}")
        except Exception as e:
            print(f"Error generating scatter for {x} vs {y}: {e}")

    def _generate_grouped_bar(self, x: str, y: str):
        """Generate grouped bar chart for two categorical columns (counts)"""
        try:
            ct = pd.crosstab(self.df[x], self.df[y])
            fig = go.Figure()
            for col in ct.columns:
                fig.add_trace(go.Bar(
                    x=ct.index.astype(str),
                    y=ct[col].values,
                    name=str(col)
                ))

            fig.update_layout(
                title=dict(text=f'Grouped Counts: {x} vs {y}', font=dict(size=18, color=self.label_color)),
                xaxis_title=x,
                yaxis_title='Count',
                template=self.template,
                barmode='stack',
                xaxis=dict(tickangle=-45, color=self.label_color),
                yaxis=dict(color=self.label_color),
                font=dict(color=self.label_color)
            )

            self._save_chart(fig, 'grouped_bar', f"{x}_vs_{y}")
        except Exception as e:
            print(f"Error generating grouped bar for {x} vs {y}: {e}")

    def _generate_boxplot_xy(self, x: str, y: str):
        """Generate boxplot of numeric y grouped by categorical x"""
        try:
            fig = px.box(self.df, x=x, y=y, points='outliers', color_discrete_sequence=[self.colors['secondary']])
            fig.update_layout(
                title=dict(text=f'Boxplot of {y} by {x}', font=dict(size=18, color=self.label_color)),
                template=self.template,
                xaxis=dict(tickangle=-45, color=self.label_color),
                yaxis=dict(color=self.label_color),
                font=dict(color=self.label_color)
            )
            self._save_chart(fig, 'boxplot_grouped', f"{x}_vs_{y}")
        except Exception as e:
            print(f"Error generating boxplot_grouped for {x} vs {y}: {e}")

    def generate_on_demand_charts(self, x_axis: str = None, y_axis: str = None, chart_types: List[str] = None) -> List[Dict[str, str]]:
        """Generate charts on-demand for given x/y axis selections.

        chart_types: optional list to restrict outputs (e.g., ['scatter','box','histogram','bar'])
        """
        # Normalize chart_types
        allowed = {'scatter', 'box', 'histogram', 'bar', 'grouped_bar', 'distribution'}
        if chart_types:
            requested = set([c.lower() for c in chart_types]) & allowed
        else:
            requested = None

        # Validate inputs
        cols = self.df.columns.tolist()
        to_generate = []

        if x_axis and x_axis not in cols:
            raise ValueError(f"x_axis '{x_axis}' not found in dataframe")
        if y_axis and y_axis not in cols:
            raise ValueError(f"y_axis '{y_axis}' not found in dataframe")

        # Determine dtypes
        numeric = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical = self.df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Both provided
        if x_axis and y_axis:
            x_is_num = x_axis in numeric
            y_is_num = y_axis in numeric
            x_is_cat = x_axis in categorical
            y_is_cat = y_axis in categorical

            if x_is_num and y_is_num:
                if (requested is None) or ('scatter' in requested):
                    self._generate_scatter(x_axis, y_axis)
                if (requested is None) or ('histogram' in requested):
                    # Generate histograms for both numeric columns
                    self._generate_histogram(x_axis)
                    self._generate_histogram(y_axis)
                if (requested is None) or ('distribution' in requested):
                    self._generate_distribution_plot(x_axis)
                    self._generate_distribution_plot(y_axis)
            elif x_is_cat and y_is_num:
                if (requested is None) or ('box' in requested):
                    self._generate_boxplot_xy(x_axis, y_axis)
                if (requested is None) or ('histogram' in requested):
                    # Generate histogram for the numeric column
                    self._generate_histogram(y_axis)
                if (requested is None) or ('distribution' in requested):
                    self._generate_distribution_plot(y_axis)
            elif x_is_num and y_is_cat:
                if (requested is None) or ('box' in requested):
                    self._generate_boxplot_xy(y_axis, x_axis)
                if (requested is None) or ('histogram' in requested):
                    # Generate histogram for the numeric column
                    self._generate_histogram(x_axis)
                if (requested is None) or ('distribution' in requested):
                    self._generate_distribution_plot(x_axis)
            elif x_is_cat and y_is_cat:
                if (requested is None) or ('grouped_bar' in requested):
                    self._generate_grouped_bar(x_axis, y_axis)
        # Only x provided
        elif x_axis:
            if x_axis in numeric:
                if (requested is None) or ('histogram' in requested):
                    self._generate_histogram(x_axis)
                if (requested is None) or ('distribution' in requested):
                    self._generate_distribution_plot(x_axis)
            else:
                if (requested is None) or ('bar' in requested):
                    self._generate_bar_chart(x_axis)
        # Only y provided
        elif y_axis:
            if y_axis in numeric:
                if (requested is None) or ('histogram' in requested):
                    self._generate_histogram(y_axis)
                if (requested is None) or ('distribution' in requested):
                    self._generate_distribution_plot(y_axis)
            else:
                if (requested is None) or ('bar' in requested):
                    self._generate_bar_chart(y_axis)
        else:
            # No axis provided -> nothing to generate
            raise ValueError('No axis provided for on-demand generation')

        return self.charts
