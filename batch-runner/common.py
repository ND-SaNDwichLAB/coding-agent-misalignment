from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config(config_path: str) -> dict:
    path = (ROOT_DIR / config_path).resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    config["_config_path"] = path
    config["_config_dir"] = path.parent
    config["prompt_path"] = str((path.parent / config["prompt_path"]).resolve())
    config["batch_dir"] = str((path.parent / config["batch_dir"]).resolve())
    return config


def batch_paths(config: dict) -> dict[str, Path]:
    batch_dir = Path(config["batch_dir"])
    return {
        "batch_dir": batch_dir,
        "inputs_dir": batch_dir / "inputs",
        "manifests_dir": batch_dir / "manifests",
        "manifest_path": batch_dir / "manifest.jsonl",
        "outputs_dir": batch_dir / "outputs",
        "errors_dir": batch_dir / "errors",
        "state_path": batch_dir / "state.json",
        "results_dir": batch_dir / "results",
    }


def ensure_batch_dirs(paths: dict[str, Path]) -> None:
    for key, path in paths.items():
        if key.endswith("_dir"):
            path.mkdir(parents=True, exist_ok=True)


def get_client():
    from openai import OpenAI

    return OpenAI()


def load_prompt(config: dict) -> str:
    return Path(config["prompt_path"]).read_text(encoding="utf-8").strip()


def load_response_format(config: dict):
    response_format_path = config.get("response_format_path")
    if response_format_path:
        path = (config["_config_dir"] / response_format_path).resolve()
        return json.loads(path.read_text(encoding="utf-8"))

    response_format = config.get("response_format", "json_object")
    if isinstance(response_format, str):
        return {"type": response_format}
    return response_format


def load_state(paths: dict[str, Path]) -> dict:
    state_path = paths["state_path"]
    if not state_path.exists():
        raise FileNotFoundError(f"Missing state file: {state_path}")
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(paths: dict[str, Path], state: dict) -> None:
    ensure_batch_dirs(paths)
    paths["state_path"].write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_batch_number(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    if value.startswith("batch_"):
        suffix = value.removeprefix("batch_")
        if suffix.isdigit():
            return int(suffix)
    return None


def expand_batch_specs(specs: list[str]) -> set[str]:
    wanted = set()

    for spec in specs:
        if "-" in spec:
            start_text, end_text = spec.split("-", 1)
            start = parse_batch_number(start_text)
            end = parse_batch_number(end_text)
            if start is not None and end is not None:
                if start > end:
                    raise ValueError(f"Invalid batch range: {spec}")

                for number in range(start, end + 1):
                    wanted.add(f"batch_{number:03d}")
                continue

        number = parse_batch_number(spec)
        if number is not None:
            wanted.add(f"batch_{number:03d}")
            continue

        # Allow explicitly named one-off batches such as retry_all.
        wanted.add(spec)

    return wanted


def iter_manifest(paths: dict[str, Path]) -> dict[str, dict]:
    records = {}
    manifest_path = paths["manifest_path"]
    if not manifest_path.exists():
        return records
    with manifest_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            records[row["custom_id"]] = row
    return records
