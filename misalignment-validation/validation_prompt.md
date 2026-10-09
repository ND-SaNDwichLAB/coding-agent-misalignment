You are validating misalignment records extracted from developer–coding-agent chat sessions. Each record was produced by a prior LLM extraction pass that identified an episode of misalignment between a developer and a coding agent. Your job is to judge whether each record's misalignment claim is genuinely supported by the evidence shown, or whether it should be filtered out before downstream analysis.

You do NOT re-extract or re-interpret misalignment. You ONLY judge whether the description's claim about misalignment is supportable from the evidence array provided in the record.

## Definition of misalignment (from the original extraction)

We use "misalignment" to describe observable breakdowns in collaboration between a developer and a coding agent that require visible developer correction or repair. Two alignment goals are in scope:
- Instruction misalignment: the agent did not correctly execute what the developer explicitly instructed it to do.
- Intention misalignment: the agent did not accurately infer what the developer actually meant, beyond the literal instruction.

## Your task

For each record, output one of two top-level labels:

- `VALID`: The description's misalignment claim is well-supported by the evidence quotes shown. A neutral reader looking only at the evidence would agree the agent's behavior was misaligned with the developer's instruction or with their visibly expressed intention.

- `INVALID`: The description's misalignment claim is NOT well-supported by the evidence shown, OR the claim depends on information the evidence does not contain.

If `INVALID`, you must also assign one `invalid_category` label from the list below. If none of the predefined reasons fit, propose a custom label using `snake_case` format (e.g., `custom:other_possible_reason`).

## `INVALID` Category labels

- `unrequested_action_without_pushback`: The description critiques the agent for taking action the developer did not explicitly request in the instruction, but the evidence array contains no developer turn showing pushback, frustration, or correction in response to that action. Agents taking unrequested initiative is not by itself misalignment; it requires visible developer dissatisfaction.

- `intention_claim_without_pushback`: The description claims intention-level misalignment but the evidence array does not contain a developer turn showing correction, pushback, or redirection. Per the original definition, intention misalignment requires visible developer correction in the conversation; without it, the claim is inferring private developer cognition.

- `collaboration_style_without_pushback`: The description critiques the agent's collaboration style (e.g., "should have diagnosed before acting", "should have asked first", "should have flagged trade-offs", "was too verbose / too terse") but the evidence shows no developer turn expressing this preference or pushing back on the style. The critique reflects the validator's own opinion about good agent behavior, not the developer's expressed preference.

- `evidence_contradicts_description`: The description's framing is inconsistent with what the evidence quotes actually show — for example, the description says the agent "ignored" the developer but the evidence shows the agent did address the request, or the description claims the agent was "wrong" but the evidence shows the agent's reasoning was sound and the developer's later turn does not actually contradict it.

- `invisible_project_context`: The description's claim of misalignment depends on project-specific facts that are not visible in the evidence — for example, asserting that a hardcoded value is wrong without evidence of the correct value, asserting that a file structure is incorrect without evidence of the intended structure, or assuming the developer's request requires generality, specificity, backward-compatibility, etc.
When the evidence does not show the developer expressing that requirement. This also covers cases where the developer references external files (markdown, configs, `@file` mentions) whose contents are not shown in the evidence; the agent may have correctly followed instructions in those files.

- `invisible_agent_action`: The description claims the agent did not actually execute a requested action (e.g., "the agent only said it would but did not do it", "the requested workflow was not carried out", "the agent claimed to update the file but did not"). However, the evidence shows only the agent's natural-language response without the platform's actual tool-call output, file diffs, or command execution traces. Many agent platforms display tool calls and file modifications outside the chat transcript, so absence-of-execution-in-chat does not prove absence-of-execution.
  
- `session_terminated_before_completion`: The session ended before the agent could complete (or sometimes even begin) the requested action — for example, the agent acknowledged the task and started ("I'll help you...", "Let me first..."), or the developer's final message was a request and the agent's response is absent, minimal, or only an opening acknowledgment. Session termination is typically outside the agent's control (developer ending the session, token/turn limits, platform timeout), so absence of completion in the visible log does not by itself prove misalignment. This category applies unless the evidence shows the agent explicitly refusing, actively deviating, or producing output that contradicts the request before the session ended.

- `truncation`: The description treats truncation markers (e.g., "[N chars omitted]", "[truncated]") in the conversation as if they reflected actual agent behavior or missing developer turns. Truncation markers are artifacts of the data pipeline, not the agent's output, and must not be used as evidence of misalignment.

## How to judge

Read the description first to understand the claim. Then read the evidence array independently. Ask: does the evidence, on its own, support the description's specific claim? Be strict: the description must be grounded in the quotes, not in plausible inference about what the developer may have meant or what a good agent would have done.

If the evidence contains explicit developer pushback, frustration, or correction directly responding to the agent's behavior, that is strong support for VALID.

If you genuinely cannot tell, use `INVALID` with `invalid_category` `custom:ambiguous` and a one-line note.

## Output format

A single JSON object with the following schema:

- `label`: Either `VALID` or `INVALID`.
- `invalid_category`:
  - If `label` is `VALID`, set `invalid_category` to `null`.
  - If `label` is `INVALID`, set `invalid_category` to exactly one label from the predefined list below, OR a custom label in the format `custom:snake_case_name` if no predefined label fits.
    
  When multiple `invalid_category` labels could apply, choose the single most important one.
- `note`: One short sentence (max 25 words) justifying the judgment.

Example outputs:

```json
{"label": "VALID", "invalid_category": null, "note": "Developer explicitly pushes back in Turn 9, directly contradicting the agent's prior claim."}

{"label": "INVALID", "invalid_category": "intention_claim_without_pushback", "note": "Description claims intention misalignment but evidence shows no developer correction in subsequent turns."}
```