# `annotated_misalignments.json` Data Specification

This file contains the final annotated misalignment records after metadata joining and annotation-field flattening.

## Row unit

One row = one validated misalignment episode with its multi-axial annotation and session metadata.

## Columns

| Column | Type | Description |
| --- | --- | --- |
| `repository_id` | string or integer | Repository identifier used in the source dataset. |
| `session_id` | string | Session key in `session_###` format within a repository/source. |
| `misalignment_id` | string | Misalignment identifier within the session, usually `M001`, `M002`, etc. |
| `alignment_goal` | string | Which alignment goal was violated: `instruction`, `intention`, or `both`. |
| `confidence` | string | Extraction-stage confidence in the record: `high`, `medium`, or `low`. |
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
| `S1` | boolean | `True` if the symptom includes **Wrong Project Diagnosis**. |
| `S2` | boolean | `True` if the symptom includes **Misread Developer Intent**. |
| `S3` | boolean | `True` if the symptom includes **Developer Constraint Violation**. |
| `S4` | boolean | `True` if the symptom includes **Self-Initiated Overreach**. |
| `S5` | boolean | `True` if the symptom includes **Faulty Implementation**. |
| `S6` | boolean | `True` if the symptom includes **Operational Execution Error**. |
| `S7` | boolean | `True` if the symptom includes **Inaccurate Self-Reporting**. |
| `S8` | boolean | `True` if the symptom includes **Other / Emerging**. |
| `symptom_other_descriptor` | string or null | Short free-text descriptor used only when `S8` is `True`. |
| `C1` | string or null | Evidence tier for **Underspecified Instruction** if assigned: `direct`, `contextual`, or `speculative`. Otherwise `null`. |
| `C2` | string or null | Evidence tier for **Scope Overreach** if assigned. Otherwise `null`. |
| `C3` | string or null | Evidence tier for **Premature Action** if assigned. Otherwise `null`. |
| `C4` | string or null | Evidence tier for **Context Loss** if assigned. Otherwise `null`. |
| `C5` | string or null | Evidence tier for **Default-Driven Override** if assigned. Otherwise `null`. |
| `C6` | string or null | Evidence tier for **Instruction-Following Failure** if assigned. Otherwise `null`. |
| `C7` | string or null | Present when the cause is **Cannot Determine**. In practice this is typically `not_applicable`. |
| `damage_severity` | string | Outcome severity: `DS0`, `DS1`, `DS2`, `DS3`, or `DS4`. |
| `damage_locus` | string or null | Damage locus when severity is `DS2` or `DS3`: `DL1`, `DL2`, `DL3`, or `DL4`. Otherwise `null`. |
| `resolution_status` | string | Annotation-stage resolution status: `RS1` or `RS2`. |
| `resolver` | string or null | Resolver label when `resolution_status` is `RS1`: `RV1`, `RV2`, or `RV3`. Otherwise `null`. |

## Label glosses

### Symptom labels

| Label | Meaning |
| --- | --- |
| `S1` | Wrong Project Diagnosis |
| `S2` | Misread Developer Intent |
| `S3` | Developer Constraint Violation |
| `S4` | Self-Initiated Overreach |
| `S5` | Faulty Implementation |
| `S6` | Operational Execution Error |
| `S7` | Inaccurate Self-Reporting |
| `S8` | Other / Emerging |

### Cause labels

| Label | Meaning |
| --- | --- |
| `C1` | Underspecified Instruction |
| `C2` | Scope Overreach |
| `C3` | Premature Action |
| `C4` | Context Loss |
| `C5` | Default-Driven Override |
| `C6` | Instruction-Following Failure |
| `C7` | Cannot Determine |

### Outcome labels

| Label | Meaning |
| --- | --- |
| `DS0` | No damage |
| `DS1` | Effort/trust cost only |
| `DS2` | System damage, easily reversed |
| `DS3` | System damage, hard to reverse |
| `DS4` | Unobservable |
| `DL1` | Code/task state |
| `DL2` | Project state |
| `DL3` | Environment/configuration |
| `DL4` | External state |

### Resolution labels

| Label | Meaning |
| --- | --- |
| `RS1` | Resolved |
| `RS2` | Unknown |
| `RV1` | Agent self-corrected |
| `RV2` | Agent after pushback |
| `RV3` | Developer took over |
