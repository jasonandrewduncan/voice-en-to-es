import argparse
import json
import sys
import time
from datetime import datetime, timezone

import numpy as np
import sounddevice as sd
import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoModelForSpeechSeq2Seq,
    AutoProcessor,
    AutoTokenizer,
)

SAMPLE_RATE = 16000
CHANNELS = 1
TRANSLATION_MODEL_ID = "Helsinki-NLP/opus-mt-en-es"


def list_devices() -> None:
    print("\nAvailable Audio Input Devices:\n")
    devices = sd.query_devices()
    default_in = sd.default.device[0]
    for idx, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            marker = " (DEFAULT)" if idx == default_in else ""
            print(
                f"  [{idx}] {dev['name']} "
                f"(in_ch={dev['max_input_channels']}, sr={int(dev['default_samplerate'])}Hz){marker}"
            )
    print()


class Translator:
    """Translates English text to Spanish with a compact PyTorch model."""

    def __init__(self, device: str) -> None:
        print(f"Loading translation model ({TRANSLATION_MODEL_ID}) on {device}...")
        self.device = torch.device(device)
        self.dtype = torch.float16 if device == "cuda" else torch.float32
        self.tokenizer = AutoTokenizer.from_pretrained(TRANSLATION_MODEL_ID)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            TRANSLATION_MODEL_ID,
            dtype=self.dtype,
        )
        self.model.to(self.device)
        self.model.eval()

    def translate(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""
        inputs = {
            key: value.to(self.device)
            for key, value in self.tokenizer(text, return_tensors="pt").items()
        }
        with torch.inference_mode():
            generated_ids = self.model.generate(**inputs, num_beams=3)
        return self.tokenizer.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()


def record_chunk(device: int | None, seconds: float) -> np.ndarray:
    """Record a fixed window of mono 16kHz float32 audio."""
    frames = int(seconds * SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", device=device)
    sd.wait()
    return np.squeeze(audio, axis=-1)


class SpeechRecognizer:
    """Transcribes English speech with a Hugging Face Whisper checkpoint."""

    def __init__(self, model_name: str, device: str) -> None:
        checkpoint = model_name if "/" in model_name else f"openai/whisper-{model_name}"
        self.device = torch.device(device)
        self.dtype = torch.float16 if device == "cuda" else torch.float32
        self.processor = AutoProcessor.from_pretrained(checkpoint)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            checkpoint,
            dtype=self.dtype,
        )
        self.model.to(self.device)
        self.model.eval()
        self.generation_kwargs = {"num_beams": 3}
        if self.model.generation_config.is_multilingual:
            self.generation_kwargs.update(language="en", task="transcribe")

    def transcribe(self, audio: np.ndarray) -> str:
        inputs = self.processor(
            audio,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
        )
        input_features = inputs.input_features.to(self.device, dtype=self.dtype)
        with torch.inference_mode():
            generated_ids = self.model.generate(
                input_features,
                **self.generation_kwargs,
            )
        return self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Live English mic/headset input to Spanish text.")
    parser.add_argument("--list-devices", action="store_true", help="List audio input devices and exit.")
    parser.add_argument("--device", type=int, default=None, help="Input device index (default: system mic).")
    parser.add_argument(
        "--source",
        choices=["mic", "headset"],
        default="mic",
        help="Informational label for input mode ('mic' or 'headset' mono jack).",
    )
    parser.add_argument(
        "--whisper-model",
        default="small.en",
        help="Whisper model size or Hugging Face checkpoint (e.g., tiny.en, base.en, small.en).",
    )
    parser.add_argument(
        "--chunk-seconds",
        type=float,
        default=4.0,
        help="Capture window length in seconds (default: 4.0).",
    )
    parser.add_argument(
        "--output",
        default="transcripts.jsonl",
        help="Path to append JSONL lines (default: transcripts.jsonl).",
    )
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    has_cuda = torch.cuda.is_available()
    device = "cuda" if has_cuda else "cpu"
    compute_type = "float16" if has_cuda else "int8"

    print(f"Source mode: {args.source} | Device index: {args.device if args.device is not None else 'default'}")
    print(f"Loading Whisper ({args.whisper_model}) on {device} [{compute_type}]...")
    asr = SpeechRecognizer(args.whisper_model, device=device)
    translator = Translator(device=device)

    print("\nListening... Press Ctrl+C to stop.\n")

    try:
        while True:
            chunk = record_chunk(args.device, args.chunk_seconds)
            # Quick silence gate using RMS energy so quiet moments don't hallucinate text
            rms = float(np.sqrt(np.mean(np.square(chunk))))
            if rms < 0.008:
                continue

            en_text = asr.transcribe(chunk)
            if not en_text:
                continue

            t0 = time.perf_counter()
            es_text = translator.translate(en_text)
            latency_ms = int((time.perf_counter() - t0) * 1000)

            now_iso = datetime.now(timezone.utc).isoformat()
            print(f"EN: {en_text}")
            print(f"ES: {es_text}  ({latency_ms}ms)\n")

            record = {
                "timestamp": now_iso,
                "source": args.source,
                "en": en_text,
                "es": es_text,
                "translate_ms": latency_ms,
            }
            with open(args.output, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    except KeyboardInterrupt:
        print("\nStopped cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    main()