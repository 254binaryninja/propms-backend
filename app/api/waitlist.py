from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from uuid import UUID
from app.api.deps import get_db, get_current_admin
from app.models import WaitlistEntry, Property, Tenant, AdminUser, TenantStatus
from app.schemas.waitlist import WaitlistEntry as WaitlistEntrySchema, WaitlistCreate, WaitlistPromote
from app.schemas.tenant import Tenant as TenantSchema
from app.utils.security import hash_password
import random

router = APIRouter()


def generate_pin() -> str:
    """Generate a random 4-digit PIN."""
    return str(random.randint(1000, 9999))


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
def list_waitlist(
    property_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """List waitlist entries ordered by position."""
    # Use window function to calculate position
    position_query = func.row_number().over(
        partition_by=WaitlistEntry.property_id,
        order_by=WaitlistEntry.created_at
    ).label('position')

    query = db.query(
        WaitlistEntry,
        position_query
    )

    # Apply filter
    if property_id:
        query = query.filter(WaitlistEntry.property_id == property_id)

    # Execute query
    results = query.all()

    # Build response
    entries_data = []
    for entry, position in results:
        entry_dict = {
            "id": entry.id,
            "name": entry.name,
            "phone": entry.phone,
            "property_id": entry.property_id,
            "property_name": entry.property.name if entry.property else None,
            "position": position,
            "source": entry.source,
            "created_at": entry.created_at
        }
        entries_data.append(entry_dict)

    return {
        "data": entries_data,
        "meta": {
            "total": len(entries_data),
            "page": 1,
            "per_page": len(entries_data),
            "pages": 1
        }
    }


@router.post("", response_model=WaitlistEntrySchema, status_code=status.HTTP_201_CREATED)
def add_to_waitlist(
    waitlist_data: WaitlistCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Add entry to waitlist and send confirmation SMS."""
    # Verify property exists
    property_obj = db.query(Property).filter(Property.id == waitlist_data.property_id).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Create waitlist entry
    new_entry = WaitlistEntry(
        name=waitlist_data.name,
        phone=waitlist_data.phone,
        property_id=waitlist_data.property_id,
        source=waitlist_data.source
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    # Calculate position
    position = db.query(func.count(WaitlistEntry.id)).filter(
        WaitlistEntry.property_id == waitlist_data.property_id,
        WaitlistEntry.created_at <= new_entry.created_at
    ).scalar()

    # TODO: Send confirmation SMS (will implement in Phase 6)
    # sms_service.send_single_sms(new_entry.phone, f"You've been added to the waitlist for {property_obj.name}. Position: {position}")

    return WaitlistEntrySchema(
        id=new_entry.id,
        name=new_entry.name,
        phone=new_entry.phone,
        property_id=new_entry.property_id,
        property_name=property_obj.name,
        position=position,
        source=new_entry.source,
        created_at=new_entry.created_at
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_waitlist(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Remove entry from waitlist."""
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found"
        )

    db.delete(entry)
    db.commit()

    return None


@router.post("/{entry_id}/promote", response_model=TenantSchema, status_code=status.HTTP_201_CREATED)
def promote_waitlist_to_tenant(
    entry_id: UUID,
    promote_data: WaitlistPromote,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Convert waitlist entry to active tenant."""
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found"
        )

    # Generate and hash PIN
    plain_pin = generate_pin()
    hashed_pin = hash_password(plain_pin)

    # Create tenant from waitlist entry
    new_tenant = Tenant(
        name=entry.name,
        phone=entry.phone,
        house_no=promote_data.house_no,
        property_id=entry.property_id,
        rent_amount=promote_data.rent_amount,
        lease_start_date=promote_data.lease_start_date,
        ussd_pin=hashed_pin,
        status=TenantStatus.ACTIVE
    )

    db.add(new_tenant)

    # Remove from waitlist
    db.delete(entry)

    db.commit()
    db.refresh(new_tenant)

    # TODO: Send welcome SMS with PIN (will implement in Phase 6)
    # sms_service.send_welcome_sms(new_tenant.phone, plain_pin)

    property_obj = new_tenant.property

    return TenantSchema(
        id=new_tenant.id,
        name=new_tenant.name,
        phone=new_tenant.phone,
        house_no=new_tenant.house_no,
        property_id=new_tenant.property_id,
        property_name=property_obj.name if property_obj else None,
        rent_amount=float(new_tenant.rent_amount),
        lease_start_date=new_tenant.lease_start_date,
        status=new_tenant.status,
        vacated_at=new_tenant.vacated_at,
        created_at=new_tenant.created_at
    )
