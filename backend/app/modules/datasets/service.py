"""
Dataset service layer.

Handles business logic for dataset operations.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import os
from sqlalchemy.orm import Session
import pandas as pd

from app.core.database import Dataset, ChatSession, Dashboard
from app.modules.datasets.schemas import ColumnInfo
from app.shared.storage import (
    save_uploaded_file,
    read_csv_file,
    read_excel_file,
    delete_file,
)
from app.shared.pandas_utils import (
    validate_dataframe,
    get_column_statistics,
    detect_column_types,
)

logger = logging.getLogger(__name__)


class DatasetService:
    """Service for dataset operations."""

    def __init__(self, db: Session):
        """
        Initialize dataset service.

        Args:
            db: Database session
        """
        self.db = db

    def create_dataset(
        self,
        user_id: str,
        filename: str,
        storage_path: str,
        df: pd.DataFrame,
        column_info: List[ColumnInfo] = None,
    ) -> Dataset:
        """
        Create new dataset record in database.

        Args:
            user_id: User ID
            filename: Original filename
            storage_path: Path in storage
            df: Processed DataFrame
            column_info: Column metadata

        Returns:
            Dataset: Created dataset model

        Raises:
            Exception: If database operation fails
        """
        try:
            dataset = Dataset(
                id=str(uuid.uuid4()),
                user_id=user_id,
                filename=filename,
                storage_path=storage_path,
                rows=len(df),
                columns=len(df.columns),
                column_info=[col.model_dump() for col in column_info] if column_info else None,
                created_at=datetime.utcnow(),
            )

            self.db.add(dataset)
            self.db.commit()
            self.db.refresh(dataset)

            logger.info(f"Dataset created: {dataset.id}")
            return dataset
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating dataset: {str(e)}")
            raise

    def get_dataset_by_id(self, dataset_id: str, user_id: str) -> Optional[Dataset]:
        """
        Get dataset by ID for a specific user.

        Args:
            dataset_id: Dataset ID
            user_id: User ID

        Returns:
            Dataset: Dataset model or None
        """
        return self.db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
        ).first()

    def get_user_datasets(self, user_id: str, limit: int = 100) -> List[Dataset]:
        """
        Get all datasets for a user.

        Args:
            user_id: User ID
            limit: Maximum number of datasets to return

        Returns:
            list: List of datasets
        """
        return self.db.query(Dataset).filter(
            Dataset.user_id == user_id,
        ).order_by(Dataset.created_at.desc()).limit(limit).all()

    def delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        """
        Delete dataset and associated data.

        Args:
            dataset_id: Dataset ID
            user_id: User ID

        Returns:
            bool: True if successful

        Raises:
            Exception: If operation fails
        """
        try:
            dataset = self.get_dataset_by_id(dataset_id, user_id)
            if not dataset:
                return False

            # Delete file from storage
            if os.path.exists(dataset.storage_path):
                delete_file(dataset.storage_path)

            # Delete dashboard
            dashboard = self.db.query(Dashboard).filter(
                Dashboard.dataset_id == dataset_id
            ).first()
            if dashboard:
                self.db.delete(dashboard)

            # Delete chat sessions and messages
            chat_sessions = self.db.query(ChatSession).filter(
                ChatSession.dataset_id == dataset_id
            ).all()
            for session in chat_sessions:
                # ChatMessages will be cascade deleted if foreign key is set up
                self.db.delete(session)

            # Delete dataset
            self.db.delete(dataset)
            self.db.commit()

            logger.info(f"Dataset deleted: {dataset_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting dataset: {str(e)}")
            raise

    def read_uploaded_file(self, file_path: str) -> pd.DataFrame:
        """
        Read uploaded file into DataFrame.

        Args:
            file_path: Path to uploaded file

        Returns:
            pd.DataFrame: Data from file

        Raises:
            Exception: If file cannot be read
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".csv":
            return read_csv_file(file_path)
        elif file_ext in [".xlsx", ".xls"]:
            return read_excel_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def process_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process dataset and extract metadata.

        Args:
            df: Input DataFrame

        Returns:
            dict: Processed data including statistics and column info

        Raises:
            Exception: If processing fails
        """
        try:
            # Validate
            is_valid, error_msg = validate_dataframe(df)
            if not is_valid:
                raise ValueError(error_msg)

            # Get column statistics
            stats = get_column_statistics(df)
            column_types = detect_column_types(df)

            # Create column info objects
            column_info = [
                ColumnInfo(
                    name=col,
                    type=column_types[col],
                    missing_count=stats[col].get("missing_count", 0),
                    unique_count=stats[col].get("unique_count", 0),
                )
                for col in df.columns
            ]

            logger.info(f"Dataset processed: {len(df)} rows, {len(df.columns)} columns")

            return {
                "column_info": column_info,
                "statistics": stats,
                "column_types": column_types,
            }
        except Exception as e:
            logger.error(f"Error processing dataset: {str(e)}")
            raise
