# `validated_misalignments.json` Data Specification

This file contains extracted misalignment records after validation and metadata joining.

## Row unit

One row = one extracted misalignment episode plus its validation judgment and session metadata.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `count_id` | integer | Global sequential row identifier inherited from the extraction aggregation pipeline. |
| `repository_id` | string or integer | Repository identifier used in the source dataset. |
| `session_id` | string | Session key in `session_###` format within a repository/source. |
| `misalignment_id` | string | Misalignment identifier within the session, usually `M001`, `M002`, etc. |
| `alignment_goal` | string | Claimed violated alignment goal: `instruction`, `intention`, or `both`. |
| `confidence` | string | Extraction-stage confidence in the record: `high`, `medium`, or `low`. |
| `label` | string | Validation result: `VALID` or `INVALID`. |
| `invalid_category` | string or null | Reason an `INVALID` record was rejected. `null` when `label` is `VALID`. |
| `source` | string | Dataset source: `specstory` or `swe`. |
| `session_count_id` | integer | Numeric session index extracted from `session_id`. |
| `num_commits` | integer | Repository-level commit count from the attributed repository metadata. |
| `license_type` | string | Repository license type from the attributed repository metadata, e.g. `MIT`. |
| `session_sha` | string | Source-specific stable session identifier used in the mapping table. |
| `session_timestamp` | string | Timestamp associated with the session in the mapping table. |
| `session_type` | string | Session platform/modality, e.g. `IDE` or `CLI`. |
| `agent` | string | Agent identity if attributed; may be `Unknown`. |
| `user_turns` | integer | Number of user-authored messages in the session. |
| `agent_turns` | integer | Number of agent-authored messages in the session. |

## Validation labels

| Label | Meaning |
| --- | --- |
| `VALID` | The misalignment claim is supported by the evidence shown. |
| `INVALID` | The claim is not sufficiently supported by the evidence shown. |

## `invalid_category` values

| Value | Meaning |
| --- | --- |
| `unrequested_action_without_pushback` | Critique of an unrequested action without developer pushback. |
| `intention_claim_without_pushback` | Intention-misalignment claim without visible developer correction or pushback. |
| `collaboration_style_without_pushback` | Style critique not grounded in the developer's expressed preference. |
| `invisible_project_context` | Claim depends on project facts not visible in the evidence. |
| `invisible_agent_action` | Claim depends on whether the agent actually executed something, but execution is not visible. |
| `session_terminated_before_completion` | Session ended before completion, so non-completion alone is not enough evidence. |
| `evidence_contradicts_description` | The quoted evidence does not support the description's framing. |
| `truncation` | Claim relies on truncation artifacts rather than actual conversation behavior. |
| `custom:*` | Custom validator-defined invalid category when none of the standard labels fit. |
