# Coding Agent Misalignment

Replication package for the paper "How Coding Agents Fail Their Users: A Large-Scale Analysis of Developer-Agent Misalignment in 20,574 Real-World Sessions", accepted at the 2026 Conference on Empirical Methods in Natural Language Processing (EMNLP 2026). Read the full paper on [arXiv](https://arxiv.org/abs/2605.29442).

**Interactive viewer.** We provide an interactive viewer for the identified misalignment cases, as well as the annotation labels, available at [Coding Agent Misalignment Atlas](https://coding-agent-misalignment.netlify.app/). The viewer includes only cases from permissively licensed repositories, with all personally identifiable information removed.

**Data release.** Due to copyright considerations, raw chat traces are not redistributed; only episodes from repositories whose licenses explicitly permit redistribution (e.g., MIT, Apache-2.0) are released in [`misalignments.json`](misalignments.json), while those from non-permissively licensed repositories are used only in aggregate analysis. To support replication of the original trace collection, we provide the SpecStory scraper as a Git submodule in [`specstory-scraper/`](specstory-scraper/), sourced from [`TTangNingzhi/vibe-coding-scraper`](https://github.com/TTangNingzhi/vibe-coding-scraper). SWE-chat sessions can be downloaded from their [original release](https://huggingface.co/datasets/SALT-NLP/SWE-chat).

**Reproducing results.** To ensure the full reproducibility of our main aggregate findings, we release the validation and annotation labels for the complete dataset, along with all session metadata, in [`data/core/`](data/core). Raw quotes, descriptions, and reasoning traces are omitted due to licensing considerations and are not needed to reproduce any of the reported aggregate results. **This release is sufficient to reproduce all figures, tables, and key quantitative results in the paper by running the notebooks in [`distribution-analysis/`](distribution-analysis).** Every notebook consumes data only from `data/core/` and is runnable end-to-end once the environment is set up from `requirements.txt`.

## Modules

- [session-formatting/](session-formatting): preprocessing step. Formats parsed sessions into LLM-ready text files for extraction.
- [batch-runner/](batch-runner): reusable OpenAI Batch toolkit (build, submit, check, download, retry, postprocess).
- [misalignment-extraction/](misalignment-extraction): extracts candidate misalignment episodes from formatted sessions.
- [misalignment-validation/](misalignment-validation): validates extracted episodes and filters unsupported cases.
- [misalignment-annotation/](misalignment-annotation): multi-axial annotation of validated episodes.
- [data-aggregation/](data-aggregation): aggregates intermediate outputs into downstream analysis tables.
- [data/core](data/core): core intermediate data for reproducing the results, including all validation and annotation labels in `validated_misalignments.json` and `annotated_misalignments.json`, as well as all session metadata in `session_mapping.json`. Each file is accompanied by a data-spec document describing its structure and contents.
- [distribution-analysis/](distribution-analysis): notebooks and utilities for reproducing the paper’s figures and tables and generating analysis-ready outputs. **All notebooks are fully runnable using only the data provided in [`data/core`](data/core).**
- [misalignment-viewer/](misalignment-viewer): static viewer for browsing the misalignment corpus.
- [workspace/](workspace): expected data layout (not distributed here) for repository/session-level inputs.
- [specstory-scraper/](specstory-scraper): Git submodule containing the scraper and parser pipeline used to reproduce the SpecStory trace collection.
- [misalignments.json](misalignments.json): aggregated list of all identified misalignment episodes with metadata and annotations, filtered to include only those from permissively licensed repositories.
- [redact_credentials.py](redact_credentials.py): utility that applies deterministic rules to redact sensitive information, primarily from evidence quotes, in raw misalignment episodes. If anyone identifies additional issues, or would prefer that their data not be included, please contact the repository owners, and we will remove the relevant data promptly.

To include the scraper when cloning this repository, use `git clone --recurse-submodules`. For an existing clone, run `git submodule update --init --recursive`.

## Minimal Pipeline Order

1. Session preprocessing: [session-formatting/](session-formatting)
2. Extraction: [misalignment-extraction/](misalignment-extraction)
3. Validation: [misalignment-validation/](misalignment-validation)
4. Annotation: [misalignment-annotation/](misalignment-annotation)
5. Aggregation: [data-aggregation/](data-aggregation)
6. Distribution analysis: [distribution-analysis/](distribution-analysis)
7. Misalignment viewer: [misalignment-viewer/](misalignment-viewer)

## Data Layout (Expected)

Typical structure under [workspace/](workspace):

```
workspace/
└── {repo_id}/
    ├── session_parsed/    # Per-session parsed chat records
    │   ├── session_001.json
    │   └── ...
    ├── session_formatted/ # Per-session formatted chat records for LLM analysis
    │   ├── session_001.txt
    │   └── ...
    └── meta.json          # Repository metadata (e.g., name, language, session count)
```

## Citation

```
@inproceedings{tang2026coding,
  title={How Coding Agents Fail Their Users: A Large-Scale Analysis of Developer-Agent Misalignment in 20,574 Real-World Sessions},
  author={Tang, Ningzhi and Chen, Chaoran and Xu, Gelei and Shi, Yiyu and Huang, Yu and McMillan, Collin and Dong, Tao and Li, Toby Jia-Jun},
  booktitle={Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing},
  year={2026}
}
```

## Acknowledgments

This research was supported in part by a Google Cloud Research Credit Award, a Google Research Scholar Award, a gift from Adobe, an Edison Innovation Fellowship from the Notre Dame IDEA Center, and NSF grants CCF-2211428, CCF-2315887, CCF-2100035, CCF-2211429, CCF-2442682, IIS-2544037, and DGE-2622415. Any opinions, findings, or recommendations expressed here are those of the authors and do not necessarily reflect the views of the sponsors.