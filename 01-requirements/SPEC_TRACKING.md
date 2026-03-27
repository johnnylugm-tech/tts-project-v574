# SPEC_TRACKING.md - 規格追蹤矩陣

**專案名稱**: 基於 edge-tts 之高品質簡報配音系統  
**版本**: 1.0.0  
**日期**: 2026-03-27

---

## 對照表：PDF 規格書 → 實作追蹤

| # | PDF 規格項目 | 對應 FR 需求 | 實作模組 | 狀態 | 備註 |
|---|-------------|-------------|----------|------|------|
| 1 | edge-tts 語音合成 | FR-01 | AsyncSynthesizer | ⏳ |  |
| 2 | zh-TW-HsiaoHsiaoNeural 音色 | FR-02 | AsyncSynthesizer | ⏳ | 預設音色 |
| 3 | 輸出 MP3 格式 | FR-04 | AudioMerger | ⏳ | 需 ffmpeg |
| 4 | 智能分段（句號） | FR-05 | TextProcessor | ⏳ |  |
| 5 | 智能分段（問號） | FR-05 | TextProcessor | ⏳ |  |
| 6 | 智能分段（驚嘆號） | FR-05 | TextProcessor | ⏳ |  |
| 7 | 根據換行符分段 | FR-06 | TextProcessor | ⏳ |  |
| 8 | 分段長度限制 800 字 | FR-07 | TextProcessor | ⏳ | 可配置 |
| 9 | 最大 20,000 字輸入 | FR-08 | TextProcessor | ⏳ |  |
| 10 | 語速參數調整 | FR-09 | AsyncSynthesizer | ⏳ |  |
| 11 | 音量參數調整 | FR-10 | AsyncSynthesizer | ⏳ |  |
| 12 | **預設語速 -2%** | FR-11 | ConfigManager | ⏳ | **關鍵差異** |
| 13 | 預設音量 +0% | FR-12 | ConfigManager | ⏳ |  |
| 14 | WebSocket 通訊 | FR-13 | AsyncSynthesizer | ⏳ | edge-tts 內建 |
| 15 | 流式音訊回傳 | FR-14 | AsyncSynthesizer | ⏳ |  |
| 16 | asyncio 非同步 | FR-15 | AsyncSynthesizer | ⏳ |  |
| 17 | 錯誤重試 3 次 | FR-16 | ErrorHandler | ⏳ |  |
| 18 | 熔斷器機制 | FR-17 | ErrorHandler | ⏳ |  |
| 19 | 錯誤分類 L1-L4 | FR-18 | ErrorHandler | ⏳ |  |
| 20 | 音訊合併為單一檔案 | FR-19 | AudioMerger | ⏳ | **v557 缺失** |
| 21 | ffmpeg 合併 | FR-20 | AudioMerger | ⏳ |  |

---

## 關鍵參數對照

| 參數 | PDF 規格 | v557 實作 | v574 目標 | 狀態 |
|------|----------|-----------|-----------|------|
| chunk_size | 500-1000 字 | 800 | 800 | ✅ 一致 |
| voice | zh-TW-HsiaoHsiaoNeural | zh-TW-HsiaoHsiaoNeural | zh-TW-HsiaoHsiaoNeural | ✅ 一致 |
| rate | 略慢，適合簡報 | +0% | **-2%** | ⚠️ 需修正 |
| volume | 標準 | +0% | +0% | ✅ 一致 |
| max_text_length | 20,000 字 | 未限制 | 20,000 | ⚠️ 需限制 |

---

## 衝突記錄（Conflict Log）

| 衝突點 | PDF 建議 | 方法論選擇 | 理由 |
|--------|-----------|-----------|------|
| 預設語速 | 「略慢，適合簡報」（描述性）| -2% | SKILL.md 優先，將描述轉為具體參數 |
| 合併功能 | 有提到輸出 MP3 | 需實作 AudioMerger | v557 缺失，v574 需補齊 |

---

## Phase 1 完成檢查

| 檢查項 | 結果 |
|--------|------|
| SRS.md 已建立 | ✅ |
| SPEC_TRACKING.md 已建立 | ✅ |
| PDF 規格完整對照 | ✅ |
| 衝突記錄已建立 | ✅ |

---

*對應 SKILL.md 規範：Phase 1 - SPEC_TRACKING*  
*最後更新: 2026-03-27*