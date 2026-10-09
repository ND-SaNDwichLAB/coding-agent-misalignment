const PROMPT_DOCS = {
  extraction: {
    file: "./prompts/extraction.md",
    step: "1",
    title: "Extraction Prompt",
    subtitle:
      "Identify developer-agent misalignment episodes from a raw session and convert them into self-contained, evidence-grounded records.",
  },
  validation: {
    file: "./prompts/validation.md",
    step: "2",
    title: "Validation Prompt",
    subtitle:
      "Judge whether each extracted misalignment claim is actually supported by the quoted evidence, and filter out false positives.",
  },
  annotation: {
    file: "./prompts/annotation.md",
    step: "3",
    title: "Annotation Prompt",
    subtitle:
      "Characterize each validated episode across symptom, cause, outcome, and resolution without re-extracting the original event.",
  },
};

const elements = {
  title: document.querySelector("#prompt-title"),
  subtitle: document.querySelector("#prompt-subtitle"),
  stepBadge: document.querySelector("#prompt-step-badge"),
  markdown: document.querySelector("#prompt-markdown"),
};

init().catch((error) => {
  console.error(error);
  renderError("Failed to load this prompt page.");
});

async function init() {
  const params = new URLSearchParams(window.location.search);
  const docKey = params.get("doc") ?? "extraction";
  const doc = PROMPT_DOCS[docKey];

  if (!doc) {
    renderError("Unknown prompt requested.");
    return;
  }

  document.title = `${doc.title} · Coding Agent Misalignment Atlas`;
  elements.title.textContent = doc.title;
  elements.subtitle.textContent = doc.subtitle;
  elements.stepBadge.textContent = doc.step;

  const response = await fetch(doc.file, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${doc.file}: ${response.status}`);
  }

  const markdown = await response.text();
  elements.markdown.innerHTML = markdownToHtml(markdown);
}

function renderError(message) {
  elements.markdown.innerHTML = `<div class="prompt-empty">${escapeHtml(message)}</div>`;
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let paragraphLines = [];
  let listType = null;
  let listItems = [];
  let blockquoteLines = [];
  let codeFence = null;
  let codeLines = [];

  const flushParagraph = () => {
    if (!paragraphLines.length) return;
    const text = paragraphLines.join(" ").trim();
    if (text) {
      blocks.push(`<p>${renderInline(text)}</p>`);
    }
    paragraphLines = [];
  };

  const flushList = () => {
    if (!listType || !listItems.length) return;
    const tag = listType === "ol" ? "ol" : "ul";
    blocks.push(`<${tag}>${listItems.map((item) => `<li>${renderInline(item)}</li>`).join("")}</${tag}>`);
    listType = null;
    listItems = [];
  };

  const flushBlockquote = () => {
    if (!blockquoteLines.length) return;
    const text = blockquoteLines.join(" ").trim();
    if (text) {
      blocks.push(`<blockquote><p>${renderInline(text)}</p></blockquote>`);
    }
    blockquoteLines = [];
  };

  const flushAll = () => {
    flushParagraph();
    flushList();
    flushBlockquote();
  };

  for (const line of lines) {
    if (codeFence !== null) {
      if (line.startsWith("```")) {
        const code = escapeHtml(codeLines.join("\n"));
        const languageClass = codeFence ? ` class="language-${escapeHtml(codeFence)}"` : "";
        blocks.push(`<pre><code${languageClass}>${code}</code></pre>`);
        codeFence = null;
        codeLines = [];
      } else {
        codeLines.push(line);
      }
      continue;
    }

    const trimmed = line.trim();

    if (!trimmed) {
      flushAll();
      continue;
    }

    const fenceMatch = trimmed.match(/^```([\w-]+)?$/);
    if (fenceMatch) {
      flushAll();
      codeFence = fenceMatch[1] ?? "";
      codeLines = [];
      continue;
    }

    if (/^---+$/.test(trimmed)) {
      flushAll();
      blocks.push("<hr />");
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,3})\s+(.*)$/);
    if (headingMatch) {
      flushAll();
      const level = headingMatch[1].length;
      blocks.push(`<h${level}>${renderInline(headingMatch[2])}</h${level}>`);
      continue;
    }

    const blockquoteMatch = line.match(/^\s*>\s?(.*)$/);
    if (blockquoteMatch) {
      flushParagraph();
      flushList();
      blockquoteLines.push(blockquoteMatch[1]);
      continue;
    }
    flushBlockquote();

    const orderedMatch = trimmed.match(/^\d+\.\s+(.*)$/);
    if (orderedMatch) {
      flushParagraph();
      if (listType && listType !== "ol") {
        flushList();
      }
      listType = "ol";
      listItems.push(orderedMatch[1]);
      continue;
    }

    const unorderedMatch = trimmed.match(/^-\s+(.*)$/);
    if (unorderedMatch) {
      flushParagraph();
      if (listType && listType !== "ul") {
        flushList();
      }
      listType = "ul";
      listItems.push(unorderedMatch[1]);
      continue;
    }

    flushList();
    paragraphLines.push(trimmed);
  }

  flushAll();
  return blocks.join("");
}

function renderInline(text) {
  const codeChunks = [];
  const rawWithPlaceholders = text.replace(/`([^`]+)`/g, (_, code) => {
    const token = `@@CODE_${codeChunks.length}@@`;
    codeChunks.push(`<code>${escapeHtml(code)}</code>`);
    return token;
  });
  let rendered = escapeHtml(rawWithPlaceholders);

  rendered = rendered
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");

  return rendered.replace(/@@CODE_(\d+)@@/g, (_, index) => codeChunks[Number(index)] ?? "");
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
