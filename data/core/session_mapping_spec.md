# `session_mapping.json` Data Specification

This file maps dataset-local session identifiers to normalized session metadata.

## Row unit

One row = one session in one source dataset.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `repository_id` | string or integer | Repository identifier used in the source dataset. |
| `num_commits` | integer | Repository-level commit count from the attributed repository metadata. |
| `license_type` | string | Repository license type from the attributed repository metadata, e.g. `MIT`. |
| `session_count_id` | integer | Numeric session index used to build `session_###` identifiers in downstream files. |
| `session_sha` | string | Source-specific stable session identifier. For example, this may be a hash-like ID or a UUID depending on source. |
| `session_timestamp` | string | Session creation timestamp from the attributed source mapping. |
| `session_type` | string | Session platform/modality, e.g. `IDE` or `CLI`. |
| `agent` | string | Attributed agent name if available; otherwise `Unknown`. |
| `user_turns` | integer | Number of user-authored messages in the session. |
| `agent_turns` | integer | Number of agent-authored messages in the session. |
| `source` | string | Dataset source: `specstory` or `swe`. |

## Join keys

This table is joined to the final misalignment files on:

`source` + `repository_id` + `session_count_id`
