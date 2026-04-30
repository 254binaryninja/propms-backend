from decimal import Decimal
from typing import Dict, cast

from sqlalchemy.orm import Session

from app.models import (
    Issue,
    IssueSource,
    IssueStatus,
    IssueType,
    IssueUrgency,
    Payment,
    PaymentStatus,
    Property,
    Tenant,
    TenantStatus,
    WaitlistEntry,
    WaitlistSource,
)
from app.utils.security import verify_password

# In-memory session storage (for production, use Redis)
sessions: Dict[str, dict] = {}


def handle_ussd_session(
    db: Session, session_id: str, phone_number: str, text: str
) -> str:
    """
    Handle USSD session and return response.

    Args:
        db: Database session
        session_id: USSD session ID
        phone_number: User phone number
        text: Accumulated USSD input

    Returns:
        USSD response string (CON... or END...)
    """
    # Parse user input
    inputs = text.split("*") if text else []
    level = len(inputs)

    # Initialize session state if new
    if session_id not in sessions:
        sessions[session_id] = {"phone": phone_number, "state": "root", "data": {}}

    session = sessions[session_id]

    # Root menu
    if level == 0:
        return "CON Welcome to PropMS\n1. I'm a tenant\n2. Find a home"

    # Level 1: Main menu choice
    if level == 1:
        choice = inputs[0]

        if choice == "1":
            # Tenant path - request PIN
            session["state"] = "awaiting_pin"
            return "CON Enter your 4-digit PIN:"

        elif choice == "2":
            # Prospect path - list properties
            properties = db.query(Property).all()
            if not properties:
                return "END No properties available at the moment."

            session["state"] = "property_selection"
            session["data"]["properties"] = [str(p.id) for p in properties]

            response = "CON Select property:\n"
            for idx, prop in enumerate(properties, 1):
                response += f"{idx}. {prop.name}\n"
            return response.rstrip()

        else:
            return "END Invalid choice."

    # Level 2: PIN validation or property selection
    if level == 2:
        if session["state"] == "awaiting_pin":
            pin_input = inputs[1]

            # Validate PIN
            tenant = (
                db.query(Tenant)
                .filter(
                    Tenant.phone == phone_number, Tenant.status == TenantStatus.ACTIVE
                )
                .first()
            )

            if not tenant or not verify_password(pin_input, cast(str, tenant.ussd_pin)):
                return "END Invalid PIN. Please try again."

            # PIN valid - show tenant menu
            session["state"] = "tenant_menu"
            session["data"]["tenant_id"] = str(tenant.id)
            return "CON 1. Report issue\n2. Rent balance"

        elif session["state"] == "property_selection":
            property_idx = int(inputs[1]) - 1
            property_ids = session["data"].get("properties", [])

            if property_idx < 0 or property_idx >= len(property_ids):
                return "END Invalid selection."

            property_id = property_ids[property_idx]
            property_obj = db.query(Property).filter(Property.id == property_id).first()

            if not property_obj:
                return "END Property not found."

            # Calculate vacant units
            occupied = (
                db.query(Tenant)
                .filter(
                    Tenant.property_id == property_id,
                    Tenant.status == TenantStatus.ACTIVE,
                )
                .count()
            )
            vacant = int(cast(int, property_obj.total_units)) - occupied

            session["state"] = "waitlist_prompt"
            session["data"]["property_id"] = property_id

            return f"CON {property_obj.name} has {vacant} vacant unit(s).\n1. Join waitlist\n2. Exit"

    # Level 3: Tenant actions or waitlist confirmation
    if level == 3:
        if session["state"] == "tenant_menu":
            choice = inputs[2]
            tenant_id = session["data"]["tenant_id"]

            if choice == "1":
                # Report issue - show issue types
                session["state"] = "issue_type"
                return "CON Select issue:\n1. Water\n2. Electricity\n3. Other"

            elif choice == "2":
                # Show rent balance
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                if not tenant:
                    return "END Error: Tenant not found."

                # Get unpaid payments
                unpaid = (
                    db.query(Payment)
                    .filter(
                        Payment.tenant_id == tenant_id,
                        Payment.status.in_(
                            [PaymentStatus.PENDING, PaymentStatus.OVERDUE]
                        ),
                    )
                    .order_by(Payment.due_date)
                    .first()
                )

                if unpaid:
                    amount = float(cast(Decimal, unpaid.amount))
                    return f"END Outstanding balance: KES {amount:,.2f}\nDue: {unpaid.due_date}"
                else:
                    return "END No outstanding payments. Thank you!"

            else:
                return "END Invalid choice."

        elif session["state"] == "waitlist_prompt":
            choice = inputs[2]

            if choice == "1":
                # Join waitlist - request name
                session["state"] = "waitlist_name"
                return "CON Enter your name:"

            elif choice == "2":
                return "END Thank you for using PropMS."

            else:
                return "END Invalid choice."

    # Level 4: Issue creation or name entry
    if level == 4:
        if session["state"] == "issue_type":
            choice = inputs[3]
            tenant_id = session["data"]["tenant_id"]

            issue_types = {
                "1": IssueType.WATER,
                "2": IssueType.ELECTRICITY,
                "3": IssueType.OTHER,
            }

            if choice not in issue_types:
                return "END Invalid choice."

            # Create issue
            new_issue = Issue(
                tenant_id=tenant_id,
                type=issue_types[choice],
                urgency=IssueUrgency.HIGH,  # Default high for USSD
                status=IssueStatus.PENDING,
                source=IssueSource.USSD,
            )

            db.add(new_issue)
            db.commit()

            # Clear session
            if session_id in sessions:
                del sessions[session_id]

            return "END Your issue has been reported. We'll respond shortly."

        elif session["state"] == "waitlist_name":
            name = inputs[3]
            property_id = session["data"]["property_id"]

            # Add to waitlist
            new_entry = WaitlistEntry(
                name=name,
                phone=phone_number,
                property_id=property_id,
                source=WaitlistSource.USSD,
            )

            db.add(new_entry)
            db.commit()

            # Calculate position
            position = (
                db.query(WaitlistEntry)
                .filter(
                    WaitlistEntry.property_id == property_id,
                    WaitlistEntry.created_at <= new_entry.created_at,
                )
                .count()
            )

            # Clear session
            if session_id in sessions:
                del sessions[session_id]

            return f"END Added to waitlist. Position: #{position}"

    # Fallback
    return "END Session error. Please try again."
