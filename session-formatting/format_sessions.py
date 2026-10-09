from pathlib import Path
import json
from tqdm import tqdm
import shutil
import numpy as np


def get_max_chars(role: str, num_turns: int, is_cli: bool) -> int:
    if num_turns <= 8:  # 62% of sessions
        agent_max = 5_000
    elif num_turns <= 16:  # p75
        agent_max = 3_000
    elif num_turns <= 42:  # p90
        agent_max = 2_000
    elif num_turns <= 74:  # p95
        agent_max = 1_000
    else:
        agent_max = 500

    if role == "USER":
        return np.inf
    elif is_cli:
        return agent_max
    else:
        return agent_max


def merge_consecutive_roles(messages: list[dict]) -> list[dict]:
    """Merge consecutive messages with the same role into one."""
    if not messages:
        return messages

    merged = []
    current = messages[0].copy()

    for msg in messages[1:]:
        if msg.get("role") == current.get("role"):
            current["content"] = current["content"] + "\n\n" + msg.get("content", "")
        else:
            merged.append(current)
            current = msg.copy()

    merged.append(current)
    return merged


def format_session_for_llm(
    session: dict,
    head_ratio: float = 0.5,
) -> str:
    TURN_DIVIDER = "─" * 40

    def truncate(text: str, max_chars: int) -> tuple[str, bool, int]:
        """Returns (display_text, was_truncated, original_length)."""
        original_len = len(text)
        if original_len <= max_chars:
            return text, False, original_len
        head = int(max_chars * head_ratio)
        tail = max_chars - head
        omitted = original_len - max_chars
        display = (
            text[:head] + f"\n\n... [{omitted} chars omitted] ...\n\n" + text[-tail:]
        )
        return display, True, original_len

    messages = session.get("messages", [])
    messages = merge_consecutive_roles(messages)
    session_id = session.get("title", session.get("session_id", "unknown"))
    date = session.get("timestamp", session.get("created_at", "unknown"))
    is_cli = (
        session.get("platform", session.get("agent", "unknown")) != "Cursor / Copilot"
    )

    turn_number = 0
    turns_output = []

    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        message_max_chars = get_max_chars(role, len(messages), is_cli)
        turn_number += 1

        # Remove special tokens if present
        content = content.replace("<|endoftext|>", "")

        if content.startswith("---"):
            content = content[3:].lstrip()
        if content.endswith("---"):
            content = content[:-3].rstrip()

        display_text, was_truncated, original_len = truncate(content, message_max_chars)

        if was_truncated:
            header = (
                f"{TURN_DIVIDER}\n"
                f"[TURN {turn_number} | {role}]"
                f" [TRUNCATED: {message_max_chars}/{original_len} chars]\n"
                f"{TURN_DIVIDER}"
            )
        else:
            header = (
                f"{TURN_DIVIDER}\n" f"[TURN {turn_number} | {role}]\n" f"{TURN_DIVIDER}"
            )

        turns_output.append(f"{header}\n{display_text}")

    total_turns = turn_number
    user_turns = sum(1 for m in messages if m.get("role", "").upper() == "USER")
    agent_turns = total_turns - user_turns

    header_block = (
        f"SESSION METADATA\n"
        f"{'=' * 40}\n"
        f"Title      : {session_id}\n"
        f"Date       : {date}\n"
        f"Total turns: {total_turns} ({user_turns} user, {agent_turns} agent)\n"
    )

    conversation_block = (
        f"{'=' * 40}\n" f"CONVERSATION\n" f"{'=' * 40}\n\n" + "\n\n".join(turns_output)
    )

    footer_block = f"\n{'=' * 40}\nEND OF SESSION\n{'=' * 40}"

    return header_block + "\n" + conversation_block + footer_block


def format_all_sessions(workspace_root: str = "../workspace") -> None:
    workspace = Path(workspace_root)
    repo_dirs = [d for d in workspace.iterdir() if d.is_dir()]

    for repo_dir in tqdm(sorted(repo_dirs)):
        parsed_dir = repo_dir / "session_parsed"
        if not parsed_dir.exists():
            continue

        formatted_dir = repo_dir / "session_formatted"
        if formatted_dir.exists():
            shutil.rmtree(formatted_dir)
        formatted_dir.mkdir()

        session_files = sorted(parsed_dir.glob("*.json"))
        if not session_files:
            continue

        for session_path in session_files:
            output_path = formatted_dir / session_path.with_suffix(".txt").name

            try:
                with open(session_path, encoding="utf-8") as f:
                    session = json.load(f)

                formatted = format_session_for_llm(session, head_ratio=0.5)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(formatted)

            except Exception as e:
                print(f"  ERROR {session_path.name}: {e}")


format_all_sessions(workspace_root="../workspace")
