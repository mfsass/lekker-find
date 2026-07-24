from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.config import load_environment
from services.database import get_candidate_leads, ingest_agency_leads


def main() -> None:
    load_environment()
    result = ingest_agency_leads(Path("data") / "agency_leads.json")
    print(result)
    print({"candidate_count": len(get_candidate_leads(10))})


if __name__ == "__main__":
    main()
