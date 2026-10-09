from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import ROOT_DIR, batch_paths, iter_manifest, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("batch_names", nargs="*")
    return parser.parse_args()


def json_record_custom_id(row: dict, index: int) -> str:
    repo_id = str(row.get("repository_id", "unknown_repo"))
    session_id = str(row.get("session_id", "unknown_session"))
    record_id = str(row.get("count_id", index))
    return f"{repo_id}:{session_id}:{record_id}"


def extract_payload(row: dict) -> dict:
    message = row["response"]["body"]["choices"][0]["message"]["content"]
    return json.loads(message)


def postprocess_file_glob(
    paths: dict[Path, Path] | dict[str, Path],
    manifest: dict[str, dict],
    wanted: set[str],
) -> int:
    written = 0

    for output_path in sorted(paths["outputs_dir"].glob("*.jsonl")):
        if wanted and output_path.stem not in wanted:
            continue

        with output_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                record = manifest.get(row["custom_id"])
                if not record:
                    continue

                payload = extract_payload(row)
                result_path = ROOT_DIR / record["output_path"]
                result_path.parent.mkdir(parents=True, exist_ok=True)
                result_path.write_text(
                    json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                written += 1

        print(f"{output_path.stem}: parsed")

    return written


def postprocess_json_records(
    config: dict, paths: dict[str, Path], manifest: dict[str, dict], wanted: set[str]
) -> int:
    input_path = (config["_config_dir"] / config["input_path"]).resolve()
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"Expected a JSON array in {input_path}")

    parsed_by_custom_id: dict[str, dict] = {}
    for output_path in sorted(paths["outputs_dir"].glob("*.jsonl")):
        if wanted and output_path.stem not in wanted:
            continue

        with output_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                if row["custom_id"] not in manifest:
                    continue
                parsed_by_custom_id[row["custom_id"]] = extract_payload(row)

        print(f"{output_path.stem}: parsed")

    combined_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Expected object at index {index} in {input_path}")
        custom_id = json_record_custom_id(row, index)
        payload = parsed_by_custom_id.get(custom_id)
        if payload is None:
            continue
        combined_rows.append({**row, **payload})

    aggregate_output_path = config.get(
        "aggregate_output_path", "validated_misalignments.json"
    )
    output_path = (config["_config_dir"] / aggregate_output_path).resolve()
    output_path.write_text(
        json.dumps(combined_rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Aggregate output: {output_path}")
    return len(combined_rows)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = batch_paths(config)
    manifest = iter_manifest(paths)
    wanted = set(args.batch_names)
    input_mode = config.get("input_mode", "file_glob")
    if input_mode == "json_records":
        written = postprocess_json_records(config, paths, manifest, wanted)
    else:
        written = postprocess_file_glob(paths, manifest, wanted)

    print(f"Results dir: {paths['results_dir']}")
    print(f"Wrote {written} parsed report(s)")


if __name__ == "__main__":
    main()
