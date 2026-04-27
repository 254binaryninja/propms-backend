import africastalking
from typing import List
from app.config import settings

# Initialize Africa's Talking
africastalking.initialize(
    username=settings.AT_USERNAME,
    api_key=settings.AT_API_KEY
)

# Get SMS service
sms = africastalking.SMS


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
        response = sms.send(message, [phone])
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


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
        response = sms.send(message, [phone])
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


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
        response = sms.send(message, [phone])
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def send_mass_sms(phones: List[str], message: str) -> dict:
    """
    Send bulk SMS to multiple recipients.

    Args:
        phones: List of phone numbers
        message: SMS message (max 160 characters)

    Returns:
        SMS response dict with recipient count
    """
    if not phones:
        return {
            "success": False,
            "error": "No recipients provided"
        }

    try:
        response = sms.send(message, phones)
        return {
            "success": True,
            "recipients": len(phones),
            "response": response
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


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
        response = sms.send(message, [phone])
        return {
            "success": True,
            "response": response
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
