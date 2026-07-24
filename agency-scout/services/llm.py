from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import requests

from services.config import (
    get_gemini_api_key,
    get_gemini_model,
    get_openrouter_final_fallback_model,
    get_openrouter_api_key,
    get_openrouter_fallback_model,
    get_openrouter_model,
    get_sender_name,
)
from services.gmail_service import build_unsubscribe_url


class LLMServiceError(RuntimeError):
    pass


SYSTEM_PROMPT = """You write cold outreach emails for Markus from Mindy Agency.
Rules:
- Under 100 words in the body.
- Use the lead's concrete Issues and Advice. Do not invent facts.
- Use the business name in the greeting. Avoid "Hi there".
- One CTA only, phrased as: "Mind if I send over a free, zero-strings mock-up?"
- Sound like a local operator who noticed one specific problem, not a marketing brochure.
- No hype, no fake urgency, no "hope you're well", no "stunning", no "modernize", no "digital experience".
- Do not add "let me know if not interested", "no pressure", "just ignore this", or a second question.
- Include one short visible opt-out line at the end: "Opt out: [unsubscribe_url]".
- Return strict JSON only: {"subject": "...", "body": "..."}."""


@dataclass(frozen=True)
class DraftResult:
    subject: str
    body: str
    model: str


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _question_count(text: str) -> int:
    without_urls = re.sub(r"https?://\S+", "", text)
    return without_urls.count("?")


def _validate(subject: str, body: str) -> None:
    if not subject or not body:
        raise LLMServiceError("Draft is missing a subject or body")
    if _word_count(body) > 100:
        raise LLMServiceError(f"Draft body exceeds 100 words ({_word_count(body)})")
    if not body.lower().startswith("hi "):
        raise LLMServiceError("Draft must start with a direct greeting")
    if _question_count(body) > 1:
        raise LLMServiceError("Draft contains more than one question/CTA")
    required_cta = "mind if i send over a free, zero-strings mock-up?"
    if required_cta not in body.lower():
        raise LLMServiceError("Draft is missing the required single CTA")
    if "opt out:" not in body.lower():
        raise LLMServiceError("Draft is missing the visible opt-out line")
    blocked_phrases = (
        "hope you're well",
        "stunning",
        "modernize",
        "digital presence",
        "digital experience",
        "premium clients",
        "premium experience",
        "premium offering",
        "smooth experience",
        "conversion rates",
        "boost conversion rates",
        "best,",
        "[high value]",
        "pitch:",
        "let me know if you're not interested",
        "just ignore",
        "no pressure",
    )
    found = [phrase for phrase in blocked_phrases if phrase in body.lower()]
    if found:
        raise LLMServiceError(f"Draft contains blocked phrase: {found[0]}")


def _normalize_body(body: str) -> str:
    normalized = body.replace("\r\n", "\n").strip()
    normalized = re.sub(r"(?<=[a-z0-9])\.(?=[A-Z])", ". ", normalized)
    normalized = re.sub(r"(?<=[a-z0-9]),(?=[A-Z])", ", ", normalized)
    normalized = re.sub(r"(?<=[a-z0-9])\?(?=[A-Z])", "? ", normalized)
    normalized = re.sub(r"(?<=[a-z0-9])!(?=[A-Z])", "! ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def _clean_name(name: str) -> str:
    return name.strip().strip(".")


def _issue_observation(lead: dict[str, Any]) -> tuple[str, str]:
    issues = str(lead.get("issues") or lead.get("Issues") or "").lower()
    advice = str(lead.get("advice") or lead.get("Advice") or "").lower()

    if "not mobile friendly" in issues:
        observation = "your site is not mobile-friendly"
    elif "slow server" in issues:
        ttfb = re.search(r"ttfb\s*([0-9.]+s)", issues)
        observation = f"your site is loading slowly ({ttfb.group(1)})" if ttfb else "your site is loading slowly"
    elif "website missing on maps" in issues:
        observation = "your website is not showing on Google Maps"
    elif "outdated" in issues:
        year = re.search(r"20\d{2}", issues)
        observation = f"your website still shows older content ({year.group(0)})" if year else "your website still shows older content"
    elif "ssl" in issues:
        observation = "your SSL setup looks broken"
    else:
        observation = "your Maps traffic could convert better"

    if "running ads" in advice or "ad spend" in advice:
        consequence = "Paid clicks can leak before someone books."
    elif any(term in advice for term in ("event", "wedding", "premium")):
        consequence = "Event guests often check the site before they book."
    elif "direct bookings" in advice:
        consequence = "That can push people back to delivery apps or third-party listings."
    else:
        consequence = "That gives busy customers a reason to leave before booking."

    return observation, consequence


def build_template_draft(lead: dict[str, Any]) -> DraftResult:
    name = _clean_name(str(lead.get("name") or lead.get("Name") or "the team"))
    observation, consequence = _issue_observation(lead)
    unsubscribe_url = build_unsubscribe_url(lead["email"])

    body = (
        f"Hi {name} team,\n\n"
        f"I noticed {observation}. {consequence}\n\n"
        "I build small, fast pages for local venues that turn Maps traffic into direct bookings. "
        "Mind if I send over a free, zero-strings mock-up?\n\n"
        f"Opt out: {unsubscribe_url}"
    )
    subject = f"Quick idea for {name}"
    body = _normalize_body(body)
    _validate(subject, body)
    return DraftResult(subject=subject, body=body, model="local-template")


def _parse_json_response(content: str) -> dict[str, str]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMServiceError(f"Model returned non-JSON content: {content[:160]}") from exc
    return {"subject": str(parsed.get("subject", "")).strip(), "body": str(parsed.get("body", "")).strip()}


def _messages_for_lead(lead: dict[str, Any]) -> list[dict[str, str]]:
    lead_context = {
        "name": lead.get("name"),
        "email": lead.get("email"),
        "lead_score": lead.get("lead_score"),
        "issues": lead.get("issues"),
        "advice": lead.get("advice"),
        "tags": lead.get("tags"),
        "vibes": lead.get("vibes"),
        "website": lead.get("website"),
        "address": lead.get("address"),
        "unsubscribe_url": build_unsubscribe_url(lead["email"]),
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(lead_context, ensure_ascii=False)},
    ]


def _model_stack(model: str | None = None) -> list[str]:
    if model:
        return [model]
    models = [get_openrouter_model(), get_openrouter_fallback_model(), get_openrouter_final_fallback_model()]
    unique: list[str] = []
    for item in models:
        if item and item not in unique:
            unique.append(item)
    return unique


def _generate_via_gemini(lead: dict[str, Any]) -> DraftResult:
    """Generate a draft using Google GenAI (Gemma 4). Raises LLMServiceError on failure."""
    from google import genai  # type: ignore[import-untyped]

    api_key = get_gemini_api_key()
    model_name = get_gemini_model()
    client = genai.Client(api_key=api_key) if api_key else genai.Client()

    lead_context = {
        "name": lead.get("name"),
        "email": lead.get("email"),
        "lead_score": lead.get("lead_score"),
        "issues": lead.get("issues"),
        "advice": lead.get("advice"),
        "tags": lead.get("tags"),
        "vibes": lead.get("vibes"),
        "website": lead.get("website"),
        "address": lead.get("address"),
        "unsubscribe_url": build_unsubscribe_url(lead["email"]),
    }

    import json as _json
    response_schema = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["subject", "body"],
    }

    response = client.models.generate_content(
        model=model_name,
        contents=_json.dumps(lead_context, ensure_ascii=False),
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_json_schema": response_schema,
            "temperature": 0.55,
            "max_output_tokens": 240,
        },
    )

    response_text = (getattr(response, "text", None) or "").strip()
    if not response_text:
        raise LLMServiceError("Gemini returned empty response")

    parsed = _parse_json_response(response_text)
    body = _normalize_body(parsed["body"])
    _validate(parsed["subject"], body)
    return DraftResult(subject=parsed["subject"], body=body, model=f"gemini/{model_name}")


def generate_draft(lead: dict[str, Any], model: str | None = None) -> DraftResult:
    # Prefer Gemma 4 via Gemini API when key is available and no explicit model override
    if not model and get_gemini_api_key():
        try:
            return _generate_via_gemini(lead)
        except Exception as exc:  # noqa: BLE001
            # Log the error and fall through to OpenRouter
            import logging
            logging.getLogger(__name__).warning("Gemini generation failed, falling back to OpenRouter: %s", exc)

    api_key = get_openrouter_api_key()
    if not api_key:
        raise LLMServiceError("OPENROUTER_API_KEY or OPEN_ROUTER_API is not configured")

    selected_models = _model_stack(model)
    payload = {
        "models": selected_models,
        "route": "fallback",
        "messages": _messages_for_lead(lead),
        "temperature": 0.55,
        "max_tokens": 240,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "cold_email_draft",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["subject", "body"],
                    "additionalProperties": False,
                },
            },
        },
        "provider": {"allow_fallbacks": True},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Mindy Autonomous Sales Agent",
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=45,
    )
    if response.status_code >= 400:
        raise LLMServiceError(f"OpenRouter request failed ({response.status_code}): {response.text[:300]}")

    response_payload = response.json()
    content = response_payload["choices"][0]["message"]["content"]
    selected_model = response_payload.get("model") or selected_models[0]
    parsed = _parse_json_response(content)
    body = _normalize_body(parsed["body"])
    _validate(parsed["subject"], body)
    return DraftResult(subject=parsed["subject"], body=body, model=selected_model)
