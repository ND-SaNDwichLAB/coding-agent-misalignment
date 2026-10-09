"""Deterministically scan and redact credential-like strings in released JSON.

Usage:
  python redact_credentials.py --check
  python redact_credentials.py --write misalignments.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "misalignments.original.json"


SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "private_key",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
    ),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("google_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("app_token", re.compile(r"\bapp-[A-Za-z0-9]{10,}\b")),
    (
        "password_query_param",
        re.compile(r"(?i)(\bpassword=)([^&#\s`\"']{4,})"),
    ),
    (
        "email_password_pair",
        re.compile(
            r"(?P<identity>\[REDACTED:email_address:[0-9a-f]{12}\]"
            r"|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})"
            r"(?P<separator>\s*/\s*)"
            r"(?P<password>[^\s`\"'<>]{8,})"
        ),
    ),
    (
        "email_address",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "uri_credentials",
        re.compile(
            r"\b(?P<scheme>[A-Za-z][A-Za-z0-9+.-]{2,}://)"
            r"(?P<username>[^:@/\s\"'<>]+)"
            r":(?P<password>[^@/\s\"'<>]+)"
            r"@"
        ),
    ),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b"
            r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|secret|password|passwd)"
            r"\b(\s*[:=]\s*)(['\"]?)([^'\"\s,;)}\]]{8,})(['\"]?)"
        ),
    ),
]


PLACEHOLDER_PREFIXES = ("YOUR_", "REDACTED", "PLACEHOLDER", "EXAMPLE_", "DUMMY_")
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(?:^|[_-])("
    r"api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|"
    r"client[_-]?secret|secret(?:[_-]?key)?|password|passwd|private[_-]?key|"
    r"token|database[_-]?url|connection[_-]?string"
    r")(?:$|[_-])"
)


def stable_placeholder(label: str, secret: str) -> str:
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]
    return f"[REDACTED:{label}:{digest}]"


def is_placeholder_like(value: str) -> bool:
    upper_value = value.upper()
    return value.startswith(PLACEHOLDER_PREFIXES) or upper_value.startswith(
        PLACEHOLDER_PREFIXES
    )


def is_env_reference(value: str) -> bool:
    lowered = value.lower()
    return (
        "process.env" in lowered
        or "import.meta.env" in lowered
        or "os.environ" in lowered
    )


def should_redact_email(value: str, text: str, start: int) -> bool:
    lowered = value.lower()
    if lowered in {"git@github.com", "git@gitlab.com", "git@bitbucket.org"}:
        return False

    prefix = text[max(0, start - 3) : start]
    if prefix.endswith("://"):
        return False

    return True


def looks_secret_like(value: str) -> bool:
    if len(value) < 8:
        return False
    if is_placeholder_like(value) or is_env_reference(value):
        return False
    if re.fullmatch(r"[A-Z0-9_]+", value):
        return False

    has_lower = any(char.islower() for char in value)
    has_upper = any(char.isupper() for char in value)
    has_digit = any(char.isdigit() for char in value)
    has_symbol = any(char in "+/=_-." for char in value)

    return sum([has_lower, has_upper, has_digit, has_symbol]) >= 2


def redact_text(text: str) -> tuple[str, list[tuple[str, str]]]:
    redacted = text
    hits: list[tuple[str, str]] = []

    for label, pattern in SECRET_PATTERNS:
        if label == "credential_assignment":

            def replace_assignment(match: re.Match[str]) -> str:
                separator = match.group(1)
                opening_quote = match.group(2)
                value = match.group(3)
                closing_quote = match.group(4)
                if not looks_secret_like(value):
                    return match.group(0)
                hits.append((label, value))
                placeholder = stable_placeholder(label, value)
                return f"{separator}{opening_quote}{placeholder}{closing_quote}"

            redacted = pattern.sub(replace_assignment, redacted)
            continue
        if label == "password_query_param":

            def replace_password_query_param(match: re.Match[str]) -> str:
                password = match.group(2)
                hits.append((label, password))
                return f"{match.group(1)}{stable_placeholder(label, password)}"

            redacted = pattern.sub(replace_password_query_param, redacted)
            continue
        if label == "email_password_pair":

            def replace_email_password_pair(match: re.Match[str]) -> str:
                password = match.group("password")
                if password.startswith("[REDACTED:"):
                    return match.group(0)
                hits.append((label, password))
                return (
                    f"{match.group('identity')}{match.group('separator')}"
                    f"{stable_placeholder(label, password)}"
                )

            redacted = pattern.sub(replace_email_password_pair, redacted)
            continue
        if label == "email_address":

            def replace_email(match: re.Match[str]) -> str:
                email = match.group(0)
                if not should_redact_email(email, redacted, match.start()):
                    return email
                hits.append((label, email))
                return stable_placeholder(label, email)

            redacted = pattern.sub(replace_email, redacted)
            continue
        if label == "uri_credentials":

            def replace_uri_credentials(match: re.Match[str]) -> str:
                password = match.group("password")
                if password.startswith("[REDACTED:"):
                    return match.group(0)
                hits.append((label, password))
                return (
                    f"{match.group('scheme')}{match.group('username')}:"
                    f"{stable_placeholder(label, password)}@"
                )

            redacted = pattern.sub(replace_uri_credentials, redacted)
            continue

        def replace_direct(match: re.Match[str]) -> str:
            secret = match.group(0)
            hits.append((label, secret))
            return stable_placeholder(label, secret)

        redacted = pattern.sub(replace_direct, redacted)

    return redacted, hits


def redact_json(value: Any) -> tuple[Any, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []

    def walk(node: Any, path: str) -> Any:
        if isinstance(node, str):
            redacted, hits = redact_text(node)
            if redacted != node:
                for label, secret in hits:
                    findings.append(
                        {
                            "path": path,
                            "label": label,
                            "sample": stable_placeholder(label, secret),
                        }
                    )
            return redacted

        if isinstance(node, list):
            return [walk(item, f"{path}[{index}]") for index, item in enumerate(node)]

        if isinstance(node, dict):
            result: dict[str, Any] = {}
            for key, item in node.items():
                child_path = f"{path}.{key}" if path else key
                if isinstance(item, str) and SENSITIVE_KEY_PATTERN.search(key):
                    redacted, hits = redact_text(item)
                    if redacted == item and looks_secret_like(item):
                        redacted = stable_placeholder("sensitive_field", item)
                        hits = [("sensitive_field", item)]
                    if redacted != item:
                        for label, secret in hits:
                            findings.append(
                                {
                                    "path": child_path,
                                    "label": label,
                                    "sample": stable_placeholder(label, secret),
                                }
                            )
                        result[key] = redacted
                        continue
                result[key] = walk(item, child_path)
            return result

        return node

    return walk(value, ""), findings


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()

    payload = load_json(args.input)
    redacted, findings = redact_json(payload)

    if args.check:
        print(f"input: {args.input}")
        print(f"findings: {len(findings)}")
        by_label: dict[str, int] = {}
        for finding in findings:
            by_label[finding["label"]] = by_label.get(finding["label"], 0) + 1
        for label, count in sorted(by_label.items()):
            print(f"  {label}: {count}")
        for finding in findings[:10]:
            print(f"  - {finding['path']} [{finding['label']}] {finding['sample']}")

    if args.write:
        write_json(args.write, redacted)
        print(f"wrote redacted output to {args.write}")


if __name__ == "__main__":
    main()
