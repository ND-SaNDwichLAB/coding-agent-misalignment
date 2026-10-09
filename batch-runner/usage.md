# Batch Runner

`batch-runner/` is a reusable workflow for OpenAI Batch API jobs where:

- each source file becomes one request
- requests are sharded into many small batch input files
- raw batch output is downloaded first
- postprocessing is a separate step

It is meant to be reusable across different folders in this repository.

## Required Per-Task Files

Each task should provide its own config file, and usually:

- a prompt file
- an input source, usually an input file glob
- a batch output directory
- optionally, a structured response schema
- optionally, `temperature`
- optionally, `reasoning_effort`
- optionally, a `price` block for local cost estimation

## Config

Schema-based example:

```json
{
  "prompt_path": "prompt.md",
  "batch_dir": "batch",
  "input_glob": "data/*.txt",
  "endpoint": "/v1/chat/completions",
  "model": "gpt-5.4",
  "response_format_path": "response_format.json",
  "temperature": 0,
  "price": {
    "input": 1.25,
    "cached_input": 0.125,
    "output": 7.50
  }
}
```

All config paths are resolved relative to the config file.

By default, `build.py` uses `input_glob` and turns each matched file into one request.
You can also set `input_mode` to `json_records` and provide `input_path`; in that mode,
the input file must be a JSON array and each array item becomes one request.

JSON-record example:

```json
{
  "prompt_path": "prompt.md",
  "batch_dir": "batch",
  "input_mode": "json_records",
  "input_path": "data/records.json",
  "endpoint": "/v1/chat/completions",
  "model": "gpt-5.4"
}
```

## Commands

Replace `path/to/task_config.json` with your task config.

Build batch input files:

```bash
.venv/bin/python batch-runner/build.py --config path/to/task_config.json --requests-per-batch 100
```

Submit only a few shards first:

```bash
.venv/bin/python batch-runner/submit.py --config path/to/task_config.json --limit 3
```

Submit specific shards:

```bash
.venv/bin/python batch-runner/submit.py --config path/to/task_config.json batch_001 batch_002
```

Submit a range of shards:

```bash
.venv/bin/python batch-runner/submit.py --config path/to/task_config.json 2-100
```

Refresh status:

```bash
.venv/bin/python batch-runner/check.py --config path/to/task_config.json
```

Cancel specific shards and remove them from `state.json` so they can be submitted again:

```bash
.venv/bin/python batch-runner/cancel.py --config path/to/task_config.json batch_014 batch_021
```

Cancel specific shards but keep them in `state.json` so you can continue checking and downloading partial results:

```bash
.venv/bin/python batch-runner/cancel.py --config path/to/task_config.json --keep-state batch_014 batch_021
```

Cancel a range of shards:

```bash
.venv/bin/python batch-runner/cancel.py --config path/to/task_config.json 14-21
```

If you only want to forget the local submission record without calling the Batch API:

```bash
.venv/bin/python batch-runner/cancel.py --config path/to/task_config.json --local-only batch_014
```

Download raw output files:

```bash
.venv/bin/python batch-runner/download.py --config path/to/task_config.json
```

Estimate spend from downloaded raw outputs:

```bash
.venv/bin/python batch-runner/cost.py --config path/to/task_config.json
```

`cost.py` reads `price.input`, `price.cached_input`, and `price.output` from the task config.

Postprocess raw output into one output file per source item:

```bash
.venv/bin/python batch-runner/postprocess.py --config path/to/task_config.json
```

Build a single retry batch from all submitted batches by selecting requests that are not already in `outputs/` (i.e. `input - processed`) without submitting it yet:

```bash
.venv/bin/python batch-runner/retry.py --config path/to/task_config.json
```

Build a retry batch only from some selected shards:

```bash
.venv/bin/python batch-runner/retry.py --config path/to/task_config.json batch_001 batch_004 7-9
```

Build and immediately submit that single retry batch:

```bash
.venv/bin/python batch-runner/retry.py --config path/to/task_config.json --retry-name retry_all --submit
```

## Output Layout

The configured `batch_dir` will contain:

- `inputs/`
- `manifests/`
- `manifest.jsonl`
- `outputs/`
- `errors/`
- `results/`
- `state.json`

Retry bundles are written under:

- `inputs/<retry_name>.jsonl`
- `manifests/<retry_name>.jsonl`
- `retries/<retry_name>.summary.json`

After that, the retry batch behaves like any other batch name in the normal workflow, so `submit.py`, `check.py`, `download.py`, and `postprocess.py` can all reuse it directly.

## Manifest Files

Both manifest layers are useful:

- `manifests/batch_XXX.jsonl` is convenient for inspecting one shard
- `manifest.jsonl` is a global index for mapping `custom_id` back to source files and output paths

Keeping `manifest.jsonl` makes postprocessing and partial reruns simpler.

## Data Backup

Strongly recommended to keep a backup of the `errors/`, `outputs/`, and `state.json` folders and files in `batch_dir` outside of the local machine, since it contains the only copy of the raw batch output files needed for post-processing and retrying.

```
zip -r batch.zip batch/errors batch/outputs batch/state.json
```