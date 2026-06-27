"""
Dashboard API routes.

Endpoints for retrieving dashboard data and visualizations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser
from app.modules.auth.dependencies import get_current_user
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.schemas import DashboardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/{dataset_id}", response_model=DashboardResponse)
async def get_dashboard(
    dataset_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """
    Get dashboard for a dataset.

    Returns dashboard summary, KPIs, and recommended charts.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        DashboardResponse: Dashboard with summary and charts

    Raises:
        HTTPException: If dataset not found
    """
    try:
        service = DashboardService(db)
        dashboard = service.get_dashboard(dataset_id, str(current_user.user_id))

        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        logger.info(f"Dashboard retrieved by {current_user.email}: {dataset_id}")

        return DashboardResponse.model_validate(dashboard)

    except HTTPException:
        raise
    except Exception as e:
      import traceback
      traceback.print_exc()

      raise HTTPException(
        status_code=500,
        detail=str(e),
    )