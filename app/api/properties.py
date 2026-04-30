from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
from app.api.deps import get_db, get_current_admin
from app.models import Property, Tenant, Payment, AdminUser, TenantStatus, PaymentStatus
from app.schemas.property import Property as PropertySchema, PropertyCreate, PropertyUpdate
from app.schemas.common import PaginatedMeta
from datetime import datetime

router = APIRouter()


def calculate_property_metrics(db: Session, property_obj: Property) -> dict:
    """Calculate derived metrics for a property."""
    # Count active tenants
    occupied_units = db.query(Tenant).filter(
        Tenant.property_id == property_obj.id,
        Tenant.status == TenantStatus.ACTIVE
    ).count()

    # Calculate vacant units
    vacant_units = property_obj.total_units - occupied_units

    # Calculate occupancy rate
    occupancy_rate = (occupied_units / property_obj.total_units * 100) if property_obj.total_units > 0 else 0.0

    # Calculate monthly rent collected (current month)
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    monthly_rent = db.query(func.sum(Payment.amount)).join(Tenant).filter(
        Tenant.property_id == property_obj.id,
        Payment.status == PaymentStatus.PAID,
        func.extract('month', Payment.paid_date) == current_month,
        func.extract('year', Payment.paid_date) == current_year
    ).scalar() or 0.0

    return {
        "occupied_units": occupied_units,
        "vacant_units": vacant_units,
        "occupancy_rate": round(occupancy_rate, 2),
        "monthly_rent_collected": float(monthly_rent)
    }


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
def list_properties(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """List all properties with derived metrics."""
    properties = db.query(Property).all()

    properties_data = []
    for prop in properties:
        metrics = calculate_property_metrics(db, prop)
        prop_dict = {
            "id": prop.id,
            "name": prop.name,
            "total_units": prop.total_units,
            "created_at": prop.created_at,
            **metrics
        }
        properties_data.append(prop_dict)

    return {
        "data": properties_data,
        "meta": PaginatedMeta(
            total=len(properties_data),
            page=1,
            per_page=len(properties_data),
            pages=1
        )
    }


@router.post("", response_model=PropertySchema, status_code=status.HTTP_201_CREATED)
def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Create a new property."""
    new_property = Property(
        name=property_data.name,
        total_units=property_data.total_units,
        admin_id=current_user.id
    )

    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Calculate metrics
    metrics = calculate_property_metrics(db, new_property)

    return PropertySchema(
        id=new_property.id,
        name=new_property.name,
        total_units=new_property.total_units,
        created_at=new_property.created_at,
        **metrics
    )


@router.get("/{property_id}", response_model=PropertySchema, status_code=status.HTTP_200_OK)
def get_property(
    property_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Get a single property by ID."""
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    metrics = calculate_property_metrics(db, property_obj)

    return PropertySchema(
        id=property_obj.id,
        name=property_obj.name,
        total_units=property_obj.total_units,
        created_at=property_obj.created_at,
        **metrics
    )


@router.patch("/{property_id}", response_model=PropertySchema, status_code=status.HTTP_200_OK)
def update_property(
    property_id: UUID,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Update a property."""
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Update fields
    if property_data.name is not None:
        property_obj.name = property_data.name
    if property_data.total_units is not None:
        property_obj.total_units = property_data.total_units

    db.commit()
    db.refresh(property_obj)

    metrics = calculate_property_metrics(db, property_obj)

    return PropertySchema(
        id=property_obj.id,
        name=property_obj.name,
        total_units=property_obj.total_units,
        created_at=property_obj.created_at,
        **metrics
    )


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Delete a property (only if no active tenants)."""
    property_obj = db.query(Property).filter(Property.id == property_id).first()

    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Check for active tenants
    active_tenants = db.query(Tenant).filter(
        Tenant.property_id == property_id,
        Tenant.status == TenantStatus.ACTIVE
    ).count()

    if active_tenants > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete property with active tenants"
        )

    db.delete(property_obj)
    db.commit()

    return None
