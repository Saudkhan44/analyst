"""
Dataset schemas using Pydantic v2.

Request and response models for dataset operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class ColumnInfo(BaseModel):
    """Information about a dataset column."""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Data type: numeric, categorical, datetime, text")
    missing_count: int = Field(default=0, description="Number of missing values")
    unique_count: int = Field(default=0, description="Number of unique values")


class DatasetCreate(BaseModel):
    """Schema for dataset creation (after file upload)."""

    filename: str = Field(..., description="Original filename")
    storage_path: str = Field(..., description="Path in storage")
    rows: int = Field(..., gt=0, description="Number of rows")
    columns: int = Field(..., gt=0, description="Number of columns")
    column_info: Optional[List[ColumnInfo]] = Field(default=None, description="Column metadata")


class DatasetResponse(BaseModel):
    """Schema for dataset response."""

    id: UUID = Field(..., description="Dataset ID")
    filename: str = Field(..., description="Original filename")
    rows: int = Field(..., description="Number of rows")
    columns: int = Field(..., description="Number of columns")
    column_info: Optional[List[ColumnInfo]] = Field(default=None, description="Column metadata")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Schema for list of datasets."""

    datasets: List[DatasetResponse] = Field(..., description="List of datasets")
    count: int = Field(..., ge=0, description="Total number of datasets")


class DatasetTableResponse(BaseModel):
    """Schema for dataset table preview."""

    id: UUID = Field(..., description="Dataset ID")
    filename: str = Field(..., description="Original filename")
    rows: int = Field(..., description="Number of rows")
    columns: int = Field(..., description="Number of columns")
    data: List[Dict[str, Any]] = Field(..., description="Table data (first 100 rows)")
    column_types: Dict[str, str] = Field(..., description="Column data types")


class UploadResponse(BaseModel):
    """Schema for file upload response."""

    id: UUID = Field(..., description="Dataset ID")
    filename: str = Field(..., description="Original filename")
    rows: int = Field(..., description="Number of rows")
    columns: int = Field(..., description="Number of columns")
    message: str = Field(..., description="Success message")


class DeleteDatasetResponse(BaseModel):
    """Schema for dataset deletion response."""

    message: str = Field(..., description="Success message")
    id: UUID = Field(..., description="Deleted dataset ID")
