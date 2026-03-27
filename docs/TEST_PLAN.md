# TEST_PLAN.md - 測試計畫

**專案名稱**: 基於 edge-tts 之高品質簡報配音系統  
**版本**: 1.0.0  
**日期**: 2026-03-28  
**Phase**: 3 - 程式碼實現

> **Coverage Target: 90%** - 總體覆蓋率目標 90%

---

## 1. 測試策略

### 1.1 測試金字塔

```
        /\
       /  \      整合測試 (Integration Tests) - 20%
      /____\     驗證模組間協作
     /      \
    /        \   單元測試 (Unit Tests) - 70%
   /__________\  每個模組獨立測試
        /\
       /  \      E2E Tests - 10%
      /____\     端到端驗證
```

測試金字塔比例：**單元測試 70% | 整合測試 20% | E2E 10%**

### 1.2 測試覆蓋率目標

**目標覆蓋率**: 90%

| 層級 | 目標覆蓋率 | 說明 |
|------|-----------|------|
| 單元測試 | 90% | 所有核心模組 |
| 整合測試 | 80% | 端到端流程 |
| 總體覆蓋 | 90% | 所有程式碼 |
| 分支覆蓋 | 80% | 關鍵邏輯分支 |

---

## 2. 測試類型

### 2.1 單元測試 (Unit Tests) - 70%

| 模組 | 測試檔案 | 覆蓋內容 |
|------|----------|----------|
| ConfigManager | test_config_manager.py | 建立、驗證、合併配置 |
| TextProcessor | test_text_processor.py | 分段、驗證、邊界處理 |
| AsyncSynthesizer | test_async_synthesizer.py | 合成、流式、驗證音色 |
| AudioMerger | test_audio_merger.py | 合併、驗證、清理 |
| ErrorHandler | test_error_handler.py | 錯誤分類、熔斷器、重試 |

### 2.2 整合測試 (Integration Tests) - 20%

| 測試場景 | 描述 |
|----------|------|
| 完整合成流程 | 文字 → 分段 → 合成 → 合併 → 輸出 |
| 批次處理 | 多個文本同時處理 |
| 錯誤復原 | 網路錯誤重試、熔斷器恢復 |

### 2.3 E2E 測試 (End-to-End) - 10%

| 測試場景 | 描述 |
|----------|------|
| 完整工作流 | 從配置加載到最終 MP3 輸出 |
| 音色切換 | 不同音色間的正確切換 |
| 長文本處理 | 10000 字以上文本處理 |

---

## 3. 關鍵路徑測試 (Critical Path)

### 3.1 核心功能覆蓋

| 優先級 | 功能 | 測試策略 |
|--------|------|----------|
| P0 | 文字轉語音合成 | 完整流程測試 |
| P0 | 音訊合併輸出 | 合併正確性驗證 |
| P1 | 錯誤處理與重試 | 網路異常復原 |
| P1 | 音色驗證 | 音色列表獲取 |
| P2 | 設定管理 | 配置載入與驗證 |

### 3.2 回歸測試 (Regression Tests)

**目的**: 確保新變更不破壞現有功能

| 測試案例 | 描述 |
|----------|------|
| test_config_load_default | 預設配置正確載入 |
| test_text_split_large | 大文本正確分段 |
| test_audio_merge_order | 音訊順序正確合併 |
| test_error_retry_network | 網路錯誤正確重試 |
| test_voice_validate_valid | 有效音色通過驗證 |

### 3.3 冒煙測試 (Smoke Tests)

**目的**: 快速驗證核心功能可用

| 測試案例 | 描述 |
|----------|------|
| test_basic_synthesize | 基本合成功能可用 |
| test_config_init | 配置初始化成功 |
| test_audio_merge_output | 合併輸出成功 |
| test_error_handler_init | 錯誤處理器正常運作 |

---

## 4. 測試環境

### 4.1 依賴

```
edge-tts>=6.1.0
ffmpeg-python>=0.2.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

### 4.2 測試資料

- **輸入文本**: 中文簡報文字（500-10000 字）
- **預設音色**: zh-TW-HsiaoHsiaoNeural
- **輸出格式**: MP3

---

## 5. 執行方式

### 5.1 執行所有測試

```bash
cd /workspace/tts-project-v574/03-implementation
pytest tests/ -v
```

### 5.2 執行單一模組測試

```bash
pytest tests/test_config_manager.py -v
```

### 5.3 產生覆蓋率報告

```bash
pytest tests/ --cov=. --cov-report=html
```

---

## 6. 驗收標準

| 標準 | 目標 |
|------|------|
| 單元測試數量 | > 50 |
| 覆蓋率 | ≥90% |
| 通過率 | 100% |
| 錯誤處理覆蓋 | 100% |

---

*對應 SKILL.md 規範：Phase 3 - 測試計畫（SWE.7）*