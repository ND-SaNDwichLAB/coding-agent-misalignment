from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import (
    batch_paths,
    expand_batch_specs,
    get_client,
    iter_manifest,
    load_config,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build one retry batch from unprocessed requests across batches, "
            "and optionally submit it."
        )
    )
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "batch_names",
        nargs="*",
        help="Optional batch names/ranges to include, e.g. batch_001 4-7",
    )
    parser.add_argument(
        "--retry-name",
        help=(
            "Name for the retry bundle directory. Defaults to retry_<source batches> "
            "or retry_all."
        ),
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit the generated retry batch after writing files.",
    )
    return parser.parse_args()


def derive_retry_name(args: argparse.Namespace, wanted_batches: set[str]) -> str:
    if args.retry_name:
        return args.retry_name
    if wanted_batches:
        joined = "_".join(sorted(wanted_batches))
        return f"retry_{joined}"
    return "retry_all"


def load_requests(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    requests: dict[str, dict[str, Any]] = {}

    for input_path in sorted(paths["inputs_dir"].glob("*.jsonl")):
        with input_path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                requests[row["custom_id"]] = row

    return requests


def collect_unprocessed_requests(
    paths: dict[str, Path],
    wanted_batches: set[str],
    request_index: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    unprocessed_requests: list[dict[str, Any]] = []
    stats = defaultdict(int)
    seen_custom_ids: set[str] = set()

    state_path = paths["state_path"]
    if not state_path.exists():
        stats["state_missing"] = 1
        return unprocessed_requests, dict(stats)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    for job in state.get("jobs", []):
        job_name = job.get("name")
        if not job_name:
            stats["jobs_missing_name"] += 1
            continue
        if wanted_batches and job_name not in wanted_batches:
            continue

        input_path_text = job.get("input_path")
        if not input_path_text:
            stats["jobs_missing_input_path"] += 1
            continue

        input_path = Path(input_path_text)
        if not input_path.exists():
            stats["jobs_missing_input_file"] += 1
            continue

        input_custom_ids: list[str] = []
        with input_path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                custom_id = row.get("custom_id")
                if custom_id:
                    input_custom_ids.append(str(custom_id))

        output_custom_ids = set()
        output_path = paths["outputs_dir"] / f"{job_name}.jsonl"
        if output_path.exists():
            with output_path.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    custom_id = row.get("custom_id")
                    if custom_id:
                        output_custom_ids.add(str(custom_id))

        for custom_id in input_custom_ids:
            if custom_id in output_custom_ids:
                continue
            if custom_id in seen_custom_ids:
                stats["duplicate_unprocessed_custom_id"] += 1
                continue
            request = request_index.get(custom_id)
            if not request:
                stats["missing_unprocessed_request"] += 1
                continue

            seen_custom_ids.add(custom_id)
            unprocessed_requests.append(
                {
                    "custom_id": custom_id,
                    "source_batch_name": job_name,
                    "source_status": job.get("status", "unknown"),
                    "source_kind": "unprocessed",
                    "request": request,
                }
            )
            stats["selected_unprocessed_requests"] += 1

    return unprocessed_requests, dict(stats)


def write_retry_bundle(
    paths: dict[str, Path],
    retry_name: str,
    unprocessed_requests: list[dict[str, Any]],
    manifest_index: dict[str, dict[str, Any]],
    submit: bool,
    config: dict[str, Any],
) -> tuple[Path, Path, Path, dict[str, Any]]:
    retries_dir = paths["batch_dir"] / "retries"
    retries_dir.mkdir(parents=True, exist_ok=True)
    input_path = paths["inputs_dir"] / f"{retry_name}.jsonl"
    manifest_path = paths["manifests_dir"] / f"{retry_name}.jsonl"
    summary_path = retries_dir / f"{retry_name}.summary.json"

    missing_manifest: list[str] = []
    written = 0
    source_batches: set[str] = set()
    source_statuses: set[str] = set()
    with input_path.open("w", encoding="utf-8") as input_f, manifest_path.open(
        "w", encoding="utf-8"
    ) as manifest_f:
        for unprocessed_request in unprocessed_requests:
            custom_id = unprocessed_request["custom_id"]
            request = unprocessed_request["request"]
            record = manifest_index.get(custom_id)
            if not record:
                missing_manifest.append(custom_id)
                continue

            source_batches.add(unprocessed_request["source_batch_name"])
            source_statuses.add(unprocessed_request.get("source_status", "unknown"))
            input_f.write(json.dumps(request, ensure_ascii=False) + "\n")

            manifest_row = {
                "custom_id": custom_id,
                "retry_batch_name": retry_name,
                "source_batch_name": unprocessed_request["source_batch_name"],
                "source_status": unprocessed_request.get("source_status", "unknown"),
            }
            for key in [
                "repo_id",
                "session",
                "record_id",
                "source_path",
                "output_path",
            ]:
                if key in record:
                    manifest_row[key] = record[key]
            manifest_f.write(json.dumps(manifest_row, ensure_ascii=False) + "\n")
            written += 1

    summary = {
        "retry_name": retry_name,
        "input_path": str(input_path),
        "manifest_path": str(manifest_path),
        "submitted": False,
        "request_count": written,
        "unprocessed_request_count": written,
        "source_batch_count": len(source_batches),
        "source_batches": sorted(source_batches),
        "source_statuses": sorted(source_statuses),
        "missing_manifest_count": len(missing_manifest),
        "missing_manifest_custom_ids": missing_manifest,
    }
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if submit and written == 0:
        raise ValueError("Retry bundle contains zero requests; refusing to submit")

    return input_path, manifest_path, summary_path, summary


def submit_retry(
    config: dict[str, Any], paths: dict[str, Path], retry_name: str, input_path: Path
) -> dict[str, Any]:
    client = get_client()
    if paths["state_path"].exists():
        state = json.loads(paths["state_path"].read_text(encoding="utf-8"))
    else:
        state = {"jobs": []}

    existing = {job["name"] for job in state["jobs"]}
    if retry_name in existing:
        raise ValueError(
            f"{retry_name} already exists in state.json; choose a different --retry-name "
            "or remove the old job first"
        )

    with input_path.open("rb") as f:
        input_file = client.files.create(file=f, purpose="batch")

    batch = client.batches.create(
        input_file_id=input_file.id,
        endpoint=config["endpoint"],
        completion_window="24h",
    )

    state["jobs"].append(
        {
            "name": retry_name,
            "input_path": str(input_path),
            "input_file_id": input_file.id,
            "batch_id": batch.id,
            "status": batch.status,
            "output_file_id": batch.output_file_id,
            "error_file_id": batch.error_file_id,
        }
    )
    paths["state_path"].write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return state["jobs"][-1]


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = batch_paths(config)
    wanted_batches = expand_batch_specs(args.batch_names) if args.batch_names else set()
    retry_name = derive_retry_name(args, wanted_batches)

    manifest_index = iter_manifest(paths)
    request_index = load_requests(paths)
    unprocessed_requests, unprocessed_stats = collect_unprocessed_requests(
        paths, wanted_batches, request_index
    )

    input_path, manifest_path, summary_path, summary = write_retry_bundle(
        paths=paths,
        retry_name=retry_name,
        unprocessed_requests=unprocessed_requests,
        manifest_index=manifest_index,
        submit=args.submit,
        config=config,
    )

    print(f"Retry input: {input_path}")
    print(f"Retry manifest: {manifest_path}")
    print(f"Retry summary: {summary_path}")
    print(f"Selected {summary['request_count']} unprocessed request(s)")

    if summary["missing_manifest_count"]:
        print(f"Missing manifest rows: {summary['missing_manifest_count']}")
    if unprocessed_stats.get("state_missing"):
        print("State file missing; no batches were scanned for unprocessed requests")

    if not args.submit:
        print(
            "Submit skipped. Re-run with --submit to create the retry batch remotely."
        )
        return

    job = submit_retry(config, paths, retry_name, input_path)
    summary["submitted"] = True
    summary["remote_job"] = job
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Submitted {retry_name}: {job['batch_id']} ({job['status']})")


if __name__ == "__main__":
    main()
