const INDEX_URL = "./data/index.json";
const FALLBACK_INDEX_URL = "./data-licensed/index.json";
const CHUNKS_URL = "./data/chunks";
const FALLBACK_CHUNKS_URL = "./data-licensed/chunks";
const PAGE_SIZE = 50;
const SEARCH_DEBOUNCE_MS = 180;

const FILTER_DEFINITIONS = [
  {
    key: "dataset",
    element: "datasetFilter",
    recordKey: "dataset_label",
    optionKey: "dataset_label",
    label: "Dataset",
    formatValue: identity,
    row: "primary",
  },
  {
    key: "validation",
    element: "validationFilter",
    recordKey: "validation_label",
    optionKey: "validation_label",
    label: "Validation",
    formatValue: humanizeValidationLabel,
    row: "primary",
  },
  {
    key: "invalidCategory",
    element: "invalidCategoryFilter",
    recordKey: "invalid_category",
    optionKey: "invalid_category",
    label: "Invalid Category",
    formatValue: humanizeCategory,
    row: "primary",
  },
  {
    key: "platform",
    element: "platformFilter",
    recordKey: "platform",
    optionKey: "platform",
    label: "Platform",
    formatValue: identity,
    row: "primary",
  },
  {
    key: "agent",
    element: "agentFilter",
    recordKey: "agent",
    optionKey: "agent",
    label: "Agent",
    formatValue: identity,
    row: "primary",
  },
  {
    key: "goal",
    element: "goalFilter",
    recordKey: "alignment_goal",
    optionKey: "alignment_goal",
    label: "Goal",
    formatValue: humanize,
    row: "primary",
  },
  {
    key: "symptomLabel",
    element: "symptomFilter",
    recordKey: "symptom_labels",
    optionKey: "symptom_labels",
    label: "Symptom",
    isArray: true,
    formatValue: formatSymptomLabel,
    row: "annotation",
  },
  {
    key: "causeLabel",
    element: "causeFilter",
    recordKey: "cause_labels",
    optionKey: "cause_labels",
    label: "Cause",
    isArray: true,
    formatValue: formatCauseLabel,
    row: "annotation",
  },
  {
    key: "evidenceTier",
    element: "evidenceTierFilter",
    recordKey: "cause_evidence_tiers",
    optionKey: "cause_evidence_tiers",
    label: "Evidence Tier",
    isArray: true,
    formatValue: humanize,
    row: "annotation",
  },
  {
    key: "damageSeverity",
    element: "damageSeverityFilter",
    recordKey: "outcome_damage_severity",
    optionKey: "outcome_damage_severity",
    label: "Damage Severity",
    formatValue: formatDamageSeverity,
    row: "annotation",
  },
  {
    key: "damageLocus",
    element: "damageLocusFilter",
    recordKey: "outcome_damage_locus",
    optionKey: "outcome_damage_locus",
    label: "Damage Locus",
    formatValue: formatDamageLocus,
    row: "annotation",
  },
  {
    key: "resolutionStatus",
    element: "resolutionFilter",
    recordKey: "resolution_status_code",
    optionKey: "resolution_status_code",
    label: "Resolution",
    formatValue: formatResolutionStatus,
    row: "annotation",
  },
  {
    key: "resolutionResolver",
    element: "resolverFilter",
    recordKey: "resolution_resolver",
    optionKey: "resolution_resolver",
    label: "Resolver",
    formatValue: formatResolutionResolver,
    row: "annotation",
  },
];

const LABEL_METADATA = {
  symptom: {
    S1: "S1. Wrong Project Diagnosis",
    S2: "S2. Misread Developer Intent",
    S3: "S3. Developer Constraint Violation",
    S4: "S4. Self-Initiated Overreach",
    S5: "S5. Faulty Implementation",
    S6: "S6. Operational Execution Error",
    S7: "S7. Inaccurate Self-Reporting",
    S8: "S8. Other / Emerging",
  },
  cause: {
    C1: "C1. Underspecified Instruction",
    C2: "C2. Scope Overreach",
    C3: "C3. Premature Action",
    C4: "C4. Context Loss",
    C5: "C5. Default-Driven Override",
    C6: "C6. Instruction-Following Failure",
    C7: "C7. Cannot Determine",
  },
  damageSeverity: {
    DS0: "DS0. None",
    DS1: "DS1. Effort/trust cost only",
    DS2: "DS2. System damage, easily reversed",
    DS3: "DS3. System damage, hard to reverse",
    DS4: "DS4. Unobservable",
  },
  damageLocus: {
    DL1: "DL1. Code/task state",
    DL2: "DL2. Project state",
    DL3: "DL3. Environment/configuration",
    DL4: "DL4. External state",
  },
  resolutionStatus: {
    RS1: "RS1. Resolved",
    RS2: "RS2. Unknown",
  },
  resolutionResolver: {
    RV1: "RV1. Agent self-corrected",
    RV2: "RV2. Agent after pushback",
    RV3: "RV3. Developer took over",
  },
};

const state = {
  summary: null,
  meta: null,
  indexedRecords: [],
  currentResults: [],
  currentPage: 1,
  pageSize: PAGE_SIZE,
  chunkCache: new Map(),
  pendingRenderToken: 0,
  filters: createDefaultFilters(),
  licensedOnly: false,
  sortMode: "default",
  chunksUrl: CHUNKS_URL,
};

const elements = {
  heroStats: document.querySelector("#hero-stats"),
  licensedOnlyToggle: document.querySelector("#licensed-only-toggle"),
  primaryToolbar: document.querySelector("#primary-toolbar"),
  searchInput: document.querySelector("#search-input"),
  datasetFilter: document.querySelector("#dataset-filter"),
  validationFilter: document.querySelector("#validation-filter"),
  platformFilter: document.querySelector("#platform-filter"),
  agentFilter: document.querySelector("#agent-filter"),
  invalidCategoryFilter: document.querySelector("#invalid-category-filter"),
  invalidCategoryFilterGroup: document.querySelector("#invalid-category-filter-group"),
  annotationToolbar: document.querySelector("#annotation-toolbar"),
  goalFilter: document.querySelector("#goal-filter"),
  symptomFilter: document.querySelector("#symptom-filter"),
  causeFilter: document.querySelector("#cause-filter"),
  evidenceTierFilter: document.querySelector("#evidence-tier-filter"),
  damageSeverityFilter: document.querySelector("#damage-severity-filter"),
  damageLocusFilter: document.querySelector("#damage-locus-filter"),
  resolutionFilter: document.querySelector("#resolution-filter"),
  resolverFilter: document.querySelector("#resolver-filter"),
  sortToggleButton: document.querySelector("#sort-toggle-button"),
  resetButton: document.querySelector("#reset-button"),
  resultSummary: document.querySelector("#result-summary"),
  activeFilters: document.querySelector("#active-filters"),
  paginationSummary: document.querySelector("#pagination-summary"),
  pageJumpForm: document.querySelector("#page-jump-form"),
  pageJumpInput: document.querySelector("#page-jump-input"),
  pagePrevButton: document.querySelector("#page-prev-button"),
  pageNextButton: document.querySelector("#page-next-button"),
  pageTotal: document.querySelector("#page-total"),
  results: document.querySelector("#results"),
  cardTemplate: document.querySelector("#card-template"),
};

let searchDebounceTimer = null;

init().catch((error) => {
  console.error(error);
  elements.results.innerHTML = `
    <div class="empty-state">
      Failed to load <code>${INDEX_URL}</code>. Run the data build script first, then serve this folder with a local HTTP server.
    </div>
  `;
});

async function init() {
  let response = await fetch(INDEX_URL, { cache: "no-store" });
  state.chunksUrl = CHUNKS_URL;
  if (!response.ok) {
    response = await fetch(FALLBACK_INDEX_URL, { cache: "no-store" });
    state.chunksUrl = FALLBACK_CHUNKS_URL;
  }
  if (!response.ok) {
    throw new Error(`Failed to load data index: ${response.status}`);
  }

  const payload = await response.json();
  state.meta = payload.meta ?? null;
  state.summary = payload.summary ?? null;
  state.indexedRecords = payload.records ?? [];
  state.filters = createDefaultFilters(state.meta);

  hydrateFilterOptions(payload.filter_options ?? {});
  bindEvents();
  syncControls();
  refreshHeroStats();
  refreshResults();
}

function createDefaultFilters(meta = null) {
  return {
    search: "",
    dataset: "",
    validation: meta?.default_validation_label ?? "VALID",
    platform: "",
    agent: "",
    invalidCategory: "",
    goal: "",
    symptomLabel: "",
    causeLabel: "",
    evidenceTier: "",
    damageSeverity: "",
    damageLocus: "",
    resolutionStatus: "",
    resolutionResolver: "",
  };
}

function bindEvents() {
  elements.licensedOnlyToggle.addEventListener("click", () => {
    state.licensedOnly = !state.licensedOnly;
    state.currentPage = 1;
    syncControls();
    refreshHeroStats();
    refreshResults();
  });

  elements.searchInput.addEventListener("input", (event) => {
    window.clearTimeout(searchDebounceTimer);
    searchDebounceTimer = window.setTimeout(() => {
      state.filters.search = event.target.value.trim();
      state.currentPage = 1;
      refreshResults();
    }, SEARCH_DEBOUNCE_MS);
  });

  for (const definition of FILTER_DEFINITIONS) {
    const element = elements[definition.element];
    if (!element) continue;
    element.addEventListener("change", (event) => {
      state.filters[definition.key] = event.target.value;

      if (definition.key === "platform") {
        syncAgentOptions();
      }

      if (definition.key === "validation" && state.filters.validation !== "INVALID") {
        state.filters.invalidCategory = "";
      }

      if (definition.key === "invalidCategory" && state.filters.invalidCategory) {
        state.filters.validation = "INVALID";
      }

      if (definition.row === "annotation" && state.filters.validation !== "VALID") {
        state.filters.validation = "VALID";
      }

      if (state.filters.validation !== "VALID") {
        clearAnnotationFilters();
      }

      state.currentPage = 1;
      syncControls();
      refreshResults();
    });
  }

  elements.resetButton.addEventListener("click", () => {
    state.filters = createDefaultFilters(state.meta);
    state.sortMode = "default";
    state.currentPage = 1;
    syncControls();
    refreshResults();
  });

  elements.sortToggleButton.addEventListener("click", () => {
    state.sortMode = state.sortMode === "random" ? "default" : "random";
    state.currentPage = 1;
    syncControls();
    refreshResults();
  });

  elements.pageJumpForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const totalPages = Math.max(1, Math.ceil(state.currentResults.length / state.pageSize));
    const requestedPage = Number(elements.pageJumpInput.value);
    if (!Number.isFinite(requestedPage)) return;

    state.currentPage = clampPage(requestedPage, totalPages);
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  elements.pagePrevButton.addEventListener("click", () => {
    const totalPages = Math.max(1, Math.ceil(state.currentResults.length / state.pageSize));
    state.currentPage = clampPage(state.currentPage - 1, totalPages);
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  elements.pageNextButton.addEventListener("click", () => {
    const totalPages = Math.max(1, Math.ceil(state.currentResults.length / state.pageSize));
    state.currentPage = clampPage(state.currentPage + 1, totalPages);
    render();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

function refreshResults() {
  const normalizedSearch = normalizeSearchText(state.filters.search);

  state.currentResults = sortRecords(
    state.indexedRecords.filter((record) => {
      if (state.licensedOnly && !recordHasUsableLicense(record)) {
        return false;
      }

      if (normalizedSearch && !normalizeSearchText(record.name || "").includes(normalizedSearch)) {
        return false;
      }

      for (const definition of FILTER_DEFINITIONS) {
        if (definition.row === "annotation" && state.filters.validation !== "VALID") {
          continue;
        }

        const selectedValue = state.filters[definition.key];
        if (!selectedValue) continue;

        const recordValue = record[definition.recordKey];
        if (definition.isArray) {
          if (!Array.isArray(recordValue) || !recordValue.includes(selectedValue)) {
            return false;
          }
          continue;
        }

        if (recordValue !== selectedValue) {
          return false;
        }
      }

      return true;
    }),
  );

  render();
}

function hydrateFilterOptions(filterOptions) {
  for (const definition of FILTER_DEFINITIONS) {
    const element = elements[definition.element];
    if (!element) continue;
    setOptions(element, filterOptions[definition.optionKey] ?? [], definition.formatValue);
  }
  syncAgentOptions();
  syncToolbarState();
}

function setOptions(select, values, labeler) {
  const firstOption = select.querySelector("option");
  select.innerHTML = "";
  if (firstOption) {
    select.append(firstOption);
  }

  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labeler(value);
    select.append(option);
  }
}

function syncAgentOptions() {
  const definition = FILTER_DEFINITIONS.find((item) => item.key === "agent");
  const select = elements.agentFilter;
  if (!definition || !select) return;

  const values = getAgentOptionsForPlatform(state.filters.platform);
  setOptions(select, values, definition.formatValue);

  if (state.filters.agent && !values.includes(state.filters.agent)) {
    state.filters.agent = "";
  }

  select.value = state.filters.agent;
}

function getAgentOptionsForPlatform(platform) {
  const normalizedPlatform = String(platform || "").trim();
  const records = normalizedPlatform
    ? state.indexedRecords.filter((record) => record.platform === normalizedPlatform)
    : state.indexedRecords;

  return [...new Set(records.map((record) => record.agent).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b),
  );
}

function identity(value) {
  return value;
}

function humanize(value) {
  return String(value)
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function normalizeSearchText(value) {
  return String(value)
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, " ")
    .trim()
    .replaceAll(/\s+/g, " ");
}

function humanizeCategory(value) {
  if (!value) return "";
  if (value.startsWith("custom:")) {
    return `Custom: ${humanize(value.slice("custom:".length))}`;
  }
  return humanize(value);
}

function humanizeValidationLabel(value) {
  if (!value) return "All";
  return value.charAt(0) + value.slice(1).toLowerCase();
}

function formatSymptomLabel(value) {
  return LABEL_METADATA.symptom[value] ?? value;
}

function formatCauseLabel(value) {
  return LABEL_METADATA.cause[value] ?? value;
}

function formatDamageSeverity(value) {
  return LABEL_METADATA.damageSeverity[value] ?? value;
}

function formatDamageLocus(value) {
  return LABEL_METADATA.damageLocus[value] ?? value;
}

function formatResolutionStatus(value) {
  return LABEL_METADATA.resolutionStatus[value] ?? value;
}

function formatResolutionResolver(value) {
  return LABEL_METADATA.resolutionResolver[value] ?? value;
}

function formatCount(value, noun) {
  return `${value.toLocaleString()} ${noun}${value === 1 ? "" : "s"}`;
}

function formatStatValue(value) {
  return typeof value === "number" ? value.toLocaleString() : String(value);
}

function refreshHeroStats() {
  const heroRecords = state.licensedOnly
    ? state.indexedRecords.filter((record) => recordHasUsableLicense(record))
    : state.indexedRecords;

  renderHeroStats(state.summary, heroRecords, state.meta, {
    licensedOnly: state.licensedOnly,
    dynamicRepositories: false,
    dynamicSessions: false,
    dynamicMisalignments: state.licensedOnly,
    dynamicValidMisalignments: state.licensedOnly,
  });
}

function renderHeroStats(summary, records, meta, options = {}) {
  const breakdown = buildDatasetBreakdown(records, meta);
  const totalBreakdown = buildDatasetTotalBreakdown(summary, meta, options.licensedOnly);
  const totalRepositories =
    options.dynamicRepositories
      ? countUnique(records, (record) => `${record.dataset_key}/${record.repo_id}`)
      : options.licensedOnly
        ? summary?.licensed_repositories ??
        countUnique(records, (record) => `${record.dataset_key}/${record.repo_id}`)
        : summary?.repositories ??
        countUnique(records, (record) => `${record.dataset_key}/${record.repo_id}`);
  const totalSessions =
    options.dynamicSessions
      ? countUnique(records, (record) => record.session_key)
      : options.licensedOnly
        ? summary?.licensed_sessions ?? countUnique(records, (record) => record.session_key)
        : summary?.sessions ?? countUnique(records, (record) => record.session_key);
  const totalMisalignments = options.dynamicMisalignments
    ? records.length
    : summary?.misalignments ?? records.length;
  const totalValidMisalignments = options.dynamicValidMisalignments
    ? records.filter((record) => record.validation_label === "VALID").length
    : summary?.validated_misalignments ?? meta?.validation_label_counts?.VALID ?? 0;
  const cards = [
    [
      "Repositories",
      totalRepositories,
      formatBreakdown(totalBreakdown.repositories ?? breakdown.repositories),
    ],
    [
      "Sessions",
      totalSessions,
      formatBreakdown(totalBreakdown.sessions ?? breakdown.sessions),
    ],
    [
      "Misalignments",
      totalMisalignments,
      formatBreakdown(breakdown.misalignments),
    ],
    [
      "Valid misalignments",
      totalValidMisalignments,
      formatBreakdown(breakdown.validMisalignments),
    ],
  ];

  elements.heroStats.innerHTML = cards
    .map(
      ([label, value, detail]) => `
        <div class="stat-card">
          <strong>${formatStatValue(value)}</strong>
          <small>${detail}</small>
          <span>${label}</span>
        </div>
      `,
    )
    .join("");
}

function buildDatasetTotalBreakdown(summary, meta, licensedOnly = false) {
  if (!summary) {
    return {};
  }

  const datasetOrder = getDatasetOrder(meta);
  return {
    repositories: mapCountsFromSummary(
      licensedOnly ? summary.repositories_by_dataset_licensed_total : summary.repositories_by_dataset_total,
      datasetOrder,
      meta,
    ),
    sessions: mapCountsFromSummary(
      licensedOnly ? summary.sessions_by_dataset_licensed_total : summary.sessions_by_dataset_total,
      datasetOrder,
      meta,
    ),
  };
}

function mapCountsFromSummary(countsByDatasetKey, datasetOrder, meta) {
  if (!countsByDatasetKey || !meta?.dataset_labels) {
    return null;
  }

  const countsByLabel = new Map();
  for (const [datasetKey, count] of Object.entries(countsByDatasetKey)) {
    const label = meta.dataset_labels[datasetKey];
    if (!label) continue;
    countsByLabel.set(label, Number(count) || 0);
  }

  return datasetOrder.map((label) => countsByLabel.get(label) ?? 0);
}

function buildDatasetBreakdown(records, meta) {
  const datasetOrder = getDatasetOrder(meta);
  const repositories = new Map(datasetOrder.map((label) => [label, new Set()]));
  const sessions = new Map(datasetOrder.map((label) => [label, new Set()]));
  const misalignments = new Map(datasetOrder.map((label) => [label, 0]));
  const validMisalignments = new Map(datasetOrder.map((label) => [label, 0]));

  for (const record of records) {
    const label = record.dataset_label;
    if (!repositories.has(label)) {
      repositories.set(label, new Set());
      sessions.set(label, new Set());
      misalignments.set(label, 0);
      validMisalignments.set(label, 0);
    }

    repositories.get(label).add(record.repo_id);
    sessions.get(label).add(record.session_key);
    misalignments.set(label, (misalignments.get(label) ?? 0) + 1);
    if (record.validation_label === "VALID") {
      validMisalignments.set(label, (validMisalignments.get(label) ?? 0) + 1);
    }
  }

  return {
    repositories: datasetOrder.map((label) => repositories.get(label)?.size ?? 0),
    sessions: datasetOrder.map((label) => sessions.get(label)?.size ?? 0),
    misalignments: datasetOrder.map((label) => misalignments.get(label) ?? 0),
    validMisalignments: datasetOrder.map((label) => validMisalignments.get(label) ?? 0),
  };
}

function getDatasetOrder(meta) {
  const labels = Object.values(meta?.dataset_labels ?? {});
  const preferred = ["SpecStory-chat", "SWE-chat"];
  const ordered = preferred.filter((label) => labels.includes(label));
  for (const label of labels) {
    if (!ordered.includes(label)) {
      ordered.push(label);
    }
  }
  return ordered;
}

function countUnique(records, selector) {
  return new Set(records.map(selector)).size;
}

function formatBreakdown(counts) {
  return counts.map((count) => count.toLocaleString()).join(" + ");
}

function recordHasUsableLicense(record) {
  const license = String(record.license || "").trim().toUpperCase();
  return Boolean(license) && license !== "NO_LICENSE" && license !== "NOASSERTION";
}

async function render() {
  const renderToken = ++state.pendingRenderToken;
  const totalPages = Math.max(1, Math.ceil(state.currentResults.length / state.pageSize));
  state.currentPage = Math.min(state.currentPage, totalPages);

  renderSummary(state.currentResults, totalPages);
  syncToolbarState();
  renderActiveFilters();
  syncPaginationControls(totalPages);

  if (!state.currentResults.length) {
    elements.results.innerHTML = `
      <div class="empty-state">
        No records match the current filters. Try clearing one or two constraints.
      </div>
    `;
    return;
  }

  elements.results.innerHTML = `
    <div class="empty-state">
      Loading page ${state.currentPage}...
    </div>
  `;

  const pageRecords = getPageRecords(state.currentResults, state.currentPage, state.pageSize);
  const details = await loadPageDetails(pageRecords);

  if (renderToken !== state.pendingRenderToken) return;
  renderResults(details);
}

function sortRecords(records) {
  const sorted = [...records];
  sorted.sort((a, b) => {
    return (
      compareText(a.dataset_label, b.dataset_label) ||
      compareText(a.repo_id, b.repo_id) ||
      compareText(a.session_id, b.session_id) ||
      compareText(a.id, b.id) ||
      compareText(a.record_key, b.record_key)
    );
  });

  if (state.sortMode === "random") {
    return shuffleRecords(sorted);
  }

  return sorted;
}

function compareText(a = "", b = "") {
  return a.localeCompare(b, undefined, { numeric: true });
}

function shuffleRecords(records) {
  const shuffled = [...records];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
  }
  return shuffled;
}

function renderSummary(records, totalPages) {
  const pageStart = records.length ? (state.currentPage - 1) * state.pageSize + 1 : 0;
  const pageEnd = Math.min(state.currentPage * state.pageSize, records.length);

  elements.resultSummary.textContent = formatCount(records.length, "record");
  elements.paginationSummary.textContent = records.length
    ? `Page ${state.currentPage} of ${totalPages} · showing ${pageStart}-${pageEnd}`
    : "Page 0 of 0";

  elements.pageJumpInput.min = records.length ? "1" : "0";
  elements.pageJumpInput.max = String(totalPages);
  elements.pageJumpInput.value = records.length ? String(state.currentPage) : "";
}

function renderActiveFilters() {
  const chips = [];
  if (state.filters.search) chips.push(["Search", state.filters.search, "search"]);

  for (const definition of FILTER_DEFINITIONS) {
    if (definition.row === "annotation" && state.filters.validation !== "VALID") {
      continue;
    }
    const value = state.filters[definition.key];
    if (!value) continue;
    chips.push([definition.label, definition.formatValue(value), definition.key]);
  }

  elements.activeFilters.innerHTML = chips
    .map(
      ([label, value, key]) => `
        <span class="chip">
          ${label}: ${value}
          <button type="button" data-filter-key="${key}" aria-label="Clear ${label} filter">x</button>
        </span>
      `,
    )
    .join("");

  for (const button of elements.activeFilters.querySelectorAll("button")) {
    button.addEventListener("click", () => {
      const key = button.dataset.filterKey;
      if (key === "search") {
        state.filters.search = "";
      } else {
        state.filters[key] = "";
        if (key === "validation") {
          state.filters.invalidCategory = "";
          clearAnnotationFilters();
        }
      }
      state.currentPage = 1;
      syncControls();
      refreshResults();
    });
  }
}

function syncControls() {
  elements.licensedOnlyToggle.setAttribute("aria-pressed", String(state.licensedOnly));
  elements.searchInput.value = state.filters.search;
  syncAgentOptions();
  for (const definition of FILTER_DEFINITIONS) {
    const element = elements[definition.element];
    if (element) {
      element.value = state.filters[definition.key];
    }
  }
  syncSortToggleButton();
  syncToolbarState();
}

function syncSortToggleButton() {
  if (!elements.sortToggleButton) return;
  const isRandom = state.sortMode === "random";
  const label = isRandom ? "Restore default sort" : "Random sort";
  elements.sortToggleButton.setAttribute("aria-pressed", String(isRandom));
  elements.sortToggleButton.setAttribute("aria-label", label);
  elements.sortToggleButton.title = label;
  elements.sortToggleButton.classList.toggle("ghost-button-active", isRandom);
}

function syncToolbarState() {
  const showInvalidCategory = state.filters.validation === "INVALID";
  if (elements.primaryToolbar) {
    elements.primaryToolbar.classList.toggle("toolbar-primary-valid", !showInvalidCategory);
    elements.primaryToolbar.classList.toggle("toolbar-primary-invalid", showInvalidCategory);
    elements.primaryToolbar.classList.toggle("toolbar-primary-solo", showInvalidCategory);
  }

  if (!showInvalidCategory) {
    state.filters.invalidCategory = "";
    elements.invalidCategoryFilter.value = "";
  }

  if (elements.invalidCategoryFilterGroup) {
    elements.invalidCategoryFilterGroup.style.display = showInvalidCategory ? "grid" : "none";
  }
  elements.invalidCategoryFilter.disabled = !showInvalidCategory;

  const showAnnotationToolbar = state.filters.validation === "VALID";
  if (!showAnnotationToolbar) {
    clearAnnotationFilters();
  }
  if (elements.annotationToolbar) {
    elements.annotationToolbar.style.display = showAnnotationToolbar ? "grid" : "none";
  }
}

function clearAnnotationFilters() {
  for (const definition of FILTER_DEFINITIONS) {
    if (definition.row === "annotation") {
      state.filters[definition.key] = "";
      const element = elements[definition.element];
      if (element) {
        element.value = "";
      }
    }
  }
}

function getPageRecords(records, currentPage, pageSize) {
  const start = (currentPage - 1) * pageSize;
  return records.slice(start, start + pageSize);
}

function clampPage(page, totalPages) {
  return Math.min(Math.max(1, Math.floor(page)), totalPages);
}

function syncPaginationControls(totalPages) {
  const hasPages = totalPages > 0;
  elements.pageTotal.textContent = String(totalPages);
  elements.pageJumpInput.disabled = !hasPages;
  elements.pagePrevButton.disabled = !hasPages || state.currentPage <= 1;
  elements.pageNextButton.disabled = !hasPages || state.currentPage >= totalPages;
}

async function loadPageDetails(pageRecords) {
  const chunkNames = [...new Set(pageRecords.map((record) => record.chunk))];
  await Promise.all(chunkNames.map((chunkName) => ensureChunkLoaded(chunkName)));

  return pageRecords.map((record) => {
    const chunk = state.chunkCache.get(record.chunk);
    return chunk.get(record.record_key) ?? record;
  });
}

async function ensureChunkLoaded(chunkName) {
  if (state.chunkCache.has(chunkName)) {
    return state.chunkCache.get(chunkName);
  }

  const response = await fetch(`${state.chunksUrl}/${chunkName}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load chunk ${chunkName}: ${response.status}`);
  }

  const payload = await response.json();
  const chunkMap = new Map((payload.records ?? []).map((record) => [record.record_key, record]));
  state.chunkCache.set(chunkName, chunkMap);
  return chunkMap;
}

function renderResults(records) {
  elements.results.innerHTML = "";

  const fragment = document.createDocumentFragment();

  for (const record of records) {
    const node = elements.cardTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".session-meta").innerHTML =
      `<span class="session-meta-dataset">${escapeHtml(record.dataset_label)}</span> / ${escapeHtml(record.repo_id)} / ${escapeHtml(record.session_id)} / ${escapeHtml(record.id)}`;

    const tagRow = node.querySelector(".tag-row");
    tagRow.innerHTML = [
      renderTag(
        humanizeValidationLabel(record.validation_label),
        `tag-validation-${String(record.validation_label || "").toLowerCase()}`,
      ),
      record.invalid_category
        ? renderTag(humanizeCategory(record.invalid_category), "tag-invalid-category")
        : "",
      record.platform ? renderTag(record.platform, "tag-platform") : "",
      record.agent ? renderTag(record.agent, "tag-agent") : "",
      record.license ? renderTag(record.license, "tag-license") : "",
      record.alignment_goal ? renderTag(humanize(record.alignment_goal)) : "",
    ]
      .filter(Boolean)
      .join("");

    const cardTitle = node.querySelector(".card-title");
    let annotationSummarySlot = node.querySelector(".annotation-summary-slot");
    if (!annotationSummarySlot) {
      annotationSummarySlot = document.createElement("div");
      annotationSummarySlot.className = "annotation-summary-slot";
    }
    node.insertBefore(annotationSummarySlot, cardTitle);

    const detailStack = node.querySelector(".detail-stack");
    if (record.validation_label === "VALID") {
      annotationSummarySlot.innerHTML = renderAnnotationSummary(record);
      detailStack.innerHTML = "";
    } else {
      annotationSummarySlot.innerHTML = renderInvalidPanel(record);
      detailStack.innerHTML = "";
    }

    cardTitle.textContent = record.name;
    node.querySelector(".card-description").textContent = record.description;

    const details = node.querySelector(".evidence-block");
    const summary = details.querySelector("summary");
    const evidenceList = details.querySelector(".evidence-list");
    const evidence = record.evidence ?? [];
    summary.textContent = `Evidence (${evidence.length})`;
    evidenceList.innerHTML = evidence
      .map(
        (item) => `
          <div class="evidence-item">
            <span class="evidence-turn">${escapeHtml(item.turn || "Unknown turn")}</span>
            <p class="evidence-quote">${escapeHtml(item.quote || "")}</p>
            <p class="evidence-context">${escapeHtml(item.context || "")}</p>
          </div>
        `,
      )
      .join("");

    fragment.append(node);
  }

  elements.results.append(fragment);
}

function renderInvalidPanel(record) {
  if (!record.validation_note) return "";
  return renderInfoPanel("Validation Note", `<p>${escapeHtml(record.validation_note)}</p>`);
}

function renderAnnotationSummary(record) {
  const sections = [
    renderAnnotationFacet(
      "Symptom",
      (record.symptom_labels ?? []).map(formatSymptomLabel),
      record.symptom_reasoning,
    ),
    renderAnnotationFacet(
      "Cause",
      buildCauseEntries(record.cause_entries ?? []),
      record.cause_reasoning,
    ),
    renderAnnotationFacet(
      "Outcome",
      [record.outcome_damage_severity, record.outcome_damage_locus]
        .filter(Boolean)
        .map((value) =>
          value.startsWith("DS") ? formatDamageSeverity(value) : formatDamageLocus(value),
        ),
      record.outcome_reasoning,
    ),
    renderAnnotationFacet(
      "Resolution",
      [record.resolution_status_code, record.resolution_resolver]
        .filter(Boolean)
        .map((value) =>
          value.startsWith("RS")
            ? formatResolutionStatus(value)
            : formatResolutionResolver(value),
        ),
      record.resolution_reasoning,
    ),
  ]
    .filter(Boolean)
    .join("");

  if (!sections) return "";

  return `
    <section class="annotation-summary">
      <div class="annotation-summary-grid">
        ${sections}
      </div>
    </section>
  `;
}

function renderAnnotationFacet(label, items, reasoning = "") {
  const filteredItems = items.filter(Boolean);
  if (!filteredItems.length) return "";

  return `
    <div class="annotation-facet">
      <div class="annotation-facet-heading">
        <span class="annotation-facet-label">${escapeHtml(label)}</span>
        ${renderReasoningHint(label, reasoning)}
      </div>
      <div class="annotation-facet-values">
        ${filteredItems
      .map((item) => `<span class="annotation-pill">${escapeHtml(item)}</span>`)
      .join("")}
      </div>
    </div>
  `;
}

function renderReasoningHint(label, reasoning) {
  if (!reasoning) return "";

  return `
    <span class="reasoning-hint">
      <button
        type="button"
        class="reasoning-trigger"
        aria-label="Show ${escapeHtml(label)} reasoning"
      >
        <span aria-hidden="true">i</span>
      </button>
      <span class="reasoning-tooltip" role="tooltip">${escapeHtml(reasoning)}</span>
    </span>
  `;
}

function buildCauseEntries(entries) {
  return entries.map((entry) => {
    const tier = entry?.evidence_tier ?? "";
    const label = entry?.label ?? "";
    return tier ? `${formatCauseLabel(label)} (${humanize(tier)})` : formatCauseLabel(label);
  });
}

function renderInfoPanel(title, body) {
  if (!body) return "";
  return `
    <section class="info-panel">
      <span class="info-panel-label">${escapeHtml(title)}</span>
      <div class="info-panel-body">${body}</div>
    </section>
  `;
}

function renderLabelList(items) {
  const filteredItems = items.filter(Boolean);
  if (!filteredItems.length) {
    return `<p class="info-panel-empty">Not available</p>`;
  }

  return `
    <ul class="info-list">
      ${filteredItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function renderTag(label, className = "") {
  return `<span class="tag ${className}">${escapeHtml(label)}</span>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
