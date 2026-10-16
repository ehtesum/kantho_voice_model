# 🎙️ Kantho (কণ্ঠ) — Bengali Voice Cloner & TTS Generator

## 💡 What is this in simple words?

Have you ever wanted an AI that speaks in **your own voice**?

**Kantho** is a Bengali speech generator with voice cloning:
1. You provide a short audio clip of your voice (or anyone's voice).
2. You type what you want the AI to say:
   - You can type in **Banglish** (English letters, like *"ami bhalo achi"* or *"kemon acho"*).
   - Or you can type in **Bengali script** (*"আমি ভালো আছি"*).
3. Kantho automatically converts Banglish into Bengali script, runs it through an AI voice synthesizer (Coqui XTTS v2), and **outputs a `.wav` audio file speaking your words in your cloned voice**!

---

## 📁 What does each file & folder do?

| File / Folder | What it actually does |
| :--- | :--- |
| **`backend/main.py`** | **The server!** A FastAPI web server that handles requests from the browser, receives text, triggers voice generation, and sends back audio. |
| **`backend/tts.py`** | The voice generation engine. Uses the Coqui XTTS v2 neural network to clone voice characteristics from your reference clip and generate new speech. |
| **`backend/transliterate.py`** | Translates romanized Banglish (*"bhalo"* -> *"ভালো"*) into proper Bengali Unicode characters. |
| **`backend/transcribe.py`** | Uses OpenAI Whisper to listen to audio clips and transcribe them into written Bengali text. |
| **`frontend/`** | The web user interface (`index.html`, `app.js`, `style.css`) where you type your text, preview your voice sample, and click "Generate". |
| **`data/reference/`** | Where you drop your reference voice audio file (`.wav`) so the model knows what voice to clone. |
| **`output/`** | Where generated voice files are saved. |
| **`scripts/download_models.py`** | Automatically downloads necessary AI models onto your machine. |
| **`start.sh` / `start.bat`** | Quick launch script to boot the web application. |

---

## 🔄 How the Pipeline Works

```
You type "kemon acho" (Banglish)
         ↓
Transliterator turns it into "কেমন আছো" (Bengali script)
         ↓
XTTS v2 matches your voice clip from data/reference/
         ↓
Out comes a clean .wav audio of YOU saying "কেমন আছো"!
```

---

## 🚀 How to Run It (Step-by-Step)

### Step 1: Open PowerShell
```powershell
cd c:\Users\user\Desktop\projects\kantho_voice_model
```

### Step 2: Activate your Virtual Environment
```powershell
.venv\Scripts\activate
```
*(If dependencies aren't installed yet: `pip install -r requirements.txt`)*

### Step 3: Put your voice sample in place
Drop a clear 10–30 second recording of the speaker's voice into:  
`data/reference/reference.wav`

### Step 4: Start the Server
```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Step 5: Open your browser
Go to: 👉 **[http://localhost:8000](http://localhost:8000)**

Type a sentence, choose your voice clip, and hit **Generate Audio**!

---

## Technical Limitations

- **Reference Audio Quality Sensitivity**: Zero-shot voice conditioning vectors encode ambient background acoustics, reverberation, and microphone distortion present in the source `reference.wav`.
- **Complex Conjunct Phonemization**: Transliteration of colloquial Banglish into Bengali script can occasionally misparse rare or ambiguous conjunct ligatures (*যুক্তবর্ণ*), requiring manual Unicode correction.
- **VRAM Footprint & RTF**: Coqui XTTS v2 requires ~4 GB of GPU memory for comfortable real-time factor (RTF < 0.5x); executing purely on CPU increases RTF to 2.5–3.5x.

---

## Future Roadmap

- [ ] **Custom Bengali Vocoder Fine-Tuning**: Adapt a HiFi-GAN vocoder specifically on native Bengali speech corpuses to eliminate breathiness and high-frequency sibilance artifacts.
- [ ] **Rule-Based IPA Grapheme-to-Phoneme (G2P)**: Replace heuristic string transliteration with a formalized International Phonetic Alphabet (IPA) conversion table.
- [ ] **Streaming Low-Latency Audio Synthesis**: Implement chunked token streaming to achieve sub-400 ms Time-To-First-Audio (TTFA).
- [ ] **Multi-Clip Speaker Embedding Fusion**: Support multi-sample reference ingestion to average out acoustic imperfections and room reverberation.

