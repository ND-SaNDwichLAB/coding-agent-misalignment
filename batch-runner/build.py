from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Iterable

from common import (
    ROOT_DIR,
    batch_paths,
    ensure_batch_dirs,
    load_config,
    load_prompt,
    load_response_format,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--requests-per-batch", type=int, default=100)
    return parser.parse_args()


def build_request(
    *,
    custom_id: str,
    prompt: str,
    response_format: dict[str, Any],
    model: str,
    endpoint: str,
    user_content: str,
    temperature: float | None,
    reasoning_effort: str | None,
) -> dict[str, Any]:
    request = {
        "custom_id": custom_id,
        "method": "POST",
        "url": endpoint,
        "body": {
            "model": model,
            "response_format": response_format,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
        },
    }
    if temperature is not None:
        request["body"]["temperature"] = temperature
    if reasoning_effort is not None:
        request["body"]["reasoning_effort"] = reasoning_effort
    return request


def iter_file_requests(
    config: dict[str, Any], paths: dict[str, Path]
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    for session_path in sorted(ROOT_DIR.glob(config["input_glob"])):
        if not session_path.is_file():
            continue

        repo_id = session_path.parent.parent.name
        session_id = session_path.stem
        custom_id = f"{repo_id}:{session_id}"
        output_path = paths["results_dir"] / repo_id / f"{session_id}.json"
        manifest = {
            "custom_id": custom_id,
            "repo_id": repo_id,
            "session": session_id,
            "source_path": str(session_path.relative_to(ROOT_DIR)),
            "output_path": str(output_path.relative_to(ROOT_DIR)),
        }
        yield manifest, {
            "custom_id": custom_id,
            "user_content": session_path.read_text(encoding="utf-8"),
        }


def iter_json_record_requests(
    config: dict[str, Any], paths: dict[str, Path]
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    input_path = (config["_config_dir"] / config["input_path"]).resolve()
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"Expected a JSON array in {input_path}")

    prompt_fields = config.get("prompt_fields")
    if prompt_fields is not None:
        if not isinstance(prompt_fields, list) or not prompt_fields:
            raise ValueError("prompt_fields must be a non-empty string array")
        if not all(isinstance(field, str) and field for field in prompt_fields):
            raise ValueError("prompt_fields must contain only non-empty strings")

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Expected object at index {index} in {input_path}")

        if prompt_fields is None:
            prompt_row = row
        else:
            missing_fields = [field for field in prompt_fields if field not in row]
            if missing_fields:
                raise ValueError(
                    f"Missing prompt_fields {missing_fields} at index {index} in {input_path}"
                )
            prompt_row = {field: row[field] for field in prompt_fields}

        repo_id = str(row.get("repository_id", "unknown_repo"))
        session_id = str(row.get("session_id", "unknown_session"))
        record_id = str(row.get("count_id", index))
        custom_id = f"{repo_id}:{session_id}:{record_id}"
        output_path = paths["results_dir"] / repo_id / session_id / f"{record_id}.json"
        manifest = {
            "custom_id": custom_id,
            "repo_id": repo_id,
            "session": session_id,
            "record_id": record_id,
            "source_path": str(input_path.relative_to(ROOT_DIR)),
            "output_path": str(output_path.relative_to(ROOT_DIR)),
        }
        yield manifest, {
            "custom_id": custom_id,
            "user_content": json.dumps(prompt_row, ensure_ascii=False, indent=2),
        }


def iter_requests(
    config: dict[str, Any], paths: dict[str, Path]
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    input_mode = config.get("input_mode", "file_glob")
    if input_mode == "file_glob":
        yield from iter_file_requests(config, paths)
        return
    if input_mode == "json_records":
        yield from iter_json_record_requests(config, paths)
        return
    raise ValueError(f"Unsupported input_mode: {input_mode}")


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = batch_paths(config)
    ensure_batch_dirs(paths)

    for key in [
        "inputs_dir",
        "manifests_dir",
        "outputs_dir",
        "errors_dir",
        "results_dir",
    ]:
        path = paths[key]
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)

    for key in ["manifest_path", "state_path"]:
        if paths[key].exists():
            paths[key].unlink()

    prompt = load_prompt(config)
    response_format = load_response_format(config)
    temperature = config.get("temperature")
    reasoning_effort = config.get("reasoning_effort")
    total = 0
    shard_index = 0
    shard_count = 0
    input_f = None
    shard_manifest_f = None
    manifest_f = paths["manifest_path"].open("w", encoding="utf-8")

    def close_files() -> None:
        if input_f:
            input_f.close()
        if shard_manifest_f:
            shard_manifest_f.close()

    def open_files(index: int):
        input_path = paths["inputs_dir"] / f"batch_{index:03d}.jsonl"
        shard_manifest_path = paths["manifests_dir"] / f"batch_{index:03d}.jsonl"
        return (
            input_path.open("w", encoding="utf-8"),
            shard_manifest_path.open("w", encoding="utf-8"),
        )

    try:
        for manifest, request_input in iter_requests(config, paths):
            if shard_count == 0:
                shard_index += 1
                input_f, shard_manifest_f = open_files(shard_index)

            total += 1
            shard_count += 1
            request = build_request(
                custom_id=request_input["custom_id"],
                prompt=prompt,
                response_format=response_format,
                model=config["model"],
                endpoint=config["endpoint"],
                user_content=request_input["user_content"],
                temperature=temperature,
                reasoning_effort=reasoning_effort,
            )
            manifest_row = {
                **manifest,
                "batch_name": f"batch_{shard_index:03d}",
            }

            line = json.dumps(request, ensure_ascii=False) + "\n"
            manifest_line = json.dumps(manifest_row, ensure_ascii=False) + "\n"
            input_f.write(line)
            shard_manifest_f.write(manifest_line)
            manifest_f.write(manifest_line)

            if shard_count == args.requests_per_batch:
                close_files()
                input_f = None
                shard_manifest_f = None
                shard_count = 0
    finally:
        close_files()
        manifest_f.close()

    print(f"Wrote {total} requests across {shard_index} shard(s)")
    print(f"Requests per batch: {args.requests_per_batch}")
    print(f"Inputs: {paths['inputs_dir']}")
    print(f"Manifest: {paths['manifest_path']}")


if __name__ == "__main__":
    main()
