# Research - What basic options exist
# Live Church Audio Transcription & Translation

Research notes and a lightweight local prototype (`v0.1`) for capturing live English audio from a church service and delivering real-time translated transcripts alongside a YouTube Live stream.

---

## Research & Architecture Options

Because YouTube Live only supports a **single** live caption track (and its built-in automatic live captions are English-only), supporting other languages requires capturing the audio feed locally before or alongside sending video to YouTube.

### Summary Comparison

| Approach | Cost | Viewer Experience | Best For |
| :--- | :--- | :--- | :--- |
| **1. Burned-In Subtitles (OBS / Browser Overlay)** | Free (LocalVocal) or ~$15–$50/mo | Hardcoded subtitles rendered directly into the video stream | Supporting 1–2 primary languages with zero extra clicks for viewers |
| **2. Companion QR Code & Livestream Link** | Free (Self-Hosted) or ~$29–$50+/mo | Mobile-friendly web page on viewer's phone/browser (text + optional TTS audio) | Supporting **multiple languages simultaneously** for both in-room and remote YouTube viewers |
| **3. External Caption Push to YouTube CC** | Usage-based (~$15–$50+/hr) | Native YouTube Closed Captions (`CC` button) | Replacing YouTube's English CC with a single translated track (or running dual streams) |
| **4. Post-Service Replay Translations (VOD)** | Free | Native YouTube `Settings → Subtitles → Auto-translate` or custom `.srt` | On-demand replay viewers watching archived services later in the week |

---

### Option 1: Burned-In Subtitles via Local Streaming Software
If the church streams through a PC or Mac running **OBS Studio**, **vMix**, or **Ecamm Live**, translated captions can be composited ("burned") directly onto the video picture before it is sent to YouTube.
* **Local AI (Free):** The open-source **LocalVocal** plugin for OBS runs Whisper locally to transcribe and translate audio into an OBS Text Source with zero cloud fees.
* **Cloud Browser Overlays:** Platforms like **Selah Translate**, **Streamlingo**, or **Maestra** provide a transparent Browser Source URL that drops into OBS or ProPresenter as a lower-third overlay.
* **Trade-off:** Every viewer sees the exact same burned-in text. Works well for English + one target language, but becomes cluttered with 3+ languages.

---

### Option 2: Companion QR Code & Livestream Link (Deep Dive)
This architecture decouples translated transcripts from YouTube's single-caption-track limitation. Instead of forcing text onto the video feed, viewers open a lightweight web page via a **QR code** (in the sanctuary) or a **URL** (in the YouTube description and pinned chat) and pick their preferred language.

#### How the Workflow Operates
1. **Clean Audio Capture:** A mono feed from the soundboard (aux/matrix/record out) or streaming computer is routed into the translation engine.
2. **Real-Time Speech-to-Text & Translation:** Speech is transcribed in real time and translated into one or more target languages simultaneously (typically outputting scrolling text, with optional text-to-speech audio for earbuds).
3. **Dual-Audience Delivery:**
   * **Sanctuary Attendees:** Scan a static QR code displayed on screen or in the bulletin to read live captions on their phone—no app install required.
   * **Remote YouTube Viewers:** Open the companion link in a second tab or split-screen mobile browser alongside the YouTube Live player.

#### Key Technical Considerations
* **Static URLs & QR Codes:** Always point the QR code to a persistent church URL rather than generating a new link each week so regular attendees can bookmark it.
* **Handling YouTube Stream Latency:** YouTube Live typically lags **10–20 seconds** behind real life, whereas local/companion transcripts arrive in **1–3 seconds**. For remote viewers, either:
  * Use a platform that supports intentional output delay, or
  * In a self-hosted web viewer, attach UTC timestamps to each JSON caption packet and include a **"Sanctuary (0s) / YouTube (+15s)"** delay toggle in the browser so captions stay synced with the video.
* **Availability & Fallback:** Cloud SaaS tools rely on third-party speech/LLM APIs and internet routing (no 100% uptime guarantee), while self-hosted setups depend on local hardware and church network stability. Keep YouTube's native English auto-captions enabled as an automatic baseline fallback.

#### Turnkey Cloud SaaS Platforms (Companion QR / Link)
* **Streamlingo:** Browser-based live translation across 80+ languages with QR/link sharing, live scrolling transcripts, matched-voice audio output, and OBS/ProPresenter browser overlays. Offers a permanent free metered tier (1 AI language-hour + 10 listener-hours) and paid plans starting around €44/month (billed by AI language-hours and listener-hours).
* **Selah Translate:** Provides QR/link listener pages with live captions and spoken translation across 80+ languages, saved session transcripts, and OBS/vMix/ProPresenter overlays. Includes a 1-hour free trial, a Basic tier (~$29/mo for 20 hours, 1 language at a time), and a Professional tier (~$49/mo for 40 hours, multiple simultaneous languages).

#### Open-Source & Self-Hosted Options (Companion QR / Link)
* **Church Cap (`Church-Cap/Live-Church-Captions`):** MIT-licensed, local-first live captioning app built specifically for churches. Captures sound desk audio, runs Whisper locally, and serves a QR-accessible web viewer over church Wi-Fi alongside OBS/ProPresenter outputs and optional translation.
* **OpenEar (`openearproject.org`):** GNU AGPL v3.0 local-first church captioning project. Streams captions to phones/browsers over local Wi-Fi with zero cloud dependency and supports translating into 200+ languages via Meta's **NLLB-200** model on an NVIDIA GPU.
* **PolyTalk Community Edition (`PolyTalkIO/polytalk`):** Self-hosted FastAPI + Docker Compose stack pairing `faster-whisper` with local or external translation backends for browser-based live translation.
* **Custom Hybrid Relay (Recommended for Mixed Sanctuary + YouTube):** Run `faster-whisper` + `NLLB-200` locally on a CUDA GPU and push lightweight timestamped JSON packets over WebSockets/SSE to a small cloud VPS or Cloudflare Tunnel. This serves unlimited remote YouTube viewers without saturating the church's upload bandwidth while supporting a client-side YouTube sync-delay slider.

---

### Option 3: Pushing a Single Translated Track into YouTube's CC Player
YouTube Live accepts external captions via an **HTTP POST caption ingestion URL** (or embedded CEA-608/708 captions from hardware encoders).
* Services like **StreamText.Net**, **AI-Media (LEXI)**, or **SyncWords** transcribe and translate live audio and push a single target language (e.g., Spanish) directly into YouTube's native `CC` toggle.
* **Trade-off:** YouTube Live still enforces a hard limit of **one** caption track per stream—pushing Spanish disables YouTube's built-in English auto-captions unless you broadcast to two separate YouTube Live events simultaneously via Restream or OBS Multi-RTMP.

---

### Option 4: Post-Service Replay Translations (VOD)
Once a live stream ends and YouTube finishes processing the recording, the single-track restriction is lifted:
* **Built-in Auto-Translate:** Within a few hours, YouTube generates a standard VOD English transcript. Replay viewers can click **Settings (gear icon) → Subtitles/CC → Auto-translate** and choose from 100+ languages for free.
* **Custom Cleaned Transcripts:** In **YouTube Studio → Subtitles**, you can download the auto-generated `.srt` file, translate/correct theological terms and names, and upload dedicated multi-language subtitle tracks (or multi-language dubbed audio tracks if Advanced Features are enabled).


# Live EN -> ES Voice-to-Text Prototype (v0.1)

Minimal local prototype for capturing English speech from a computer microphone or mono headphone/headset input and outputting real-time English + Spanish text.

## Setup

### Windows (PowerShell)

Python 3.10 or newer is required. The setup script checks `py`, `python`, and
`python3`, so a broken Windows Store alias on `PATH` is ignored:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
```

### Linux / WSL

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

## Usage

1. **List available audio input devices** (mic, USB audio, or headset/TRRS jack input):
   ```powershell
   .\run.ps1 --list-devices
   ```

2. **Run with built-in microphone:**
   ```powershell
   .\run.ps1 --source mic
   ```

3. **Run with headphone/headset jack mono input** (replace `2` with your device index from `--list-devices`):
   ```powershell
   .\run.ps1 --source headset --device 2 --chunk-seconds 3.5
   ```

On Linux / WSL, replace `.\run.ps1` with `.venv/bin/python live_en_es.py`.

## Next Steps

### Continuous Processing Pipeline

- Replace fixed blocking recordings with a continuous `sounddevice.InputStream`
  callback so microphone capture continues during model inference.
- Add a bounded, thread-safe audio queue with dropped-frame and queue-depth
  monitoring.
- Add silence/voice-activity detection and overlapping windows so utterances
  are not cut at fixed chunk boundaries.
- Move transcription into a dedicated worker and pass completed English
  utterances to translation through a separate queue.
- Fan translations out to language-specific workers while keeping output
  synchronized with utterance sequence numbers and timestamps.
- Evaluate whether a dedicated model per target language or one multilingual
  model provides the best throughput, accuracy, and memory use.
- Add graceful shutdown, worker health reporting, and backpressure behavior.

### Testing and Performance Analysis

- Record baseline processing time, peak RAM, GPU/CPU utilization, disk usage,
  queue depth, and output latency for representative audio.
- Measure capture, Whisper, translation, and total end-to-end latency separately.
- Compare `tiny.en`, `base.en`, and `small.en` for speed, resource use, and
  transcription quality.
- Test CPU versus CUDA execution where available.
- Test utterances crossing chunk boundaries, pauses, background music,
  multiple speakers, accents, and theological terminology.
- Measure whether processing keeps pace with real time; target processing time
  below audio duration for sustained streaming.
- Benchmark one, then multiple, target languages to determine concurrency and
  memory limits before adding a browser/streaming output layer.

## Notes
- First run downloads Whisper (`small.en`) and the compact `Helsinki-NLP/opus-mt-en-es` translation model.
- Output is printed to the terminal and appended to `transcripts.jsonl`.