# Configuration Records - TTS Project v574

## 1. 版本資訊
| 元件 | 版本 | 日期 | 備註 |
|------|------|------|------|
| Core | v574 | 2026-03-27 | 初始發布 |
| AsyncSynthesizer | v1.0 | 2026-03-27 | 非同步合成 |
| TextProcessor | v1.0 | 2026-03-27 | 文本處理 |
| ConfigManager | v1.0 | 2026-03-27 | 配置管理 |
| ErrorHandler | v1.0 | 2026-03-27 | 錯誤處理 |
| AudioMerger | v1.0 | 2026-03-27 | 音訊合併 |

## 2. 環境配置
### 2.1 開發環境
- Python: 3.11+
- 依賴: edge-tts, asyncio (內建)
- 測試框架: pytest

### 2.2 生產環境
- Python: 3.11+
- edge-tts 服務: 線上（需網路）
- ffmpeg: 用於音訊合併

## 3. 依賴管理
| 套件 | 版本 | 用途 |
|------|------|------|
| edge-tts | 最新 | Microsoft TTS 服務 |
| (asyncio) | Python 內建 | 非同步處理 |

## 4. TTS 配置參數
| 參數 | 預設值 | 範圍 | 說明 |
|------|--------|------|------|
| voice | zh-TW-HsiaoHsiaoNeural | zh-*, en-*, ja-*, ko-* | 音色 |
| rate | -2% | -100% ~ +100% | 語速 |
| volume | +0% | -100% ~ +100% | 音量 |
| chunk_size | 800 | 100-10000 | 分段大小 |
| max_text_length | 20000 | 1-100000 | 最大文字長度 |
| retry_count | 3 | 0-10 | 重試次數 |
| timeout | 60 | 1-300 | 超時秒數 |

## 5. 部署記錄
| 日期 | 版本 | 部署環境 | 變更內容 |
|------|------|----------|----------|
| 2026-03-27 | v574 | Development | 初始發布 |

## 6. 配置變更記錄
| 日期 | 變更內容 | 變更者 | 批准人 |
|------|----------|--------|--------|
| 2026-03-27 | 初始配置建立 | Developer Agent | Methodologist |

## 7. 安全配置
- 音色驗證：僅允許特定前綴 (zh-, en-, ja-, ko-)
- 配置不可變：使用 frozen dataclass
- 錯誤訊息：脫敏處理，不透露架構
