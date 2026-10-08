/**
 * Quizora — Production Frontend
 * ES Module · No external dependencies
 */

/* ══════════════════════════════════════════════════════
   UTILITIES
══════════════════════════════════════════════════════ */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str ?? "";
  return d.innerHTML;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function diffClass(level) {
  const k = (level || "medium").toLowerCase();
  return ["easy", "medium", "hard"].includes(k) ? k : "medium";
}

/* ══════════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════════ */
const state = {
  file: null,
  response: null,
  showAnswers: false,
  practiceAnswered: false,
};

/* ══════════════════════════════════════════════════════
   API
══════════════════════════════════════════════════════ */
function apiBase() {
  const custom = ($("#api-base")?.value ?? "").trim();
  if (custom) return custom.replace(/\/$/, "");

  // If running locally, use relative path
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "";
  }
  // If deployed (e.g. on Vercel), fall back to global config or current origin
  return (window.__QUIZORA_API_BASE__ || "").replace(/\/$/, "");
}


function apiUrl(path) {
  const base = apiBase();
  return base ? `${base}${path}` : path;
}

/* ══════════════════════════════════════════════════════
   TOAST NOTIFICATIONS
══════════════════════════════════════════════════════ */
function toast(message, type = "info", duration = 4000) {
  const container = $("#toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<div class="toast-dot"></div><span>${escapeHtml(message)}</span>`;
  container.appendChild(el);

  setTimeout(() => {
    el.classList.add("fade-out");
    el.addEventListener("animationend", () => el.remove(), { once: true });
    setTimeout(() => el.remove(), 400);
  }, duration);
}

/* ══════════════════════════════════════════════════════
   NAVBAR — scroll shadow
══════════════════════════════════════════════════════ */
function initNavbar() {
  const nav = $("#navbar");
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 10);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}

/* ══════════════════════════════════════════════════════
   SETTINGS PANEL
══════════════════════════════════════════════════════ */
function initSettings() {
  const panel = $("#settings-panel");
  const backdrop = $("#settings-backdrop");

  function openSettings() {
    panel.classList.add("open");
    backdrop.classList.remove("hidden");
    panel.removeAttribute("aria-hidden");
    document.body.style.overflow = "hidden";
  }

  function closeSettings() {
    panel.classList.remove("open");
    backdrop.classList.add("hidden");
    panel.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  $("#settings-toggle").addEventListener("click", openSettings);
  $("#settings-toggle-2").addEventListener("click", openSettings);
  $("#settings-close").addEventListener("click", closeSettings);
  backdrop.addEventListener("click", closeSettings);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && panel.classList.contains("open")) closeSettings();
  });
}

/* ══════════════════════════════════════════════════════
   DIFFICULTY SLIDERS
══════════════════════════════════════════════════════ */
function updateDifficultyUI() {
  const easy   = Number($("#easy").value);
  const medium = Number($("#medium").value);
  const hard   = Number($("#hard").value);
  const total  = easy + medium + hard;

  $("#easy-out").textContent   = `${easy}%`;
  $("#medium-out").textContent = `${medium}%`;
  $("#hard-out").textContent   = `${hard}%`;

  // Stacked bar
  $("#easy-seg").style.width   = `${easy}%`;
  $("#medium-seg").style.width = `${medium}%`;
  $("#hard-seg").style.width   = `${hard}%`;

  const totalEl = $("#diff-total");
  totalEl.textContent = `Total: ${total}%`;
  totalEl.classList.toggle("ok",  total === 100);
  totalEl.classList.toggle("bad", total !== 100);

  // Update chips
  $("#chip-easy").textContent   = easy;
  $("#chip-medium").textContent = medium;
  $("#chip-hard").textContent   = hard;

  validateForm();
}

function initSliders() {
  ["easy", "medium", "hard"].forEach((id) => {
    $(`#${id}`).addEventListener("input", updateDifficultyUI);
  });

  // Number stepper
  $("#num-dec").addEventListener("click", () => {
    const el = $("#num-questions");
    const val = Number(el.value);
    if (val > Number(el.min)) { el.value = val - 1; updateChipQuestions(); validateForm(); }
  });

  $("#num-inc").addEventListener("click", () => {
    const el = $("#num-questions");
    const val = Number(el.value);
    if (val < Number(el.max)) { el.value = val + 1; updateChipQuestions(); validateForm(); }
  });

  $("#num-questions").addEventListener("input", () => { updateChipQuestions(); validateForm(); });

  updateDifficultyUI();
}

function updateChipQuestions() {
  $("#chip-questions").textContent = $("#num-questions").value;
}

/* ══════════════════════════════════════════════════════
   FORM VALIDATION
══════════════════════════════════════════════════════ */
function validateForm() {
  const total =
    Number($("#easy").value) +
    Number($("#medium").value) +
    Number($("#hard").value);

  const numQ = Number($("#num-questions").value);
  const ok = state.file && total === 100 && numQ >= 1 && numQ <= 100;

  const btn = $("#generate-btn");
  btn.disabled = !ok;
}

/* ══════════════════════════════════════════════════════
   STATUS MESSAGE
══════════════════════════════════════════════════════ */
function setStatus(message, type = "") {
  const el = $("#status-msg");
  el.textContent = message;
  el.className = `status-msg ${type}`.trim();
}

/* ══════════════════════════════════════════════════════
   DROPZONE / FILE UPLOAD
══════════════════════════════════════════════════════ */
function initUpload() {
  const dropzone   = $("#dropzone");
  const input      = $("#file-input");
  const fileView   = $("#dropzone-file");
  const defaultView = $("#dropzone-icon");
  const textView   = $("#dropzone-text");

  function pickFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast("Please upload a PDF file.", "error");
      setStatus("Please choose a PDF file.", "error");
      return;
    }
    state.file = file;
    $("#file-name").textContent = file.name;
    $("#file-size").textContent = formatBytes(file.size);

    fileView.classList.remove("hidden");
    defaultView.style.display  = "none";
    textView.style.display     = "none";
    dropzone.classList.add("has-file");

    setStatus("");
    validateForm();
    toast(`"${file.name}" ready to upload.`, "success", 2500);
  }

  function clearFile() {
    state.file = null;
    input.value = "";
    $("#file-name").textContent = "";
    $("#file-size").textContent = "";

    fileView.classList.add("hidden");
    defaultView.style.display = "";
    textView.style.display    = "";
    dropzone.classList.remove("has-file");

    validateForm();
  }

  dropzone.addEventListener("click", (e) => {
    if (e.target.closest("#remove-file")) return;
    if (!state.file) input.click();
  });

  dropzone.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && !state.file) {
      e.preventDefault();
      input.click();
    }
  });

  input.addEventListener("change", () => pickFile(input.files[0]));

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (!state.file) dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (!state.file) pickFile(e.dataTransfer.files[0]);
  });

  $("#remove-file").addEventListener("click", (e) => {
    e.stopPropagation();
    clearFile();
  });
}

/* ══════════════════════════════════════════════════════
   LOADING OVERLAY WITH STEPS
══════════════════════════════════════════════════════ */

// Steps 1–4 are timer-driven (rough estimates of pipeline stages).
// Step 5 "Exporting files" is NEVER timer-driven — it only fires
// when stopLoading() is actually called so it never gets stuck.
const LOADING_STEPS = [
  { id: "lstep-1", msg: "Parsing PDF content…",            pct: 8,  delay: 0      },
  { id: "lstep-2", msg: "Analyzing topics & structure…",   pct: 22, delay: 18_000 },
  { id: "lstep-3", msg: "Generating questions with AI…",   pct: 50, delay: 45_000 },
  { id: "lstep-4", msg: "Validating & ranking questions…", pct: 78, delay: 90_000 },
  // Step 5 has NO delay — it is triggered manually by stopLoading()
  { id: "lstep-5", msg: "Exporting files…", pct: 95 },
];

// Cycling messages that rotate while the AI is generating
// so the overlay never looks frozen during long waits.
const CYCLING_MSGS = [
  "Generating questions with AI…",
  "Reading source passages…",
  "Crafting distractors…",
  "Writing explanations…",
  "Cross-checking answers…",
  "Large PDFs take a little longer…",
  "Hang tight, quality takes time!",
  "Still working — almost there…",
];

let _loadingTimers  = [];
let _cycleTimer     = null;
let _cycleIndex     = 0;
let _creepTimer     = null;  // gently nudges progress bar while waiting
let _creepPct       = 0;

function _startCyclingMessages() {
  _cycleIndex = 0;
  _stopCyclingMessages();
  _cycleTimer = setInterval(() => {
    _cycleIndex = (_cycleIndex + 1) % CYCLING_MSGS.length;
    const el = $("#loading-msg");
    if (el) el.textContent = CYCLING_MSGS[_cycleIndex];
  }, 6_000);
}

function _stopCyclingMessages() {
  if (_cycleTimer) { clearInterval(_cycleTimer); _cycleTimer = null; }
}

// Slowly inches the bar from its current value toward 88%
// (never reaching 95% — that's reserved for "Exporting files")
function _startCreep(fromPct) {
  _stopCreep();
  _creepPct = fromPct;
  _creepTimer = setInterval(() => {
    if (_creepPct >= 88) { _stopCreep(); return; }
    _creepPct += 0.15;                          // ~0.15% every 500 ms → ~2 min to reach 88%
    const bar = $("#loading-bar");
    if (bar) bar.style.width = `${_creepPct.toFixed(1)}%`;
  }, 500);
}

function _stopCreep() {
  if (_creepTimer) { clearInterval(_creepTimer); _creepTimer = null; }
}

function _activateStep(index) {
  LOADING_STEPS.forEach((s, j) => {
    const el = $(`#${s.id}`);
    if (!el) return;
    el.classList.toggle("done",   j < index);
    el.classList.toggle("active", j === index);
  });
}

function startLoading() {
  const overlay = $("#loading-overlay");
  overlay.classList.remove("hidden");
  overlay.removeAttribute("aria-hidden");

  // Reset
  LOADING_STEPS.forEach((s) => $(`#${s.id}`)?.classList.remove("active", "done"));
  $("#loading-bar").style.width = "0%";
  const msgEl = $("#loading-msg");
  if (msgEl) msgEl.textContent = LOADING_STEPS[0].msg;

  _loadingTimers.forEach(clearTimeout);
  _loadingTimers = [];
  _stopCyclingMessages();
  _stopCreep();

  // Schedule steps 1–4 only (indices 0–3).
  // Step 5 (index 4, "Exporting files") is triggered manually
  // by stopLoading() so it NEVER appears before the API responds.
  const timedSteps = LOADING_STEPS.slice(0, 4); // first 4 steps only
  timedSteps.forEach((step, i) => {
    const t = setTimeout(() => {
      _activateStep(i);
      const msgEl = $("#loading-msg");
      if (msgEl) msgEl.textContent = step.msg;
      $("#loading-bar").style.width = `${step.pct}%`;

      // After step 3 (Validating), start the slow creep so the bar
      // keeps moving visually without jumping to 95%.
      if (i === 3) _startCreep(step.pct);

      // After step 2 (Generating), cycle the subtitle messages.
      if (i === 2) _startCyclingMessages();

    }, step.delay);
    _loadingTimers.push(t);
  });

  // Immediately activate step 1 (index 0) so something is visible
  _activateStep(0);
  $("#loading-bar").style.width = `${LOADING_STEPS[0].pct}%`;
}

function stopLoading() {
  // Kill all timers
  _loadingTimers.forEach(clearTimeout);
  _loadingTimers = [];
  _stopCyclingMessages();
  _stopCreep();

  // Manually trigger step 5 "Exporting files" — this is the only
  // place it ever gets shown, right when the API actually responds.
  const lastStep = LOADING_STEPS[4];
  _activateStep(4);
  const msgEl = $("#loading-msg");
  if (msgEl) msgEl.textContent = lastStep.msg;
  $("#loading-bar").style.width = `${lastStep.pct}%`;

  // Short pause so user sees "Exporting files", then mark all done & hide.
  setTimeout(() => {
    LOADING_STEPS.forEach((s) => {
      const el = $(`#${s.id}`);
      if (!el) return;
      el.classList.remove("active");
      el.classList.add("done");
    });
    if (msgEl) msgEl.textContent = "Done! ✓";
    $("#loading-bar").style.width = "100%";

    setTimeout(() => {
      const overlay = $("#loading-overlay");
      overlay.classList.add("hidden");
      overlay.setAttribute("aria-hidden", "true");
      $("#loading-bar").style.width = "0%";
    }, 700);
  }, 1_200);
}


/* ══════════════════════════════════════════════════════
   QUIZ GENERATION
══════════════════════════════════════════════════════ */
async function generateQuiz() {
  const total =
    Number($("#easy").value) +
    Number($("#medium").value) +
    Number($("#hard").value);

  if (!state.file || total !== 100) return;

  const fd = new FormData();
  fd.append("file", state.file);
  fd.append("number_of_questions", $("#num-questions").value);
  fd.append("easy_percent",   $("#easy").value);
  fd.append("medium_percent", $("#medium").value);
  fd.append("hard_percent",   $("#hard").value);

  setStatus("");
  startLoading();

  try {
    const res = await fetch(apiUrl("/api/v1/generate"), { method: "POST", body: fd });
    const body = await res.json().catch(() => ({}));

    if (!res.ok) {
      const detail = body.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((d) => d.msg).join("; ")
          : "Quiz generation failed.";
      throw new Error(msg);
    }

    stopLoading();
    showResults(body);
    setStatus("Quiz generated successfully!", "success");
    toast("Your quiz is ready! 🎉", "success");

    // Smooth scroll to results
    setTimeout(() => {
      $("#results-panel").scrollIntoView({ behavior: "smooth", block: "start" });
    }, 200);

  } catch (err) {
    stopLoading();
    const msg = err.message || "Request failed. Please try again.";
    setStatus(msg, "error");
    toast(msg, "error", 6000);
  }
}

/* ══════════════════════════════════════════════════════
   RESULTS — METRICS
══════════════════════════════════════════════════════ */
function renderMetrics(data) {
  const questions = data.quiz?.questions ?? [];
  const meta = data.meta ?? {};
  const byDiff = { easy: 0, medium: 0, hard: 0 };
  questions.forEach((q) => { const d = diffClass(q.difficulty); byDiff[d]++; });

  const cards = [
    { cls: "total-card",  value: questions.length,          label: "Generated" },
    { cls: "source-card", value: escapeHtml(meta.source_filename ?? "—"), label: "Source PDF", small: true },
    { cls: "easy-card",   value: byDiff.easy,               label: "Easy" },
    { cls: "medium-card", value: byDiff.medium,             label: "Medium" },
    { cls: "hard-card",   value: byDiff.hard,               label: "Hard" },
  ];

  $("#metrics-grid").innerHTML = cards
    .map(
      (c) => `
      <div class="metric-card ${c.cls}">
        <div class="metric-value ${c.small ? 'metric-value-sm' : ''}"
          style="${c.small ? 'font-size:1rem;word-break:break-all;' : ''}">${c.value}</div>
        <div class="metric-label">${c.label}</div>
      </div>`
    )
    .join("");

  // Subtitle
  const total = meta.requested_questions ?? questions.length;
  $("#results-subtitle").textContent =
    `${questions.length} of ${total} questions generated`;
}

/* ══════════════════════════════════════════════════════
   OVERVIEW TAB
══════════════════════════════════════════════════════ */
function renderOverview(data) {
  const questions = data.quiz?.questions ?? [];
  const downloads = data.downloads ?? {};

  // Topics
  const byTopic = {};
  questions.forEach((q) => {
    const t = q.topic || "General";
    byTopic[t] = (byTopic[t] || 0) + 1;
  });

  const topTopics = Object.entries(byTopic)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const topicHTML = topTopics.length
    ? topTopics
        .map(
          ([t, n]) => `
        <li class="topic-item">
          <span class="topic-item-name">${escapeHtml(t)}</span>
          <span class="topic-item-count">${n}</span>
        </li>`
        )
        .join("")
    : `<li class="topic-item"><span class="topic-item-name">No topics</span></li>`;

  // Difficulty breakdown
  const byDiff = { easy: 0, medium: 0, hard: 0 };
  questions.forEach((q) => { const d = diffClass(q.difficulty); byDiff[d]++; });
  const total = questions.length || 1;

  const diffHTML = ["easy", "medium", "hard"]
    .map(
      (d) => `
      <div class="diff-summary-row">
        <span class="diff-label-text">${d.charAt(0).toUpperCase() + d.slice(1)}</span>
        <div class="diff-bar-track">
          <div class="diff-bar-fill ${d}-fill" style="width:${Math.round((byDiff[d] / total) * 100)}%"></div>
        </div>
        <span class="diff-count">${byDiff[d]}</span>
      </div>`
    )
    .join("");

  // Downloads
  const dlCards = [
    {
      url: downloads.question_paper,
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10,9 9,9 8,9"/></svg>`,
      label: "Question Paper",
      sublabel: "PDF",
    },
    {
      url: downloads.answer_key,
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9,12 11,14 15,10"/></svg>`,
      label: "Answer Key",
      sublabel: "PDF",
    },
    {
      url: downloads.json,
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16,18 22,12 16,6"/><polyline points="8,6 2,12 8,18"/></svg>`,
      label: "Raw Data",
      sublabel: "JSON",
    },
  ]
    .filter((d) => d.url)
    .map(
      (d) => `
      <a class="download-card" href="${apiUrl(d.url)}" download>
        ${d.icon}
        <span>${d.label}</span>
        <span style="font-size:.72rem;color:var(--neutral-400);font-weight:500;">${d.sublabel}</span>
      </a>`
    )
    .join("");

  $("#tab-overview").innerHTML = `
    <div class="overview-grid">
      <div>
        <p class="overview-section-title">Top Topics</p>
        <ul class="topic-list">${topicHTML}</ul>
      </div>
      <div>
        <p class="overview-section-title">Difficulty Breakdown</p>
        <div class="diff-summary">${diffHTML}</div>
      </div>
    </div>
    <div class="download-section">
      <p class="download-title">Downloads</p>
      <div class="download-grid">${dlCards || "<p style='color:var(--neutral-400);font-size:.875rem;'>No download links available.</p>"}</div>
    </div>
  `;
}

/* ══════════════════════════════════════════════════════
   PREVIEW TAB
══════════════════════════════════════════════════════ */
function renderPreview(data) {
  const questions = data.quiz?.questions ?? [];

  const cards = questions
    .map((q, i) => {
      const dc = diffClass(q.difficulty);
      const opts = (q.options ?? [])
        .map(
          (o, idx) => `
          <li class="option-item ${state.showAnswers && o === q.correct_answer ? "correct-option" : ""}">
            <span class="option-letter">${String.fromCharCode(65 + idx)}</span>
            <span>${escapeHtml(o)}</span>
          </li>`
        )
        .join("");

      const answerBlock = state.showAnswers
        ? `<div class="answer-block">
            <div class="answer-block-title">Correct Answer</div>
            <div class="answer-text">${escapeHtml(q.correct_answer ?? "")}</div>
            ${
              q.explanation
                ? `<div class="explanation-block">
                    <div class="explanation-title">Explanation</div>
                    <div class="explanation-text">${escapeHtml(q.explanation)}</div>
                   </div>`
                : ""
            }
           </div>`
        : "";

      return `
        <article class="question-card" style="animation-delay:${i * 40}ms">
          <div class="question-header">
            <div class="question-num">${i + 1}</div>
            <div class="question-meta">
              <p class="question-text">${escapeHtml(q.question ?? "")}</p>
              <div class="question-badges">
                <span class="badge badge-${dc}">${dc.charAt(0).toUpperCase() + dc.slice(1)}</span>
                ${q.topic ? `<span class="badge badge-topic">${escapeHtml(q.topic)}</span>` : ""}
              </div>
            </div>
          </div>
          <ul class="options-list">${opts}</ul>
          ${answerBlock}
        </article>`;
    })
    .join("");

  $("#tab-preview").innerHTML = `
    <div class="preview-controls">
      <label class="toggle-label">
        <span class="toggle-switch">
          <input type="checkbox" id="show-answers" ${state.showAnswers ? "checked" : ""} />
          <span class="toggle-track"></span>
        </span>
        Show answers &amp; explanations
      </label>
      <span style="font-size:.8rem;color:var(--neutral-400);">${questions.length} question${questions.length !== 1 ? "s" : ""}</span>
    </div>
    <div class="question-cards">
      ${cards || "<p style='color:var(--neutral-400)'>No questions to display.</p>"}
    </div>
  `;

  $("#show-answers")?.addEventListener("change", (e) => {
    state.showAnswers = e.target.checked;
    renderPreview(data);
  });
}

/* ══════════════════════════════════════════════════════
   PRACTICE TAB
══════════════════════════════════════════════════════ */
function renderPractice(data) {
  const questions = data.quiz?.questions ?? [];
  state.practiceAnswered = false;

  const items = questions
    .map((q, i) => {
      const dc = diffClass(q.difficulty);
      const name = `pq-${i}`;
      const opts = (q.options ?? [])
        .map(
          (o, idx) => `
          <label class="practice-option" data-value="${escapeHtml(o)}" data-qindex="${i}">
            <input type="radio" name="${name}" value="${escapeHtml(o)}" />
            <span class="practice-radio"></span>
            <span class="option-letter">${String.fromCharCode(65 + idx)}</span>
            <span>${escapeHtml(o)}</span>
          </label>`
        )
        .join("");

      return `
        <div class="practice-item" id="pi-${i}" data-answer="${escapeHtml(q.correct_answer ?? "")}">
          <div class="practice-q-header">
            <div class="question-num">${i + 1}</div>
            <div>
              <p class="practice-q-text">${escapeHtml(q.question ?? "")}</p>
              <span class="badge badge-${dc}" style="margin-top:6px;display:inline-flex">${dc.charAt(0).toUpperCase() + dc.slice(1)}</span>
            </div>
          </div>
          <div class="practice-options">${opts}</div>
        </div>`;
    })
    .join("");

  $("#tab-practice").innerHTML = `
    <div class="practice-header">
      <h3>${questions.length} Question${questions.length !== 1 ? "s" : ""}</h3>
      <button class="btn btn-primary btn-sm" id="score-btn" type="button">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="16" height="16"><polyline points="20,6 9,17 4,12"/></svg>
        Score my answers
      </button>
    </div>
    <div class="practice-items">${items || "<p style='color:var(--neutral-400)'>No questions available.</p>"}</div>
    <div class="score-banner" id="score-banner"></div>
  `;

  // Option selection
  $$("#tab-practice .practice-option").forEach((label) => {
    label.addEventListener("click", () => {
      if (state.practiceAnswered) return;
      const qIndex = label.dataset.qindex;
      const name = label.querySelector("input").name;

      // Clear selection within same question
      $$(`input[name="${name}"]`).forEach((inp) => {
        inp.closest(".practice-option").classList.remove("selected");
        inp.checked = false;
      });

      label.querySelector("input").checked = true;
      label.classList.add("selected");
    });
  });

  // Score button
  $("#score-btn")?.addEventListener("click", () => {
    if (state.practiceAnswered) {
      // Reset
      resetPractice();
      return;
    }
    scorePractice(questions);
  });
}

function scorePractice(questions) {
  state.practiceAnswered = true;
  let correct = 0;

  questions.forEach((q, i) => {
    const pi = $(`#pi-${i}`);
    const correctAnswer = q.correct_answer ?? "";
    const selected = pi.querySelector(".practice-option.selected");
    const selectedValue = selected?.dataset.value ?? null;

    const isCorrect = selectedValue === correctAnswer;
    if (isCorrect) correct++;

    if (selected) {
      pi.classList.add(isCorrect ? "answered-correct" : "answered-wrong");
    }

    // Reveal all options
    $$(".practice-option", pi).forEach((opt) => {
      if (opt.dataset.value === correctAnswer) {
        opt.classList.add("correct-reveal");
        opt.querySelector(".practice-radio").innerHTML =
          `<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><polyline points="2,6 5,9 10,3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`;
      } else if (opt.classList.contains("selected")) {
        opt.classList.add("wrong-reveal");
      }
    });
  });

  const pct = questions.length ? Math.round((correct / questions.length) * 100) : 0;
  const tier = pct >= 80 ? "great" : pct >= 50 ? "good" : "low";
  const emoji = pct >= 80 ? "🎉" : pct >= 50 ? "👍" : "📚";
  const label = pct >= 80 ? "Excellent work!" : pct >= 50 ? "Good effort!" : "Keep studying!";

  const banner = $("#score-banner");
  banner.className = `score-banner ${tier} visible`;
  banner.innerHTML = `
    <div class="score-value">${pct}%</div>
    <div class="score-label">${emoji} ${label}</div>
    <div class="score-sub">${correct} of ${questions.length} correct</div>
  `;

  const btn = $("#score-btn");
  btn.textContent = "Try again";
  btn.classList.remove("btn-primary");
  btn.classList.add("btn-outline");

  banner.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function resetPractice() {
  state.practiceAnswered = false;
  if (state.response) renderPractice(state.response);
}

/* ══════════════════════════════════════════════════════
   SHOW RESULTS
══════════════════════════════════════════════════════ */
function showResults(data) {
  state.response = data;
  state.showAnswers = false;
  state.practiceAnswered = false;

  const panel = $("#results-panel");
  panel.classList.remove("hidden");

  // Wire prominent 2 PDF download buttons
  const downloads = data.downloads || {};
  const qBtn = $("#main-dl-questions");
  if (qBtn) {
    if (downloads.question_paper) {
      qBtn.href = apiUrl(downloads.question_paper);
      qBtn.style.display = "";
    } else {
      qBtn.style.display = "none";
    }
  }

  const aBtn = $("#main-dl-answers");
  if (aBtn) {
    if (downloads.answer_key) {
      aBtn.href = apiUrl(downloads.answer_key);
      aBtn.style.display = "";
    } else {
      aBtn.style.display = "none";
    }
  }

  renderMetrics(data);
  renderOverview(data);
  renderPreview(data);
  renderPractice(data);

  switchTab("overview");
}


/* ══════════════════════════════════════════════════════
   TABS
══════════════════════════════════════════════════════ */
function switchTab(name) {
  $$(".tab").forEach((t) => {
    const active = t.dataset.tab === name;
    t.classList.toggle("active", active);
    t.setAttribute("aria-selected", String(active));
  });

  $$(".tab-panel").forEach((p) => {
    const isTarget = p.id === `tab-${name}`;
    p.classList.toggle("hidden", !isTarget);
    p.classList.toggle("active",  isTarget);
  });
}

function initTabs() {
  $$(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });
}

/* ══════════════════════════════════════════════════════
   NEW QUIZ button
══════════════════════════════════════════════════════ */
function initNewQuiz() {
  $("#new-quiz-btn").addEventListener("click", () => {
    $("#results-panel").classList.add("hidden");
    state.response = null;
    setStatus("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

/* ══════════════════════════════════════════════════════
   HEALTH CHECK
══════════════════════════════════════════════════════ */
async function checkApi() {
  const dot = $("#api-dot");
  try {
    const res = await fetch(apiUrl("/api/health"), { signal: AbortSignal.timeout(5000) });
    if (res.ok) {
      dot.classList.add("ok");
      dot.classList.remove("err");
      dot.title = "API connected";
    } else {
      throw new Error("Non-OK response");
    }
  } catch {
    dot.classList.add("err");
    dot.classList.remove("ok");
    dot.title = "Cannot reach API — start the server with: uvicorn api.main:app --reload --port 8000";
    setStatus(
      "Cannot reach API. Run: uvicorn api.main:app --reload --port 8000",
      "error"
    );
  }
}

/* ══════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════ */
function init() {
  initNavbar();
  initSettings();
  initSliders();
  initUpload();
  initTabs();
  initNewQuiz();

  $("#generate-btn").addEventListener("click", generateQuiz);

  checkApi();
}

init();
