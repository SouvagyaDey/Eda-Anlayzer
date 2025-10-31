import google.generativeai as genai
import pandas as pd
from typing import Dict, List, Any
import json
import base64
from pathlib import Path


class AiInsightsGenerator:
    """Generate AI-powered insights using Google Gemini API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
    
    def generate_insights(self, df: pd.DataFrame, summary: Dict[str, Any], 
                         chart_paths: List[Dict[str, str]] = None) -> str:
        """Generate comprehensive EDA insights using Gemini with visual analysis of charts"""
        
        if not self.model:
            print("⚠️ Gemini API not configured. Using fallback analysis.")
            print("ℹ️ To enable AI insights: Set GEMINI_API_KEY in .env file")
            return self._generate_fallback_insights(df, summary, chart_paths)
        
        try:
            print(f"🤖 Generating AI insights using Gemini 2.0 Flash with Vision...")
            print(f"📊 Analyzing {len(summary['columns'])} columns and {len(df)} rows...")
            
            # Prepare only essential data summary (no CSV data)
            data_summary = self._prepare_compact_summary(df, summary)
            
            # Load chart images for Gemini vision analysis
            chart_images = []
            if chart_paths:
                print(f"📈 Loading {len(chart_paths)} visualization charts for visual analysis...")
                chart_images = self._load_chart_images(chart_paths)
                print(f"✅ Loaded {len(chart_images)} chart images")
            
            if not chart_images:
                print("⚠️ No charts loaded successfully. Generating text-only insights...")
                prompt = self._create_text_only_prompt(data_summary, summary)
                response = self.model.generate_content(prompt)
                insights_text = response.text
            else:
                # Validate that charts have images
                valid_charts = [c for c in chart_images if 'image' in c and c['image'] is not None]
                
                if not valid_charts:
                    print("⚠️ No valid chart images. Generating text-only insights...")
                    prompt = self._create_text_only_prompt(data_summary, summary)
                    response = self.model.generate_content(prompt)
                    insights_text = response.text
                else:
                    # Create prompt for visual analysis with charts
                    prompt = self._create_visual_analysis_prompt(data_summary, summary, valid_charts)
                    
                    # Send images + text to Gemini for visual analysis
                    print(f"🎨 Sending {len(valid_charts)} valid images to Gemini for visual analysis...")
                    response = self.model.generate_content(prompt)
                    insights_text = response.text
            
            # Add chart references to the insights markdown
            insights_with_charts = self._embed_charts_in_insights(insights_text, chart_paths)
            
            print("✅ AI insights generated successfully with visual analysis!")
            return insights_with_charts
            
        except Exception as e:
            print(f"❌ Error generating AI insights: {str(e)}")
            print(f"🔄 Falling back to rule-based analysis...")
            return self._generate_fallback_insights(df, summary, chart_paths)
    
    def _prepare_csv_sample(self, df: pd.DataFrame, max_rows: int = 100) -> str:
        """Prepare a CSV sample with first and last rows for Gemini analysis"""
        
        # Get head and tail of dataset
        head_rows = min(50, len(df) // 2)
        tail_rows = min(50, len(df) // 2)
        
        if len(df) <= max_rows:
            # Send entire dataset if small enough
            sample_df = df
            sample_note = f"Complete dataset ({len(df)} rows):"
        else:
            # Send first 50 and last 50 rows
            sample_df = pd.concat([df.head(head_rows), df.tail(tail_rows)])
            sample_note = f"Dataset sample (first {head_rows} and last {tail_rows} rows of {len(df)} total):"
        
        # Convert to CSV string
        csv_string = sample_df.to_csv(index=False)
        
        return f"{sample_note}\n\n```csv\n{csv_string}\n```\n"
    
    def _prepare_data_summary(self, df: pd.DataFrame, summary: Dict[str, Any]) -> str:
        """Prepare a detailed text summary of the dataset in markdown format"""
        
        text = "## Dataset Dimensions\n\n"
        text += f"| Metric | Value |\n"
        text += f"|--------|-------|\n"
        text += f"| Total Rows | {summary['shape']['rows']:,} |\n"
        text += f"| Total Columns | {summary['shape']['columns']} |\n"
        text += f"| Duplicate Rows | {summary['duplicates']:,} |\n"
        text += f"| Numeric Columns | {len(summary['numeric_columns'])} |\n"
        text += f"| Categorical Columns | {len(summary['categorical_columns'])} |\n"
        text += f"| Datetime Columns | {len(summary['datetime_columns'])} |\n\n"
        
        # Detailed column breakdown
        text += "## Column Details\n\n"
        
        # Numeric columns with full statistics
        if summary['numeric_columns']:
            text += "### Numeric Columns\n\n"
            for col_info in summary['columns']:
                if col_info['name'] in summary['numeric_columns']:
                    text += f"#### {col_info['name']}\n"
                    text += f"- **Data Type:** {col_info['dtype']}\n"
                    text += f"- **Missing Values:** {col_info['missing']} ({col_info['missing']/summary['shape']['rows']*100:.2f}%)\n"
                    text += f"- **Unique Values:** {col_info['unique']:,}\n"
                    
                    if 'statistics' in col_info and col_info['statistics']:
                        stats = col_info['statistics']
                        text += f"- **Statistics:**\n"
                        if stats.get('mean') is not None:
                            text += f"  - Mean: {stats['mean']:.4f}\n"
                        if stats.get('median') is not None:
                            text += f"  - Median: {stats['median']:.4f}\n"
                        if stats.get('std') is not None:
                            text += f"  - Std Dev: {stats['std']:.4f}\n"
                        if stats.get('min') is not None:
                            text += f"  - Min: {stats['min']:.4f}\n"
                        if stats.get('max') is not None:
                            text += f"  - Max: {stats['max']:.4f}\n"
                        if stats.get('min') is not None and stats.get('max') is not None:
                            text += f"  - Range: {stats['max'] - stats['min']:.4f}\n"
                    text += "\n"
        
        # Categorical columns
        if summary['categorical_columns']:
            text += "### Categorical Columns\n\n"
            for col_info in summary['columns']:
                if col_info['name'] in summary['categorical_columns']:
                    text += f"#### {col_info['name']}\n"
                    text += f"- **Data Type:** {col_info['dtype']}\n"
                    text += f"- **Missing Values:** {col_info['missing']} ({col_info['missing']/summary['shape']['rows']*100:.2f}%)\n"
                    text += f"- **Unique Categories:** {col_info['unique']:,}\n"
                    
                    if 'top_values' in col_info:
                        text += f"- **Top Categories:**\n"
                        for cat, count in col_info['top_values'].items():
                            pct = (count / summary['shape']['rows']) * 100
                            text += f"  - `{cat}`: {count:,} ({pct:.1f}%)\n"
                    text += "\n"
        
        # Datetime columns
        if summary['datetime_columns']:
            text += "### Datetime Columns\n\n"
            for col_info in summary['columns']:
                if col_info['name'] in summary['datetime_columns']:
                    text += f"#### {col_info['name']}\n"
                    text += f"- **Data Type:** {col_info['dtype']}\n"
                    text += f"- **Missing Values:** {col_info['missing']}\n"
                    if 'statistics' in col_info:
                        text += f"- **Date Range:** {col_info['statistics'].get('min')} to {col_info['statistics'].get('max')}\n"
                    text += "\n"
        
        # Missing values summary
        if summary['missing_values']:
            text += "## Missing Values Summary\n\n"
            text += "| Column | Missing Count | Percentage |\n"
            text += "|--------|---------------|------------|\n"
            for col, count in sorted(summary['missing_values'].items(), key=lambda x: x[1], reverse=True):
                pct = (count / summary['shape']['rows']) * 100
                text += f"| {col} | {count:,} | {pct:.2f}% |\n"
            text += "\n"
        else:
            text += "## Missing Values Summary\n\n"
            text += "✅ **No missing values detected in the dataset.**\n\n"
        
        # List all numeric columns for correlation
        if len(summary['numeric_columns']) >= 2:
            text += "## Variables Available for Correlation Analysis\n\n"
            text += "The following numeric columns are available for correlation analysis:\n"
            for col in summary['numeric_columns']:
                text += f"- `{col}`\n"
            text += "\n"
        
        return text
    
    def _create_csv_focused_prompt(self, data_summary: str, csv_sample: str, summary: Dict[str, Any]) -> str:
        """Create a comprehensive prompt focused on CSV data analysis"""
        
        prompt = f"""You are a senior data scientist with 15+ years of experience conducting Exploratory Data Analysis (EDA). Analyze the provided CSV data and generate comprehensive, actionable insights.

# DATASET INFORMATION

{data_summary}

# CSV DATA SAMPLE

{csv_sample}

# YOUR TASK

Provide a COMPREHENSIVE, DETAILED analysis (2000-3000 words minimum) covering the following:

## 1. Executive Summary (200-300 words)
- Dataset overview: {summary['shape']['rows']:,} rows × {summary['shape']['columns']} columns
- Data quality status and completeness
- 5-7 key findings with specific numbers
- Critical patterns or anomalies discovered
- Top 3 actionable recommendations

## 2. Data Quality Assessment (400-500 words)

### Completeness Analysis
- Overall completeness rate across all columns
- List columns with missing values (exact counts and percentages)
- Missing data patterns: Random, systematic, or clustered?
- Impact on analysis reliability
- Recommendations for handling missing data (imputation methods, removal, etc.)

### Data Integrity
- Duplicate records: {summary['duplicates']:,} found
- Data type consistency check
- Value range validation (logical min/max for each numeric column)
- Categorical consistency (spelling, casing, special characters)
- Outlier vs error detection strategy

## 3. Detailed Column Analysis (1000-1500 words)

### Numeric Columns ({len(summary['numeric_columns'])} columns)

For EACH numeric column, analyze:
- **Distribution characteristics**: Normal, skewed, uniform, bimodal?
- **Central tendency**: Mean, median, mode interpretation
- **Spread**: Standard deviation, range, IQR
- **Outliers**: Identify using IQR method or Z-scores, discuss if legitimate
- **Business meaning**: What do these values represent?
- **Recommendations**: Normalization needs, transformations, binning

### Categorical Columns ({len(summary['categorical_columns'])} columns)

For EACH categorical column, analyze:
- **Cardinality**: Number of unique categories and what it means
- **Distribution**: Most/least common categories with exact counts
- **Imbalance**: Are categories evenly distributed or skewed?
- **Data quality**: Spelling variations, case sensitivity issues
- **Business meaning**: What do these categories represent?
- **Recommendations**: Encoding strategy, grouping rare categories

## 4. Relationships & Patterns (400-600 words)

### Correlation Analysis (for numeric variables)
- Identify strong positive correlations (>0.7)
- Identify strong negative correlations (<-0.7)
- Multicollinearity concerns for modeling
- Surprising correlations requiring further investigation
- Recommendations: Feature selection, dimensionality reduction

### Cross-Column Insights
- Relationships between categorical and numeric variables
- Conditional distributions (e.g., salary by department)
- Segmentation opportunities
- Hidden patterns in data combinations

## 5. Actionable Recommendations (200-300 words)

### Immediate Actions (Priority 1)
1. Critical data quality fixes required
2. Columns that need attention before analysis
3. Essential preprocessing steps

### Important Improvements (Priority 2)
1. Data enrichment opportunities
2. Feature engineering suggestions
3. Analysis depth enhancements

### Optional Enhancements (Priority 3)
1. Advanced analysis possibilities
2. Additional data collection suggestions
3. Long-term data strategy improvements

## 6. Statistical Summary Tables

Include these formatted markdown tables:

### Numeric Variables Summary
| Variable | Mean | Median | Std Dev | Min | Max | Missing % | Outliers |
|----------|------|--------|---------|-----|-----|-----------|----------|
[Fill for each numeric column]

### Categorical Variables Summary  
| Variable | Unique Count | Top Category | Top Count | Top % | Missing % |
|----------|--------------|--------------|-----------|-------|-----------|
[Fill for each categorical column]

### Data Quality Scorecard
| Metric | Value | Status |
|--------|-------|--------|
| Overall Completeness | XX% | ✅/⚠️/❌ |
| Duplicate Rate | XX% | ✅/⚠️/❌ |
| Outlier Rate | XX% | ✅/⚠️/❌ |
| Type Consistency | XX% | ✅/⚠️/❌ |

# OUTPUT FORMAT

Use proper markdown formatting:
- Use ## for main sections, ### for subsections
- Use **bold** for emphasis
- Use `code blocks` for column names and values
- Use tables for statistical summaries
- Use bullet points and numbered lists
- Use emojis sparingly for visual appeal (✅, ⚠️, ❌, 📊, 💡, 🔍)

# IMPORTANT GUIDELINES

1. **Be Specific**: Always cite exact numbers, percentages, and column names
2. **Be Actionable**: Every insight should have a practical implication
3. **Be Thorough**: Don't skip any columns - analyze each one
4. **Be Professional**: This report will be read by stakeholders
5. **Be Honest**: Flag data quality issues clearly
6. **Reference CSV Data**: Cite specific examples from the data sample provided

Generate your comprehensive analysis now:"""
        
        return prompt
    
    def _prepare_compact_summary(self, df: pd.DataFrame, summary: Dict[str, Any]) -> str:
        """Prepare a compact text summary without CSV data"""
        
        text = f"## Dataset Overview\n\n"
        text += f"- **Total Rows:** {summary['shape']['rows']:,}\n"
        text += f"- **Total Columns:** {summary['shape']['columns']}\n"
        text += f"- **Duplicate Rows:** {summary['duplicates']:,}\n"
        text += f"- **Numeric Columns:** {len(summary['numeric_columns'])}\n"
        text += f"- **Categorical Columns:** {len(summary['categorical_columns'])}\n\n"
        
        # Column details
        text += "## Column Summary\n\n"
        
        for col_info in summary['columns']:
            text += f"### {col_info['name']}\n"
            text += f"- Type: {col_info['dtype']}\n"
            text += f"- Missing: {col_info['missing']} ({col_info['missing']/summary['shape']['rows']*100:.1f}%)\n"
            text += f"- Unique: {col_info['unique']:,}\n"
            
            if 'statistics' in col_info and col_info['statistics']:
                stats = col_info['statistics']
                if stats.get('mean') is not None:
                    text += f"- Mean: {stats['mean']:.2f}, Median: {stats.get('median', 0):.2f}\n"
                    text += f"- Min: {stats.get('min', 0):.2f}, Max: {stats.get('max', 0):.2f}\n"
            
            if 'top_values' in col_info:
                text += f"- Top values: {', '.join([f'{k} ({v})' for k, v in list(col_info['top_values'].items())[:3]])}\n"
            
            text += "\n"
        
        return text
    
    def _load_chart_images(self, chart_paths: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Load chart images as PIL Image objects for Gemini vision"""
        from PIL import Image
        import os
        from django.conf import settings
        
        images = []
        
        # Priority order: most important charts first
        priority_types = ['correlation_heatmap', 'missing_values', 'distribution', 'pairplot', 'histogram']
        
        # Sort charts by priority
        sorted_charts = sorted(chart_paths, 
                              key=lambda x: priority_types.index(x.get('type', '')) if x.get('type') in priority_types else 999)
        
        print(f"   📂 Looking for charts in: {settings.EDA_OUTPUT_DIR}")
        print(f"   📋 Charts received: {len(chart_paths)}")
        
        # Load only top 4-5 most important charts to keep it fast
        for chart in sorted_charts[:5]:
            try:
                # Construct full path
                chart_path = chart.get('path', '')
                chart_type = chart.get('type', 'unknown')
                
                if not chart_path:
                    print(f"   ⚠️ Empty path for chart: {chart}")
                    continue
                
                # chart_path format: "eda_outputs/session-id/chart.png"
                if chart_path.startswith('eda_outputs/'):
                    # Remove 'eda_outputs/' prefix and construct full path
                    relative_path = chart_path.replace('eda_outputs/', '')
                    full_path = Path(settings.EDA_OUTPUT_DIR) / relative_path
                    
                    if full_path.exists():
                        img = Image.open(str(full_path))
                        images.append({
                            'image': img,
                            'type': chart['type'],
                            'column': chart.get('column', ''),
                            'path': chart_path
                        })
                        print(f"   ✅ Loaded: {chart['type']} from {full_path}")
                    else:
                        print(f"   ❌ File not found: {full_path}")
                else:
                    # Try as absolute path
                    full_path = Path(chart_path)
                    if full_path.exists():
                        img = Image.open(str(full_path))
                        images.append({
                            'image': img,
                            'type': chart['type'],
                            'column': chart.get('column', ''),
                            'path': chart_path
                        })
                        print(f"   ✅ Loaded: {chart['type']} from {full_path}")
                    else:
                        print(f"   ❌ File not found: {full_path}")
                        
            except Exception as e:
                print(f"   ⚠️ Could not load {chart.get('type', 'chart')}: {str(e)}")
                continue
        
        return images
    
    def _create_visual_analysis_prompt(self, data_summary: str, summary: Dict[str, Any], 
                                      chart_images: List[Dict[str, Any]]) -> List:
        """Create prompt with images for Gemini vision analysis"""
        
        prompt_parts = []
        
        # Text prompt
        text_prompt = f"""You are a senior data scientist with 15+ years of experience in Exploratory Data Analysis. 

# DATASET INFORMATION

{data_summary}

# VISUALIZATION ANALYSIS

I'm providing you with {len(chart_images)} key visualization charts from this dataset. Please analyze these visualizations carefully and provide comprehensive insights.

**Charts provided:**
"""
        
        for i, chart in enumerate(chart_images, 1):
            chart_type = chart.get('type', 'Unknown').replace('_', ' ').title()
            column = chart.get('column', '')
            text_prompt += f"\n{i}. **{chart_type}**"
            if column:
                text_prompt += f" - Column: `{column}`"
        
        text_prompt += """

# YOUR TASK

Provide a COMPREHENSIVE analysis (2000-3000 words) with the following sections:

## 1. Executive Summary (200-300 words)
- Dataset overview and key statistics
- 5-7 major findings from the visualizations
- Critical insights and patterns discovered
- Top 3 actionable recommendations

## 2. Visual Analysis of Charts

For EACH chart provided, analyze:
- **What the chart shows**: Describe the patterns, distributions, relationships
- **Key insights**: What does this tell us about the data?
- **Data quality observations**: Any issues visible in the chart?
- **Business implications**: What actions should be taken?

## 3. Data Quality Assessment
- Completeness (missing values analysis from the chart)
- Distribution characteristics (normal, skewed, outliers)
- Correlation patterns (if heatmap provided)
- Anomalies or unusual patterns

## 4. Relationships & Patterns
- Strong correlations discovered
- Distribution characteristics
- Outliers and anomalies
- Segmentation opportunities

## 5. Actionable Recommendations

### Immediate Actions
1. Critical data quality fixes
2. Preprocessing requirements
3. Feature engineering opportunities

### Modeling Suggestions
- Appropriate algorithms based on data characteristics
- Feature selection recommendations
- Handling of outliers and missing values

### Next Steps
- Additional analysis needed
- Data collection suggestions
- Visualization improvements

# OUTPUT FORMAT

- Use clear markdown formatting
- Reference specific charts when making points
- Provide specific numbers and percentages
- Be actionable and practical
- Flag any data quality concerns

**Analyze the visualizations and generate your comprehensive insights:**
"""
        
        prompt_parts.append(text_prompt)
        
        # Add images - ensure each chart dict has 'image' key
        for chart in chart_images:
            if 'image' in chart and chart['image'] is not None:
                prompt_parts.append(chart['image'])
            else:
                print(f"   ⚠️ Skipping chart without image: {chart.get('type', 'unknown')}")
        
        return prompt_parts
    
    def _create_text_only_prompt(self, data_summary: str, summary: Dict[str, Any]) -> str:
        """Create prompt when no charts are available"""
        
        prompt = f"""You are a senior data scientist conducting Exploratory Data Analysis.

# DATASET INFORMATION

{data_summary}

# YOUR TASK

Provide a comprehensive analysis (1500-2000 words) covering:

## 1. Executive Summary
- Dataset overview: {summary['shape']['rows']:,} rows × {summary['shape']['columns']} columns
- Key statistics and characteristics
- Major findings
- Top recommendations

## 2. Data Quality Assessment
- Missing values analysis
- Duplicate records
- Data type consistency
- Outlier detection needs

## 3. Column Analysis

Analyze each column:
- Distribution characteristics
- Value ranges and validity
- Relationships with other columns
- Data quality issues

## 4. Recommendations
- Data preprocessing steps
- Feature engineering opportunities
- Modeling approaches
- Next steps for analysis

Generate your detailed analysis:
"""
        return prompt
    
    def _create_prompt(self, data_summary: str, chart_paths: List[Dict[str, str]]) -> str:
        """Create the prompt for Gemini"""
        
        prompt = """You are a senior data scientist with 15+ years of experience conducting comprehensive Exploratory Data Analysis (EDA). Your task is to provide an EXTREMELY DETAILED, publication-quality analysis that could be presented to C-level executives or published in a data science journal.

# DATASET OVERVIEW & COLUMN INVENTORY

The detailed column information below provides a complete breakdown of every variable in the dataset. Study each column carefully and reference specific values throughout your analysis.

""" + data_summary + """

# VISUALIZATION CATALOG

The following visualizations have been generated for in-depth analysis. Analyze EACH visualization thoroughly:

"""
        
        for chart in chart_paths:
            prompt += f"• **{chart['type'].title()}**"
            if chart.get('column'):
                prompt += f" - Analyzing variable: `{chart['column']}`"
            prompt += "\n"
        
        prompt += """

# COMPREHENSIVE ANALYSIS REQUIREMENTS

⚠️ **CRITICAL INSTRUCTION**: Your analysis must be EXTREMELY DETAILED (minimum 3000-5000 words). This is a professional report that will be reviewed by senior stakeholders. Every section must be thoroughly explored with specific numbers, percentages, and insights.

## 1. Executive Summary (250-400 words)

Write a comprehensive executive summary that includes:
- **Dataset Overview**: Describe the dataset dimensions, number of observations, number and types of variables
- **Data Quality Status**: Overall assessment of data completeness, duplicate records, data integrity
- **Key Findings**: Highlight the 5-7 most important discoveries from your analysis (with specific numbers)
- **Critical Insights**: Mention patterns, correlations, or anomalies that stand out
- **Business Implications**: What do these findings mean for decision-making?
- **Recommended Actions**: Top 3 immediate recommendations
- **Analysis Scope**: Mention what aspects were analyzed (distributions, correlations, outliers, etc.)

## 2. Data Quality & Integrity Assessment (400-600 words)

### 2.1 Completeness Analysis
Provide an exhaustive analysis of data completeness:
- **Overall Completeness Rate**: Calculate the percentage of non-missing values across the entire dataset
- **Column-by-Column Completeness**: List each column with missing data, ordered by severity
- **Missing Data Patterns**: Are missing values concentrated in specific rows or distributed randomly?
- **Missing Data Mechanisms**: 
  - MCAR (Missing Completely At Random): Which variables show random missingness?
  - MAR (Missing At Random): Are there patterns in missingness related to other variables?
  - MNAR (Missing Not At Random): Could missingness be related to the value itself?
- **Visualization Analysis**: Study the missing value matrix/chart and describe patterns
- **Impact Assessment**: How does missing data affect statistical power and analysis validity?
- **Critical Thresholds**: Which variables exceed 5%, 10%, or 20% missingness?

### 2.2 Data Integrity & Consistency
Conduct a thorough data integrity audit:
- **Duplicate Records**: Report exact count and percentage of duplicates
- **Duplicate Patterns**: Are duplicates exact copies or near-duplicates?
- **Data Type Consistency**: Are all columns using appropriate data types?
- **Value Ranges**: Do all numeric values fall within expected/logical ranges?
- **Categorical Consistency**: Are there spelling variations, case differences, or extra spaces in categories?
- **Outliers vs Errors**: Distinguish between legitimate outliers and potential data entry errors
- **Cross-Column Validation**: Check for logical inconsistencies between related columns
- **Temporal Consistency**: For datetime columns, check for impossible dates or sequences

### 2.3 Data Cleaning Recommendations
Provide specific, actionable cleaning steps:
- **Priority 1 (Critical)**: Issues that must be addressed before analysis
- **Priority 2 (Important)**: Issues that should be addressed for reliable results
- **Priority 3 (Optional)**: Nice-to-have improvements
- **Missing Value Strategies**:
  - Which columns should use mean/median imputation?
  - Which columns need forward-fill or backward-fill?
  - Which columns should use KNN or model-based imputation?
  - Which columns should create a "missing" indicator variable?
- **Outlier Treatment**: Specify which outliers to remove, cap, or keep
- **Standardization Needs**: List columns requiring normalization or standardization

## 3. Column-by-Column Deep Dive (1000-1500 words)

⚠️ **MANDATORY**: Analyze EVERY SINGLE COLUMN in detail. This is the most important section.

### 3.1 Numeric Variables - Individual Analysis

For **EACH AND EVERY** numeric variable, provide this comprehensive analysis:

**[Variable Name]**

1. **Basic Profile**:
   - Data type and memory usage
   - Total non-null values (count and percentage)
   - Number of unique values and what this indicates
   - Any missing values (count and percentage)

2. **Distribution Characteristics** (reference the histogram):
   - **Shape**: Normal, left-skewed, right-skewed, bimodal, multimodal, uniform, or U-shaped?
   - **Symmetry**: Is the distribution symmetric around the median?
   - **Modality**: How many peaks? What might multiple peaks indicate?
   - **Tail Behavior**: Are there long tails? Which direction?
   - **Visual Pattern**: Describe what you see in the histogram

3. **Central Tendency Analysis**:
   - **Mean**: Report the exact value and what it represents
   - **Median**: Report the exact value
   - **Mode**: If applicable
   - **Mean vs Median**: Which is higher? What does this indicate about skewness?
   - **Practical Interpretation**: What does the "average" value mean in business terms?

4. **Dispersion & Variability**:
   - **Standard Deviation**: Report exact value and interpret the spread
   - **Variance**: How much variability exists?
   - **Range**: Min to Max span
   - **Coefficient of Variation**: (Std Dev / Mean) × 100 - high or low variability?
   - **Quartiles**: Report Q1, Q2 (median), Q3
   - **Interquartile Range (IQR)**: Q3 - Q1, indicating middle 50% spread

5. **Outlier Analysis** (reference the box plot):
   - **Outlier Detection**: Using IQR method (below Q1-1.5×IQR or above Q3+1.5×IQR)
   - **Outlier Count**: How many outliers detected?
   - **Outlier Percentage**: What % of data points are outliers?
   - **Outlier Values**: Mention specific outlier values if visible
   - **Outlier Impact**: How do outliers affect the mean and std dev?
   - **Legitimacy**: Are these data errors or valid extreme values?
   - **Treatment Recommendation**: Remove, cap (winsorize), transform, or keep?

6. **Data Quality Checks**:
   - **Logical Range**: Are all values within expected/possible ranges?
   - **Negative Values**: If present, are they logical for this variable?
   - **Zero Values**: Meaningful or potential data quality issue?
   - **Extreme Values**: Any values that seem impossible?

7. **Statistical Properties**:
   - **Skewness**: Calculate approximate skewness (mean vs median relationship)
   - **Kurtosis Indication**: Peaked or flat distribution?
   - **Normality Assessment**: How close to normal distribution?

8. **Transformation Recommendations**:
   - **Log Transformation**: Needed for right-skewed data?
   - **Square Root Transform**: For moderate skewness?
   - **Box-Cox Transform**: For severe non-normality?
   - **Standardization**: Need z-score normalization?
   - **Scaling**: Need min-max scaling (0-1)?

9. **Feature Engineering Opportunities**:
   - **Binning**: Should this be converted to categories?
   - **Polynomial Features**: Create squared or cubed terms?
   - **Interaction Terms**: Combine with other variables?
   - **Derived Metrics**: Calculate ratios or differences?

10. **Business Interpretation & Insights**:
    - What does this variable represent in real-world terms?
    - What do these statistics tell us about the business/phenomenon?
    - Are there any surprising findings?
    - What decisions can be informed by this variable?

### 3.2 Categorical Variables - Individual Analysis

For **EACH AND EVERY** categorical variable, provide this detailed analysis:

**[Variable Name]**

1. **Basic Profile**:
   - Data type (object, category, etc.)
   - Total non-null values
   - Number of unique categories (cardinality)
   - Any missing values (count and percentage)

2. **Category Distribution** (reference bar chart):
   - **Top Categories**: List top 5 categories with exact counts and percentages
   - **Bottom Categories**: List least frequent categories
   - **Category Spread**: Are frequencies evenly distributed or concentrated?
   - **Visual Pattern**: Describe the bar chart pattern

3. **Frequency Analysis**:
   - **Most Common**: Which category dominates? By how much?
   - **Least Common**: Which categories are rare (< 1% or < 5%)?
   - **Middle Categories**: Distribution of mid-frequency categories
   - **Frequency Ratios**: Compare top category to second, third, etc.

4. **Class Balance Analysis**:
   - **Balance Ratio**: Compare largest to smallest category
   - **Imbalance Severity**: Mild (<3:1), Moderate (3:1 to 10:1), Severe (>10:1)?
   - **Majority Class Dominance**: Does one class exceed 80%? 90%?
   - **Rare Class Threshold**: How many classes have < 5% representation?

5. **Cardinality Analysis**:
   - **Low Cardinality** (2-10 categories): Suitable for one-hot encoding
   - **Medium Cardinality** (11-50 categories): May need frequency encoding
   - **High Cardinality** (>50 categories): Target encoding or embedding needed
   - **Cardinality Implications**: Impact on memory, model complexity

6. **Data Quality Checks**:
   - **Spelling Variations**: "Yes" vs "yes" vs "YES"?
   - **Whitespace Issues**: Leading/trailing spaces?
   - **Null Representations**: "None", "N/A", "Unknown", "Missing"?
   - **Inconsistent Formatting**: Mixed case, abbreviations?
   - **Suspicious Categories**: Unexpected or invalid values?

7. **Encoding Recommendations**:
   - **One-Hot Encoding**: Suitable for low cardinality?
   - **Label Encoding**: If ordinal relationship exists?
   - **Frequency Encoding**: Replace with frequency counts?
   - **Target Encoding**: Use mean target value per category?
   - **Embedding**: For very high cardinality?
   - **Grouping Strategy**: Combine rare categories into "Other"?

8. **Feature Engineering Opportunities**:
   - **Binning Rare Categories**: Combine categories with < 5% frequency?
   - **Creating Indicators**: Binary flags for important categories?
   - **Category Combinations**: Combine with other categorical variables?
   - **Hierarchy Extraction**: Extract parent categories from detailed ones?

9. **Business Relevance & Insights**:
   - What does this categorical variable represent?
   - What does the distribution tell us about the business?
   - Are there surprising category frequencies?
   - Which categories drive key outcomes?
   - Are there seasonal or temporal patterns in categories?

10. **Predictive Potential**:
    - Is this variable likely to be predictive?
    - Which categories might have different behavior?
    - Should this be a target variable or feature?

### 3.3 Datetime Variables - Individual Analysis

For **EACH** datetime variable (if present):

1. **Temporal Coverage**:
   - Earliest date in dataset
   - Latest date in dataset
   - Total time span covered
   - Is the time range appropriate?

2. **Temporal Distribution**:
   - Are records evenly distributed over time?
   - Any time periods with gaps?
   - Concentration in specific periods?
   - Frequency of records (daily, weekly, monthly)?

3. **Missing Values & Quality**:
   - Missing date count and percentage
   - Any impossible dates (future dates, dates before 1900)?
   - Consistency in date format?

4. **Seasonality & Trends**:
   - Could this show seasonal patterns?
   - Monthly or quarterly trends visible?
   - Day-of-week patterns relevant?
   - Holiday effects?

5. **Feature Engineering**:
   - Extract: year, quarter, month, week, day, day-of-week, hour
   - Create: time_since_first_record, days_until_now
   - Binary: is_weekend, is_holiday, is_business_hours
   - Cyclical: sin/cos transformations for circular time features

## 4. Bivariate & Multivariate Relationship Analysis (600-800 words)

### 4.1 Correlation Analysis - In-Depth Examination

Study the correlation heatmap systematically and provide:

**Strong Positive Correlations (r > 0.7)**:
- List EVERY pair of variables with strong positive correlation
- Report exact correlation coefficient for each pair
- Explain the practical meaning of each correlation
- Discuss causation vs correlation - which is which?
- Identify potential multicollinearity issues
- Business interpretation: Why might these variables be related?

**Moderate Positive Correlations (0.4 < r < 0.7)**:
- List all pairs with moderate positive correlation
- Note which relationships are expected vs surprising
- Potential for feature combinations?

**Strong Negative Correlations (r < -0.7)**:
- List EVERY pair with strong negative correlation
- Report exact correlation coefficient
- Explain the inverse relationship
- Business implications of negative correlations

**Moderate Negative Correlations (-0.7 < r < -0.4)**:
- List all pairs with moderate negative correlation
- Discuss practical significance

**Weak or No Correlations (|r| < 0.3)**:
- Which variables show surprisingly weak correlations?
- Were any strong correlations expected but not found?
- Independent variables that can provide unique information?

**Multicollinearity Assessment**:
- Identify variable groups with r > 0.8 (severe multicollinearity)
- Which variables are redundant and could be dropped?
- Impact on modeling: Which models are sensitive to multicollinearity?
- Feature selection recommendations based on correlations

**Correlation Patterns**:
- Are there variable clusters (groups of correlated variables)?
- Any hierarchical correlation structures?
- Variables that correlate with many others (hub variables)?
- Variables that are isolated (low correlation with everything)?

### 4.2 Relationship Patterns & Scatter Plot Analysis

Examine the pairplot and individual scatter plots in detail:

**Linear Relationships**:
- List all variable pairs showing linear relationships
- Estimate the slope and strength of linear associations
- Positive or negative linear trends?
- How tight is the linear relationship? (R² estimation)
- Which relationships are suitable for linear regression?

**Non-Linear Relationships**:
- **Exponential**: Which pairs show exponential growth/decay?
- **Logarithmic**: Any logarithmic relationships visible?
- **Polynomial**: Quadratic or cubic patterns?
- **Sinusoidal**: Any cyclical/wave patterns?
- **Step Functions**: Abrupt transitions between levels?
- Recommend non-linear transformations for these pairs

**Clustering & Grouping**:
- Are there natural clusters or groups visible in scatter plots?
- How many distinct clusters? (2, 3, more?)
- Are clusters well-separated or overlapping?
- What might these clusters represent? (customer segments, product categories, etc.)
- Suitable for clustering algorithms? (K-means, DBSCAN, hierarchical)

**Heteroscedasticity (Non-Constant Variance)**:
- Which scatter plots show fan-shaped patterns?
- Does variance increase with X or Y values?
- Implications for regression assumptions
- Need for variance-stabilizing transformations?
- Weighted regression considerations?

**Outliers in Bivariate Space**:
- Points that are outliers in 2D but not in univariate analysis
- Leverage points (extreme X values)
- Influential points that affect relationship
- Should these points be investigated or removed?

**Interaction Effects**:
- Relationships that vary by subgroup
- Synergistic effects between variables
- Multiplicative interaction terms to consider (X1 × X2)
- Conditional relationships (relationship exists only when Z > threshold)

**Segmentation Opportunities**:
- Different patterns in different regions of the data?
- Breakpoints or thresholds where relationships change?
- Suitable for decision tree / rule-based models?

## 5. Distribution Deep Dive & Statistical Properties (400-500 words)

### 5.1 Distribution Shape Analysis

For each major distribution visible in histograms:

**Normality Assessment**:
- Which variables follow approximately normal distributions?
- Empirical rule check: ~68% within 1 SD, ~95% within 2 SD, ~99.7% within 3 SD?
- Visual assessment: bell-shaped, symmetric, single peak?
- Implications for parametric statistical tests
- Variables suitable for techniques assuming normality

**Skewness Analysis**:
- **Right-Skewed (Positive Skew)**: List all right-skewed variables
  - Mean > Median (by how much?)
  - Long right tail with high values
  - Common in: income, prices, counts, etc.
  - Transformation recommendation: log, square root
- **Left-Skewed (Negative Skew)**: List all left-skewed variables
  - Mean < Median (by how much?)
  - Long left tail with low values
  - Less common, investigate why
  - Transformation options: reflect and transform
- **Symmetric**: Variables with mean ≈ median
  - Well-balanced distributions
  - No transformation needed

**Kurtosis Analysis**:
- **Leptokurtic (Heavy Tails)**: More outliers than normal distribution
  - Peaked distributions
  - Higher risk of extreme values
  - Which variables show this pattern?
- **Platykurtic (Light Tails)**: Fewer outliers than normal
  - Flat distributions
  - More uniform appearance
  - Which variables show this pattern?
- **Mesokurtic**: Normal-like tail behavior

**Modality Analysis**:
- **Unimodal (Single Peak)**: Most common, list these variables
  - Clear central tendency
  - Standard statistical measures applicable
- **Bimodal (Two Peaks)**: Indicates two subpopulations
  - List variables with two modes
  - What might the two peaks represent?
  - Consider splitting dataset or creating indicator variable
- **Multimodal (Multiple Peaks)**: Complex mixture
  - List any multimodal variables
  - Investigate underlying causes
  - May need mixture models or segmentation

**Uniform or Random Distributions**:
- Any variables with flat, uniform distributions?
- Could indicate: random assignment, synthetic data, data quality issues
- Limited predictive value for modeling

### 5.2 Comparative Distribution Analysis

**Distributional Differences**:
- Compare shapes across related variables
- Which variables have similar distributions? (might be redundant)
- Which variables have contrasting distributions? (provide complementary information)

**Subgroup Comparisons**:
- For categorical variables, compare distributions of numeric variables across categories
- Are distributions shifted? Different shapes? Different variances?
- Suitable for ANOVA or t-tests?

**Temporal Distribution Changes** (if applicable):
- Have distributions changed over time?
- Seasonal effects on distributions?
- Trend shifts in mean or variance?

## 6. Comprehensive Outlier & Anomaly Analysis (400-500 words)

### 6.1 Univariate Outlier Identification

For **EACH numeric variable** with outliers (from box plots):

**[Variable Name]**:
- **Outlier Count**: Exact number of outliers detected
- **Outlier Percentage**: % of total observations
- **Lower Outliers**: Count and approximate values below Q1 - 1.5×IQR
- **Upper Outliers**: Count and approximate values above Q3 + 1.5×IQR
- **Extreme Outliers**: Beyond 3×IQR from quartiles?
- **Outlier Values**: Mention specific outlier values if visible/known
- **Impact on Mean**: How much do outliers inflate/deflate the mean?
- **Impact on Std Dev**: How much do outliers inflate variability?

### 6.2 Multivariate Outlier Identification

From scatter plots and pairplots:
- **Bivariate Outliers**: Points that are outliers in 2D space
- **Leverage Points**: Extreme X values that influence relationships
- **Influential Points**: Points that significantly affect correlation/regression
- **Mahalanobis Distance**: Consider multivariate outlier detection
- **Isolation**: Are outliers isolated individuals or form small clusters?

### 6.3 Outlier Root Cause Analysis

For significant outliers, investigate:

**Data Entry Errors**:
- **Impossible Values**: Values that can't exist (negative age, 200% percentage, etc.)
- **Unit Errors**: Cm entered as m, thousands entered as millions, etc.
- **Typos**: Extra zeros, decimal point errors (100.0 entered as 1000)
- **Copy-Paste Errors**: Values from wrong row/column
- **Recommendation**: Flag for review and correction

**Measurement Errors**:
- Sensor malfunction or calibration issues
- Survey response errors
- Recording mistakes
- **Recommendation**: Investigate and possibly remove

**Legitimate Extreme Values**:
- **Rare Events**: Genuine but unusual occurrences
- **Natural Variation**: Within expected range of phenomenon
- **VIP Cases**: High-value customers, premium products, etc.
- **Recommendation**: Keep but possibly analyze separately

**Population Heterogeneity**:
- Values from a different subpopulation mixed in
- Different context or time period
- **Recommendation**: Create indicator variable or separate analysis

### 6.4 Outlier Treatment Strategy

Provide specific recommendations for each variable:

**Option 1: Remove**:
- Which outliers should be removed? Why?
- What % of data loss is acceptable?
- Impact on sample size and statistical power

**Option 2: Cap (Winsorize)**:
- Which outliers should be capped at a threshold?
- What threshold? (95th percentile, 99th percentile, 3 standard deviations?)
- Preserves sample size while limiting extreme influence

**Option 3: Transform**:
- Which variables need log/sqrt transformation to reduce outlier impact?
- Will transformation make distribution more normal?

**Option 4: Keep**:
- Which outliers are legitimate and should remain?
- Use robust statistics (median, IQR) instead of mean/std dev
- Use robust models (tree-based, regularized regression)

**Option 5: Separate Analysis**:
- Analyze outliers as a separate segment
- Build separate models for outlier group
- "Outlier indicator" feature for unified model

## 7. Advanced Feature Engineering Recommendations (500-600 words)

### 7.1 Numeric Variable Transformations

**Scaling & Normalization**:
For EACH numeric variable, specify:
- **Standardization (Z-score)**: (X - mean) / std_dev
  - List variables that need standardization
  - Why: For algorithms sensitive to scale (SVM, KNN, Neural Networks, PCA)
  - When features have different units or magnitudes
- **Min-Max Scaling**: (X - min) / (max - min) → [0,1]
  - List variables suitable for min-max scaling
  - Why: When you need bounded range [0,1]
  - When distribution is not Gaussian
- **Robust Scaling**: Using median and IQR instead of mean/std
  - List variables with outliers that need robust scaling
  - Why: Less sensitive to outliers
  - Good alternative when outliers are legitimate

**Mathematical Transformations**:
- **Log Transform**: log(X + 1) or log(X)
  - List variables needing log transformation
  - Why: Reduce right skew, handle exponential relationships
  - When: Data spans multiple orders of magnitude (prices, counts, income)
  - Note: Add 1 if zeros exist
- **Square Root Transform**: √X
  - List variables for square root transformation
  - Why: Moderate right skew, count data
  - When: Poisson-distributed data
- **Box-Cox Transform**: Optimal power transformation
  - Variables with severe non-normality
  - Find optimal λ parameter
- **Reciprocal Transform**: 1/X
  - For specific relationships (time → rate)
- **Power Transforms**: X², X³
  - Create polynomial features for non-linear relationships
  - List candidate variables for polynomial expansion

**Binning & Discretization**:
For continuous variables that should become categorical:
- **Equal-Width Binning**: Same-sized intervals
  - List variables and number of bins
  - Example: Age → AgeGroup (0-18, 19-35, 36-50, 51+)
- **Equal-Frequency Binning**: Same number of observations per bin
  - Variables with skewed distributions
  - Ensures balanced bins
- **Custom Binning**: Business-driven thresholds
  - Domain knowledge boundaries
  - Example: Income → Low, Middle, High based on quartiles
- **Target-Based Binning**: Optimize bins for target variable
  - Decision tree-based binning

### 7.2 Categorical Variable Encoding

Specify encoding strategy for EACH categorical variable:

**One-Hot Encoding (Dummy Variables)**:
- List low-cardinality variables (< 10 categories)
- Creates N-1 binary columns
- Example: Color (Red, Blue, Green) → Color_Red, Color_Blue
- Warning: Avoid with high cardinality (dimension explosion)

**Label Encoding (Ordinal Encoding)**:
- List ordinal variables with natural order
- Example: Education (High School=1, Bachelor=2, Master=3, PhD=4)
- Warning: Don't use for nominal variables (implies order)

**Frequency Encoding**:
- List high-cardinality variables
- Replace category with its frequency/count
- Preserves information about category popularity

**Target Encoding (Mean Encoding)**:
- Replace category with mean target value for that category
- Use with cross-validation to avoid leakage
- Good for high-cardinality variables in supervised learning

**Binary Encoding**:
- For medium cardinality (10-100 categories)
- Converts to binary digits
- More compact than one-hot

**Embedding**:
- For very high cardinality (100+ categories)
- Learn dense representations
- Use in neural networks

**Group Rare Categories**:
- List categories with < 5% frequency
- Combine into "Other" category
- Reduces dimensionality and overfitting

### 7.3 New Feature Creation

**Interaction Features**:
List specific interaction terms to create:
- **Multiplicative**: X1 × X2 (e.g., price × quantity = revenue)
- **Additive**: X1 + X2 (e.g., multiple income sources)
- **Ratio**: X1 / X2 (e.g., profit/revenue = margin%)
- **Difference**: X1 - X2 (e.g., end_date - start_date)
- **Boolean Interactions**: (X1 > threshold) AND (X2 == category)

**Ratio & Derived Features**:
Suggest meaningful ratios:
- Example: Revenue/Employees = Revenue per employee
- Example: Total_Bill/Number_of_Items = Average item price
- Example: Distance/Time = Speed
- List all ratio features that make business sense

**Aggregation Features**:
Group-based statistics:
- Group by categorical variable, compute statistics on numeric variables
- Example: Average_Salary_By_Department
- Example: Max_Temperature_By_Month
- Example: Customer_Lifetime_Value = Sum of all purchases
- List specific aggregations to create

**Temporal Features** (if datetime present):
- Extract: Year, Quarter, Month, Week, DayOfYear, DayOfWeek, Hour, Minute
- Create: IsWeekend, IsHoliday, IsBusinessHours, IsPeakSeason
- Calculate: DaysSince_FirstRecord, DaysUntil_Today, RecencyScore
- Cyclical: Sin/Cos transforms for hour, month, day_of_week
- Lag Features: Previous_Day_Value, Moving_Average_7days
- List all temporal features to engineer

**Domain-Specific Features**:
Based on business context, suggest:
- Customer Segmentation: RFM scores (Recency, Frequency, Monetary)
- Text Features: Length, Word count, Sentiment score
- Geographic: Distance calculations, Region grouping
- Business Metrics: Conversion rate, Churn risk score
- List 5-10 domain-specific features

**Polynomial Features**:
- Create squared terms: X1², X2²
- Create interaction terms: X1 × X2
- Use degree 2 or 3 for non-linear relationships
- Warning: Can create many features, use feature selection

### 7.4 Feature Selection Strategy

After engineering features, recommend:
- **Filter Methods**: Correlation threshold, Variance threshold, Chi-square test
- **Wrapper Methods**: Forward selection, Backward elimination, RFE
- **Embedded Methods**: L1 regularization (Lasso), Tree feature importance
- **Dimensionality Reduction**: PCA, t-SNE, UMAP for high-dimensional data

## 8. Statistical Insights & Key Discoveries (400-500 words)

### 8.1 Top Statistical Findings

List the **10-15 most important statistical discoveries**:

1. **[Finding Name]**:
   - **Observation**: Describe what you found (with specific numbers)
   - **Evidence**: Which chart/statistic supports this?
   - **Statistical Significance**: How strong is the evidence?
   - **Practical Significance**: Does it matter in real terms?
   - **Business Implication**: What does this mean for decisions?

2. [Repeat for each major finding]

### 8.2 Unexpected & Counterintuitive Patterns

List **surprising findings** that defy expectations:

1. **[Unexpected Pattern]**:
   - **What's Surprising**: What did you expect vs what you found?
   - **Magnitude**: How different from expectations?
   - **Possible Explanations**: Why might this occur?
   - **Further Investigation Needed**: What questions does this raise?
   - **Implications**: How does this change our understanding?

### 8.3 Pattern Summary

**Strong Patterns Identified**:
- List 5-7 clear, robust patterns in the data
- Patterns that appear consistently across multiple analyses
- High confidence findings

**Weak or Inconclusive Patterns**:
- Patterns that showed up but aren't strong enough to be conclusive
- Need more data or different analysis
- Be transparent about uncertainty

**Absence of Expected Patterns**:
- Patterns that should be there but aren't
- Variables that should correlate but don't
- Missing relationships to investigate

## 9. Machine Learning & Modeling Recommendations (500-600 words)

### 9.1 Problem Type Identification

**Potential ML Tasks**:

Based on the data structure, identify suitable tasks:

**Supervised Learning - Regression**:
- If you have numeric target variables
- **Potential Target Variables**: List candidates (with justification)
- **Prediction Goals**: What could we predict? (sales, price, score, etc.)
- **Evaluation Metrics**: RMSE, MAE, R², MAPE
- **Business Value**: What's the value of accurate predictions?

**Supervised Learning - Classification**:
- If you have categorical target variables
- **Potential Target Variables**: List candidates (with justification)
- **Prediction Goals**: What categories could we predict? (churn, category, outcome)
- **Class Balance**: Is target balanced or imbalanced?
- **Evaluation Metrics**: Accuracy, Precision, Recall, F1, AUC-ROC
- **Business Value**: Cost of false positives vs false negatives

**Unsupervised Learning - Clustering**:
- For customer segmentation, anomaly detection, pattern discovery
- **Clustering Potential**: Did you see natural clusters in scatter plots?
- **Number of Clusters**: Estimate based on visual analysis
- **Clustering Variables**: Which variables to use for clustering?
- **Business Application**: What decisions would clusters inform?

**Unsupervised Learning - Dimensionality Reduction**:
- If many correlated variables (>20 features)
- **PCA Potential**: High correlation among features?
- **Variance Explained**: Estimate % variance in top components
- **Use Case**: Data compression, visualization, preprocessing

**Anomaly Detection**:
- To identify outliers, fraud, errors
- **Outlier Context**: Supervised or unsupervised detection?
- **Methods**: Isolation Forest, One-Class SVM, Autoencoder
- **Business Application**: Fraud detection, quality control

### 9.2 Algorithm Recommendations

**For Regression Problems**:

Suggest 3-5 algorithms in order of priority:

1. **[Algorithm Name]** (e.g., Random Forest Regression)
   - **Why Suitable**: Handles non-linearity, robust to outliers, feature importance
   - **Data Characteristics**: Works well with mixed types, interactions
   - **Pros**: Non-parametric, handles missing values, less preprocessing
   - **Cons**: Black box, computationally expensive
   - **Expected Performance**: Estimate based on data quality

2. **[Second Algorithm]** (e.g., Gradient Boosting)
   - [Repeat detailed justification]

3. **[Third Algorithm]** (e.g., Ridge Regression)
   - [Repeat detailed justification]

**For Classification Problems**:

Suggest 3-5 algorithms:

1. **[Algorithm]** with detailed justification
2. **[Algorithm]** with detailed justification
3. **[Algorithm]** with detailed justification

**For Clustering**:

1. **K-Means**: For well-separated spherical clusters
2. **DBSCAN**: For arbitrary shapes, automatic outlier detection
3. **Hierarchical**: For interpretable dendrograms

### 9.3 Detailed Preprocessing Pipeline

Provide step-by-step preprocessing:

**Step 1: Data Cleaning**
- Handle missing values (specify method per column)
- Remove or treat outliers (specify per variable)
- Fix data type issues
- Remove duplicates

**Step 2: Feature Engineering**
- Create new features (reference section 7)
- Extract temporal features
- Create interaction terms
- Calculate ratios

**Step 3: Encoding**
- One-hot encode categorical variables (specify which)
- Target encode high-cardinality variables (specify which)
- Create dummy variables

**Step 4: Transformation**
- Log transform skewed variables (specify which)
- Scale numeric features (specify method)
- Handle outliers in features

**Step 5: Feature Selection**
- Remove low-variance features (variance < 0.01)
- Remove highly correlated features (r > 0.95)
- Select top K features by importance/correlation
- Specify final feature count

**Step 6: Train-Test Split**
- Recommend split ratio (70-30, 80-20, or k-fold CV)
- Stratification needed for imbalanced classes?
- Time-based split for temporal data

**Step 7: Validation Strategy**
- K-fold cross-validation (specify K)
- Stratified K-fold for classification
- Time series cross-validation for temporal data
- Hold-out validation set?

### 9.4 Model Evaluation & Monitoring

**Metrics to Track**:
- Primary metric (most important for business)
- Secondary metrics (additional perspectives)
- Baseline to beat (random, mean, simple heuristic)

**Model Interpretation**:
- Feature importance analysis
- SHAP values for complex models
- Partial dependence plots
- Business-friendly explanations

## 10. Business Intelligence & Strategic Recommendations (400-500 words)

### 10.1 Business Implications Translation

Translate statistical findings into business language:

**Revenue Implications**:
- Which findings could increase revenue?
- Quantify potential revenue impact (estimate or range)
- What actions would realize this potential?

**Cost Implications**:
- Which findings could reduce costs?
- Quantify potential savings
- Implementation costs vs benefits

**Risk Implications**:
- What risks are revealed by the data?
- Quantify risk exposure if possible
- Risk mitigation strategies

**Customer Insights**:
- What do we learn about customers?
- Segmentation opportunities
- Personalization possibilities

**Operational Insights**:
- Process improvements suggested by data
- Efficiency opportunities
- Resource allocation recommendations

### 10.2 Prioritized Strategic Recommendations

**Top 5 Actionable Recommendations** (in priority order):

**#1 Recommendation**: [Clear Action Item]
- **What**: Specific action to take
- **Why**: Statistical/business justification
- **Expected Impact**: Quantified benefit (revenue, cost, time)
- **Implementation Difficulty**: Easy / Medium / Hard
- **Timeline**: Immediate / Short-term (1-3 months) / Long-term (6+ months)
- **Resources Needed**: People, budget, tools
- **Success Metrics**: How to measure success
- **Risk**: What could go wrong?

**#2-5**: [Repeat same structure]

### 10.3 Further Investigation Priorities

**Questions Raised by This Analysis**:
List 5-10 specific questions that need deeper investigation

**Additional Data Needs**:
- What data is missing that would enhance analysis?
- External data sources to integrate?
- More granular data needed?
- Historical data requirements?

**Proposed Follow-Up Analyses**:
1. **[Analysis Type]**: Specific analysis to conduct next
   - Objective: What will it reveal?
   - Methods: How to conduct it?
   - Timeline: When to do it?
   - Value: Why is it important?

## 11. Limitations, Caveats & Assumptions (200-300 words)

### 11.1 Data Limitations

**Sample Limitations**:
- Sample size: Is it sufficient for conclusions?
- Sampling method: Random or biased?
- Time period: Is it representative?
- Coverage: Any gaps in data collection?

**Data Quality Limitations**:
- Missing data impact
- Outlier treatment assumptions
- Data accuracy concerns
- Measurement limitations

### 11.2 Analysis Limitations

**Methodological Limitations**:
- Correlation does not imply causation
- Assumptions made in statistical tests
- Limitations of visualization types used
- Multivariate effects not fully explored

**Interpretation Caveats**:
- Alternative explanations for patterns
- Confounding variables not controlled
- Generalizability concerns
- Temporal limitations (snapshot vs trends)

### 11.3 Assumptions Made

List all key assumptions:
- Data is representative of population
- Missing data is [MCAR/MAR/MNAR]
- Outliers are [legitimate/errors]
- Relationships are [stable over time]
- [Other domain-specific assumptions]

### 11.4 Recommended Validation

**Validation Steps**:
- Cross-validate findings with domain experts
- Test conclusions on new data
- A/B testing for recommendations
- Sensitivity analysis on key findings

---

## FINAL INSTRUCTIONS FOR COMPREHENSIVE ANALYSIS:

✅ **Length**: Your full analysis should be 3000-5000 words minimum - this is a detailed professional report

✅ **Specificity**: Use EXACT numbers from the dataset overview (means, medians, percentages, counts)

✅ **Chart References**: Mention specific visualizations ("as shown in the [column_name] histogram...")

✅ **Every Column**: Analyze EVERY single column in section 3, don't skip any

✅ **Professional Tone**: Write as if presenting to executives or publishing in a journal

✅ **Actionable**: Every insight should lead to recommendations or next steps

✅ **Quantified**: Provide numbers, percentages, and ranges whenever possible

✅ **Structured**: Use all the headers and subheaders provided above

✅ **Honest**: Acknowledge uncertainties, limitations, and alternative explanations

Your analysis is a comprehensive professional data science report that will guide major business decisions. Treat it with appropriate rigor and detail.
"""
        
        return prompt
    
    def _load_chart_images(self, chart_paths: List[Dict[str, str]]) -> List[Any]:
        """Load chart images for Gemini"""
        
        images = []
        
        for chart_info in chart_paths[:10]:  # Limit to 10 images
            try:
                path = Path(chart_info['path'])
                if path.exists():
                    # Read image file
                    with open(path, 'rb') as f:
                        image_data = f.read()
                    
                    # Create image part for Gemini
                    image_part = {
                        'mime_type': 'image/png',
                        'data': image_data
                    }
                    images.append(image_part)
            except Exception as e:
                print(f"Error loading chart image {chart_info['path']}: {e}")
        
        return images
    
    def _embed_charts_in_insights(self, insights_text: str, chart_paths: List[Dict[str, str]]) -> str:
        """Embed chart images in the insights markdown"""
        
        if not chart_paths:
            return insights_text
        
        # Create a visualization section to insert after the executive summary
        viz_section = "\n\n---\n\n## 📈 Key Visualizations\n\n"
        viz_section += "*The following charts provide visual insights into your data:*\n\n"
        
        # Group charts by type
        chart_types = {}
        for chart in chart_paths:
            chart_type = chart['type']
            if chart_type not in chart_types:
                chart_types[chart_type] = []
            chart_types[chart_type].append(chart)
        
        # Add charts organized by type
        chart_labels = {
            'missing_values': '🔍 Missing Values Analysis',
            'correlation_heatmap': '🔗 Correlation Heatmap',
            'histogram': '📊 Distribution Histograms',
            'boxplot': '📦 Box Plots (Outlier Detection)',
            'distribution': '📈 Distribution Plots',
            'bar_chart': '📊 Categorical Distributions',
            'pairplot': '🔬 Pairwise Relationships',
        }
        
        for chart_type, charts in chart_types.items():
            label = chart_labels.get(chart_type, chart_type.replace('_', ' ').title())
            viz_section += f"### {label}\n\n"
            
            for chart in charts:
                # Create image markdown with proper path
                chart_path = chart['path']
                column = chart.get('column', '')
                
                if column:
                    viz_section += f"**{column}**\n\n"
                
                # Use the media URL path for frontend display
                viz_section += f"![{chart_type}](/{chart_path})\n\n"
        
        viz_section += "---\n\n"
        
        # Insert visualization section after executive summary or at the beginning
        if "## 1. Executive Summary" in insights_text or "## Executive Summary" in insights_text:
            # Find the end of executive summary section
            parts = insights_text.split("## 2.", 1)
            if len(parts) == 2:
                return parts[0] + viz_section + "## 2." + parts[1]
            else:
                # Try alternative format
                parts = insights_text.split("## Data Quality", 1)
                if len(parts) == 2:
                    return parts[0] + viz_section + "## Data Quality" + parts[1]
        
        # If no specific section found, add at the beginning after title
        lines = insights_text.split('\n', 5)
        if len(lines) > 3:
            return '\n'.join(lines[:3]) + '\n' + viz_section + '\n'.join(lines[3:])
        
        # Fallback: append to the end
        return insights_text + "\n\n" + viz_section
    
    def _generate_fallback_insights(self, df: pd.DataFrame, summary: Dict[str, Any], 
                                   chart_paths: List[Dict[str, str]] = None) -> str:
        """Generate comprehensive insights without AI when API is not available"""
        
        insights = "# 📊 Comprehensive Exploratory Data Analysis Report\n\n"
        insights += "> *This is an automated statistical analysis. For AI-powered insights with advanced pattern recognition, please configure your GEMINI_API_KEY environment variable.*\n\n"
        insights += "---\n\n"
        
        # Executive Summary
        insights += "## 1. Executive Summary\n\n"
        insights += f"This dataset contains **{summary['shape']['rows']:,} observations** across **{summary['shape']['columns']} variables**. "
        
        if summary['duplicates'] > 0:
            dup_pct = (summary['duplicates'] / summary['shape']['rows']) * 100
            insights += f"There are {summary['duplicates']:,} duplicate records ({dup_pct:.2f}%). "
        else:
            insights += "No duplicate records were detected. "
        
        if summary['missing_values']:
            total_missing = sum(summary['missing_values'].values())
            total_cells = summary['shape']['rows'] * summary['shape']['columns']
            missing_pct = (total_missing / total_cells) * 100
            insights += f"Missing values account for {missing_pct:.2f}% of the total dataset."
        else:
            insights += "The dataset is complete with no missing values."
        
        insights += f"\n\nThe dataset comprises {len(summary['numeric_columns'])} numeric variables, "
        insights += f"{len(summary['categorical_columns'])} categorical variables"
        if summary['datetime_columns']:
            insights += f", and {len(summary['datetime_columns'])} datetime variables"
        insights += ".\n\n"
        
        insights += "---\n\n"
        
        # Data Quality Assessment
        insights += "## 2. Data Quality & Integrity Assessment\n\n"
        
        insights += "### 2.1 Completeness Analysis\n\n"
        if summary['missing_values']:
            insights += f"**Overall Completeness Rate:** {100 - (sum(summary['missing_values'].values()) / (summary['shape']['rows'] * summary['shape']['columns']) * 100):.2f}%\n\n"
            insights += "**Columns with Missing Data:**\n\n"
            insights += "| Column | Missing Count | Percentage | Severity |\n"
            insights += "|--------|---------------|------------|----------|\n"
            
            sorted_missing = sorted(summary['missing_values'].items(), key=lambda x: x[1], reverse=True)
            for col, count in sorted_missing:
                pct = (count / summary['shape']['rows']) * 100
                if pct >= 20:
                    severity = "🔴 Critical"
                elif pct >= 10:
                    severity = "🟠 High"
                elif pct >= 5:
                    severity = "🟡 Moderate"
                else:
                    severity = "🟢 Low"
                insights += f"| {col} | {count:,} | {pct:.2f}% | {severity} |\n"
            
            insights += "\n**Recommendations:**\n"
            for col, count in sorted_missing[:3]:
                pct = (count / summary['shape']['rows']) * 100
                if pct >= 20:
                    insights += f"- **{col}**: High missing rate ({pct:.1f}%). Consider dropping this column or using advanced imputation.\n"
                elif pct >= 5:
                    insights += f"- **{col}**: Moderate missing rate ({pct:.1f}%). Use mean/median imputation for numeric or mode for categorical.\n"
                else:
                    insights += f"- **{col}**: Low missing rate ({pct:.1f}%). Simple imputation should suffice.\n"
        else:
            insights += "✅ **Perfect Data Quality**: No missing values detected in any column.\n"
        
        insights += "\n### 2.2 Data Integrity\n\n"
        if summary['duplicates'] > 0:
            dup_pct = (summary['duplicates'] / summary['shape']['rows']) * 100
            insights += f"⚠️ **Duplicate Records**: {summary['duplicates']:,} duplicate rows found ({dup_pct:.2f}% of dataset)\n"
            insights += "- **Recommendation**: Review duplicates to determine if they are legitimate repeated observations or data quality issues.\n\n"
        else:
            insights += "✅ **No Duplicate Records**: Each row represents a unique observation.\n\n"
        
        insights += "---\n\n"
        
        # Column-by-Column Analysis
        insights += "## 3. Detailed Column Analysis\n\n"
        
        # Numeric Columns
        if summary['numeric_columns']:
            insights += "### 3.1 Numeric Variables (Quantitative Analysis)\n\n"
            insights += f"The dataset contains **{len(summary['numeric_columns'])} numeric columns** suitable for statistical analysis and modeling.\n\n"
            
            for col_info in summary['columns']:
                if col_info['name'] in summary['numeric_columns']:
                    insights += f"#### 📈 {col_info['name']}\n\n"
                    insights += f"**Data Type:** `{col_info['dtype']}` | "
                    insights += f"**Non-Null:** {summary['shape']['rows'] - col_info['missing']:,} ({((summary['shape']['rows'] - col_info['missing'])/summary['shape']['rows']*100):.1f}%) | "
                    insights += f"**Unique Values:** {col_info['unique']:,}\n\n"
                    
                    if 'statistics' in col_info and col_info['statistics']:
                        stats = col_info['statistics']
                        insights += "**Statistical Summary:**\n\n"
                        insights += "| Metric | Value |\n"
                        insights += "|--------|-------|\n"
                        
                        if stats.get('mean') is not None:
                            insights += f"| Mean (Average) | {stats['mean']:.4f} |\n"
                        if stats.get('median') is not None:
                            insights += f"| Median (50th Percentile) | {stats['median']:.4f} |\n"
                        if stats.get('std') is not None:
                            insights += f"| Standard Deviation | {stats['std']:.4f} |\n"
                        if stats.get('min') is not None:
                            insights += f"| Minimum Value | {stats['min']:.4f} |\n"
                        if stats.get('max') is not None:
                            insights += f"| Maximum Value | {stats['max']:.4f} |\n"
                        if stats.get('min') is not None and stats.get('max') is not None:
                            insights += f"| Range (Max - Min) | {stats['max'] - stats['min']:.4f} |\n"
                        
                        # Distribution Analysis
                        if stats.get('mean') is not None and stats.get('median') is not None:
                            insights += "\n**Distribution Characteristics:**\n"
                            if stats['mean'] > stats['median'] * 1.1:
                                insights += "- 📊 **Right-Skewed Distribution**: Mean > Median suggests a long tail of high values\n"
                                insights += "- 💡 Consider log transformation to normalize the distribution\n"
                            elif stats['mean'] < stats['median'] * 0.9:
                                insights += "- 📊 **Left-Skewed Distribution**: Mean < Median suggests a long tail of low values\n"
                            else:
                                insights += "- 📊 **Approximately Symmetric**: Mean ≈ Median indicates balanced distribution\n"
                        
                        # Variability Assessment
                        if stats.get('mean') is not None and stats.get('std') is not None and stats['mean'] != 0:
                            cv = (stats['std'] / abs(stats['mean'])) * 100
                            insights += f"- 📏 **Coefficient of Variation**: {cv:.1f}% "
                            if cv > 100:
                                insights += "(High variability - data is very spread out)\n"
                            elif cv > 30:
                                insights += "(Moderate variability)\n"
                            else:
                                insights += "(Low variability - data is concentrated around mean)\n"
                    
                    if col_info['missing'] > 0:
                        missing_pct = (col_info['missing'] / summary['shape']['rows']) * 100
                        insights += f"\n⚠️ **Missing Values**: {col_info['missing']:,} ({missing_pct:.2f}%)\n"
                    
                    insights += "\n"
        
        # Categorical Columns
        if summary['categorical_columns']:
            insights += "### 3.2 Categorical Variables (Qualitative Analysis)\n\n"
            insights += f"The dataset contains **{len(summary['categorical_columns'])} categorical columns** for grouping and segmentation.\n\n"
            
            for col_info in summary['columns']:
                if col_info['name'] in summary['categorical_columns']:
                    insights += f"#### 🏷️ {col_info['name']}\n\n"
                    insights += f"**Data Type:** `{col_info['dtype']}` | "
                    insights += f"**Non-Null:** {summary['shape']['rows'] - col_info['missing']:,} ({((summary['shape']['rows'] - col_info['missing'])/summary['shape']['rows']*100):.1f}%) | "
                    insights += f"**Unique Categories:** {col_info['unique']:,}\n\n"
                    
                    # Cardinality Assessment
                    if col_info['unique'] <= 5:
                        insights += "**Cardinality:** 🟢 Low (Excellent for one-hot encoding)\n"
                    elif col_info['unique'] <= 20:
                        insights += "**Cardinality:** 🟡 Medium (Consider frequency or target encoding)\n"
                    elif col_info['unique'] <= 100:
                        insights += "**Cardinality:** 🟠 High (Use target encoding or embeddings)\n"
                    else:
                        insights += "**Cardinality:** 🔴 Very High (Consider grouping rare categories)\n"
                    
                    if 'top_values' in col_info and col_info['top_values']:
                        insights += "\n**Top Categories:**\n\n"
                        insights += "| Category | Count | Percentage |\n"
                        insights += "|----------|-------|------------|\n"
                        
                        for cat, count in list(col_info['top_values'].items())[:10]:
                            pct = (count / summary['shape']['rows']) * 100
                            insights += f"| {cat} | {count:,} | {pct:.1f}% |\n"
                        
                        # Class Balance Analysis
                        if len(col_info['top_values']) >= 2:
                            top_values_list = list(col_info['top_values'].values())
                            if top_values_list[0] > 0:
                                balance_ratio = top_values_list[0] / (top_values_list[-1] if top_values_list[-1] > 0 else 1)
                                insights += f"\n**Class Balance Ratio:** {balance_ratio:.1f}:1 "
                                if balance_ratio > 10:
                                    insights += "(⚠️ Severe imbalance - consider SMOTE or class weights)\n"
                                elif balance_ratio > 3:
                                    insights += "(🟡 Moderate imbalance - monitor model performance per class)\n"
                                else:
                                    insights += "(✅ Well balanced)\n"
                    
                    if col_info['missing'] > 0:
                        missing_pct = (col_info['missing'] / summary['shape']['rows']) * 100
                        insights += f"\n⚠️ **Missing Values**: {col_info['missing']:,} ({missing_pct:.2f}%)\n"
                    
                    insights += "\n"
        
        # Datetime Columns
        if summary['datetime_columns']:
            insights += "### 3.3 Temporal Variables (Time-Based Analysis)\n\n"
            insights += f"The dataset contains **{len(summary['datetime_columns'])} datetime columns** for temporal analysis.\n\n"
            
            for col_info in summary['columns']:
                if col_info['name'] in summary['datetime_columns']:
                    insights += f"#### 📅 {col_info['name']}\n\n"
                    insights += f"**Data Type:** `{col_info['dtype']}`\n\n"
                    
                    if 'statistics' in col_info and col_info['statistics']:
                        stats = col_info['statistics']
                        insights += f"**Temporal Range:**\n"
                        insights += f"- Earliest: {stats.get('min', 'N/A')}\n"
                        insights += f"- Latest: {stats.get('max', 'N/A')}\n\n"
                    
                    insights += "**Recommended Feature Engineering:**\n"
                    insights += "- Extract: Year, Quarter, Month, Week, DayOfWeek, Hour\n"
                    insights += "- Create: IsWeekend, IsHoliday, IsPeakSeason flags\n"
                    insights += "- Calculate: DaysSince, RecencyScore, SeasonalityIndex\n\n"
        
        insights += "---\n\n"
        
        # Correlation Insights
        if len(summary['numeric_columns']) >= 2:
            insights += "## 4. Correlation & Relationships\n\n"
            insights += f"### Numeric Variables Available for Correlation Analysis\n\n"
            insights += f"**{len(summary['numeric_columns'])} numeric columns** can be analyzed for relationships:\n\n"
            
            for i, col in enumerate(summary['numeric_columns'], 1):
                insights += f"{i}. `{col}`\n"
            
            insights += "\n**Analysis Recommendations:**\n"
            insights += "- 📊 Review the **correlation heatmap** to identify strong positive (>0.7) or negative (<-0.7) correlations\n"
            insights += "- 🔍 Check **scatter plots** for non-linear relationships that correlation might miss\n"
            insights += "- ⚠️ Watch for **multicollinearity** (highly correlated predictors) which can affect model interpretation\n"
            insights += "- 💡 Look for **unexpected correlations** that might reveal interesting patterns\n\n"
        
        insights += "---\n\n"
        
        # Feature Engineering Recommendations
        insights += "## 5. Feature Engineering Opportunities\n\n"
        
        insights += "### 5.1 Encoding Strategies\n\n"
        low_card = [col for col in summary['columns'] if col['name'] in summary['categorical_columns'] and col['unique'] <= 10]
        high_card = [col for col in summary['columns'] if col['name'] in summary['categorical_columns'] and col['unique'] > 10]
        
        if low_card:
            insights += "**One-Hot Encoding** (Low Cardinality):\n"
            for col in low_card[:5]:
                insights += f"- `{col['name']}` ({col['unique']} categories)\n"
        
        if high_card:
            insights += "\n**Target/Frequency Encoding** (High Cardinality):\n"
            for col in high_card[:5]:
                insights += f"- `{col['name']}` ({col['unique']} categories)\n"
        
        insights += "\n### 5.2 Scaling & Normalization\n\n"
        insights += "**Recommended for these numeric columns:**\n"
        for col_info in summary['columns'][:5]:
            if col_info['name'] in summary['numeric_columns']:
                if 'statistics' in col_info and col_info['statistics']:
                    stats = col_info['statistics']
                    if stats.get('std', 0) > 1000:
                        insights += f"- `{col_info['name']}`: Use StandardScaler (high variance)\n"
                    else:
                        insights += f"- `{col_info['name']}`: Use MinMaxScaler or StandardScaler\n"
        
        insights += "\n### 5.3 Transformation Suggestions\n\n"
        for col_info in summary['columns']:
            if col_info['name'] in summary['numeric_columns'] and 'statistics' in col_info:
                stats = col_info['statistics']
                if stats.get('mean') and stats.get('median'):
                    if stats['mean'] > stats['median'] * 1.5:
                        insights += f"- `{col_info['name']}`: **Log transformation** (right-skewed)\n"
        
        insights += "\n---\n\n"
        
        # Modeling Recommendations
        insights += "## 6. Machine Learning Recommendations\n\n"
        
        insights += "### 6.1 Preprocessing Pipeline\n\n"
        insights += "**Recommended Steps:**\n\n"
        insights += "1. **Handle Missing Values**\n"
        if summary['missing_values']:
            insights += "   - Impute or drop columns with missing data\n"
        else:
            insights += "   - ✅ No action needed (complete dataset)\n"
        
        insights += "2. **Encode Categorical Variables**\n"
        insights += f"   - One-hot encode {len([c for c in summary['columns'] if c['name'] in summary['categorical_columns'] and c['unique'] <= 10])} low-cardinality columns\n"
        
        insights += "3. **Scale Numeric Features**\n"
        insights += f"   - Standardize {len(summary['numeric_columns'])} numeric columns\n"
        
        insights += "4. **Feature Engineering**\n"
        insights += "   - Create interaction terms from correlated variables\n"
        insights += "   - Extract datetime components if applicable\n"
        
        insights += "5. **Split Data**\n"
        insights += "   - Train/Test: 80/20 or 70/30\n"
        insights += "   - Use stratification for classification tasks\n"
        
        insights += "\n### 6.2 Suggested Algorithms\n\n"
        insights += "**For Regression Tasks:**\n"
        insights += "- 🌳 Random Forest Regressor (handles non-linearity, feature importance)\n"
        insights += "- 📈 Gradient Boosting (XGBoost, LightGBM) - high performance\n"
        insights += "- 📐 Ridge/Lasso Regression (if linear relationships exist)\n\n"
        
        insights += "**For Classification Tasks:**\n"
        insights += "- 🌲 Random Forest Classifier (robust, interpretable)\n"
        insights += "- 🚀 Gradient Boosting (XGBoost, CatBoost) - excellent for tabular data\n"
        insights += "- 🎯 Logistic Regression (baseline, interpretable)\n\n"
        
        insights += "**For Clustering:**\n"
        insights += "- 🔵 K-Means (for spherical clusters)\n"
        insights += "- 🌐 DBSCAN (for arbitrary shapes, outlier detection)\n\n"
        
        insights += "---\n\n"
        
        # Key Recommendations
        insights += "## 7. Key Recommendations & Next Steps\n\n"
        insights += "### Priority Actions:\n\n"
        
        priority = 1
        
        if summary['missing_values']:
            top_missing = sorted(summary['missing_values'].items(), key=lambda x: x[1], reverse=True)[0]
            pct = (top_missing[1] / summary['shape']['rows']) * 100
            insights += f"**{priority}.** Address missing values in `{top_missing[0]}` ({pct:.1f}% missing)\n"
            priority += 1
        
        if summary['duplicates'] > 0:
            insights += f"**{priority}.** Investigate and handle {summary['duplicates']:,} duplicate records\n"
            priority += 1
        
        insights += f"**{priority}.** Review correlation heatmap for multicollinearity\n"
        priority += 1
        
        insights += f"**{priority}.** Examine distribution plots (histograms, box plots) for outliers\n"
        priority += 1
        
        insights += f"**{priority}.** Perform feature engineering (interactions, transformations)\n"
        priority += 1
        
        insights += f"**{priority}.** Select appropriate model based on problem type\n\n"
        
        insights += "### Visualization Checklist:\n\n"
        insights += "- ✅ Distribution plots generated for numeric variables\n"
        insights += "- ✅ Box plots available for outlier detection\n"
        insights += "- ✅ Correlation heatmap created\n"
        insights += "- ✅ Bar charts generated for categorical variables\n\n"
        
        insights += "---\n\n"
        
        # Footer
        insights += "## 🔧 Enable Advanced AI Insights\n\n"
        insights += "**This analysis is rule-based.** For advanced pattern recognition, business insights, and detailed recommendations:\n\n"
        insights += "1. Get a free API key from [Google AI Studio](https://ai.google.dev/)\n"
        insights += "2. Add to `.env` file: `GEMINI_API_KEY=your_actual_key`\n"
        insights += "3. Restart the server\n\n"
        insights += "**AI-powered insights include:**\n"
        insights += "- 🧠 Intelligent pattern recognition across all variables\n"
        insights += "- 📊 Visual analysis of charts and graphs\n"
        insights += "- 💼 Business-focused recommendations\n"
        insights += "- 🔬 Advanced statistical interpretations\n"
        insights += "- 🎯 Specific modeling strategies\n"
        insights += "- 📈 Predictive insights and opportunities\n\n"
        
        insights += "---\n\n"
        insights += f"*Report generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        # Add chart visualizations if available
        if chart_paths:
            insights = self._embed_charts_in_insights(insights, chart_paths)
        
        return insights
