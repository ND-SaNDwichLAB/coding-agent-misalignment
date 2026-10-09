from __future__ import annotations

import argparse

from common import (
    batch_paths,
    expand_batch_specs,
    get_client,
    load_config,
    load_state,
    save_state,
)

TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cancel submitted batches and remove them from state so they can be resubmitted."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("batch_names", nargs="+")
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only remove batches from local state without calling the Batch API.",
    )
    parser.add_argument(
        "--keep-state",
        action="store_true",
        help="Cancel batches but keep their entries in state.json for later check/download.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = batch_paths(config)
    state = load_state(paths)
    wanted = expand_batch_specs(args.batch_names)
    client = None if args.local_only else get_client()

    updated_jobs = []
    removed = 0

    for job in state["jobs"]:
        if job["name"] not in wanted:
            updated_jobs.append(job)
            continue

        if client is not None:
            batch = client.batches.retrieve(job["batch_id"])
            if batch.status not in TERMINAL_STATUSES:
                batch = client.batches.cancel(job["batch_id"])
            job.update(
                {
                    "status": batch.status,
                    "output_file_id": batch.output_file_id,
                    "error_file_id": batch.error_file_id,
                }
            )
            if args.keep_state:
                updated_jobs.append(job)
                print(
                    f"{job['name']}: kept in state after remote status={batch.status}"
                )
            else:
                print(
                    f"{job['name']}: removed from state after remote status={batch.status}"
                )
        else:
            if args.keep_state:
                updated_jobs.append(job)
                print(f"{job['name']}: kept in state (local only)")
            else:
                print(f"{job['name']}: removed from state (local only)")

        removed += 1

    missing = sorted(wanted - {job["name"] for job in state["jobs"]})
    for batch_name in missing:
        print(f"{batch_name}: not found in state")

    state["jobs"] = updated_jobs
    save_state(paths, state)
    if args.keep_state:
        print(
            f"Cancelled {removed} batch entr{'y' if removed == 1 else 'ies'} and kept them in state"
        )
    else:
        print(
            f"Removed {removed} batch entr{'y' if removed == 1 else 'ies'} from state"
        )


if __name__ == "__main__":
    main()
