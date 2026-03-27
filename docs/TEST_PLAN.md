# TEST_PLAN.md - 測試計畫

**專案名稱**: 基於 edge-tts 之高品質簡報配音系統  
**版本**: 1.0.0  
**日期**: 2026-03-27  
**Phase**: 3 - 程式碼實現

---

## 1. 測試策略

### 1.1 測試金字塔

```
        /\
       /  \      整合測試 (Integration Tests)
      /____\     5% - 驗證模組間協作
     /      \
    /        \   單元測試 (Unit Tests)  
   /__________\  95% - 每個模組獨立測試
```

### 1.2 測試覆蓋率目標

| 層級 | 目標覆蓋率 | 說明 |
|------|-----------|------|
| 單元測試 | > 90% | 所有核心模組 |
| 整合測試 | > 80% | 端到端流程 |
| 總體覆蓋 | > 85% | 所有程式碼 |

---

## 2. 測試類型

### 2.1 單元測試 (Unit Tests)

| 模組 | 測試檔案 | 覆蓋內容 |
|------|----------|----------|
| ConfigManager | test_config_manager.py | 建立、驗證、合併配置 |
| TextProcessor | test_text_processor.py | 分段、驗證、邊界處理 |
| AsyncSynthesizer | test_async_synthesizer.py | 合成、流式、驗證音色 |
| AudioMerger | test_audio_merger.py | 合併、驗證、清理 |
| ErrorHandler | test_error_handler.py | 錯誤分類、熔斷器、重試 |

### 2.2 整合測試 (Integration Tests)

| 測試場景 | 描述 |
|----------|------|
| 完整合成流程 | 文字 → 分段 → 合成 → 合併 → 輸出 |
| 批次處理 | 多個文本同時處理 |
| 錯誤復原 | 網路錯誤重試、熔斷器恢復 |

---

## 3. 測試環境

### 3.1 依賴

```
edge-tts>=6.1.0
ffmpeg-python>=0.2.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

### 3.2 測試資料

- **輸入文本**: 中文簡報文字（500-10000 字）
- **預設音色**: zh-TW-HsiaoHsiaoNeural
- **輸出格式**: MP3

---

## 4. 執行方式

### 4.1 執行所有測試

```bash
cd /workspace/tts-project-v574/03-implementation
pytest tests/ -v
```

### 4.2 執行單一模組測試

```bash
pytest tests/test_config_manager.py -v
```

### 4.3 產生覆蓋率報告

```bash
pytest tests/ --cov=. --cov-report=html
```

---

## 5. 驗收標準

| 標準 | 目標 | 實際 |
|------|------|------|
| 單元測試數量 | > 50 | ⏳ |
| 覆蓋率 | > 90% | ⏳ |
| 通過率 | 100% | ⏳ |
| 錯誤處理覆蓋 | 100% | ⏳ |

---

*對應 SKILL.md 規範：Phase 3 - 測試計畫（SWE.7）*