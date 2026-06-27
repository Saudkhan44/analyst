"""
Shared Pandas utilities for data processing.

Handles data validation, type detection, and statistical calculations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ColumnType(str, Enum):
    """Data type classifications."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"


def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Detect the type of each column in a DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        dict: Column names mapped to their detected types
    """
    column_types = {}

    for col in df.columns:
        dtype = df[col].dtype

        # Check for datetime
        if pd.api.types.is_datetime64_any_dtype(dtype):
            column_types[col] = ColumnType.DATETIME
        # Check for numeric
        elif pd.api.types.is_numeric_dtype(dtype):
            column_types[col] = ColumnType.NUMERIC
        # Check for categorical (low cardinality strings)
        elif pd.api.types.is_string_dtype(dtype) or dtype == "object":
            unique_ratio = df[col].nunique() / len(df[col])
            if unique_ratio < 0.05 or df[col].nunique() < 50:
                column_types[col] = ColumnType.CATEGORICAL
            else:
                column_types[col] = ColumnType.TEXT
        else:
            column_types[col] = ColumnType.TEXT

    return column_types


def get_column_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate statistics for all columns.

    Args:
        df: Input DataFrame

    Returns:
        dict: Column statistics including missing values and basic stats
    """
    stats = {}
    column_types = detect_column_types(df)

    for col in df.columns:
        col_type = column_types[col]
        missing_count = int(df[col].isnull().sum())
        unique_count = int(df[col].nunique())

        stats[col] = {
            "type": col_type,
            "missing_count": missing_count,
            "unique_count": unique_count,
            "non_null_count": int(df[col].notna().sum()),
        }

        # Add type-specific statistics
        if col_type == ColumnType.NUMERIC:
            stats[col].update(
                {
                    "min": float(df[col].min()) if df[col].notna().any() else None,
                    "max": float(df[col].max()) if df[col].notna().any() else None,
                    "mean": float(df[col].mean()) if df[col].notna().any() else None,
                    "median": float(df[col].median()) if df[col].notna().any() else None,
                    "std": float(df[col].std()) if df[col].notna().any() else None,
                }
            )
        elif col_type == ColumnType.CATEGORICAL:
            top_values = df[col].value_counts().head(5).to_dict()
            stats[col]["top_values"] = {str(k): int(v) for k, v in top_values.items()}

    return stats


def validate_dataframe(df: pd.DataFrame, min_rows: int = 2) -> Tuple[bool, str]:
    """
    Validate a DataFrame for analytics.

    Args:
        df: DataFrame to validate
        min_rows: Minimum required rows

    Returns:
        tuple: (is_valid, error_message)
    """
    if df is None or df.empty:
        return False, "Dataset is empty"

    if len(df) < min_rows:
        return False, f"Dataset has fewer than {min_rows} rows"

    if len(df.columns) == 0:
        return False, "Dataset has no columns"

    # Check if all columns are missing
    if df.isnull().all().all():
        return False, "All data is missing"

    return True, ""


def prepare_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for aggregation operations.

    Handles type conversions and missing value treatment.

    Args:
        df: Input DataFrame

    Returns:
        pd.DataFrame: Prepared DataFrame
    """
    df_copy = df.copy()

    # Convert datetime columns
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            continue
        try:
            # Try to convert to datetime if looks like dates
            if df_copy[col].dtype == "object" and df_copy[col].notna().any():
                sample = df_copy[col].dropna().iloc[0]
                if isinstance(sample, str):
                    df_copy[col] = pd.to_datetime(df_copy[col], errors="coerce")
        except Exception:
            pass

    return df_copy


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of numeric columns.

    Args:
        df: Input DataFrame

    Returns:
        list: Numeric column names
    """
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of categorical columns.

    Args:
        df: Input DataFrame

    Returns:
        list: Categorical column names
    """
    column_types = detect_column_types(df)
    return [col for col, dtype in column_types.items() if dtype == ColumnType.CATEGORICAL]


def get_datetime_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of datetime columns.

    Args:
        df: Input DataFrame

    Returns:
        list: Datetime column names
    """
    return df.select_dtypes(include=["datetime64"]).columns.tolist()
