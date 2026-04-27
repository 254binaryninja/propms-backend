from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.api.deps import get_db, get_current_admin
from app.models import Issue, Tenant, AdminUser, IssueStatus, IssueUrgency
from app.schemas.issue import Issue as IssueSchema, IssueCreate, IssueStatusUpdate
from app.utils.pagination import paginate, create_pagination_meta

router = APIRouter()


@router.get("", response_model=dict, status_code=status.HTTP_200_OK)
def list_issues(
    property_id: Optional[UUID] = Query(None),
    status_filter: Optional[IssueStatus] = Query(None, alias="status"),
    urgency: Optional[IssueUrgency] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """List issues with filtering and pagination."""
    query = db.query(Issue).join(Tenant)

    # Apply filters
    if property_id:
        query = query.filter(Tenant.property_id == property_id)
    if status_filter:
        query = query.filter(Issue.status == status_filter)
    if urgency:
        query = query.filter(Issue.urgency == urgency)

    # Order by urgency and creation time
    query = query.order_by(Issue.urgency.desc(), Issue.created_at.desc())

    # Paginate
    issues, total = paginate(query, page, per_page)

    # Add tenant/property info
    issues_data = []
    for issue in issues:
        issue_dict = {
            "id": issue.id,
            "tenant_id": issue.tenant_id,
            "tenant_name": issue.tenant.name if issue.tenant else None,
            "house_no": issue.tenant.house_no if issue.tenant else None,
            "property_id": issue.tenant.property_id if issue.tenant else None,
            "property_name": issue.tenant.property.name if issue.tenant and issue.tenant.property else None,
            "type": issue.type,
            "description": issue.description,
            "urgency": issue.urgency,
            "status": issue.status,
            "source": issue.source,
            "created_at": issue.created_at,
            "resolved_at": issue.resolved_at
        }
        issues_data.append(issue_dict)

    return {
        "data": issues_data,
        "meta": create_pagination_meta(total, page, per_page)
    }


@router.post("", response_model=IssueSchema, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_data: IssueCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Create a new issue (admin-side)."""
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == issue_data.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Create issue
    new_issue = Issue(
        tenant_id=issue_data.tenant_id,
        type=issue_data.type,
        description=issue_data.description,
        urgency=issue_data.urgency,
        source=issue_data.source,
        status=IssueStatus.PENDING
    )

    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)

    return IssueSchema(
        id=new_issue.id,
        tenant_id=new_issue.tenant_id,
        tenant_name=tenant.name,
        house_no=tenant.house_no,
        property_id=tenant.property_id,
        property_name=tenant.property.name if tenant.property else None,
        type=new_issue.type,
        description=new_issue.description,
        urgency=new_issue.urgency,
        status=new_issue.status,
        source=new_issue.source,
        created_at=new_issue.created_at,
        resolved_at=new_issue.resolved_at
    )


@router.patch("/{issue_id}", response_model=IssueSchema, status_code=status.HTTP_200_OK)
def update_issue_status(
    issue_id: UUID,
    update_data: IssueStatusUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_admin)
):
    """Update issue status and/or urgency."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )

    # Update status
    issue.status = update_data.status

    # Set resolved_at if status is resolved
    if update_data.status == IssueStatus.RESOLVED and not issue.resolved_at:
        issue.resolved_at = datetime.utcnow()

    # Update urgency if provided
    if update_data.urgency is not None:
        issue.urgency = update_data.urgency

    db.commit()
    db.refresh(issue)

    tenant = issue.tenant

    return IssueSchema(
        id=issue.id,
        tenant_id=issue.tenant_id,
        tenant_name=tenant.name if tenant else None,
        house_no=tenant.house_no if tenant else None,
        property_id=tenant.property_id if tenant else None,
        property_name=tenant.property.name if tenant and tenant.property else None,
        type=issue.type,
        description=issue.description,
        urgency=issue.urgency,
        status=issue.status,
        source=issue.source,
        created_at=issue.created_at,
        resolved_at=issue.resolved_at
    )
