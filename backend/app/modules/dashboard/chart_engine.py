"""
Chart engine for generating dashboard recommendations.

Core logic for chart type recommendations and data aggregation.
"""

import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from enum import Enum

from app.shared.pandas_utils import (
    detect_column_types,
    get_numeric_columns,
    get_categorical_columns,
    get_datetime_columns,
    ColumnType,
)

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Supported chart types."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"


class ChartEngine:
    """Engine for generating chart recommendations and data."""

    def __init__(self, df: pd.DataFrame):
        """
        Initialize chart engine with DataFrame.

        Args:
            df: Input DataFrame
        """
        self.df = df
        self.column_types = detect_column_types(df)
        self.numeric_cols = get_numeric_columns(df)
        self.categorical_cols = get_categorical_columns(df)
        self.datetime_cols = get_datetime_columns(df)

    def recommend_charts(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Generate chart recommendations based on data.

        Args:
            limit: Maximum number of charts to recommend

        Returns:
            list: List of recommended chart objects
        """
        charts = []

        # Recommend bar charts for categorical data with numeric values
        if self.categorical_cols and self.numeric_cols:
            for cat_col in self.categorical_cols[:2]:
                for num_col in self.numeric_cols[:2]:
                    if len(charts) < limit:
                        chart = self._create_bar_chart(cat_col, num_col)
                        if chart:
                            charts.append(chart)

        # Recommend pie charts for categorical data with counts
        if self.categorical_cols and len(charts) < limit:
            chart = self._create_pie_chart(self.categorical_cols[0])
            if chart:
                charts.append(chart)

        # Recommend line charts for time series if datetime columns exist
        if self.datetime_cols and self.numeric_cols and len(charts) < limit:
            chart = self._create_line_chart(self.datetime_cols[0], self.numeric_cols[0])
            if chart:
                charts.append(chart)

        # Recommend scatter plots for multiple numeric columns
        if len(self.numeric_cols) >= 2 and len(charts) < limit:
            chart = self._create_scatter_chart(self.numeric_cols[0], self.numeric_cols[1])
            if chart:
                charts.append(chart)

        # Recommend histograms for numeric distributions
        if self.numeric_cols and len(charts) < limit:
            chart = self._create_histogram(self.numeric_cols[0])
            if chart:
                charts.append(chart)

        return charts[:limit]

    def _create_bar_chart(self, category_col: str, value_col: str) -> Dict[str, Any]:
        """
        Create bar chart data.

        Args:
            category_col: Categorical column name
            value_col: Numeric column name

        Returns:
            dict: Chart object or None
        """
        try:
            # Group and aggregate
            grouped = self.df.groupby(category_col)[value_col].agg(["sum", "count", "mean"])
            grouped = grouped.reset_index()

            # Limit categories for readability
            if len(grouped) > 20:
                grouped = grouped.nlargest(20, "sum")

            data = []
            for _, row in grouped.iterrows():
                data.append({
                    "category": str(row[category_col]),
                    "value": float(row["sum"]),
                    "count": int(row["count"]),
                    "average": float(row["mean"]),
                })

            return {
                "chart_type": ChartType.BAR,
                "title": f"{value_col} by {category_col}",
                "x_axis": category_col,
                "y_axis": value_col,
                "data": data,
                "metadata": {
                    "total_categories": len(grouped),
                    "aggregation": "sum",
                },
            }
        except Exception as e:
            logger.warning(f"Could not create bar chart for {category_col}, {value_col}: {str(e)}")
            return None

    def _create_pie_chart(self, category_col: str) -> Dict[str, Any]:
        """
        Create pie chart data.

        Args:
            category_col: Categorical column name

        Returns:
            dict: Chart object or None
        """
        try:
            # Count values
            counts = self.df[category_col].value_counts()

            # Limit slices for readability
            if len(counts) > 10:
                counts = counts.head(10)

            data = []
            for category, count in counts.items():
                data.append({
                    "category": str(category),
                    "value": int(count),
                })

            return {
                "chart_type": ChartType.PIE,
                "title": f"Distribution of {category_col}",
                "data": data,
                "metadata": {
                    "total_categories": len(counts),
                },
            }
        except Exception as e:
            logger.warning(f"Could not create pie chart for {category_col}: {str(e)}")
            return None

    def _create_line_chart(self, datetime_col: str, value_col: str) -> Dict[str, Any]:
        """
        Create line chart data.

        Args:
            datetime_col: Datetime column name
            value_col: Numeric column name

        Returns:
            dict: Chart object or None
        """
        try:
            # Sort by datetime
            df_sorted = self.df.sort_values(datetime_col)

            # Group by date and aggregate
            df_sorted[datetime_col] = pd.to_datetime(df_sorted[datetime_col])
            grouped = df_sorted.groupby(df_sorted[datetime_col].dt.date)[value_col].mean()

            data = []
            for date, value in grouped.items():
                data.append({
                    "date": str(date),
                    "value": float(value),
                })

            return {
                "chart_type": ChartType.LINE,
                "title": f"{value_col} over Time",
                "x_axis": datetime_col,
                "y_axis": value_col,
                "data": data,
                "metadata": {
                    "total_points": len(data),
                },
            }
        except Exception as e:
            logger.warning(f"Could not create line chart for {datetime_col}, {value_col}: {str(e)}")
            return None

    def _create_scatter_chart(self, x_col: str, y_col: str) -> Dict[str, Any]:
        """
        Create scatter plot data.

        Args:
            x_col: X-axis numeric column
            y_col: Y-axis numeric column

        Returns:
            dict: Chart object or None
        """
        try:
            # Sample if too many points
            df_sample = self.df[[x_col, y_col]].dropna()
            if len(df_sample) > 1000:
                df_sample = df_sample.sample(n=1000)

            data = []
            for _, row in df_sample.iterrows():
                data.append({
                    "x": float(row[x_col]),
                    "y": float(row[y_col]),
                })

            return {
                "chart_type": ChartType.SCATTER,
                "title": f"{y_col} vs {x_col}",
                "x_axis": x_col,
                "y_axis": y_col,
                "data": data,
                "metadata": {
                    "total_points": len(data),
                },
            }
        except Exception as e:
            logger.warning(f"Could not create scatter chart for {x_col}, {y_col}: {str(e)}")
            return None

    def _create_histogram(self, numeric_col: str, bins: int = 20) -> Dict[str, Any]:
        """
        Create histogram data.

        Args:
            numeric_col: Numeric column name
            bins: Number of histogram bins

        Returns:
            dict: Chart object or None
        """
        try:
            # Create histogram
            counts, edges = np.histogram(self.df[numeric_col].dropna(), bins=bins)

            data = []
            for i in range(len(counts)):
                data.append({
                    "bin": f"{edges[i]:.2f}-{edges[i+1]:.2f}",
                    "count": int(counts[i]),
                })

            return {
                "chart_type": ChartType.HISTOGRAM,
                "title": f"Distribution of {numeric_col}",
                "x_axis": numeric_col,
                "y_axis": "Frequency",
                "data": data,
                "metadata": {
                    "bins": bins,
                    "total_count": int(counts.sum()),
                },
            }
        except Exception as e:
            logger.warning(f"Could not create histogram for {numeric_col}: {str(e)}")
            return None

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate dashboard summary with KPIs.

        Returns:
            dict: Summary with KPIs and statistics
        """
        summary = {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "kpis": [],
            "column_summaries": {},
        }

        # Generate KPIs
        # Overall completeness
        total_cells = len(self.df) * len(self.df.columns)
        missing_cells = self.df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 100

        summary["kpis"].append({
            "label": "Data Completeness",
            "value": round(completeness, 2),
            "unit": "%",
        })

        # Numeric columns stats
        if self.numeric_cols:
            for col in self.numeric_cols[:3]:  # Top 3 numeric columns
                col_data = self.df[col].dropna()
                summary["kpis"].append({
                    "label": f"{col} Average",
                    "value": round(float(col_data.mean()), 2),
                    "unit": None,
                })

        # Generate column summaries
        for col in self.df.columns:
            col_type = self.column_types.get(col, "unknown")
            col_summary = {
                "type": col_type,
                "non_null_count": int(self.df[col].notna().sum()),
                "null_count": int(self.df[col].isnull().sum()),
                "unique_count": int(self.df[col].nunique()),
            }

            if col_type == ColumnType.NUMERIC:
                col_summary.update({
                    "min": float(self.df[col].min()),
                    "max": float(self.df[col].max()),
                    "mean": float(self.df[col].mean()),
                    "median": float(self.df[col].median()),
                })

            summary["column_summaries"][col] = col_summary

        return summary
