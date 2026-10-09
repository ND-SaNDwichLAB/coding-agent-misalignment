from __future__ import annotations

import argparse

from common import batch_paths, get_client, load_config, load_state, save_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("batch_names", nargs="*")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = batch_paths(config)
    state = load_state(paths)
    client = get_client()
    wanted = set(args.batch_names)

    for job in state["jobs"]:
        if wanted and job["name"] not in wanted:
            continue

        batch = client.batches.retrieve(job["batch_id"])
        job.update(
            {
                "status": batch.status,
                "output_file_id": batch.output_file_id,
                "error_file_id": batch.error_file_id,
            }
        )

        if batch.output_file_id:
            output_path = paths["outputs_dir"] / f"{job['name']}.jsonl"
            output_path.write_text(
                client.files.content(batch.output_file_id).text, encoding="utf-8"
            )
            print(f"{job['name']}: {output_path}")

        if batch.error_file_id:
            error_path = paths["errors_dir"] / f"{job['name']}.jsonl"
            error_path.write_text(
                client.files.content(batch.error_file_id).text, encoding="utf-8"
            )
            print(f"{job['name']} errors: {error_path}")

        if not batch.output_file_id and not batch.error_file_id:
            print(f"{job['name']}: skipped ({batch.status})")

    save_state(paths, state)


if __name__ == "__main__":
    main()
