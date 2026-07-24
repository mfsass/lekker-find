from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.config import load_environment
from services.database import get_candidate_leads, get_email_drafts
from services.outreach import export_queue_snapshot, generate_drafts, ingest_default_leads


def main() -> None:
    load_environment()
    ingestion = ingest_default_leads()
    result = generate_drafts(limit=5, candidate_limit=10, allow_template_fallback=True)
    export_queue_snapshot(Path("data") / "masa_queue_snapshot.json", candidate_limit=10, draft_limit=5)
    print(
        {
            "ingestion": ingestion,
            "candidate_count": len(get_candidate_leads(10)),
            "draft_count": len(get_email_drafts(5, status="Drafted")),
            "generation_errors": result["errors"],
            "snapshot": "data\\masa_queue_snapshot.json",
        }
    )


if __name__ == "__main__":
    main()
