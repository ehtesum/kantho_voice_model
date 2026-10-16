const API = "";

// ── Tabs ──────────────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function setStatus(el, message, type = "") {
  el.textContent = message;
  el.className = "status";
  if (type) el.classList.add(type);
  el.classList.remove("hidden");
}

function showEl(el) { el.classList.remove("hidden"); }
function hideEl(el) { el.classList.add("hidden"); }

// ── Reference status ──────────────────────────────────────────────────────────
const referenceWarning = document.getElementById("reference-warning");
const referenceStatusDisplay = document.getElementById("reference-status-display");

async function checkReferenceStatus() {
  try {
    const res = await fetch(`${API}/api/reference-status`);
    const data = await res.json();
    if (data.has_reference) {
      hideEl(referenceWarning);
      referenceStatusDisplay.textContent = `✓ Reference clip: ${data.files.join(", ")}`;
      referenceStatusDisplay.className = "status-display ok";
    } else {
      showEl(referenceWarning);
      referenceStatusDisplay.textContent = "No reference clip uploaded yet.";
      referenceStatusDisplay.className = "status-display missing";
    }
  } catch {
    referenceStatusDisplay.textContent = "Could not check status.";
  }
}

document.getElementById("btn-refresh-reference").addEventListener("click", checkReferenceStatus);
checkReferenceStatus();

// ── Upload reference ───────────────────────────────────────────────────────────
document.getElementById("file-reference").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  referenceStatusDisplay.textContent = "Uploading...";
  referenceStatusDisplay.className = "status-display";
  try {
    const res = await fetch(`${API}/api/upload-reference`, { method: "POST", body: fd });
    const data = await res.json();
    if (res.ok) {
      referenceStatusDisplay.textContent = `✓ ${data.message}`;
      referenceStatusDisplay.className = "status-display ok";
      checkReferenceStatus();
    } else {
      referenceStatusDisplay.textContent = `Error: ${data.detail}`;
      referenceStatusDisplay.className = "status-display missing";
    }
  } catch {
    referenceStatusDisplay.textContent = "Upload failed.";
    referenceStatusDisplay.className = "status-display missing";
  }
});

// ── Upload recordings (multiple) ───────────────────────────────────────────────
const recordingsStatus = document.getElementById("recordings-upload-status");

document.getElementById("file-recordings").addEventListener("change", async (e) => {
  const files = Array.from(e.target.files);
  if (!files.length) return;
  setStatus(recordingsStatus, `Uploading ${files.length} file(s)...`);
  showEl(recordingsStatus);

  let uploaded = 0;
  for (const file of files) {
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${API}/api/upload-recording`, { method: "POST", body: fd });
      if (res.ok) uploaded++;
    } catch {}
  }
  setStatus(recordingsStatus, `✓ Uploaded ${uploaded}/${files.length} files.`, "success");
});

// ── Auto-transcribe ────────────────────────────────────────────────────────────
const transcribeStatus = document.getElementById("transcribe-status");
const btnTranscribe = document.getElementById("btn-transcribe");

btnTranscribe.addEventListener("click", async () => {
  btnTranscribe.disabled = true;
  setStatus(transcribeStatus, "Transcribing with Whisper... this may take a few minutes.");
  showEl(transcribeStatus);

  try {
    const res = await fetch(`${API}/api/transcribe`, { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      setStatus(transcribeStatus, `✓ Transcribed ${data.transcribed} file(s).`, "success");
    } else {
      setStatus(transcribeStatus, `Error: ${data.detail}`, "error");
    }
  } catch (err) {
    setStatus(transcribeStatus, `Request failed: ${err}`, "error");
  } finally {
    btnTranscribe.disabled = false;
  }
});

// ── Load transcripts ───────────────────────────────────────────────────────────
document.getElementById("btn-load-transcripts").addEventListener("click", async () => {
  const list = document.getElementById("transcripts-list");
  list.innerHTML = "<p style='color:#888;font-size:.88rem'>Loading...</p>";
  try {
    const res = await fetch(`${API}/api/transcripts`);
    const data = await res.json();
    if (!data.transcripts.length) {
      list.innerHTML = "<p style='color:#888;font-size:.88rem'>No transcripts yet. Upload recordings and click Auto-Transcribe.</p>";
      return;
    }
    list.innerHTML = data.transcripts.map(t => `
      <div class="transcript-item">
        <div class="t-file">${t.file}</div>
        <div class="t-text">${t.text || "<em>empty</em>"}</div>
      </div>
    `).join("");
  } catch {
    list.innerHTML = "<p style='color:#fca5a5;font-size:.88rem'>Failed to load.</p>";
  }
});

// ── Live transliteration preview ───────────────────────────────────────────────
const inputText = document.getElementById("input-text");
const preview = document.getElementById("transliteration-preview");
const previewBengali = document.getElementById("preview-bengali");

let previewTimeout;
inputText.addEventListener("input", () => {
  clearTimeout(previewTimeout);
  const val = inputText.value.trim();
  if (!val) { hideEl(preview); return; }
  previewTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`${API}/api/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "__preview__" + val }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.bengali_text) {
          previewBengali.textContent = data.bengali_text;
          showEl(preview);
        }
      }
    } catch {}
  }, 600);
});

// ── Generate voice note ────────────────────────────────────────────────────────
const btnGenerate = document.getElementById("btn-generate");
const generateStatus = document.getElementById("generate-status");
const audioResult = document.getElementById("audio-result");
const audioPlayer = document.getElementById("audio-player");
const downloadLink = document.getElementById("download-link");
const historyDiv = document.getElementById("history");
const historyList = document.getElementById("history-list");

const history = [];

btnGenerate.addEventListener("click", async () => {
  const text = inputText.value.trim();
  if (!text) return;

  btnGenerate.disabled = true;
  hideEl(audioResult);
  setStatus(generateStatus, "Generating... (first run loads the model, ~30s)");
  showEl(generateStatus);

  try {
    const res = await fetch(`${API}/api/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus(generateStatus, `Error: ${data.detail}`, "error");
      return;
    }

    setStatus(generateStatus, `✓ Done — Bengali: ${data.bengali_text}`, "success");

    const audioUrl = `${API}${data.audio_url}`;
    audioPlayer.src = audioUrl;
    downloadLink.href = audioUrl;
    downloadLink.download = data.filename;
    showEl(audioResult);
    audioPlayer.play();

    if (data.was_transliterated) {
      previewBengali.textContent = data.bengali_text;
      showEl(preview);
    }

    history.unshift({ text: data.original_text, bengali: data.bengali_text, url: audioUrl, file: data.filename });
    if (history.length > 10) history.pop();
    renderHistory();

  } catch (err) {
    setStatus(generateStatus, `Request failed: ${err}`, "error");
  } finally {
    btnGenerate.disabled = false;
  }
});

function renderHistory() {
  if (!history.length) return;
  showEl(historyDiv);
  historyList.innerHTML = history.map(h => `
    <li>
      <span>${h.bengali || h.text}</span>
      <a href="${h.url}" download="${h.file}">↓ wav</a>
    </li>
  `).join("");
}

// Enter key submits
inputText.addEventListener("keydown", e => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) btnGenerate.click();
});
