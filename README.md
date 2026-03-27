# TTS Project v574 - 高鐵語音訂票系統

## 專案概述
TTS (Text-to-Speech) 語音合成系統，支援中文語音合成與簡報整合。

## 目錄結構
```
tts-project-v574/
├── 01-requirements/     # Phase 1: 需求規格
├── 02-architecture/    # Phase 2: 架構設計
├── 03-implementation/  # Phase 3: 代碼實現
│   ├── async_synthesizer.py  # 非同步語音合成
│   ├── text_processor.py     # 文本處理
│   ├── config_manager.py     # 配置管理
│   ├── error_handler.py      # 錯誤處理
│   ├── audio_merger.py       # 音訊合併
│   └── tests/                # 單元測試
└── docs/               # Phase 5-8 文件
```

## 快速開始
```bash
cd 03-implementation
pip install -r requirements.txt
python -c "from async_synthesizer import AsyncSynthesizer; print('OK')"
```

## 核心模組
- **AsyncSynthesizer**: edge-tts 非同步合成
- **TextProcessor**: 智能文本分段
- **ConfigManager**: frozen dataclass 配置
- **ErrorHandler**: L1-L4 錯誤分類

## 測試
- 單元測試位於 `tests/` 目錄
- 24 個測試案例，全部通過
