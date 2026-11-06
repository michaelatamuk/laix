const STORAGE_KEY = "laix-user-study-v1";
const app = {
  payload: null,
  participantId: "",
  trials: [],
  responses: [],
  index: 0,
};

const elements = {
  intro: document.getElementById("intro"),
  trial: document.getElementById("trial"),
  done: document.getElementById("done"),
  start: document.getElementById("start"),
  next: document.getElementById("next"),
  download: document.getElementById("download"),
  progress: document.getElementById("progress"),
  situation: document.getElementById("situation"),
  options: document.getElementById("options"),
  recommendationLabel: document.getElementById("recommendation-label"),
  recommendationText: document.getElementById("recommendation-text"),
  choices: document.getElementById("choices"),
  timeliness: document.getElementById("timeliness"),
  timelinessOut: document.getElementById("timeliness-out"),
  trust: document.getElementById("trust"),
  trustOut: document.getElementById("trust-out"),
  workload: document.getElementById("workload"),
  workloadOut: document.getElementById("workload-out"),
  error: document.getElementById("error"),
  summary: document.getElementById("summary"),
  preview: document.getElementById("preview"),
};

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const other = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[other]] = [copy[other], copy[index]];
  }
  return copy;
}

function randomId() {
  if (globalThis.crypto?.randomUUID) return `p-${crypto.randomUUID()}`;
  return `p-${Date.now()}-${Math.floor(Math.random() * 1e9)}`;
}

function buildTrials(vignettes) {
  const trials = [];
  for (const vignette of shuffle(vignettes)) {
    const conditions = shuffle(["laix", "baseline"]);
    const labels = shuffle(["A", "B"]);
    for (const [position, condition] of conditions.entries()) {
      trials.push({
        vignette,
        condition,
        label: labels[position],
        recommendation: vignette[`${condition}_choice`],
      });
    }
  }
  return trials;
}

function save() {
  const state = {
    participantId: app.participantId,
    trials: app.trials,
    responses: app.responses,
    index: app.index,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function restore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return false;
    const state = JSON.parse(raw);
    if (!state.participantId || !Array.isArray(state.trials)) return false;
    app.participantId = state.participantId;
    app.trials = state.trials;
    app.responses = state.responses ?? [];
    app.index = state.index ?? 0;
    return true;
  } catch {
    return false;
  }
}

function optionLabel(vignette, optionId) {
  return vignette.options.find((option) => option.id === optionId)?.label ?? optionId;
}

function showOnly(section) {
  for (const item of [elements.intro, elements.trial, elements.done]) {
    item.classList.toggle("hidden", item !== section);
  }
}

function showTrial() {
  const trial = app.trials[app.index];
  if (!trial) {
    finish();
    return;
  }
  const { vignette, label, recommendation } = trial;
  elements.progress.textContent = `Scenario ${app.index + 1} of ${app.trials.length}`;
  elements.situation.textContent = vignette.situation;
  elements.options.innerHTML = "";
  for (const option of vignette.options) {
    const item = document.createElement("li");
    item.textContent = option.label;
    elements.options.appendChild(item);
  }
  elements.recommendationLabel.textContent = label;
  elements.recommendationText.textContent = optionLabel(vignette, recommendation);
  elements.choices.innerHTML = "";
  for (const option of vignette.options) {
    const wrapper = document.createElement("label");
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "choice";
    input.value = option.id;
    wrapper.appendChild(input);
    wrapper.appendChild(document.createTextNode(` ${option.label}`));
    elements.choices.appendChild(wrapper);
  }
  elements.error.textContent = "";
  elements.trial.classList.remove("hidden");
  elements.done.classList.add("hidden");
  elements.intro.classList.add("hidden");
  window.scrollTo(0, 0);
}

function readChoice() {
  const input = document.querySelector('input[name="choice"]:checked');
  return input ? input.value : null;
}

function currentResponse(choice) {
  const trial = app.trials[app.index];
  return {
    participant_id: app.participantId,
    vignette_id: trial.vignette.id,
    condition: trial.condition,
    recommendation: trial.recommendation,
    choice,
    timeliness: Number(elements.timeliness.value),
    trust: Number(elements.trust.value),
    workload: Number(elements.workload.value),
  };
}

function finish() {
  showOnly(elements.done);
  elements.summary.textContent = `${app.responses.length} trials recorded for ${app.participantId}.`;
  elements.preview.textContent = app.responses.map((item) => JSON.stringify(item)).join("\n");
}

function download() {
  const text = app.responses.map((item) => JSON.stringify(item)).join("\n") + "\n";
  const blob = new Blob([text], { type: "application/x-ndjson" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `user-study-results-${app.participantId}.jsonl`;
  link.click();
  URL.revokeObjectURL(url);
}

async function start() {
  if (!app.payload) {
    const response = await fetch("../vignettes.json");
    if (!response.ok) throw new Error("Could not load vignettes.json");
    app.payload = await response.json();
  }
  if (!restore()) {
    app.participantId = randomId();
    app.trials = buildTrials(app.payload.vignettes);
    app.responses = [];
    app.index = 0;
    save();
  }
  showTrial();
}

function next() {
  const choice = readChoice();
  if (!choice) {
    elements.error.textContent = "Choose an action before continuing.";
    return;
  }
  app.responses.push(currentResponse(choice));
  app.index += 1;
  save();
  if (app.index >= app.trials.length) {
    finish();
  } else {
    showTrial();
  }
}

for (const [input, output] of [
  [elements.timeliness, elements.timelinessOut],
  [elements.trust, elements.trustOut],
  [elements.workload, elements.workloadOut],
]) {
  input.addEventListener("input", () => {
    output.textContent = input.value;
  });
}

elements.start.addEventListener("click", () => {
  start().catch((error) => {
    elements.error.textContent = error.message;
  });
});
elements.next.addEventListener("click", next);
elements.download.addEventListener("click", download);
