from __future__ import annotations

import argparse
import json

from common import batch_paths, expand_batch_specs, get_client, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("batch_names", nargs="*")
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = batch_paths(config)
    client = get_client()

    if paths["state_path"].exists():
        state = json.loads(paths["state_path"].read_text(encoding="utf-8"))
    else:
        state = {"jobs": []}

    existing = {job["name"] for job in state["jobs"]}
    inputs = sorted(paths["inputs_dir"].glob("*.jsonl"))

    if args.batch_names:
        wanted = expand_batch_specs(args.batch_names)
        inputs = [path for path in inputs if path.stem in wanted]
    if args.limit:
        inputs = inputs[: args.limit]

    for input_path in inputs:
        if input_path.stem in existing:
            print(f"{input_path.stem}: already submitted")
            continue

        with input_path.open("rb") as f:
            input_file = client.files.create(file=f, purpose="batch")

        batch = client.batches.create(
            input_file_id=input_file.id,
            endpoint=config["endpoint"],
            completion_window="24h",
        )

        state["jobs"].append(
            {
                "name": input_path.stem,
                "input_path": str(input_path),
                "input_file_id": input_file.id,
                "batch_id": batch.id,
                "status": batch.status,
                "output_file_id": batch.output_file_id,
                "error_file_id": batch.error_file_id,
            }
        )
        print(f"{input_path.stem}: {batch.id} ({batch.status})")

    paths["state_path"].write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
