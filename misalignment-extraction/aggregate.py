from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "misalignment-extraction" / "batch" / "results"
OUTPUT_PATH = ROOT / "misalignment-extraction" / "misalignments.json"


def main() -> None:
    records: list[dict] = []
    count = 0

    for session_path in sorted(RESULTS_DIR.glob("*/*.json")):
        repository_id = session_path.parent.name
        session_id = session_path.stem
        payload = json.loads(session_path.read_text(encoding="utf-8"))

        for item in payload.get("misalignments", []):
            records.append(
                {
                    "count_id": count,
                    "repository_id": repository_id,
                    "session_id": session_id,
                    "misalignment-id": item.get("id"),
                    **{key: value for key, value in item.items() if key != "id"},
                }
            )
            count += 1

    OUTPUT_PATH.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
