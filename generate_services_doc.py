#!/usr/bin/env python3
"""
Standalone script to generate PDF documentation for backend/eda/services/ files.
This script does not modify any existing code - it only reads and documents.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from pathlib import Path
import sys

# Paths
BACKEND_DIR = Path(__file__).parent / 'backend'
SERVICES_DIR = BACKEND_DIR / 'eda' / 'services'
OUTPUT_PDF = Path(__file__).parent / 'backend_services_documentation.pdf'

# Documentation content
DOCUMENTATION = """
# Backend Services Documentation

## Overview

The `backend/eda/services/` directory contains three core Python modules that power the EDA (Exploratory Data Analysis) functionality:

1. **data_processor.py** - Data cleaning and preprocessing
2. **chart_generator.py** - Plotly visualization generation
3. **ai_insights.py** - AI-powered insights using Google Gemini

---

## 1. data_processor.py

### Purpose
Handles all data preprocessing, cleaning, type inference, and statistical summary generation for uploaded CSV files.

### Main Class: DataProcessor

**Constructor:**
```python
DataProcessor(dataframe: pd.DataFrame)
```
- Takes a pandas DataFrame as input
- Creates working and original copies

**Key Methods:**

1. **clean_data() → pd.DataFrame**
   - Main orchestration method for data cleaning
   - Normalizes column names (strip, lowercase, replace spaces with underscores)
   - Infers appropriate data types (numeric, datetime)
   - Handles missing values automatically
   - Returns cleaned DataFrame

2. **_infer_types() → pd.DataFrame**
   - Attempts to convert columns to numeric types
   - Tries datetime conversion for object columns
   - Preserves original types if conversion fails

3. **_handle_missing_values() → pd.DataFrame**
   - For numeric columns: fills with median
   - For categorical columns: fills with mode (or 'Unknown' if no mode)
   - Conservative strategy for reproducibility

4. **get_summary() → Dict[str, Any]**
   - Returns comprehensive dataset summary including:
     * Shape (rows, columns)
     * Column metadata (dtype, missing count, unique values)
     * Statistics for numeric columns (mean, median, std, min, max)
     * Top values for categorical columns
     * Lists of numeric/categorical/datetime columns
     * Duplicate row count
     * Missing value counts per column

5. **detect_outliers(column: str) → pd.Series**
   - Uses IQR (Interquartile Range) method
   - Returns boolean mask indicating outliers
   - Formula: outliers are below Q1 - 1.5*IQR or above Q3 + 1.5*IQR

**Dependencies:**
- pandas
- numpy

**Usage Example:**
```python
processor = DataProcessor(raw_df)
cleaned_df = processor.clean_data()
summary = processor.get_summary()
outliers = processor.detect_outliers('loan_amount')
```

---

## 2. chart_generator.py

### Purpose
Generates interactive Plotly visualizations and exports them as high-resolution PNG images for both user viewing and AI analysis.

### Main Class: ChartGenerator

**Constructor:**
```python
ChartGenerator(dataframe: pd.DataFrame, session_id: str, 
               output_dir: Path, theme: str = 'light')
```
- dataframe: Cleaned pandas DataFrame
- session_id: Unique identifier for the analysis session
- output_dir: Base directory for chart outputs (eda_outputs/)
- theme: 'light' or 'dark' mode for charts

**Initialization:**
- Creates session-specific output directory
- Sets up color palette and theme templates
- Generates unique timestamp for file naming
- Configures label colors and background colors

**Key Methods:**

1. **generate_all_charts() → List[Dict[str, str]]**
   - Generates complete set of EDA visualizations
   - Creates charts for ALL numeric and categorical columns
   - Returns list of chart metadata dictionaries
   - Used for initial upload to show full dataset visualization

2. **generate_essential_charts_for_ai(chart_types: List[str] = None) → List[Dict[str, str]]**
   - Generates minimal set of charts for AI analysis
   - Default types: ['missing_values', 'correlation_heatmap', 'distribution', 'pairplot']
   - Optimized for speed and Gemini API token limits
   - Can accept custom chart type list

3. **generate_on_demand_charts(x_axis: str = None, y_axis: str = None, 
                                chart_types: List[str] = None) → List[Dict[str, str]]**
   - Generates charts based on user-selected axes
   - Intelligently chooses chart types based on data types:
     * Numeric × Numeric → scatter plot, histograms
     * Categorical × Numeric → boxplot grouped by category
     * Categorical × Categorical → grouped/stacked bar chart
   - Allows filtering by specific chart types

**Internal Chart Generation Methods:**

- **_generate_histogram(column)** - 30-bin histogram for numeric columns
- **_generate_boxplot(column)** - Box plot showing quartiles and outliers
- **_generate_bar_chart(column)** - Top 10 values for categorical data
- **_generate_correlation_heatmap(numeric_cols)** - Correlation matrix heatmap
- **_generate_pairplot(numeric_cols)** - Scatter matrix (samples 1000 rows)
- **_generate_missing_value_chart()** - Visual summary of missing data
- **_generate_distribution_plot(column)** - Histogram with KDE overlay
- **_generate_scatter(x, y)** - Scatter plot for two numeric variables
- **_generate_grouped_bar(x, y)** - Stacked bar for two categorical variables
- **_generate_boxplot_xy(x, y)** - Boxplot of numeric grouped by categorical

**Chart Saving:**

- **_save_chart(fig, chart_type, column=None) → str**
  - Exports Plotly figure to PNG (1000×600px, 2× scale)
  - Adds timestamp to filename for uniqueness
  - Updates layout with theme colors
  - Returns relative path: `eda_outputs/{session_id}/{filename}.png`
  - Appends metadata to self.charts list

**Chart Metadata Format:**
```python
{
    'type': 'histogram',
    'path': 'eda_outputs/abc-123/histogram_age_1731234567890.png',
    'column': 'age'
}
```

**Dependencies:**
- plotly (graph_objects, express)
- pandas, numpy
- scipy (for KDE in distribution plots)
- kaleido (Plotly's static image export engine)

**Color Palette:**
- Primary: #2563eb (blue)
- Secondary: #7c3aed (purple)
- Success: #10b981 (green)
- Danger: #ef4444 (red)
- Warning: #f59e0b (orange)

**Usage Example:**
```python
generator = ChartGenerator(df, session_id, settings.EDA_OUTPUT_DIR, theme='dark')
charts = generator.generate_essential_charts_for_ai(['correlation_heatmap', 'distribution'])
# Returns: [{'type': 'correlation', 'path': '...', 'column': None}, ...]
```

---

## 3. ai_insights.py

### Purpose
Generates AI-powered insights using Google Gemini 2.0 Flash with vision capabilities. Sends chart images and data summary to Gemini for multimodal analysis.

### Main Class: AiInsightsGenerator

**Constructor:**
```python
AiInsightsGenerator(api_key: str)
```
- Configures Google Generative AI with provided API key
- Initializes gemini-2.0-flash model
- Falls back to text-only mode if no API key

**Key Methods:**

1. **generate_insights(df: pd.DataFrame, summary: Dict[str, Any], 
                       chart_paths: List[Dict[str, str]] = None) → str**
   - Main entry point for insight generation
   - Combines text summary and chart images
   - Sends to Gemini with structured prompt
   - Returns markdown-formatted insights
   - Falls back to basic insights on error

2. **_short_prompt(data_summary: str, chart_paths: List[Dict[str, str]]) → str**
   - Creates concise, actionable prompt for Gemini
   - Structured into 5 sections:
     1. High-Level Overview
     2. Chart-Based Interpretations
     3. Feature-vs-Feature Plot Order (next plots to generate)
     4. Key Findings
     5. Recommended Next Steps
   - Optimized for speed and clarity

3. **_compact_summary(summary: Dict[str, Any]) → str**
   - Converts full summary dict to 5-7 line text format
   - Includes: rows, columns, duplicates, numeric/categorical counts, missing cells
   - Minimal format to reduce token usage

4. **_load_images(chart_paths: List[Dict[str, str]]) → List[Dict]**
   - Loads PNG files from eda_outputs/ directory
   - Converts to format required by Gemini Vision API
   - Returns list of: `{'mime_type': 'image/png', 'data': bytes}`
   - Skips files that don't exist
   - Handles absolute path resolution from project root

5. **_fallback_insights(df, summary) → str**
   - Provides basic text-based insights when AI is disabled
   - Shows shape, column types, missing values, duplicates
   - Used when GEMINI_API_KEY is not configured

**AI Prompt Structure:**

The prompt asks Gemini to analyze:
- Dataset characteristics (rows, columns, types)
- Visual patterns in each provided chart
- Correlation strengths from heatmap
- Distribution shapes and outliers
- Recommended next plots with explanations
- Actionable next steps for analysis

**Image Loading Logic:**
- Resolves paths relative to project root
- Expects format: `eda_outputs/{session_id}/{filename}.png`
- Reads files as bytes for Gemini API
- Gracefully handles missing files

**Dependencies:**
- google.generativeai
- pandas
- pathlib

**Usage Example:**
```python
ai_gen = AiInsightsGenerator(settings.GEMINI_API_KEY)
insights_text = ai_gen.generate_insights(cleaned_df, summary, chart_paths)
# Returns: Markdown-formatted string with 5 sections
```

**Gemini API Configuration:**
- Model: gemini-2.0-flash
- Input: Text prompt + multiple PNG images
- Output: Structured markdown text
- Supports multimodal vision analysis

---

## Integration Flow

### Typical Workflow in views.py

1. **Upload & Load**
   ```python
   df = pd.read_csv(file_path)
   ```

2. **Process Data**
   ```python
   processor = DataProcessor(df)
   cleaned_df = processor.clean_data()
   summary = processor.get_summary()
   ```

3. **Generate Charts**
   ```python
   chart_gen = ChartGenerator(cleaned_df, session_id, output_dir)
   chart_paths = chart_gen.generate_essential_charts_for_ai()
   ```

4. **Save to Database**
   ```python
   for chart_info in chart_paths:
       EdaChart.objects.create(
           session=session,
           chart_type=chart_info['type'],
           chart_path=chart_info['path'],
           column_name=chart_info.get('column')
       )
   ```

5. **Generate AI Insights**
   ```python
   ai_gen = AiInsightsGenerator(GEMINI_API_KEY)
   insights = ai_gen.generate_insights(cleaned_df, summary, chart_paths)
   session.insights = insights
   session.save()
   ```

---

## File Outputs

### Chart Files
- Location: `backend/eda_outputs/{session_id}/`
- Format: PNG (1000×600px, 2× scale for retina displays)
- Naming: `{type}_{column}_{timestamp}.png`
- Example: `histogram_age_1731234567890.png`

### Database Records
- Model: `EdaChart`
- Fields: session, chart_type, chart_path, column_name
- Used for retrieval and display in frontend

---

## Environment Requirements

### Python Version
- Python 3.12+ recommended

### Key Dependencies
- **Data Processing:** pandas, numpy
- **Visualization:** plotly, kaleido
- **Statistics:** scipy
- **AI:** google-generativeai
- **Django:** djangorestframework

### Environment Variables
- `GEMINI_API_KEY` - Required for AI insights
- `EDA_OUTPUT_DIR` - Base directory for chart outputs

---

## Performance Considerations

### Chart Generation
- Pairplots limited to first 6 numeric columns (performance)
- Sampling: 1000 rows for pairplot scatter matrix
- Bar charts show top 10 categories only
- Timestamps prevent cache collisions

### AI Insights
- Optimized prompt length for faster responses
- Sends only essential charts (4 default types)
- Compact summary format reduces token usage
- Fallback mode when API unavailable

### Data Processing
- Median/mode imputation is fast and deterministic
- Type inference runs once during cleaning
- Summary statistics computed efficiently with pandas

---

## Best Practices

1. **Always clean data before chart generation**
   - Use DataProcessor.clean_data() first
   - This ensures consistent column names and types

2. **Use appropriate chart generation method**
   - `generate_all_charts()` for UI display (comprehensive)
   - `generate_essential_charts_for_ai()` for AI analysis (fast)
   - `generate_on_demand_charts()` for user-selected axes

3. **Handle missing API key gracefully**
   - AiInsightsGenerator provides fallback insights
   - Check if model is configured before calling

4. **Store chart paths in database**
   - Enables retrieval without regeneration
   - Supports filtering and download features

5. **Clean up old sessions periodically**
   - Chart files accumulate in eda_outputs/
   - Implement cleanup task for old sessions

---

## Error Handling

### DataProcessor
- Type inference failures → preserves original type
- Missing value handling → uses median/mode or 'Unknown'
- Outlier detection → returns empty mask for non-numeric

### ChartGenerator
- Chart generation errors → printed, continues with next
- Missing columns → skipped gracefully
- Invalid axis selection → raises ValueError with clear message

### AiInsightsGenerator
- API errors → falls back to text-based insights
- Missing images → skipped from image list
- No API key → uses fallback mode from start

---

## Extensibility

### Adding New Chart Types
1. Add method to ChartGenerator: `_generate_newchart()`
2. Update `generate_essential_charts_for_ai()` to recognize new type
3. Update chart type options in views.py

### Custom Data Cleaning
1. Subclass DataProcessor
2. Override `_handle_missing_values()` or `_infer_types()`
3. Implement custom strategies

### Enhanced AI Prompts
1. Modify `_short_prompt()` in AiInsightsGenerator
2. Add new sections or change structure
3. Test with different datasets

---

## Conclusion

These three service modules work together to provide a complete EDA pipeline:
- **data_processor.py** ensures clean, well-typed data
- **chart_generator.py** creates publication-quality visualizations
- **ai_insights.py** provides intelligent analysis and recommendations

The modular design allows each component to be tested, extended, and maintained independently while integrating seamlessly in the Django views layer.
"""

def create_pdf():
    """Generate PDF documentation from the content above."""
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1e40af',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#1e40af',
        spaceAfter=12,
        spaceBefore=16,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#2563eb',
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor='#3b82f6',
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        textColor='#1f2937',
        backColor='#f3f4f6',
        leftIndent=20,
        rightIndent=20,
        spaceAfter=10,
        spaceBefore=5
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        alignment=TA_LEFT
    )
    
    # Build document
    story = []
    
    # Parse markdown-like content
    lines = DOCUMENTATION.strip().split('\n')
    i = 0
    in_code_block = False
    code_buffer = []
    
    while i < len(lines):
        line = lines[i]
        
        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_buffer)
                safe_code = code_text.replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f'<font name="Courier" size="9">{safe_code}</font>', code_style))
                code_buffer = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            i += 1
            continue
        
        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue
        
        # Skip empty lines
        if not line.strip():
            story.append(Spacer(1, 0.1*inch))
            i += 1
            continue
        
        # Headers
        if line.startswith('# '):
            text = line[2:].strip()
            if i == 0:  # First heading is title
                story.append(Paragraph(text, title_style))
            else:
                story.append(Paragraph(text, heading1_style))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].strip(), heading2_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:].strip(), heading3_style))
        elif line.startswith('---'):
            story.append(Spacer(1, 0.2*inch))
        elif line.startswith('- ') or line.startswith('* '):
            # Bullet point
            text = line[2:].strip()
            safe_text = text.replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f'• {safe_text}', body_style))
        else:
            # Regular paragraph
            safe_text = line.replace('<', '&lt;').replace('>', '&gt;')
            if safe_text.strip().replace('*', '').strip():  # Skip lines with only asterisks
                story.append(Paragraph(safe_text, body_style))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    print(f'✅ PDF documentation created: {OUTPUT_PDF}')
    print(f'   File size: {OUTPUT_PDF.stat().st_size / 1024:.1f} KB')

if __name__ == '__main__':
    try:
        create_pdf()
    except ImportError as e:
        print('❌ Error: ReportLab library not installed')
        print('   Install with: pip install reportlab')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Error generating PDF: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
