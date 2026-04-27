from pydantic import BaseModel
from typing import List
from app.schemas.property import PropertySummary


class DashboardStats(BaseModel):
    """Dashboard statistics schema."""
    total_properties: int
    total_active_tenants: int
    rent_collected_this_month: float
    rent_outstanding_this_month: float
    open_issues: int
    delayed_payments: int
    waitlist_total: int
    properties_summary: List[PropertySummary]
