"""
Dataset API routes.

Endpoints for uploading, retrieving, and managing datasets.
"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.modules.auth.dependencies import get_current_user
from app.modules.datasets.service import DatasetService
from app.modules.datasets.schemas import (
    DatasetResponse,
    DatasetListResponse,
    DatasetTableResponse,
    UploadResponse,
    DeleteDatasetResponse,
)
from app.shared.storage import validate_file_type, validate_file_size
import os
import uuid
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """
    Upload and process a CSV or Excel file.

    Creates a new dataset and generates dashboard data.

    Args:
        file: Uploaded file (CSV or Excel)
        current_user: Current authenticated user
        db: Database session

    Returns:
        UploadResponse: Dataset ID and basic info

    Raises:
        HTTPException: For validation errors
    """
    try:
        # Validate file type
        is_valid, error_msg = validate_file_type(file.filename)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # Read file content
        content = await file.read()

        # Validate file size
        is_valid, error_msg = validate_file_size(len(content))
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # Save file
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1].lower()
        file_path = os.path.join(str(current_user.user_id), f"{file_id}{file_ext}")
        
        from app.shared.storage import save_uploaded_file
        success, full_path = save_uploaded_file(file_path, content)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file",
            )

        # Read and process file
        service = DatasetService(db)
        df = service.read_uploaded_file(full_path)

        # Process dataset
        processed_data = service.process_dataset(df)

        # Create dataset record
        dataset = service.create_dataset(
            user_id=str(current_user.user_id),
            filename=file.filename,
            storage_path=full_path,
            df=df,
            column_info=processed_data["column_info"],
        )

        logger.info(f"Dataset uploaded by {current_user.email}: {dataset.id}")

        return UploadResponse(
            id=dataset.id,
            filename=dataset.filename,
            rows=dataset.rows,
            columns=dataset.columns,
            message="Dataset uploaded and processed successfully",
        )

    except HTTPException:
        raise
    except Exception:
      logger.exception("Error uploading dataset")

      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error processing file",
    )


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetListResponse:
    """
    Get all datasets for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        DatasetListResponse: List of user's datasets
    """
    try:
        service = DatasetService(db)
        datasets = service.get_user_datasets(str(current_user.user_id))

        return DatasetListResponse(
            datasets=[DatasetResponse.model_validate(ds) for ds in datasets],
            count=len(datasets),
        )
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving datasets",
        )


@router.get("/{dataset_id}/table", response_model=DatasetTableResponse)
async def get_dataset_table(
    dataset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DatasetTableResponse:
    """
    Get dataset table preview (first 100 rows).

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        DatasetTableResponse: Table preview

    Raises:
        HTTPException: If dataset not found
    """
    try:
        service = DatasetService(db)
        dataset = service.get_dataset_by_id(dataset_id, str(current_user.user_id))

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        # Read file
        df = service.read_uploaded_file(dataset.storage_path)

        # Get first 100 rows
        preview_df = df.head(100)

        # Convert to records
        records = preview_df.to_dict("records")

        # Get column types
        from app.shared.pandas_utils import detect_column_types
        column_types = detect_column_types(df)

        return DatasetTableResponse(
            id=dataset.id,
            filename=dataset.filename,
            rows=dataset.rows,
            columns=dataset.columns,
            data=records,
            column_types=column_types,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset table: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving dataset",
        )


@router.delete("/{dataset_id}", response_model=DeleteDatasetResponse)
async def delete_dataset(
    dataset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeleteDatasetResponse:
    """
    Delete a dataset and all associated data.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        DeleteDatasetResponse: Confirmation message

    Raises:
        HTTPException: If dataset not found
    """
    try:
        service = DatasetService(db)
        success = service.delete_dataset(dataset_id, str(current_user.user_id))

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        logger.info(f"Dataset deleted by {current_user.email}: {dataset_id}")

        return DeleteDatasetResponse(
            message="Dataset deleted successfully",
            id=dataset_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting dataset",
        )
