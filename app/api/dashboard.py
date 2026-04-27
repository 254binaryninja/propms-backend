from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models import AdminUser
from app.schemas.dashboard import DashboardStats
from app.services.analytics_service import get_dashboard_stats

router = APIRouter()


@router.get("", response_model=DashboardStats, status_code=status.HTTP_200_OK)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Get aggregated dashboard statistics."""
    return get_dashboard_stats(db)
