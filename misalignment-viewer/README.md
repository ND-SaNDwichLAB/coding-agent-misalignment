# Misalignment Viewer

Static viewer for browsing examples from the coding-agent misalignment corpus.

This directory is a frozen snapshot of the interface used for the paper artifact. It consumes a prebuilt static data bundle rather than rebuilding data from the repository's released analysis files.

The deployed bundle contains:

- `data-licensed/index.json`: summary statistics, filter options, and lightweight per-record metadata used for search, filtering, and pagination
- `data-licensed/chunks/*.json`: full record payloads loaded lazily for the visible page
- `prompts/*.md`: viewer-local copies of the extraction, validation, and annotation prompts

The public episode-level release is available in the repository root as `misalignments.json`. Full-dataset validation labels, annotation labels, and session metadata used to reproduce the paper's aggregate analyses are available under `data/core/`.

## Run locally

Option 1, from the repository root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/misalignment-viewer/
```

Option 2, from inside `misalignment-viewer/`:

```bash
cd misalignment-viewer
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/
```

## Notes

- The UI is plain `html/css/js` with no framework.
- Pagination is client-side at `50` records per page, while full record details and long-form reasoning fields are fetched lazily from chunk files.
- The default view shows `VALID` records only.
- Search currently matches normalized record titles (`name`) only.
- `Invalid Category` is only shown when `Validation = INVALID`.
- Annotation filters (`Symptom`, `Cause`, `Evidence Tier`, `Damage Severity`, `Damage Locus`, `Resolution`, `Resolver`) are only shown for `VALID` records.
- Choosing an annotation filter forces `Validation = VALID`; choosing an invalid category forces `Validation = INVALID`.
- The `Agent` filter options are dynamically narrowed by the selected `Platform`.
- Do not open `index.html` via `file://...`; use a local HTTP server so `fetch("./data/index.json")` works.
