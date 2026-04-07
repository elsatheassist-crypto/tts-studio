#!/usr/bin/env python3
"""
tts.py — 統一 TTS 腳本，支援 Gemini TTS 與 MiMo TTS

用法:
    python3 tts.py "要合成的文字" --provider gemini --voice Zephyr
    python3 tts.py "要合成的文字" --provider mimo --voice default_zh
    python3 tts.py @input.txt --provider gemini -o output.mp3

支援的 provider:
    gemini   — Gemini 2.5 Flash Preview TTS (via Google AI API)
    mimo     — MiMo v2 TTS (via xiaomimimo.com)
"""

import argparse
import base64
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, "..", ".env")
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/generated_speech")

# 所有要移除的標點符號（中英文）
PUNCT_PATTERN = re.compile(
    r'[，。！？、；：「」『』（）【】《》〈〉""''…—–\-'
    r'/,\.!?;:\(\)\[\]\{\}\"\'`~@#$%^&*+=<>|\\'
    r'，。！？；：「」（）【】《》…—'
    r'｡｢｣､･　]'
)


def load_env(env_path):
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()


load_env(ENV_FILE)


def clean_text(text: str) -> str:
    """移除所有標點符號，替換為空白，避免 TTS 模型混淆"""
    text = PUNCT_PATTERN.sub(' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def sanitize_filename(text: str, max_total: int = 30) -> str:
    """從文字產生簡短英文檔名"""
    clean = re.sub(r'[^a-zA-Z0-9\s-]', ' ', text)
    words = clean.split()[:4]
    slug = '_'.join(words).lower()
    if len(slug) > max_total - 15:
        slug = slug[:max_total - 15]
    return slug or "speech"


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, bits: int = 16) -> bytes:
    """將 raw PCM 資料加上 WAV 檔頭"""
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    data_size = len(pcm_data)

    header = struct.pack("<4sI4s", b"RIFF", 36 + data_size, b"WAVE")
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, channels, sample_rate, byte_rate, block_align, bits)
    data_header = struct.pack("<4sI", b"data", data_size)

    return header + fmt + data_header + pcm_data


def convert_pcm_to_mp3(pcm_data: bytes, output: str, sample_rate: int = 24000) -> str:
    """將 raw PCM 轉為 MP3"""
    wav_data = pcm_to_wav(pcm_data, sample_rate)
    wav_path = output.replace(".mp3", "_raw.wav")

    with open(wav_path, "wb") as f:
        f.write(wav_data)

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "2", output],
        capture_output=True, timeout=60
    )
    if os.path.exists(wav_path):
        os.remove(wav_path)

    if not os.path.exists(output):
        raise RuntimeError(f"MP3 轉換失敗: {result.stderr.decode('utf-8', errors='replace')[:200]}")

    return os.path.getsize(output)


def generate_gemini(text: str, output: str, voice: str) -> str:
    """Gemini TTS via Google AI API (native generateContent)"""
    api_key = os.environ.get("GEMINI_TTS_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    model = os.environ.get("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    endpoint = os.environ.get("GEMINI_TTS_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta")

    if not api_key:
        raise RuntimeError("請在 .env 檔設定 GEMINI_TTS_API_KEY 或 GEMINI_API_KEY")

    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice}
                }
            }
        }
    }

    data = json.dumps(payload).encode("utf-8")
    from urllib.parse import quote
    url = f"{endpoint}/models/{quote(model, safe='')}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

    print(f"[Gemini TTS] model={model}, voice={voice}, text={len(text)} chars", file=sys.stderr)

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Gemini TTS API 錯誤: {e}")

    candidates = result.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini TTS 回應異常: {json.dumps(result, ensure_ascii=False)[:500]}")

    parts = candidates[0].get("content", {}).get("parts", [])
    audio_data = None
    mime = "audio/L16;codec=pcm;rate=24000"
    for part in parts:
        if "inlineData" in part and "audio" in part["inlineData"].get("mimeType", ""):
            audio_data = part["inlineData"]["data"]
            mime = part["inlineData"].get("mimeType", mime)
            break

    if not audio_data:
        raise RuntimeError(f"Gemini TTS 無音訊資料，收到的 parts: {[list(p.keys()) for p in parts]}")

    pcm_data = base64.b64decode(audio_data)
    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)

    sample_rate = 24000
    if "rate=" in mime:
        try:
            sample_rate = int(mime.split("rate=")[1].split(";")[0])
        except ValueError:
            pass

    print(f"[Gemini TTS] audio format: {mime}, PCM size: {len(pcm_data)} bytes", file=sys.stderr)

    size = convert_pcm_to_mp3(pcm_data, output, sample_rate)
    return output, size


def generate_mimo(text: str, output: str, voice: str, style: str, audio_format: str) -> str:
    """MiMo TTS via xiaomimimo.com API"""
    url = os.environ.get("MIMO_TTS_URL", "https://token-plan-sgp.xiaomimimo.com/v1/chat/completions")
    api_key = os.environ.get("MIMO_TTS_KEY", "")
    model = os.environ.get("MIMO_TTS_MODEL", "mimo-v2-tts")

    content = f"<style>{style}</style>{text}" if style else text

    payload = {
        "model": model,
        "messages": [{"role": "assistant", "content": content}],
        "audio": {"format": audio_format, "voice": voice}
    }

    print(f"[MiMo TTS] model={model}, voice={voice}, style={style or 'default'}, text={len(text)} chars", file=sys.stderr)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        payload_file = f.name

    try:
        result = subprocess.run(
            ["/usr/bin/curl", "-s", url,
             "-H", f"api-key: {api_key}",
             "-H", "Content-Type: application/json",
             "-d", f"@{payload_file}"],
            capture_output=True, text=True, timeout=300
        )
    finally:
        if os.path.exists(payload_file):
            os.unlink(payload_file)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"MiMo TTS 回應非 JSON: {result.stdout[:500]}")

    if "error" in data:
        raise RuntimeError(f"MiMo TTS 錯誤: {json.dumps(data['error'], ensure_ascii=False)}")

    if "choices" not in data:
        raise RuntimeError(f"MiMo TTS 回應異常: {json.dumps(data, ensure_ascii=False)[:500]}")

    msg = data["choices"][0]["message"]
    if "audio" not in msg:
        raise RuntimeError(f"MiMo TTS 無音訊資料: {msg.get('content', '')[:200]}")

    audio_data = base64.b64decode(msg["audio"]["data"])
    os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)

    if output.endswith(".mp3"):
        size = convert_pcm_to_mp3(audio_data, output, sample_rate=16000)
    else:
        with open(output, "wb") as f:
            f.write(audio_data)
        size = len(audio_data)

    return output, size


PROVIDERS = {
    "gemini": generate_gemini,
    "mimo": generate_mimo,
}


def main():
    parser = argparse.ArgumentParser(description="統一 TTS — 支援 Gemini / MiMo")
    parser.add_argument("text", help="要合成的文字，或 @檔案路徑")
    parser.add_argument("--provider", "-p", default="gemini", choices=PROVIDERS.keys(),
                        help="TTS 提供者 (預設: gemini)")
    parser.add_argument("--voice", "-v", default=None, help="聲音選擇")
    parser.add_argument("--style", "-s", default=None, help="語音風格 (MiMo 專用)")
    parser.add_argument("--format", "-f", default="mp3", choices=["mp3", "wav"],
                        help="音訊格式 (預設: mp3)")
    parser.add_argument("--output", "-o", default=None, help="輸出路徑")
    args = parser.parse_args()

    if os.path.isfile(args.text):
        with open(args.text) as f:
            text = f.read()
    elif args.text.startswith("@"):
        with open(args.text[1:]) as f:
            text = f.read()
    else:
        text = args.text

    # 預處理：移除標點符號
    text = clean_text(text)

    if not text.strip():
        print("錯誤：文字為空", file=sys.stderr)
        sys.exit(1)

    if args.voice is None:
        if args.provider == "gemini":
            args.voice = os.environ.get("GEMINI_TTS_VOICE", "Zephyr")
        else:
            args.voice = "default_zh"

    if not args.output:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        slug = sanitize_filename(text)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = os.path.join(DEFAULT_OUTPUT_DIR, f"{slug}_{ts}.mp3")

    func = PROVIDERS[args.provider]
    if args.provider == "mimo":
        path, size = func(text, args.output, args.voice, args.style, args.format)
    else:
        path, size = func(text, args.output, args.voice)

    print(f"✅ 音訊已儲存: {path} ({size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
