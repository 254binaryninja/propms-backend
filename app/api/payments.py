from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from app.api.deps import get_db, get_current_admin
from app.models import Payment, Tenant, AdminUser, PaymentStatus
from app.schemas.payment import Payment as PaymentSchema, PaymentCreate, PaymentMarkPaid
from app.utils.pagination import paginate, create_pagination_meta

router = APIRouter()


def calculate_payment_status(payment: Payment) -> PaymentStatus:
    """Calculate payment status based on due date and current status."""
    if payment.status == PaymentStatus.PAID:
        return PaymentStatus.PAID

    if payment.due_date < date.today():
        return PaymentStatus.OVERDUE

    return PaymentStatus.PENDING


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
def list_payments(
    property_id: Optional[UUID] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    status_filter: Optional[PaymentStatus] = Query(None, alias="status"),
    month: Optional[str] = Query(None, regex=r'^\d{4}-\d{2}$'),  # YYYY-MM format
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """List payments with filtering and pagination."""
    query = db.query(Payment).join(Tenant)

    # Apply filters
    if property_id:
        query = query.filter(Tenant.property_id == property_id)
    if tenant_id:
        query = query.filter(Payment.tenant_id == tenant_id)
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    if month:
        year, month_num = month.split('-')
        query = query.filter(
            db.func.extract('year', Payment.due_date) == int(year),
            db.func.extract('month', Payment.due_date) == int(month_num)
        )

    # Order by due date
    query = query.order_by(Payment.due_date.desc())

    # Paginate
    payments, total = paginate(query, page, per_page)

    # Add tenant/property info and update overdue status
    payments_data = []
    for payment in payments:
        # Auto-calculate overdue status
        actual_status = calculate_payment_status(payment)
        if actual_status != payment.status:
            payment.status = actual_status
            db.add(payment)

        tenant = payment.tenant
        payment_dict = {
            "id": payment.id,
            "tenant_id": payment.tenant_id,
            "tenant_name": tenant.name if tenant else None,
            "property_id": tenant.property_id if tenant else None,
            "property_name": tenant.property.name if tenant and tenant.property else None,
            "house_no": tenant.house_no if tenant else None,
            "amount": float(payment.amount),
            "due_date": payment.due_date,
            "paid_date": payment.paid_date,
            "status": payment.status,
            "created_at": payment.created_at
        }
        payments_data.append(payment_dict)

    db.commit()

    return {
        "data": payments_data,
        "meta": create_pagination_meta(total, page, per_page)
    }


@router.post("", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Create a new payment record."""
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == payment_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Create payment
    new_payment = Payment(
        tenant_id=payment_data.tenant_id,
        amount=payment_data.amount,
        due_date=payment_data.due_date,
        status=PaymentStatus.PENDING
    )

    # Auto-set overdue if due date has passed
    if new_payment.due_date < date.today():
        new_payment.status = PaymentStatus.OVERDUE

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return PaymentSchema(
        id=new_payment.id,
        tenant_id=new_payment.tenant_id,
        tenant_name=tenant.name,
        property_id=tenant.property_id,
        property_name=tenant.property.name if tenant.property else None,
        house_no=tenant.house_no,
        amount=float(new_payment.amount),
        due_date=new_payment.due_date,
        paid_date=new_payment.paid_date,
        status=new_payment.status,
        created_at=new_payment.created_at
    )


@router.post("/{payment_id}/mark-paid", response_model=PaymentSchema, status_code=status.HTTP_200_OK)
def mark_payment_paid(
    payment_id: UUID,
    mark_paid_data: PaymentMarkPaid,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Mark a payment as paid."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Update payment
    payment.status = PaymentStatus.PAID
    payment.paid_date = mark_paid_data.paid_date or date.today()

    db.commit()
    db.refresh(payment)

    tenant = payment.tenant

    return PaymentSchema(
        id=payment.id,
        tenant_id=payment.tenant_id,
        tenant_name=tenant.name if tenant else None,
        property_id=tenant.property_id if tenant else None,
        property_name=tenant.property.name if tenant and tenant.property else None,
        house_no=tenant.house_no if tenant else None,
        amount=float(payment.amount),
        due_date=payment.due_date,
        paid_date=payment.paid_date,
        status=payment.status,
        created_at=payment.created_at
    )


@router.post("/{payment_id}/send-reminder", response_model=dict, status_code=status.HTTP_200_OK)
def send_payment_reminder(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Send rent reminder SMS for this payment."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    tenant = payment.tenant
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found for this payment"
        )

    # TODO: Send SMS reminder (will implement in Phase 6)
    # sms_service.send_payment_reminder(tenant.phone, float(payment.amount), payment.due_date)

    return {
        "recipients": 1,
        "at_message_id": "mock-message-id",
        "status": "queued"
    }
