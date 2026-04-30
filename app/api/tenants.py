from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date
import random
from app.api.deps import get_db, get_current_admin
from app.models import Tenant, Property, Payment, Issue, AdminUser, TenantStatus, IssueStatus
from app.schemas.tenant import (
    Tenant as TenantSchema,
    TenantCreate,
    TenantUpdate,
    TenantVacate,
    TenantDetail
)
from app.utils.security import hash_password
from app.utils.pagination import paginate, create_pagination_meta

router = APIRouter()


def generate_pin() -> str:
    """Generate a random 4-digit PIN."""
    return str(random.randint(1000, 9999))


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
def list_tenants(
    property_id: Optional[UUID] = Query(None),
    status_filter: Optional[TenantStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """List tenants with filtering and pagination."""
    query = db.query(Tenant).join(Property).filter(Property.admin_id == current_user.id)

    # Apply filters
    if property_id:
        query = query.filter(Tenant.property_id == property_id)
    if status_filter:
        query = query.filter(Tenant.status == status_filter)

    # Paginate
    tenants, total = paginate(query, page, per_page)

    # Add property names
    tenants_data = []
    for tenant in tenants:
        tenant_dict = {
            "id": tenant.id,
            "name": tenant.name,
            "phone": tenant.phone,
            "house_no": tenant.house_no,
            "property_id": tenant.property_id,
            "property_name": tenant.property.name if tenant.property else None,
            "rent_amount": float(tenant.rent_amount),
            "lease_start_date": tenant.lease_start_date,
            "status": tenant.status,
            "vacated_at": tenant.vacated_at,
            "created_at": tenant.created_at
        }
        tenants_data.append(tenant_dict)

    return {
        "data": tenants_data,
        "meta": create_pagination_meta(total, page, per_page)
    }


@router.post("", response_model=TenantSchema, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Create a new tenant and send welcome SMS with PIN."""
    # Verify property exists and belongs to current admin
    property_obj = db.query(Property).filter(
        Property.id == tenant_data.property_id,
        Property.admin_id == current_user.id
    ).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Generate and hash PIN
    plain_pin = generate_pin()
    hashed_pin = hash_password(plain_pin)

    # Create tenant
    new_tenant = Tenant(
        name=tenant_data.name,
        phone=tenant_data.phone,
        house_no=tenant_data.house_no,
        property_id=tenant_data.property_id,
        rent_amount=tenant_data.rent_amount,
        lease_start_date=tenant_data.lease_start_date,
        ussd_pin=hashed_pin,
        status=TenantStatus.ACTIVE
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    # TODO: Send welcome SMS with PIN (will implement in Phase 6)
    # sms_service.send_welcome_sms(new_tenant.phone, plain_pin)

    return TenantSchema(
        id=new_tenant.id,
        name=new_tenant.name,
        phone=new_tenant.phone,
        house_no=new_tenant.house_no,
        property_id=new_tenant.property_id,
        property_name=property_obj.name,
        rent_amount=float(new_tenant.rent_amount),
        lease_start_date=new_tenant.lease_start_date,
        status=new_tenant.status,
        vacated_at=new_tenant.vacated_at,
        created_at=new_tenant.created_at
    )


@router.get("/{tenant_id}", response_model=TenantDetail, status_code=status.HTTP_200_OK)
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Get tenant detail with recent payments and open issues."""
    tenant = db.query(Tenant).join(Property).filter(
        Tenant.id == tenant_id,
        Property.admin_id == current_user.id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Get recent payments (last 5)
    recent_payments = db.query(Payment).filter(
        Payment.tenant_id == tenant_id
    ).order_by(Payment.created_at.desc()).limit(5).all()

    # Get open issues
    open_issues = db.query(Issue).filter(
        Issue.tenant_id == tenant_id,
        Issue.status != IssueStatus.RESOLVED
    ).all()

    return TenantDetail(
        id=tenant.id,
        name=tenant.name,
        phone=tenant.phone,
        house_no=tenant.house_no,
        property_id=tenant.property_id,
        property_name=tenant.property.name if tenant.property else None,
        rent_amount=float(tenant.rent_amount),
        lease_start_date=tenant.lease_start_date,
        status=tenant.status,
        vacated_at=tenant.vacated_at,
        created_at=tenant.created_at,
        recent_payments=[
            {
                "id": p.id,
                "tenant_id": p.tenant_id,
                "amount": float(p.amount),
                "due_date": p.due_date,
                "paid_date": p.paid_date,
                "status": p.status,
                "created_at": p.created_at
            } for p in recent_payments
        ],
        open_issues=[
            {
                "id": i.id,
                "tenant_id": i.tenant_id,
                "type": i.type,
                "description": i.description,
                "urgency": i.urgency,
                "status": i.status,
                "source": i.source,
                "created_at": i.created_at,
                "resolved_at": i.resolved_at
            } for i in open_issues
        ]
    )


@router.patch("/{tenant_id}", response_model=TenantSchema, status_code=status.HTTP_200_OK)
def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Update tenant information."""
    tenant = db.query(Tenant).join(Property).filter(
        Tenant.id == tenant_id,
        Property.admin_id == current_user.id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Update fields
    if tenant_data.name is not None:
        tenant.name = tenant_data.name
    if tenant_data.phone is not None:
        tenant.phone = tenant_data.phone
    if tenant_data.house_no is not None:
        tenant.house_no = tenant_data.house_no
    if tenant_data.rent_amount is not None:
        tenant.rent_amount = tenant_data.rent_amount
    if tenant_data.status is not None:
        tenant.status = tenant_data.status

    db.commit()
    db.refresh(tenant)

    return TenantSchema(
        id=tenant.id,
        name=tenant.name,
        phone=tenant.phone,
        house_no=tenant.house_no,
        property_id=tenant.property_id,
        property_name=tenant.property.name if tenant.property else None,
        rent_amount=float(tenant.rent_amount),
        lease_start_date=tenant.lease_start_date,
        status=tenant.status,
        vacated_at=tenant.vacated_at,
        created_at=tenant.created_at
    )


@router.post("/{tenant_id}/vacate", response_model=dict, status_code=status.HTTP_200_OK)
def vacate_tenant(
    tenant_id: UUID,
    vacate_data: TenantVacate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Mark tenant as vacated and notify waitlist."""
    tenant = db.query(Tenant).join(Property).filter(
        Tenant.id == tenant_id,
        Property.admin_id == current_user.id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Update tenant status
    tenant.status = TenantStatus.VACATED
    tenant.vacated_at = vacate_data.vacated_at or date.today()

    db.commit()
    db.refresh(tenant)

    # TODO: Notify waitlist #1 (will implement in Phase 7)
    # waitlist_entry = tenant_service.notify_waitlist(db, tenant.property_id)

    return {
        "tenant": TenantSchema(
            id=tenant.id,
            name=tenant.name,
            phone=tenant.phone,
            house_no=tenant.house_no,
            property_id=tenant.property_id,
            property_name=tenant.property.name if tenant.property else None,
            rent_amount=float(tenant.rent_amount),
            lease_start_date=tenant.lease_start_date,
            status=tenant.status,
            vacated_at=tenant.vacated_at,
            created_at=tenant.created_at
        ),
        "waitlist_notified": False,
        "waitlist_entry": None
    }


@router.post("/{tenant_id}/reset-pin", response_model=dict, status_code=status.HTTP_200_OK)
def reset_tenant_pin(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Reset tenant USSD PIN and send via SMS."""
    tenant = db.query(Tenant).join(Property).filter(
        Tenant.id == tenant_id,
        Property.admin_id == current_user.id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Generate new PIN
    new_pin = generate_pin()
    tenant.ussd_pin = hash_password(new_pin)

    db.commit()

    # TODO: Send SMS with new PIN (will implement in Phase 6)
    # sms_service.send_single_sms(tenant.phone, f"Your new PropMS PIN is {new_pin}")

    return {
        "message": f"PIN reset. SMS sent to {tenant.phone}"
    }
