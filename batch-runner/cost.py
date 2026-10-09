from __future__ import annotations

import argparse
import json
from typing import Any

from common import batch_paths, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("batch_names", nargs="*")
    return parser.parse_args()


def load_price(config: dict) -> dict[str, float]:
    price = config.get("price")
    if not isinstance(price, dict):
        raise ValueError("Missing price configuration in task config")

    required_keys = ["input", "cached_input", "output"]
    missing = [key for key in required_keys if key not in price]
    if missing:
        raise ValueError(f"Missing price values in task config: {', '.join(missing)}")

    return {
        "input": float(price["input"]),
        "cached_input": float(price["cached_input"]),
        "output": float(price["output"]),
    }


def get_usage(row: dict[str, Any]) -> dict[str, Any]:
    response = row.get("response") or {}
    body = response.get("body") or {}
    usage = body.get("usage") or row.get("usage") or {}
    return usage if isinstance(usage, dict) else {}


def get_token_counts(usage: dict[str, Any]) -> tuple[int, int, int]:
    prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
    completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")

    prompt_tokens = int(prompt_tokens or 0)
    completion_tokens = int(completion_tokens or 0)

    prompt_details = (
        usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    )
    cached_tokens = 0
    if isinstance(prompt_details, dict):
        cached_tokens = int(prompt_details.get("cached_tokens") or 0)
    cached_tokens = min(cached_tokens, prompt_tokens)

    return prompt_tokens, cached_tokens, completion_tokens


def cost_for_row(
    usage: dict[str, Any], price: dict[str, float]
) -> tuple[int, int, int, float, float, float, float]:
    prompt_tokens, cached_tokens, completion_tokens = get_token_counts(usage)
    uncached_tokens = max(prompt_tokens - cached_tokens, 0)
    input_cost = uncached_tokens / 1_000_000 * price["input"]
    cached_cost = cached_tokens / 1_000_000 * price["cached_input"]
    output_cost = completion_tokens / 1_000_000 * price["output"]
    total_cost = input_cost + cached_cost + output_cost
    return (
        uncached_tokens,
        cached_tokens,
        completion_tokens,
        input_cost,
        cached_cost,
        output_cost,
        total_cost,
    )


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    paths = batch_paths(config)
    price = load_price(config)
    wanted = set(args.batch_names)

    output_paths = sorted(paths["outputs_dir"].glob("*.jsonl"))
    if wanted:
        output_paths = [path for path in output_paths if path.stem in wanted]

    if not output_paths:
        print(f"No output files found in {paths['outputs_dir']}")
        return

    grand = {
        "files": 0,
        "rows": 0,
        "requests_with_usage": 0,
        "requests_without_usage": 0,
        "uncached_input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "input_cost": 0.0,
        "cached_cost": 0.0,
        "output_cost": 0.0,
        "cost": 0.0,
    }

    for output_path in output_paths:
        file_rows = 0
        file_with_usage = 0
        file_without_usage = 0
        file_uncached = 0
        file_cached = 0
        file_output = 0
        file_input_cost = 0.0
        file_cached_cost = 0.0
        file_output_cost = 0.0
        file_cost = 0.0

        with output_path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                file_rows += 1
                usage = get_usage(row)
                if not usage:
                    file_without_usage += 1
                    continue

                (
                    uncached_tokens,
                    cached_tokens,
                    completion_tokens,
                    row_input_cost,
                    row_cached_cost,
                    row_output_cost,
                    row_cost,
                ) = cost_for_row(usage, price)
                file_with_usage += 1
                file_uncached += uncached_tokens
                file_cached += cached_tokens
                file_output += completion_tokens
                file_input_cost += row_input_cost
                file_cached_cost += row_cached_cost
                file_output_cost += row_output_cost
                file_cost += row_cost

        grand["files"] += 1
        grand["rows"] += file_rows
        grand["requests_with_usage"] += file_with_usage
        grand["requests_without_usage"] += file_without_usage
        grand["uncached_input_tokens"] += file_uncached
        grand["cached_input_tokens"] += file_cached
        grand["output_tokens"] += file_output
        grand["input_cost"] += file_input_cost
        grand["cached_cost"] += file_cached_cost
        grand["output_cost"] += file_output_cost
        grand["cost"] += file_cost

        print(
            f"{output_path.stem}: rows={file_rows}, usage={file_with_usage}, "
            f"missing_usage={file_without_usage}, "
            f"input={file_uncached:,}, cached={file_cached:,}, output={file_output:,}, "
            f"input_cost=${file_input_cost:.2f}, cached_cost=${file_cached_cost:.2f}, "
            f"output_cost=${file_output_cost:.2f}, cost=${file_cost:.2f}"
        )

    print("-")
    print(
        f"TOTAL: files={grand['files']}, rows={grand['rows']}, usage={grand['requests_with_usage']}, "
        f"missing_usage={grand['requests_without_usage']}, "
        f"input={grand['uncached_input_tokens']:,}, cached={grand['cached_input_tokens']:,}, "
        f"output={grand['output_tokens']:,}, input_cost=${grand['input_cost']:.2f}, "
        f"cached_cost=${grand['cached_cost']:.2f}, output_cost=${grand['output_cost']:.2f}, "
        f"cost=${grand['cost']:.2f}"
    )
    print(
        f"Prices per 1M tokens: input=${price['input']}, cached_input=${price['cached_input']}, "
        f"output=${price['output']}"
    )


if __name__ == "__main__":
    main()
