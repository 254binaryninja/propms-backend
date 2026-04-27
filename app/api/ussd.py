from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.ussd_service import handle_ussd_session

router = APIRouter()


@router.post("/callback", response_class=PlainTextResponse)
def ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(...),
    networkCode: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Africa's Talking USSD callback endpoint.

    Receives USSD session data and returns menu text.
    Response must be plain text prefixed with CON (continue) or END (terminate).

    Args:
        sessionId: USSD session ID
        serviceCode: USSD service code (e.g., *384#)
        phoneNumber: User phone number
        text: Accumulated user input
        networkCode: Mobile network code
        db: Database session

    Returns:
        Plain text USSD response (CON... or END...)
    """
    response = handle_ussd_session(
        db=db,
        session_id=sessionId,
        phone_number=phoneNumber,
        text=text
    )

    return response
