"""
Dashboard schemas using Pydantic v2.

Request and response models for dashboard operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID


class ChartData(BaseModel):
    """Chart data structure."""

    chart_type: str = Field(..., description="Type of chart: bar, line, pie, scatter, histogram")
    title: str = Field(..., description="Chart title")
    x_axis: Optional[str] = Field(default=None, description="X-axis label")
    y_axis: Optional[str] = Field(default=None, description="Y-axis label")
    data: List[Dict[str, Any]] = Field(..., description="Chart data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class KPIData(BaseModel):
    """Key Performance Indicator."""

    label: str = Field(..., description="KPI label")
    value: Any = Field(..., description="KPI value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    change: Optional[float] = Field(default=None, description="Change percentage")


class DashboardSummary(BaseModel):
    """Dashboard summary with KPIs."""

    total_rows: int = Field(..., description="Total number of rows")
    total_columns: int = Field(..., description="Total number of columns")
    kpis: List[KPIData] = Field(..., description="Key metrics")
    column_summaries: Dict[str, Any] = Field(..., description="Per-column statistics")


class DashboardResponse(BaseModel):
    """Complete dashboard response."""

    id: UUID = Field(..., description="Dashboard ID")
    dataset_id: UUID = Field(..., description="Associated dataset ID")
    summary: DashboardSummary = Field(..., description="Dashboard summary")
    charts: List[ChartData] = Field(..., description="Recommended charts")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class ChartRecommendationRequest(BaseModel):
    """Request for chart recommendations."""

    dataset_id: UUID = Field(..., description="Dataset ID")
