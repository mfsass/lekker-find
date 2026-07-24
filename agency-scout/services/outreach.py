from __future__ import annotations

from pathlib import Path
from typing import Any

from services.config import PROJECT_ROOT, load_environment
from services.database import (
    add_to_suppression,
    create_email_draft,
    get_candidate_leads,
    get_email_draft,
    get_email_drafts,
    get_lead,
    ingest_agency_leads,
    latest_draft_for_lead,
    mark_draft_sent,
)
from services.gmail_service import GmailServiceError, send_message, validate_unsubscribe_token
from services.llm import LLMServiceError, build_template_draft, generate_draft


LEADS_JSON = PROJECT_ROOT / "data" / "agency_leads.json"


def ingest_default_leads() -> dict[str, int]:
    return ingest_agency_leads(LEADS_JSON)


def generate_drafts(limit: int = 5, candidate_limit: int = 10, allow_template_fallback: bool = False) -> dict[str, Any]:
    load_environment()
    candidates = get_candidate_leads(candidate_limit)
    created: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for lead in candidates:
        if len(created) >= limit:
            break
        existing = latest_draft_for_lead(lead["id"])
        if existing and existing["status"] == "Drafted":
            created.append(existing)
            continue

        try:
            result = generate_draft(lead)
        except LLMServiceError as exc:
            if not allow_template_fallback:
                errors.append({"lead_id": lead["id"], "name": lead["name"], "error": str(exc)})
                continue
            result = build_template_draft(lead)

        created.append(
            create_email_draft(
                lead_id=lead["id"],
                recipient_email=lead["email"],
                subject=result.subject,
                body=result.body,
                model=result.model,
            )
        )

    return {"created": created, "errors": errors, "candidates": candidates}


def regenerate_draft(draft_id: int, allow_template_fallback: bool = False) -> dict[str, Any]:
    draft = get_email_draft(draft_id)
    lead = get_lead(draft["lead_id"])
    try:
        result = generate_draft(lead)
    except LLMServiceError:
        if not allow_template_fallback:
            raise
        result = build_template_draft(lead)
    return create_email_draft(lead["id"], lead["email"], result.subject, result.body, result.model)


def approve_and_send(draft_id: int) -> dict[str, str]:
    draft = get_email_draft(draft_id)
    if draft["status"] != "Drafted":
        raise GmailServiceError(f"Draft {draft_id} is not sendable because status is {draft['status']}")
    message_id = send_message(draft["recipient_email"], draft["subject"], draft["body"])
    mark_draft_sent(draft_id, message_id)
    return {"message_id": message_id}


def process_unsubscribe(email: str, token: str) -> None:
    if not validate_unsubscribe_token(email, token):
        raise ValueError("Invalid unsubscribe token")
    add_to_suppression(email, "One-click unsubscribe")


def export_queue_snapshot(path: Path, candidate_limit: int = 10, draft_limit: int = 5) -> None:
    snapshot = {
        "candidates": get_candidate_leads(candidate_limit),
        "drafts": get_email_drafts(draft_limit, status="Drafted"),
    }
    path.write_text(__import__("json").dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
