from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from services.config import DATA_DIR, get_database_path


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
GENERIC_LOCAL_PARTS = ("info", "hello", "contact", "restaurant", "bookings", "sales", "admin")
LOW_PRIORITY_LOCAL_PARTS = ("orders", "feedback", "quality", "privacy", "support", "noreply", "no-reply")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect() -> Iterable[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(get_database_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                all_emails TEXT,
                issues TEXT,
                advice TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                last_contacted TEXT,
                lead_score REAL DEFAULT 0,
                website TEXT,
                phone TEXT,
                address TEXT,
                tags TEXT,
                vibes TEXT,
                package_name TEXT,
                package_price TEXT,
                package_includes TEXT,
                source_payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS suppression_list (
                email TEXT PRIMARY KEY,
                reason TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS email_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                recipient_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Drafted',
                word_count INTEGER NOT NULL,
                error TEXT,
                gmail_message_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sent_at TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            );

            CREATE INDEX IF NOT EXISTS idx_leads_status_score ON leads(status, lead_score DESC);
            CREATE INDEX IF NOT EXISTS idx_drafts_status_created ON email_drafts(status, created_at DESC);
            """
        )


def _clean_email(raw: str) -> str | None:
    email = raw.strip().strip(".,;:()[]{}<>").lower()
    email = re.sub(r"\.za[a-z]+$", ".za", email)
    email = re.sub(r"\.com[a-z]+$", ".com", email)

    if "@" not in email:
        return None

    local, domain = email.split("@", 1)
    if any(bad in email for bad in (".png", ".jpg", ".jpeg", ".svg", "example.com", "yourdomain.com")):
        return None

    if "+" in local and "info" in local:
        local = "info"
    if local.startswith(tuple(str(n) for n in range(10))) and "info" in local:
        local = "info"

    cleaned = f"{local}@{domain}"
    return cleaned if EMAIL_RE.fullmatch(cleaned) else None


def extract_emails(value: Any) -> list[str]:
    if not value:
        return []
    matches = EMAIL_RE.findall(str(value))
    cleaned = [_clean_email(match) for match in matches]
    unique: list[str] = []
    for email in cleaned:
        if email and email not in unique:
            unique.append(email)
    return unique


def choose_primary_email(emails: list[str]) -> str | None:
    if not emails:
        return None

    def priority(email: str) -> tuple[int, str]:
        local = email.split("@", 1)[0]
        if local in GENERIC_LOCAL_PARTS:
            return (0, email)
        if any(part in local for part in GENERIC_LOCAL_PARTS):
            return (1, email)
        if local in LOW_PRIORITY_LOCAL_PARTS or any(part in local for part in LOW_PRIORITY_LOCAL_PARTS):
            return (3, email)
        return (2, email)

    return sorted(emails, key=priority)[0]


def add_to_suppression(email: str, reason: str = "Opted out") -> None:
    init_db()
    normalized = _clean_email(email)
    if not normalized:
        raise ValueError(f"Invalid suppression email: {email}")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO suppression_list (email, reason, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET reason=excluded.reason
            """,
            (normalized, reason, utc_now()),
        )
        conn.execute(
            "UPDATE leads SET status = 'Opted-Out', updated_at = ? WHERE email = ?",
            (utc_now(), normalized),
        )
        conn.execute(
            "UPDATE email_drafts SET status = 'Suppressed', updated_at = ? WHERE recipient_email = ? AND status = 'Drafted'",
            (utc_now(), normalized),
        )


def is_suppressed(conn: sqlite3.Connection, email: str) -> bool:
    row = conn.execute("SELECT 1 FROM suppression_list WHERE email = ?", (email,)).fetchone()
    return row is not None


def ingest_agency_leads(json_path: Path) -> dict[str, int]:
    init_db()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    now = utc_now()
    inserted = 0
    updated = 0
    skipped_missing_email = 0
    skipped_suppressed = 0

    with connect() as conn:
        for record in payload:
            emails = extract_emails(record.get("Emails"))
            primary_email = choose_primary_email(emails)
            if not primary_email:
                skipped_missing_email += 1
                continue
            if is_suppressed(conn, primary_email):
                skipped_suppressed += 1
                continue

            lead_id = str(record.get("id") or f"{record.get('Name')}:{primary_email}")
            existing = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
            status = existing["status"] if existing else "Pending"
            params = {
                "id": lead_id,
                "name": record.get("Name") or "Unknown venue",
                "email": primary_email,
                "all_emails": ", ".join(emails),
                "issues": record.get("Issues") or "",
                "advice": record.get("Advice") or "",
                "status": status,
                "lead_score": float(record.get("Lead_Score") or 0),
                "website": record.get("Website") or "",
                "phone": record.get("Phone") or "",
                "address": record.get("Address") or "",
                "tags": str(record.get("Tags") or ""),
                "vibes": str(record.get("Vibes") or ""),
                "package_name": record.get("Package_Name") or "",
                "package_price": record.get("Package_Price") or "",
                "package_includes": record.get("Package_Includes") or "",
                "source_payload": json.dumps(record, ensure_ascii=False),
                "created_at": now,
                "updated_at": now,
            }
            conn.execute(
                """
                INSERT INTO leads (
                    id, name, email, all_emails, issues, advice, status, lead_score, website,
                    phone, address, tags, vibes, package_name, package_price, package_includes,
                    source_payload, created_at, updated_at
                )
                VALUES (
                    :id, :name, :email, :all_emails, :issues, :advice, :status, :lead_score,
                    :website, :phone, :address, :tags, :vibes, :package_name, :package_price,
                    :package_includes, :source_payload, :created_at, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    email=excluded.email,
                    all_emails=excluded.all_emails,
                    issues=excluded.issues,
                    advice=excluded.advice,
                    lead_score=excluded.lead_score,
                    website=excluded.website,
                    phone=excluded.phone,
                    address=excluded.address,
                    tags=excluded.tags,
                    vibes=excluded.vibes,
                    package_name=excluded.package_name,
                    package_price=excluded.package_price,
                    package_includes=excluded.package_includes,
                    source_payload=excluded.source_payload,
                    updated_at=excluded.updated_at
                """,
                params,
            )
            if existing:
                updated += 1
            else:
                inserted += 1

    return {
        "inserted": inserted,
        "updated": updated,
        "skipped_missing_email": skipped_missing_email,
        "skipped_suppressed": skipped_suppressed,
    }


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def get_candidate_leads(limit: int = 10) -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT l.*
            FROM leads l
            LEFT JOIN suppression_list s ON s.email = l.email
            WHERE s.email IS NULL
              AND l.email != ''
              AND l.status IN ('Pending', 'Drafted')
            ORDER BY l.lead_score DESC, l.name ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def get_outreach_stats() -> dict[str, int]:
    init_db()
    with connect() as conn:
        lead_rows = conn.execute("SELECT status, COUNT(*) AS count FROM leads GROUP BY status").fetchall()
        draft_rows = conn.execute("SELECT status, COUNT(*) AS count FROM email_drafts GROUP BY status").fetchall()
        suppressed = conn.execute("SELECT COUNT(*) AS count FROM suppression_list").fetchone()["count"]
    return {
        "pending_leads": sum(row["count"] for row in lead_rows if row["status"] == "Pending"),
        "drafted_leads": sum(row["count"] for row in lead_rows if row["status"] == "Drafted"),
        "sent_leads": sum(row["count"] for row in lead_rows if row["status"] == "Sent"),
        "opted_out": suppressed,
        "active_drafts": sum(row["count"] for row in draft_rows if row["status"] == "Drafted"),
        "sent_drafts": sum(row["count"] for row in draft_rows if row["status"] == "Sent"),
    }


def get_suppression_list(limit: int = 50) -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT email, reason, created_at
            FROM suppression_list
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def get_lead(lead_id: str) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if not row:
        raise KeyError(f"Lead not found: {lead_id}")
    return dict(row)


def latest_draft_for_lead(lead_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM email_drafts
            WHERE lead_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (lead_id,),
        ).fetchone()
    return dict(row) if row else None


def create_email_draft(
    lead_id: str,
    recipient_email: str,
    subject: str,
    body: str,
    model: str,
    status: str = "Drafted",
    error: str | None = None,
) -> dict[str, Any]:
    init_db()
    now = utc_now()
    word_count = len(re.findall(r"\b[\w'-]+\b", body))
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO email_drafts (
                lead_id, recipient_email, subject, body, model, status,
                word_count, error, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (lead_id, recipient_email, subject, body, model, status, word_count, error, now, now),
        )
        conn.execute(
            "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
            ("Drafted" if status == "Drafted" else status, now, lead_id),
        )
        draft_id = cur.lastrowid
        row = conn.execute("SELECT * FROM email_drafts WHERE id = ?", (draft_id,)).fetchone()
    return dict(row)


def get_email_drafts(limit: int = 5, status: str | None = None) -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        if status:
            rows = conn.execute(
                """
                SELECT d.*, l.name, l.issues, l.advice, l.lead_score, l.website, l.address
                FROM email_drafts d
                JOIN leads l ON l.id = d.lead_id
                WHERE d.status = ?
                ORDER BY d.created_at DESC
                LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT d.*, l.name, l.issues, l.advice, l.lead_score, l.website, l.address
                FROM email_drafts d
                JOIN leads l ON l.id = d.lead_id
                ORDER BY d.created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    return rows_to_dicts(rows)


def get_email_draft(draft_id: int) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT d.*, l.name, l.issues, l.advice, l.lead_score, l.website, l.address
            FROM email_drafts d
            JOIN leads l ON l.id = d.lead_id
            WHERE d.id = ?
            """,
            (draft_id,),
        ).fetchone()
    if not row:
        raise KeyError(f"Draft not found: {draft_id}")
    return dict(row)


def update_email_draft(draft_id: int, subject: str, body: str) -> dict[str, Any]:
    if not subject.strip() or not body.strip():
        raise ValueError("Subject and body are required")
    now = utc_now()
    word_count = len(re.findall(r"\b[\w'-]+\b", body))
    with connect() as conn:
        existing = conn.execute("SELECT status FROM email_drafts WHERE id = ?", (draft_id,)).fetchone()
        if not existing:
            raise KeyError(f"Draft not found: {draft_id}")
        if existing["status"] != "Drafted":
            raise ValueError(f"Only drafted emails can be edited; current status is {existing['status']}")
        conn.execute(
            """
            UPDATE email_drafts
            SET subject = ?, body = ?, word_count = ?, model = model || '+manual-edit', updated_at = ?
            WHERE id = ?
            """,
            (subject.strip(), body.strip(), word_count, now, draft_id),
        )
    return get_email_draft(draft_id)


def mark_draft_status(draft_id: int, status: str) -> None:
    allowed = {"Drafted", "Archived", "Suppressed", "Superseded"}
    if status not in allowed:
        raise ValueError(f"Unsupported draft status: {status}")
    now = utc_now()
    with connect() as conn:
        existing = conn.execute("SELECT lead_id FROM email_drafts WHERE id = ?", (draft_id,)).fetchone()
        if not existing:
            raise KeyError(f"Draft not found: {draft_id}")
        conn.execute(
            "UPDATE email_drafts SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, draft_id),
        )


def mark_draft_sent(draft_id: int, gmail_message_id: str) -> None:
    draft = get_email_draft(draft_id)
    now = utc_now()
    with connect() as conn:
        conn.execute(
            """
            UPDATE email_drafts
            SET status = 'Sent', gmail_message_id = ?, sent_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (gmail_message_id, now, now, draft_id),
        )
        conn.execute(
            "UPDATE leads SET status = 'Sent', last_contacted = ?, updated_at = ? WHERE id = ?",
            (now, now, draft["lead_id"]),
        )
