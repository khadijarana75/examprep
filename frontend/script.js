"use strict";

/*
  ExamForge frontend.
  Talks to the FastAPI routes:
    POST /api/upload    (multipart "file")                          -> {filename, chars_extracted, chunks_indexed, collection}
    POST /api/generate  {source_name, topic, num_questions, final_top_k} -> {questions, rejected_count, ...}
    POST /api/submit    {source_name, verified_questions, submitted_answers} -> {grading_result, weak_topics}
    POST /api/followup  {source_name, weak_topics, num_questions}   -> {questions, rejected_count}
*/

const API_BASE = location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
const RECENT_KEY = "examforge.recent";
const LETTERS = "ABCDEFGHIJ";
const VIEWS = ["upload", "setup", "exam", "results"];

const S = {
  source: null,
  numQuestions: 3,
  questions: [],
  meta: {},
  answers: {},     // {questionIndex: chosenOptionIndex}
  current: 0,
  grading: null,
  weakTopics: [],
  busy: false,
};

const $ = (sel) => document.querySelector(sel);

/* Build DOM without innerHTML, so question text from the LLM is never parsed as HTML. */
function el(tag, props = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, value);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false || kid === "") continue;
    node.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return node;
}

/* ---------- Network ---------- */

async function request(path, options) {
  let res;
  try {
    res = await fetch(API_BASE + path, options);
  } catch (_) {
    throw new Error("Can't reach the ExamForge server. Is uvicorn running?");
  }
  let data = null;
  try { data = await res.json(); } catch (_) { /* body was not JSON */ }
  if (!res.ok) {
    const detail = data && data.detail;
    const message = typeof detail === "string" ? detail
      : Array.isArray(detail) ? detail.map((d) => d.msg).join("; ")
      : `Request failed (HTTP ${res.status}).`;
    throw new Error(message);
  }
  return data;
}

function postJSON(path, body) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

/* Runs one backend action behind the loading overlay; ignores re-entry while busy. */
async function guarded(message, task) {
  if (S.busy) return;
  S.busy = true;
  clearError();

  const started = Date.now();
  const tick = () => { $("#loading-time").textContent = `${Math.floor((Date.now() - started) / 1000)}s elapsed`; };
  $("#loading-text").textContent = message;
  tick();
  $("#loading").hidden = false;
  const timer = setInterval(tick, 1000);

  try {
    await task();
  } catch (err) {
    showError(err.message || String(err));
  } finally {
    clearInterval(timer);
    $("#loading").hidden = true;
    S.busy = false;
  }
}

/* ---------- Errors and views ---------- */

function showError(message) {
  $("#error-text").textContent = message;
  $("#error").hidden = false;
}

function clearError() {
  $("#error").hidden = true;
}

function showView(name) {
  const current = VIEWS.indexOf(name);
  VIEWS.forEach((v) => { $("#view-" + v).hidden = v !== name; });
  document.querySelectorAll("#steps li").forEach((li) => {
    const idx = VIEWS.indexOf(li.dataset.step);
    li.classList.toggle("active", idx === current);
    li.classList.toggle("done", idx < current);
    if (idx === current) li.setAttribute("aria-current", "step");
    else li.removeAttribute("aria-current");
  });
  window.scrollTo(0, 0);
}

/* ---------- Upload ---------- */

function loadRecent() {
  try {
    const list = JSON.parse(localStorage.getItem(RECENT_KEY));
    return Array.isArray(list) ? list.filter((n) => typeof n === "string") : [];
  } catch (_) {
    return [];
  }
}

function rememberDoc(name) {
  try {
    const list = [name, ...loadRecent().filter((n) => n !== name)].slice(0, 5);
    localStorage.setItem(RECENT_KEY, JSON.stringify(list));
  } catch (_) { /* storage unavailable: recent list is a convenience only */ }
}

function renderRecent() {
  const names = loadRecent();
  $("#recent").hidden = names.length === 0;
  $("#recent-list").replaceChildren(...names.map((name) =>
    el("button", {
      type: "button", class: "chip", title: name, text: name,
      onclick: () => selectSource(name, "Previously indexed document."),
    })
  ));
}

function uploadFile(file) {
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  return guarded(`Indexing "${file.name}": extracting, chunking and embedding…`, async () => {
    const data = await request("/api/upload", { method: "POST", body: form });
    rememberDoc(data.filename);
    selectSource(
      data.filename,
      `${data.chunks_indexed} chunks indexed from ${Number(data.chars_extracted).toLocaleString()} characters.`
    );
  });
}

function selectSource(name, info) {
  S.source = name;
  $("#setup-source").textContent = name;
  $("#setup-info").textContent = info;
  showView("setup");
  $("#topic").focus();
}

/* ---------- Generate ---------- */

function generate() {
  const topic = $("#topic").value.trim();
  if (!topic) {
    showError("Enter a topic first.");
    $("#topic").focus();
    return;
  }
  const requested = Math.min(10, Math.max(1, parseInt($("#num-questions").value, 10) || 3));

  return guarded("Retrieving passages, then generating and verifying questions. This can take up to a minute…", async () => {
    const data = await postJSON("/api/generate", {
      source_name: S.source,
      topic,
      num_questions: requested,
      final_top_k: 5,
    });
    if (!data.questions || data.questions.length === 0) {
      throw new Error(`No question passed verification (${data.rejected_count || 0} rejected). Try a more specific topic.`);
    }
    S.numQuestions = requested;
    startExam(data.questions, { label: topic, rejected: data.rejected_count || 0, requested });
  });
}

/* ---------- Exam ---------- */

function startExam(questions, meta) {
  S.questions = questions;
  S.meta = meta;
  S.answers = {};
  S.current = 0;
  renderExam();
  showView("exam");
}

function renderExam(focusOption) {
  const total = S.questions.length;
  const q = S.questions[S.current];
  const answeredCount = Object.keys(S.answers).length;
  const isLast = S.current === total - 1;

  const notes = [];
  if (S.meta.rejected > 0) {
    notes.push(`${S.meta.rejected} draft question${S.meta.rejected === 1 ? " was" : "s were"} rejected by the source check.`);
  }
  if (S.meta.requested && total < S.meta.requested) {
    notes.push(`Showing ${total} of ${S.meta.requested} requested questions.`);
  }

  const optionButtons = (q.options || []).map((text, i) => {
    const selected = S.answers[S.current] === i;
    return el("button", {
      type: "button",
      class: "option" + (selected ? " selected" : ""),
      role: "radio",
      "aria-checked": String(selected),
      onclick: () => selectAnswer(i),
    },
      el("span", { class: "letter", text: LETTERS[i] || String(i + 1) }),
      el("span", { class: "opt-text", text }),
    );
  });

  const dots = S.questions.map((_, i) => el("button", {
    type: "button",
    class: "dot" + (i === S.current ? " current" : "") + (i in S.answers ? " answered" : ""),
    "aria-label": `Go to question ${i + 1}` + (i in S.answers ? " (answered)" : ""),
    text: String(i + 1),
    onclick: () => { S.current = i; renderExam(); },
  }));

  $("#exam-body").replaceChildren(
    el("div", { class: "exam-head" },
      el("span", { text: S.meta.label }),
      el("span", { text: `Question ${S.current + 1} of ${total} · ${answeredCount} answered` }),
    ),
    el("div", { class: "progress", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": String(total), "aria-valuenow": String(answeredCount) },
      el("span", { style: `width:${(answeredCount / total) * 100}%` }),
    ),
    ...notes.map((n) => el("p", { class: "note", text: n })),
    el("h1", { class: "question", text: q.question }),
    el("div", { class: "options", role: "radiogroup", "aria-label": "Answer options" }, optionButtons),
    el("div", { class: "nav" },
      el("button", {
        type: "button", class: "secondary", text: "Previous",
        disabled: S.current === 0,
        onclick: () => { S.current -= 1; renderExam(); },
      }),
      isLast
        ? el("button", { type: "button", class: "primary", text: "Submit answers", onclick: submitExam })
        : el("button", { type: "button", class: "primary", text: "Next", onclick: () => { S.current += 1; renderExam(); } }),
    ),
    el("div", { class: "dots" }, dots),
  );

  if (focusOption != null && optionButtons[focusOption]) optionButtons[focusOption].focus();
}

function selectAnswer(optionIndex) {
  S.answers[S.current] = optionIndex;
  renderExam(optionIndex);
}

function onKey(event) {
  if (S.busy || $("#view-exam").hidden) return;
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  const tag = (event.target.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea") return;

  const optionCount = (S.questions[S.current].options || []).length;
  let pick = -1;
  if (/^[1-9]$/.test(event.key)) pick = Number(event.key) - 1;
  else if (/^[a-j]$/i.test(event.key)) pick = LETTERS.indexOf(event.key.toUpperCase());

  if (pick >= 0 && pick < optionCount) {
    selectAnswer(pick);
  } else if (event.key === "ArrowRight" && S.current < S.questions.length - 1) {
    S.current += 1;
    renderExam();
  } else if (event.key === "ArrowLeft" && S.current > 0) {
    S.current -= 1;
    renderExam();
  }
}

/* ---------- Submit and results ---------- */

function submitExam() {
  const unanswered = S.questions.length - Object.keys(S.answers).length;
  if (unanswered > 0 &&
      !window.confirm(`${unanswered} question${unanswered === 1 ? " is" : "s are"} unanswered and will count as wrong. Submit anyway?`)) {
    return;
  }

  // The backend expects {"0": 2, "1": 0, ...}; unanswered questions are simply omitted.
  const submitted = {};
  for (const [index, choice] of Object.entries(S.answers)) submitted[String(index)] = choice;

  return guarded("Grading your answers…", async () => {
    const data = await postJSON("/api/submit", {
      source_name: S.source,
      verified_questions: S.questions,
      submitted_answers: submitted,
    });
    S.grading = data.grading_result;
    S.weakTopics = (data.weak_topics || []).map(topicLabel);
    renderResults();
    showView("results");
  });
}

function topicLabel(topic) {
  if (typeof topic === "string") return topic;
  if (topic && typeof topic === "object") return topic.topic || topic.name || topic.label || JSON.stringify(topic);
  return String(topic);
}

function renderResults() {
  const g = S.grading;
  const missed = g.results.filter((r) => !r.is_correct).length;
  const verdict = g.percentage >= 80 ? "Strong result" : g.percentage >= 50 ? "Getting there" : "Needs more practice";

  let weakSection;
  if (S.weakTopics.length > 0) {
    weakSection = el("section", { class: "card" },
      el("h2", { text: "Topics to revisit" }),
      el("ul", { class: "weak-list" }, S.weakTopics.map((t) => el("li", { text: t }))),
      el("button", { type: "button", class: "primary", text: "Practice these topics", onclick: practiceWeak }),
    );
  } else {
    weakSection = el("p", {
      class: "note",
      text: missed === 0 ? "Nothing missed, so there are no weak topics to practice." : "No specific weak topics were identified.",
    });
  }

  $("#results-body").replaceChildren(
    el("div", { class: "score-card" },
      el("div", { class: "score-big", text: `${g.score}/${g.total}` }),
      el("div", { class: "score-sub", text: `${g.percentage}% · ${verdict}` }),
    ),
    weakSection,
    el("h2", { text: "Review" }),
    ...g.results.map(reviewItem),
    el("div", { class: "actions" },
      el("button", { type: "button", class: "secondary", text: "Retake this exam", onclick: () => startExam(S.questions, S.meta) }),
      el("button", { type: "button", class: "secondary", text: "New topic", onclick: () => showView("setup") }),
      el("button", { type: "button", class: "secondary", text: "Different document", onclick: () => { renderRecent(); showView("upload"); } }),
    ),
  );
}

function reviewItem(result, i) {
  const options = (S.questions[i] && S.questions[i].options) || [];

  const rows = options.map((text, j) => {
    const isCorrect = j === result.correct_index;
    const isChosen = j === result.chosen_index;
    const tag = isCorrect ? (isChosen ? "Your answer · correct" : "Correct answer") : isChosen ? "Your answer" : "";
    return el("li", { class: "review-opt" + (isCorrect ? " correct" : "") + (isChosen && !isCorrect ? " wrong" : "") },
      el("span", { class: "letter", text: LETTERS[j] || String(j + 1) }),
      el("span", { class: "opt-text", text }),
      tag ? el("span", { class: "tag", text: tag }) : null,
    );
  });

  return el("details", { class: "review " + (result.is_correct ? "ok" : "bad"), open: !result.is_correct },
    el("summary", {},
      el("span", { class: "badge", text: result.is_correct ? "Correct" : "Incorrect" }),
      el("span", { class: "q-title", text: `${i + 1}. ${result.question}` }),
    ),
    result.chosen_index == null ? el("p", { class: "note", text: "Not answered." }) : null,
    el("ul", { class: "review-opts" }, rows),
    result.explanation
      ? el("p", { class: "explain" }, el("strong", { text: "Why: " }), result.explanation)
      : null,
  );
}

/* ---------- Weak-topic follow-up ---------- */

function practiceWeak() {
  return guarded("Generating new questions on the topics you missed…", async () => {
    const data = await postJSON("/api/followup", {
      source_name: S.source,
      weak_topics: S.weakTopics,
      num_questions: S.numQuestions,
    });
    if (!data.questions || data.questions.length === 0) {
      throw new Error("No follow-up question passed verification. Try again, or pick a new topic.");
    }
    startExam(data.questions, {
      label: "Weak-topic practice",
      rejected: data.rejected_count || 0,
      requested: S.numQuestions,
    });
  });
}

/* ---------- Init ---------- */

function init() {
  const dropzone = $("#dropzone");
  const fileInput = $("#file-input");

  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    fileInput.value = "";
    uploadFile(file);
  });

  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (e) => {
    e.preventDefault();
    dropzone.classList.add("drag");
  }));
  ["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag");
  }));
  dropzone.addEventListener("drop", (e) => uploadFile(e.dataTransfer.files[0]));

  // A file dropped outside the zone would otherwise navigate the tab away to the file.
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => e.preventDefault());

  $("#setup-form").addEventListener("submit", (e) => { e.preventDefault(); generate(); });
  $("#change-doc").addEventListener("click", () => { renderRecent(); showView("upload"); });
  $("#error-close").addEventListener("click", clearError);
  document.addEventListener("keydown", onKey);

  renderRecent();
  showView("upload");
  request("/api/health").catch((err) => showError(err.message));
}

init();