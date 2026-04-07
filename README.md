# tts

統一 TTS（文字轉語音）skill，支援 **Microsoft TTS**（內建）、**Gemini TTS** 與 **MiMo TTS** 三個提供者。

## 功能

- **三提供者**：Microsoft（內建）、Gemini TTS、MiMo TTS
- **多語言**：支援中文、英文等多種語言
- **多音色**：Microsoft 預設聲音、30+ 種 Gemini 聲音、多種 MiMo 音色與風格
- **可設定**：模型、API 端點、聲音皆可透過 `.env` 調整

## 前置需求

- Python 3
- FFmpeg（MiMo TTS 輸出 MP3 時需要）
- API Key：Google AI API（Gemini TTS）或 MiMo API Key
- Microsoft TTS 不需額外設定（OpenClaw 內建）

## 安裝

1. 複製環境變數範本並填入設定：

```bash
cp .env_example .env
```

2. 編輯 `.env`：

```
# Gemini TTS (via Google AI API)
GEMINI_TTS_API_KEY=你的Google AI API Key
GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts
GEMINI_TTS_ENDPOINT=https://generativelanguage.googleapis.com/v1beta

# MiMo TTS (via xiaomimimo.com)
MIMO_TTS_URL=https://token-plan-sgp.xiaomimimo.com/v1/chat/completions
MIMO_TTS_KEY=你的MiMo API Key
MIMO_TTS_MODEL=mimo-v2-tts
```

## 使用方式

### Microsoft TTS（內建，最簡單）

直接呼叫 OpenClaw 內建 `tts` tool，不需任何設定：

```
tts("你好，我是小艾")
```

- 自動發送到聊天視窗
- 不支援存檔、不能選聲音
- 適合快速語音回覆

### Gemini / MiMo TTS（script）

```bash
# 基本用法（Gemini，預設 Zephyr 女聲）
python3 scripts/tts.py "你好，我是小艾"

# 指定提供者和聲音
python3 scripts/tts.py "Hello world" --provider gemini --voice Puck

# MiMo TTS 中文
python3 scripts/tts.py "你好世界" --provider mimo --voice default_zh

# MiMo TTS 帶風格
python3 scripts/tts.py "歡迎收聽今日新聞" --provider mimo --style newscast

# 從檔案讀取文字
python3 scripts/tts.py @article.txt -o article.mp3

# 指定輸出路徑
python3 scripts/tts.py "測試" --output /tmp/test.mp3
```

### 參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `text` | 必填 | 要合成的文字，或 `@檔案路徑` |
| `--provider`, `-p` | `gemini` | 提供者：`gemini` 或 `mimo` |
| `--voice`, `-v` | 各提供者預設 | 聲音名稱（見下方列表） |
| `--style`, `-s` | 無 | 語音風格（MiMo 專用） |
| `--format`, `-f` | `mp3` | 音訊格式：`mp3` 或 `wav` |
| `--output`, `-o` | 自動 | 自訂輸出路徑 |

## 聲音列表

### Gemini TTS 聲音

> ⚠️ 並非所有列舉聲音都支援 TTS。以下標記 ✅ 為已驗證可用，❌ 為回傳 400 不可用，未測試的聲音請自行測試。

#### 女聲（已驗證 14 種可用）

| 聲音 | 狀態 | 適合場景 |
|------|------|----------|
| **Zephyr** | ✅ | 通用、溫柔（預設） |
| **Aoede** | ✅ | 清亮、友善 |
| **Despina** | ✅ | 柔和、舒適 |
| **Erinome** | ✅ | 英式口音 |
| **Algieba** | ✅ | 優雅 |
| **Alnilam** | ✅ | 清晰 |
| **Autonoe** | ✅ | 自然 |
| **Callirrhoe** | ✅ | 柔美 |
| **Gacrux** | ✅ | 成熟 |
| **Laomedeia** | ✅ | 英式 |
| **Leda** | ✅ | 溫暖 |
| **Pulcherrima** | ✅ | 精緻 |
| **Sadachbia** | ✅ | 輕快 |
| **Vindemiatrix** | ✅ | 悠閒 |
| Kore | ❌ | 回傳 400，不支援 TTS |
| Achernar | ❌ | 回傳 400，不支援 TTS |
| Schedar | ❌ | 回傳 400，不支援 TTS |

#### 男聲（未測試）

| 聲音 | 適合場景 |
|------|----------|
| **Puck** | 活潑、年輕 |
| **Charon** | 沉穩、敘事 |
| **Fenrir** | 低沉、有力 |
| **Iapetus** | 中性、清晰 |
| **Enceladus** | 年輕、自然 |
| **Algenib** | 深沉 |
| **Achird** | 溫和 |
| **Orus** | 穩重 |
| **Rasalgethi** | 多變 |
| **Sadaltager** | 可靠 |
| **Sulafar** | 專業 |
| **Umbriel** | 低調 |

#### 中性（未測試）

| 聲音 | 適合場景 |
|------|----------|
| **Zubenelgenubi** | 中性 |

### MiMo TTS 聲音

| 聲音 | 語言 | 說明 |
|------|------|------|
| `default_zh` | 中文 | 預設中文女聲 |
| `default_en` | 英文 | 預設英文女聲 |

### MiMo TTS 風格（`--style` 參數）

| 風格 | 說明 |
|------|------|
| `newscast` | 新聞播報風格 |
| `chat` | 聊天風格 |
| `assistant` | 助理風格 |
| `poem` | 詩歌朗誦 |
| `story` | 故事講述 |

## 輸出

- 預設目錄：`~/.openclaw/workspace/generated_speech/`
- 檔名格式：`<文字關鍵詞>_<YYYYMMDD_HHMMSS>.mp3`
- 檔名自動截斷至 30 字元（英文）

## 提供者比較

| 提供者 | 方式 | 聲音數量 | 中文 | 英文 | 風格控制 | 存檔 | 設定 |
|--------|------|----------|------|------|----------|------|------|
| **microsoft** | 內建 tts tool | 幾種 | ✅ | ✅ | ❌ | ❌ | 不需 |
| **gemini** | script | 30+ | 普通 | 優 | ❌ | ✅ | API key |
| **mimo** | script | 2+ | 優 | 普通 | ✅ | ✅ | API key |

## 技術說明

- **Microsoft TTS**：透過 OpenClaw 內建 `tts` tool，走 Azure Cognitive Services
- **Gemini TTS**：直接呼叫 Google AI API `generateContent` 端點，回傳 raw PCM 音訊
- **MiMo TTS**：呼叫 xiaomimimo.com API，回傳 WAV 格式，腳本自動用 FFmpeg 轉 MP3
- Gemini / MiMo 共用 `.env` 設定，可獨立切換
