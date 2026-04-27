from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models import Tenant, AdminUser, TenantStatus
from app.schemas.messaging import MassSMSRequest, SingleSMSRequest, SMSResponse, SMSStatus
from app.services import sms_service

router = APIRouter()


@router.post("/mass-sms", response_model=SMSResponse, status_code=status.HTTP_200_OK)
def send_mass_sms(
    sms_data: MassSMSRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Send mass SMS to all tenants in a property (or all properties)."""
    query = db.query(Tenant).filter(Tenant.status == TenantStatus.ACTIVE)

    # Filter by property if specified
    if sms_data.property_id:
        query = query.filter(Tenant.property_id == sms_data.property_id)

    tenants = query.all()

    if not tenants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active tenants found"
        )

    # Extract phone numbers
    phone_numbers = [tenant.phone for tenant in tenants]

    # Send SMS
    result = sms_service.send_mass_sms(phone_numbers, sms_data.message)

    if result.get("success"):
        return SMSResponse(
            recipients=len(phone_numbers),
            at_message_id="bulk-message-id",
            status=SMSStatus.QUEUED
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS sending failed: {result.get('error')}"
        )


@router.post("/single-sms", response_model=SMSResponse, status_code=status.HTTP_200_OK)
def send_single_sms(
    sms_data: SingleSMSRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Send SMS to a single tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == sms_data.tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Send SMS
    result = sms_service.send_single_sms(tenant.phone, sms_data.message)

    if result.get("success"):
        return SMSResponse(
            recipients=1,
            at_message_id="single-message-id",
            status=SMSStatus.QUEUED
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS sending failed: {result.get('error')}"
        )
