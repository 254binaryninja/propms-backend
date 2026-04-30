from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from uuid import UUID
from app.models import (
    Property, Tenant, Payment, Issue, WaitlistEntry,
    TenantStatus, PaymentStatus, IssueStatus
)
from app.schemas.dashboard import DashboardStats
from app.schemas.property import PropertySummary


def get_dashboard_stats(db: Session, admin_id: UUID) -> DashboardStats:
    """
    Calculate and return dashboard statistics for a specific admin.

    Args:
        db: Database session
        admin_id: Admin user ID to filter properties

    Returns:
        DashboardStats object with aggregated data scoped to admin
    """
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    # Total properties (filtered by admin)
    total_properties = db.query(func.count(Property.id)).filter(
        Property.admin_id == admin_id
    ).scalar() or 0

    # Total active tenants (filtered by admin's properties)
    total_active_tenants = db.query(func.count(Tenant.id)).join(Property).filter(
        Property.admin_id == admin_id,
        Tenant.status == TenantStatus.ACTIVE
    ).scalar() or 0

    # Rent collected this month (filtered by admin's properties)
    rent_collected = db.query(func.sum(Payment.amount)).join(Tenant).join(Property).filter(
        Property.admin_id == admin_id,
        Payment.status == PaymentStatus.PAID,
        func.extract('month', Payment.paid_date) == current_month,
        func.extract('year', Payment.paid_date) == current_year
    ).scalar() or 0.0

    # Rent outstanding (filtered by admin's properties)
    rent_outstanding = db.query(func.sum(Payment.amount)).join(Tenant).join(Property).filter(
        Property.admin_id == admin_id,
        Payment.status == PaymentStatus.OVERDUE
    ).scalar() or 0.0

    # Open issues (filtered by admin's properties)
    open_issues = db.query(func.count(Issue.id)).join(Tenant).join(Property).filter(
        Property.admin_id == admin_id,
        Issue.status != IssueStatus.RESOLVED
    ).scalar() or 0

    # Delayed payments (filtered by admin's properties)
    delayed_payments = db.query(func.count(Payment.id)).join(Tenant).join(Property).filter(
        Property.admin_id == admin_id,
        Payment.status == PaymentStatus.OVERDUE
    ).scalar() or 0

    # Waitlist total (filtered by admin's properties)
    waitlist_total = db.query(func.count(WaitlistEntry.id)).join(Property).filter(
        Property.admin_id == admin_id
    ).scalar() or 0

    # Properties summary (filtered by admin)
    properties = db.query(Property).filter(Property.admin_id == admin_id).all()
    properties_summary = []

    for prop in properties:
        occupied_units = db.query(func.count(Tenant.id)).filter(
            Tenant.property_id == prop.id,
            Tenant.status == TenantStatus.ACTIVE
        ).scalar() or 0

        vacant_units = prop.total_units - occupied_units
        occupancy_rate = (occupied_units / prop.total_units * 100) if prop.total_units > 0 else 0.0

        properties_summary.append(PropertySummary(
            id=prop.id,
            name=prop.name,
            total_units=prop.total_units,
            occupied_units=occupied_units,
            vacant_units=vacant_units,
            occupancy_rate=round(occupancy_rate, 2)
        ))

    return DashboardStats(
        total_properties=total_properties,
        total_active_tenants=total_active_tenants,
        rent_collected_this_month=float(rent_collected),
        rent_outstanding_this_month=float(rent_outstanding),
        open_issues=open_issues,
        delayed_payments=delayed_payments,
        waitlist_total=waitlist_total,
        properties_summary=properties_summary
    )
