"""
Dashboard service layer.

Handles business logic for dashboard operations and chart generation.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
import pandas as pd
import json

from app.core.database import Dashboard, Dataset
from app.modules.dashboard.chart_engine import ChartEngine
from app.modules.dashboard.schemas import DashboardSummary, KPIData, ChartData
from app.modules.datasets.service import DatasetService

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard operations."""

    def __init__(self, db: Session):
        """
        Initialize dashboard service.

        Args:
            db: Database session
        """
        self.db = db

    def generate_dashboard(
        self,
        dataset_id: str,
        user_id: str,
        df: pd.DataFrame,
    ) -> Dashboard:
        """
        Generate dashboard for a dataset.

        Args:
            dataset_id: Dataset ID
            user_id: User ID
            df: DataFrame to analyze

        Returns:
            Dashboard: Created dashboard model

        Raises:
            Exception: If generation fails
        """
        try:
            # Initialize chart engine
            engine = ChartEngine(df)

            # Generate summary
            summary_data = engine.generate_summary()
            summary = DashboardSummary(
                total_rows=summary_data["total_rows"],
                total_columns=summary_data["total_columns"],
                kpis=[KPIData(**kpi) for kpi in summary_data["kpis"]],
                column_summaries=summary_data["column_summaries"],
            )

            # Generate chart recommendations
            charts_data = engine.recommend_charts(limit=5)
            charts = [ChartData(**chart) for chart in charts_data]

            # Create dashboard record
            dashboard = Dashboard(
              id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            summary=summary.model_dump(),
            charts=[chart.model_dump() for chart in charts],
            created_at=datetime.utcnow(),
)

            self.db.add(dashboard)
            self.db.commit()
            self.db.refresh(dashboard)

            logger.info(f"Dashboard generated: {dashboard.id} for dataset {dataset_id}")
            return dashboard
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating dashboard: {str(e)}")
            raise

    def get_dashboard(self, dataset_id: str, user_id: str) -> Optional[Dashboard]:
        """
        Get dashboard for a dataset.

        Args:
            dataset_id: Dataset ID
            user_id: User ID

        Returns:
            Dashboard: Dashboard model or None
        """
        try:
            # Verify dataset belongs to user
            dataset = self.db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.user_id == user_id,
            ).first()

            if not dataset:
                return None

            # Get or create dashboard
            dashboard = self.db.query(Dashboard).filter(
                Dashboard.dataset_id == dataset_id
            ).first()

            if not dashboard:
                # Generate new dashboard if it doesn't exist
                dataset_service = DatasetService(self.db)
                df = dataset_service.read_uploaded_file(dataset.storage_path)
                dashboard = self.generate_dashboard(dataset_id, user_id, df)

            return dashboard
        except Exception as e:
            logger.error(f"Error getting dashboard: {str(e)}")
            raise

    def delete_dashboard(self, dataset_id: str) -> bool:
        """
        Delete dashboard for a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            bool: True if successful
        """
        try:
            dashboard = self.db.query(Dashboard).filter(
                Dashboard.dataset_id == dataset_id
            ).first()

            if dashboard:
                self.db.delete(dashboard)
                self.db.commit()
                logger.info(f"Dashboard deleted: {dashboard.id}")
                return True

            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting dashboard: {str(e)}")
            raise
