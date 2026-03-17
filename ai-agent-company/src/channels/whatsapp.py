"""WhatsApp channel — Twilio send/receive."""
import os
from twilio.rest import Client
from twilio.request_validator import RequestValidator


def _client() -> Client:
    return Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )


def send_whatsapp(to_phone: str, message: str) -> bool:
    """
    Send a WhatsApp message via Twilio.
    to_phone: raw E.164 number like +34612345678 (no 'whatsapp:' prefix needed).
    Returns True on success.
    """
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    to = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"

    try:
        _client().messages.create(body=message, from_=from_number, to=to)
        return True
    except Exception as e:
        print(f"[WhatsApp] send error: {e}")
        return False


def validate_twilio_signature(url: str, params: dict, signature: str) -> bool:
    """Validate that an incoming webhook is genuinely from Twilio."""
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    validator = RequestValidator(auth_token)
    return validator.validate(url, params, signature)


def parse_inbound(form_data: dict) -> dict:
    """
    Extract the useful fields from a Twilio inbound WhatsApp webhook payload.
    Returns a normalised dict.
    """
    return {
        "from_phone": form_data.get("From", "").replace("whatsapp:", ""),
        "to_phone": form_data.get("To", "").replace("whatsapp:", ""),
        "body": form_data.get("Body", "").strip(),
        "profile_name": form_data.get("ProfileName", ""),
        "message_sid": form_data.get("MessageSid", ""),
        "num_media": int(form_data.get("NumMedia", 0)),
    }
