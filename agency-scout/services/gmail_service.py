from __future__ import annotations

import base64
import hashlib
import os
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote, urlencode

from services.config import (
    PROJECT_ROOT,
    get_sender_email,
    get_sender_name,
    get_unsubscribe_base_url,
    get_unsubscribe_secret,
    load_environment,
)


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailServiceError(RuntimeError):
    pass


def make_unsubscribe_token(email: str) -> str:
    secret = get_unsubscribe_secret().encode("utf-8")
    return hashlib.sha256(secret + email.lower().encode("utf-8")).hexdigest()


def build_unsubscribe_url(email: str) -> str:
    base_url = get_unsubscribe_base_url().rstrip("/")
    query = urlencode({"email": email, "token": make_unsubscribe_token(email)})
    return f"{base_url}/unsubscribe?{query}"


def validate_unsubscribe_token(email: str, token: str) -> bool:
    return bool(email and token and token == make_unsubscribe_token(email))


def _credentials_paths() -> tuple[Path, Path]:
    client_secret = Path(os.getenv("GOOGLE_CLIENT_SECRET_FILE", PROJECT_ROOT / "credentials.json"))
    token_file = Path(os.getenv("GOOGLE_TOKEN_FILE", PROJECT_ROOT / "token.json"))
    return client_secret, token_file


def _get_gmail_service():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GmailServiceError(
            "Gmail dependencies are missing. Run: pip install -r requirements.txt"
        ) from exc

    load_environment()
    client_secret, token_file = _credentials_paths()
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not client_secret.exists():
            raise GmailServiceError(
                f"Missing Gmail OAuth client file: {client_secret}. Create it in Google Cloud Console or set GOOGLE_CLIENT_SECRET_FILE."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def build_message(to_email: str, subject: str, body: str) -> dict[str, str]:
    sender = f"{get_sender_name()} <{get_sender_email()}>"
    unsubscribe_url = build_unsubscribe_url(to_email)

    message = EmailMessage()
    message["To"] = to_email
    message["From"] = sender
    message["Subject"] = subject
    message["List-Unsubscribe"] = f"<{unsubscribe_url}>, <mailto:{get_sender_email()}?subject=unsubscribe>"
    message["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    message["Auto-Submitted"] = "no"
    message.set_content(body)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return {"raw": raw}


def send_message(to_email: str, subject: str, body: str) -> str:
    service = _get_gmail_service()
    sent = service.users().messages().send(userId="me", body=build_message(to_email, subject, body)).execute()
    message_id = sent.get("id")
    if not message_id:
        raise GmailServiceError("Gmail did not return a message id")
    return message_id
