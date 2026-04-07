---
name: tts-studio
description: "統一 TTS（文字轉語音），支援 Gemini TTS、MiMo TTS 與 Microsoft TTS（內建）。當需要將文字轉為語音、生成語音檔案、朗讀文字時使用。Trigger: TTS, 語音, 讀出來, 說出來, 轉語音, 聲音, 朗讀, text to speech, 合成語音"
---

# TTS — 統一文字轉語音

三個 TTS 提供者，依需求選擇：

| 提供者 | 方式 | 適合場景 |
|--------|------|----------|
| **microsoft** | OpenClaw 內建 `tts` tool | 最方便，不需設定，快速朗讀 |
| **gemini** | script (`scripts/tts.py`) | 30 種聲音，英文為主 |
| **mimo** | script (`scripts/tts.py`) | 中文自然，支援風格控制 |

## Microsoft TTS（內建，最簡單）

直接呼叫 OpenClaw 內建 `tts` tool，不需任何設定：

```
tts("你好，我是小艾")
```

- 自動發送到聊天視窗
- 不支援存檔、不能選聲音
- 適合快速語音回覆

## Gemini / MiMo TTS（script）

### 前置設定

```bash
cp skills/tts-studio/.env_example skills/tts-studio/.env
# 編輯 .env 填入 API keys
```

### 使用方式

```bash
# Gemini TTS（預設 Zephyr 女聲）
python3 skills/tts-studio/scripts/tts.py "你好，我是小艾"

# 指定聲音
python3 skills/tts-studio/scripts/tts.py "Hello world" --provider gemini --voice Puck

# MiMo TTS 中文
python3 skills/tts-studio/scripts/tts.py "你好世界" --provider mimo --voice default_zh

# MiMo TTS 帶風格
python3 skills/tts-studio/scripts/tts.py "歡迎收聽" --provider mimo --style newscast

# 從檔案讀取
python3 skills/tts-studio/scripts/tts.py @article.txt -o article.mp3
```

### 參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `text` | 必填 | 要合成的文字，或 `@檔案路徑` |
| `--provider`, `-p` | `gemini` | 提供者：`gemini` 或 `mimo` |
| `--voice`, `-v` | 各提供者預設 | 聲音名稱 |
| `--style`, `-s` | 無 | 語音風格（MiMo 專用） |
| `--format`, `-f` | `mp3` | 音訊格式：`mp3` 或 `wav` |
| `--output`, `-o` | 自動 | 自訂輸出路徑 |

### 聲音選擇

**Gemini TTS（30 種）**：`Zephyr`（女/溫柔）、`Puck`（男/活潑）、`Charon`（男/沉穩）、`Kore`（女/專業）、`Fenrir`（男/低沉）... 完整列表見 README.md

**MiMo TTS**：`default_zh`（中文女聲）、`default_en`（英文女聲）
- 風格：`newscast`（新聞）、`chat`（聊天）、`story`（故事）、`poem`（詩歌）

### 輸出

- 預設目錄：`~/.openclaw/workspace/generated_speech/`
- 檔名格式：`<文字關鍵詞>_<YYYYMMDD_HHMMSS>.mp3`
