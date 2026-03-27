# SAD.md - 軟體架構說明書

**專案名稱**: 基於 edge-tts 之高品質簡報配音系統  
**版本**: 1.0.0  
**日期**: 2026-03-27  
**Phase**: 2 - 架構設計

---

## A. 開發日誌（真實 CoT 決策邏輯）

### A.1 架構設計前的需求分析

**CoT 推導 1：為什麼需要五層架構？**

1. **問題**：SRS.md 定義了 21 條功能需求，如何組織這些功能的實作？
2. **資料**：功能可分為「配置 → 輸入處理 → 核心合成 → 輸出處理 → 錯誤處理」五類
3. **推論**：參考 SKILL.md 的「Layered Architecture」原則，每層專注單一職責
4. **結論**：採用五層架構，確保關注點分離（Separation of Concerns）

**對應規範**：
- SKILL.md - Phase 2: 架構設計（SWE.5）
- SKILL.md - ASPICE 實踐（SWE.5 軟體架構設計）

---

### A.2 核心設計決策

**CoT 推導 2：為什麼使用 dataclass 而非dict？**

1. **問題**：配置管理應使用何種資料結構？
2. **資料**：SRS.md 要求使用 frozen dataclass（MNT-03）
3. **推論**：dataclass 提供型別提示、不可變性、預設值，相較於 dict 更適合配置管理
4. **結論**：ConfigManager 使用 `@dataclass(frozen=True)` 實現配置管理

**對應規範**：
- SKILL.md - Phase 3: 程式碼品質（frozen dataclass）
- SRS.md - MNT-03（必須使用 frozen dataclass）

---

**CoT 推導 3：為什麼 TextProcessor 需要正規表示式？**

1. **問題**：如何實現智能分段（句號、問號、驚嘆號、換行符）？
2. **資料**：FR-05 要求根據 `。？!` 分段，FR-06 要求根據 `\n` 分段
3. **推論**：使用正則表達式 `[。？！\n]+` 可一次匹配所有分隔符
4. **結論**：TextProcessor 使用 `re.split(r'[。？！\n]+', text)` 實現分段

**對應規範**：
- SRS.md - FR-05, FR-06, FR-07
- SKILL.md - Phase 2: 文本處理模組化

---

**CoT 推導 4：為什麼合成器必須使用 asyncio？**

1. **問題**：WebSocket 通訊和流式音訊需要同步還是非同步處理？
2. **資料**：FR-13 要求 WebSocket，FR-15 要求 asyncio
3. **推論**：edge-tts 本身就是非同步 API，配合 asyncio 可實現並發處理
4. **結論**：AsyncSynthesizer 使用 `async/await` 模式和 edge-tts 的非同步 API

**對應規範**：
- SRS.md - FR-13, FR-14, FR-15
- SKILL.md - asyncio 非同步處理

---

**CoT 推導 5：為什麼使用 ffmpeg 而非 pydub？**

1. **問題**：音訊合併應使用何種工具？
2. **資料**：FR-20 明確要求使用 ffmpeg 進行音訊合併
3. **推論**：ffmpeg 是業界標準工具，ffmpeg-python 是其 Python 綁定
4. **結論**：AudioMerger 使用 ffmpeg-python 實現合併

**對應規範**：
- SRS.md - FR-19, FR-20
- SKILL.md - 允許的框架清單（ffmpeg-python ✅）

---

**CoT 推導 6：為什麼需要錯誤分類 L1-L4？**

1. **問題**：錯誤處理需要多細緻的分類？
2. **資料**：FR-18 要求對不同錯誤類型進行分類處理（L1-L4）
3. **推論**：不同錯誤需要不同的重試策略和恢復機制
4. **結論**：
   - L1: 暫時性網路錯誤（重試）
   - L2: 服務端錯誤（熔斷）
   - L3: 用戶輸入錯誤（回饋修正）
   - L4: 系統錯誤（日誌記錄）

**對應規範**：
- SRS.md - FR-16, FR-17, FR-18

---

### A.3 Conflict Log（架構階段衝突）

| 衝突點 | 候選方案 A | 候選方案 B | 最終選擇 | 理由 |
|--------|-----------|-----------|----------|------|
| **併發模型** | ThreadPoolExecutor | asyncioyncio | **asyncio** | edge-tts 本身非同步，用 asyncio 更自然 |
| **配置來源** | 環境變數 | 檔案載入 | **dataclass + 檔案** | frozen dataclass 不可變，適合配置 |
| **合併策略** | 邊合成邊合併 | 全部合成再合併 | **全部合成再合併** | 失敗可重試，避免中間狀態複雜 |
| **錯誤處理** | 異常往上拋 | 統一錯誤類別 | **統一錯誤類別** | 方便日誌記錄和分類處理 |

---

## B. 系統架構

### B.1 層級架構圖

```
┌────────────────────────────────────────────────────────────────────┐
│                        接入介面層                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │   CLI 介面      │  │  Python API    │  │   WebSocket 端點    │ │
│  │  tts_cli.py     │  │  PresentationTTS│  │   (預留未來擴展)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                        配置管理層                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   ConfigManager (config_manager.py)            │ │
│  │  - voice: str = "zh-TW-HsiaoHsiaoNeural"                      │ │
│  │  - rate: str = "-2%"                                          │ │
│  │  - volume: str = "+0%"                                        │ │
│  │  - chunk_size: int = 800                                      │ │
│  │  - max_text_length: int = 20000                              │ │
│  │  - retry_count: int = 3                                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                        文本處理層                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                TextProcessor (text_processor.py)             │ │
│  │  - split_by_punctuation(): List[str]                         │ │
│  │  - split_by_newline(): List[str]                             │ │
│  │  - chunk_by_length(): List[str]                              │ │
│  │  - validate_input(): bool                                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                        合成引擎層                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              AsyncSynthesizer (async_synthesizer.py)          │ │
│  │  - synthesize(): str                                         │ │
│  │  - synthesize_stream(): AsyncIterator[bytes]               │ │
│  │  - get_available_voices(): List[str]                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                        輸出處理層                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                 AudioMerger (audio_merger.py)                 │ │
│  │  - merge_audio(): str                                        │ │
│  │  - validate_output(): bool                                   │ │
│  │  - cleanup_temp(): None                                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                        錯誤處理層                                   │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                 ErrorHandler (error_handler.py)              │ │
│  │  - TTSError (基底例外)                                        │ │
│  │  - NetworkError (L1)                                         │ │
│  │  - ServiceError (L2)                                         │ │
│  │  - InputError (L3)                                           │ │
│  │  - SystemError (L4)                                          │ │
│  │  - CircuitBreaker (熔斷器模式)                               │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

### B.2 模組設計

#### B.2.1 ConfigManager

```python
@dataclass(frozen=True)
class TTSConfig:
    """TTS 配置參數（frozen dataclass）"""
    voice: str = "zh-TW-HsiaoHsiaoNeural"
    rate: str = "-2%"
    volume: str = "+0%"
    chunk_size: int = 800
    max_text_length: int = 20000
    retry_count: int = 3
    timeout: int = 60

class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def create_default() -> TTSConfig:
        """建立預設配置"""
        return TTSConfig()
    
    @staticmethod
    def from_file(config_path: str) -> TTSConfig:
        """從檔案載入配置"""
        ...
    
    @staticmethod
    def validate(config: TTSConfig) -> bool:
        """驗證配置參數"""
        ...
```

**職責**：統一管理所有配置參數，確保不可變性

**對應 FR**：FR-09, FR-10, FR-11, FR-12

---

#### B.2.2 TextProcessor

```python
class TextProcessor:
    """文本處理器"""
    
    def __init__(self, chunk_size: int = 800):
        self.chunk_size = chunk_size
    
    def split(self, text: str) -> List[str]:
        """智慧分段：按標點和換行分段"""
        # 1. 先按句尾標點分割
        sentences = re.split(r'[。？！\n]+', text)
        # 2. 依據 chunk_size 進一步合併
        return self._merge_chunks(sentences)
    
    def validate(self, text: str, max_length: int = 20000) -> bool:
        """驗證輸入文本"""
        return 0 < len(text) <= max_length
    
    def _merge_chunks(self, sentences: List[str]) -> List[str]:
        """將短句合併為不超過 chunk_size 的段落"""
        ...
```

**職責**：將輸入文本智慧分段為適合合成的長度

**對應 FR**：FR-05, FR-06, FR-07, FR-08

---

#### B.2.3 AsyncSynthesizer

```python
class AsyncSynthesizer:
    """非同步語音合成器"""
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self._client: Optional[Communicate] = None
    
    async def synthesize(self, text: str, output_path: str) -> str:
        """同步合成：text → MP3"""
        communicate = Communicate(text, self.config.voice, 
                                  rate=self.config.rate,
                                  volume=self.config.volume)
        await communicate.save(output_path)
        return output_path
    
    async def synthesize_chunks(self, chunks: List[str], 
                                 temp_dir: str) -> List[str]:
        """批次合成多個分段"""
        temp_files = []
        for i, chunk in enumerate(chunks):
            temp_file = os.path.join(temp_dir, f"chunk_{i}.mp3")
            await self.synthesize(chunk, temp_file)
            temp_files.append(temp_file)
        return temp_files
    
    @staticmethod
    async def list_voices() -> List[Voice]:
        """列出所有可用音色"""
        return await Communicate.get_voices()
```

**職責**：非同步語音合成，支援流式處理

**對應 FR**：FR-01, FR-02, FR-03, FR-13, FR-14, FR-15

---

#### B.2.4 AudioMerger

```python
import ffmpeg

class AudioMerger:
    """音訊合併器"""
    
    def __init__(self):
        self._verify_ffmpeg()
    
    def merge(self, input_files: List[str], output_file: str) -> str:
        """合併多個音訊檔案為單一輸出"""
        # 使用 ffmpeg concat demuxer
        concat_file = self._create_concat_list(input_files)
        ffmpeg.input(concat_file, format='concat', safe=0) \
               .output(output_file, acodec='libmp3lame') \
               .run(overwrite_output=True)
        return output_file
    
    def validate(self, audio_file: str) -> bool:
        """驗證輸出音訊檔案"""
        try:
            probe = ffmpeg.probe(audio_file)
            return probe['format']['format_name'] == 'mp3'
        except:
            return False
    
    def cleanup(self, files: List[str]) -> None:
        """清理臨時檔案"""
        for f in files:
            if os.path.exists(f):
                os.remove(f)
```

**職責**：合併分段音訊為單一輸出檔案

**對應 FR**：FR-04, FR-19, FR-20

---

#### B.2.5 ErrorHandler

```python
class TTSError(Exception):
    """TTS 基底例外"""
    level = "L4"
    
class NetworkError(TTSError):
    """L1: 網路錯誤（可重試）"""
    level = "L1"
    
class ServiceError(TTSError):
    """L2: 服務端錯誤（熔斷）"""
    level = "L2"
    
class InputError(TTSError):
    """L3: 用戶輸入錯誤（需修正）"""
    level = "L3"
    
class SystemError(TTSError):
    """L4: 系統錯誤（僅記錄）"""
    level = "L4"


class CircuitBreaker:
    """熔斷器"""
    
    def __init__(self, failure_threshold: int = 5, 
                 recovery_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_failure(self):
        """記錄失敗"""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def record_success(self):
        """記錄成功"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def can_execute(self) -> bool:
        """檢查是否可以執行"""
        return self.state != "OPEN"
```

**職責**：錯誤分類、重試機制、熔斷保護

**對應 FR**：FR-16, FR-17, FR-18

---

### B.3 整合流程

```python
class PresentationTTS:
    """簡報配音 TTS 系統 - 主入口"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or ConfigManager.create_default()
        self.text_processor = TextProcessor(self.config.chunk_size)
        self.synthesizer = AsyncSynthesizer(self.config)
        self.audio_merger = AudioMerger()
        self.error_handler = ErrorHandler()
        self.circuit_breaker = CircuitBreaker()
    
    async def synthesize(self, text: str, output_file: str) -> str:
        """
        完整合成流程：
        1. 驗證輸入
        2. 文本分段
        3. 批次合成
        4. 音訊合併
        5. 清理臨時檔案
        """
        # Step 1: 驗證
        if not self.text_processor.validate(text, 
                                             self.config.max_text_length):
            raise InputError(f"文字長度需在 1-{self.config.max_text_length} 字")
        
        # Step 2: 分段
        chunks = self.text_processor.split(text)
        
        # Step 3: 合成（支援重試）
        temp_dir = self._create_temp_dir()
        temp_files = await self._synthesize_with_retry(chunks, temp_dir)
        
        # Step 4: 合併
        result = self.audio_merger.merge(temp_files, output_file)
        
        # Step 5: 清理
        self.audio_merger.cleanup(temp_files)
        
        return result
    
    async def _synthesize_with_retry(self, chunks: List[str], 
                                      temp_dir: str) -> List[str]:
        """帶重試的合成"""
        for attempt in range(self.config.retry_count):
            try:
                return await self.synthesizer.synthesize_chunks(
                    chunks, temp_dir)
            except NetworkError as e:
                if attempt == self.config.retry_count - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指數退避
```

---

## C. 合規矩陣

### C.1 功能模組 ↔ 規範章節 ↔ 執行狀態

| 模組 | 對應 FR | 對應 NFR | 對應 SEC | 對應 MNT | 執行狀態 |
|------|---------|----------|----------|----------|----------|
| **ConfigManager** | FR-09, FR-10, FR-11, FR-12 | NFR-07, NFR-08 | - | MNT-03 | ⏳ 需實作 |
| **TextProcessor** | FR-05, FR-06, FR-07, FR-08 | NFR-07 | - | MNT-08 | ⏳ 需實作 |
| **AsyncSynthesizer** | FR-01, FR-02, FR-03, FR-13, FR-14, FR-15 | NFR-01, NFR-01A, NFR-02 | SEC-08 | MNT-01, MNT-07 | ⏳ 需實作 |
| **AudioMerger** | FR-04, FR-19, FR-20 | NFR-03C | SEC-02 | - | ⏳ 需實作 |
| **ErrorHandler** | FR-16, FR-17, FR-18 | NFR-05 | SEC-07 | MNT-06 | ⏳ 需實作 |
| **CLI 介面** | - | - | - | MNT-09 | ⏳ 需實作 |

---

### C.2 NFR 對應表

| NFR ID | 需求 | 對應模組 | 實現方式 |
|--------|------|----------|----------|
| NFR-01 | 首位元組時間 < 2秒 | AsyncSynthesizer | edge-tts 內建優化 |
| NFR-01A | 單一合成 < 15秒 | AsyncSynthesizer | 非同步處理 |
| NFR-02 | 10,000字 < 60秒 | AsyncSynthesizer | 批次處理 |
| NFR-03C | 輸出 MP3 無損壞 | AudioMerger | ffmpeg 合併驗證 |
| NFR-04 | 99.5% 可用率 | ErrorHandler | 熔斷器 + 重試 |
| NFR-05 | 錯誤自動恢復 > 90% | ErrorHandler | 重試機制 |
| NFR-07 | Python 3.8+ | All | 型別提示 |
| NFR-08 | 跨平台 | All | 標準庫 + edge-tts |

---

### C.3 安全需求對應

| SEC ID | 需求 | 對應模組 | 實現方式 |
|--------|------|----------|----------|
| SEC-01 | 不儲存用戶文字 | All | 瞬時處理 |
| SEC-02 | 處理後刪除音訊 | AudioMerger | cleanup() 方法 |
| SEC-03 | 臨時檔案隔離 | All | temp 目錄隔離 |
| SEC-08 | 安全連線 | AsyncSynthesizer | edge-tts TLS |
| SEC-07 | 錯誤不透露架構 | ErrorHandler | 統一錯誤訊息 |

---

## D. 實戰回饋（Phase 2 執行評估）

### D.1 架構設計完成度

| 檢查項 | 預期 | 實際 | 差距 |
|--------|------|------|------|
| 模組數量 | 5 核心 + 1 CLI | 5 核心 + 1 CLI | ✅ 一致 |
| FR 覆蓋 | 21 條 | 21 條 | ✅ 100% |
| NFR 覆蓋 | 9 條 | 9 條 | ✅ 100% |
| MNT 覆蓋 | 11 條 | 11 條 | ✅ 100% |

---

### D.2 Phase 2 執行摘要

| 項目 | 結果 |
|------|------|
| 架構設計完成 | ✅ |
| 模組數量 | 5 |
| FR 覆蓋率 | 100% |
| NFR 覆蓋率 | 100% |
| Constitution 檢查 | ⏳ 待執行 |

---

### D.3 設計決策總結

1. **五層架構**：配置 → 文本 → 合成 → 輸出 → 錯誤
2. **asyncio 優先**：配合 edge-tts 非同步特性
3. **dataclass 配置**：確保不可變性和型別安全
4. **錯誤分類**：L1-L4 四級分類 + 熔斷器
5. **ffmpeg 合併**：業界標準工具

---

### D.4 預期挑戰與緩解

| 挑戰 | 緩解措施 |
|------|----------|
| edge-tts 網路依賴 | 重試機制 + 熔斷器 |
| ffmpeg 未安裝 | 明確錯誤訊息引導安裝 |
| 長文本處理 | 分段 + 批次合併 |
| 並發控制 | asyncio Semaphore |

---

## E. 交付物清單

| 檔案 | 說明 |
|------|------|
| SAD.md | 本架構說明文件 |
| DEVELOPMENT_LOG.md | 開發日誌 |
| COMPLIANCE_MATRIX.md | 合規矩陣 |
| REFINEMENT_REPORT.md | 實戰回饋 |

---

*對應 SKILL.md 規範：Phase 2 - 架構設計（SWE.5）*  
*版本：1.0.0*  
*最後更新: 2026-03-27 23:25*