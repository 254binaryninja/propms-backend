from typing import Any, Protocol, Sequence, cast

import africastalking

from app.config import settings


class SMSSender(Protocol):
    def send(
        self,
        message: str,
        recipients: Sequence[str],
        sender_id: str | None = None,
        enqueue: bool = False,
        callback: str | None = None,
        timeout: tuple[float, float] | None = None,
    ) -> Any: ...


# Initialize Africa's Talking
africastalking.initialize(username=settings.AT_USERNAME, api_key=settings.AT_API_KEY)

# Get SMS service
_raw_sms = africastalking.SMS
if _raw_sms is None:
    raise RuntimeError("Africa's Talking SMS service is not initialized")

sms: SMSSender = cast(SMSSender, _raw_sms)


def send_sms_with_sender(message: str, recipients: Sequence[str]):
    """Send SMS using configured sender ID if available."""
    normalized = list(recipients)
    sender_id = getattr(settings, "AT_SENDER_ID", None)
    if sender_id:
        return sms.send(message, normalized, sender_id=sender_id)
    return sms.send(message, normalized)


def send_welcome_sms(phone: str, pin: str) -> dict:
    """
    Send welcome SMS with USSD PIN to new tenant.

    Args:
        phone: Tenant phone number (E.164 format)
        pin: 4-digit USSD PIN (plain text)

    Returns:
        SMS response dict
    """
    message = f"Welcome to PropMS! Your USSD PIN is {pin}. Dial {settings.AT_SHORTCODE} to report issues and check rent balance."

    try:
        response = send_sms_with_sender(message, [phone])
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_waitlist_notification(phone: str, property_name: str) -> dict:
    """
    Send SMS notification to waitlist member about vacant unit.

    Args:
        phone: Prospect phone number
        property_name: Name of the property

    Returns:
        SMS response dict
    """
    message = f"Good news! A unit is now vacant at {property_name}. Contact us to schedule a viewing."

    try:
        response = send_sms_with_sender(message, [phone])
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_payment_reminder(phone: str, amount: float, due_date: str) -> dict:
    """
    Send rent payment reminder SMS.

    Args:
        phone: Tenant phone number
        amount: Payment amount
        due_date: Payment due date (string format)

    Returns:
        SMS response dict
    """
    message = f"Rent reminder: KES {amount:,.2f} is due on {due_date}. Thank you for your prompt payment."

    try:
        response = send_sms_with_sender(message, [phone])
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_mass_sms(phones: Sequence[str], message: str) -> dict:
    """
    Send bulk SMS to multiple recipients.

    Args:
        phones: List of phone numbers
        message: SMS message (max 160 characters)

    Returns:
        SMS response dict with recipient count
    """
    if not phones:
        return {"success": False, "error": "No recipients provided"}

    try:
        response = send_sms_with_sender(message, phones)
        return {"success": True, "recipients": len(phones), "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_single_sms(phone: str, message: str) -> dict:
    """
    Send SMS to a single recipient.

    Args:
        phone: Phone number
        message: SMS message

    Returns:
        SMS response dict
    """
    try:
        response = send_sms_with_sender(message, [phone])
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}