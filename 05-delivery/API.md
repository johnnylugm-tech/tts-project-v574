# API.md - TTS Project v574 開發者 API 參考

---

## 1. 核心類別

### 1.1 PresentationTTS

簡報配音 TTS 系統主入口，協調所有模組提供完整 TTS 流程。

```python
from presentation_tts import PresentationTTS
```

#### 建構函式

```python
def __init__(self, config: Optional[TTSConfig] = None)
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| config | TTSConfig | 組態物件（可選，預設使用建立預設配置） |

**引發異常:**
- `InputError` - 配置參數無效

#### 方法

##### synthesize()

完整合成流程：text → MP3

```python
async def synthesize(self, text: str, output_file: str,
                    voice: Optional[str] = None) -> str
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| text | str | 要合成的文字 |
| output_file | str | 輸出 MP3 檔案路徑 |
| voice | str | 音色名稱（可選） |

**回傳:** `str` - 輸出的 MP3 檔案路徑

**引發異常:**
- `InputError` - 文字長度不符
- `NetworkError` - 網路錯誤
- `ServiceError` - 服務錯誤
- `TTSError` - 一般 TTS 錯誤

---

##### synthesize_stream()

流式合成，返回音訊位元組

```python
async def synthesize_stream(self, text: str,
                           voice: Optional[str] = None) -> bytes
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| text | str | 要合成的文字 |
| voice | str | 音色名稱（可選） |

**回傳:** `bytes` - 音訊資料

---

##### synthesize_batch()

批次合成多個文本

```python
async def synthesize_batch(self, texts: List[str], output_dir: str,
                         voice: Optional[str] = None) -> List[str]
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| texts | List[str] | 要合成的文字清單 |
| output_dir | str | 輸出目錄 |
| voice | str | 音色名稱（可選） |

**回傳:** `List[str]` - 輸出檔案路徑清單（失敗時回傳錯誤訊息）

---

##### get_text_info()

取得文本資訊

```python
def get_text_info(self, text: str) -> Dict
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| text | str | 要分析的文本 |

**回傳:** `Dict` - 包含字數、行數、分段數等資訊

---

##### get_available_voices()

取得所有可用中文音色

```python
async def get_available_voices(self) -> List[str]
```

**回傳:** `List[str]` - 音色名稱清單

---

##### list_all_voices()

列出所有可用音色（靜態方法）

```python
@staticmethod
async def list_all_voices() -> List[dict]
```

**回傳:** `List[dict]` - 音色詳細資訊，包含 name, locale, gender, short_name

---

##### from_file()

從檔案建立實例（類別方法）

```python
@classmethod
def from_file(cls, config_path: str) -> 'PresentationTTS'
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| config_path | str | 組態檔案路徑（JSON） |

**回傳:** `PresentationTTS` - 新實例

---

---

### 1.2 TTSConfig

Frozen dataclass 組態類別

```python
from config_manager import TTSConfig
```

#### 屬性

| 屬性 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| voice | str | "zh-TW-HsiaoHsiaoNeural" | 音色名稱 |
| rate | str | "-2%" | 語速調整 |
| volume | str | "+0%" | 音量調整 |
| chunk_size | int | 500 | 文本分段大小 |
| max_text_length | int | 10000 | 最大輸入字數 |
| retry_count | int | 3 | 重試次數 |
| timeout | int | 30 | 請求超時（秒） |

---

### 1.3 ConfigManager

配置管理器

```python
from config_manager import ConfigManager, TTSConfig
```

#### 靜態方法

##### create_default()

```python
@staticmethod
def create_default() -> TTSConfig
```

建立預設配置

---

##### from_file()

```python
@staticmethod
def from_file(path: str) -> TTSConfig
```

從 JSON 檔案載入配置

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| path | str | JSON 檔案路徑 |

---

##### validate()

```python
@staticmethod
def validate(config: TTSConfig) -> bool
```

驗證配置是否有效

---

##### merge_configs()

```python
@staticmethod
def merge_configs(base: TTSConfig, override: dict) -> TTSConfig
```

合併配置（基礎配置 + 覆蓋值）

---

---

### 1.4 TextProcessor

文本處理器

```python
from text_processor import TextProcessor
```

#### 建構函式

```python
def __init__(self, chunk_size: int = 500)
```

#### 方法

##### split()

智能分段

```python
def split(self, text: str) -> List[str]
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| text | str | 要分段的文本 |

**回傳:** `List[str]` - 分段後的文字清單

---

##### validate_input()

驗證輸入

```python
def validate_input(self, text: str, max_length: int) -> bool
```

---

##### get_text_info()

取得文本資訊

```python
def get_text_info(self, text: str) -> Dict
```

**回傳:** `Dict` - 包含 keys: char_count, line_count, chunk_count, avg_chunk_length

---

---

### 1.5 AsyncSynthesizer

非同步語音合成器

```python
from async_synthesizer import AsyncSynthesizer
```

#### 建構函式

```python
def __init__(self, config: TTSConfig)
```

#### 方法

##### synthesize()

同步合成

```python
async def synthesize(self, text: str, output_file: str,
                    voice: Optional[str] = None) -> str
```

---

##### synthesize_stream()

流式合成

```python
async def synthesize_stream(self, text: str,
                          voice: Optional[str] = None) -> AsyncIterator[bytes]
```

---

##### synthesize_chunks()

批次合成多個分段

```python
async def synthesize_chunks(self, chunks: List[str],
                          output_dir: str) -> List[str]
```

**回傳:** `List[str]` - 輸出音訊檔案路徑清單

---

##### list_voices()

列出所有可用音色

```python
@classmethod
async def list_voices(cls) -> List[dict]
```

---

##### get_chinese_voices()

取得中文音色

```python
@classmethod
async def get_chinese_voices(cls) -> List[str]
```

---

---

### 1.6 AudioMerger

音訊合併器

```python
from audio_merger import AudioMerger
```

#### 方法

##### merge_audios()

合併多個音訊檔案

```python
def merge_audios(self, input_files: List[str], output_file: str,
                silence_duration: float = 0.5) -> str
```

**參數:**
| 參數 | 類型 | 說明 |
|------|------|------|
| input_files | List[str] | 輸入音訊檔案清單 |
| output_file | str | 輸出檔案路徑 |
| silence_duration | float | 檔案間隔沉默時間（秒） |

**回傳:** `str` - 輸出的合併檔案路徑

---

##### validate_output()

驗證輸出

```python
def validate_output(self, file_path: str) -> bool
```

---

---

### 1.7 ErrorHandler

錯誤處理器

```python
from error_handler import ErrorHandler, TTSError, NetworkError, ServiceError, InputError, SystemError
```

#### 錯誤類型

| 類別 | 等級 | 說明 |
|------|------|------|
| TTSError | - | 一般錯誤基底 |
| NetworkError | L1 | 網路連線失敗 |
| ServiceError | L2 | 服務端錯誤 |
| InputError | L3 | 用戶輸入錯誤 |
| SystemError | L4 | 系統錯誤 |

#### 建構函式

```python
def __init__(self, max_retries: int = 3,
            circuit_breaker_threshold: int = 5,
            circuit_breaker_timeout: int = 60)
```

#### 方法

##### handle_error()

處理錯誤

```python
def handle_error(self, error: Exception, context: dict = None) -> ErrorResult
```

---

##### is_circuit_open()

檢查熔斷器是否開啟

```python
def is_circuit_open(self) -> bool
```

---

##### reset_circuit()

重置熔斷器

```python
def reset_circuit(self) -> None
```

---

---

## 2. 快速合成函式

### quick_synthesize()

快速合成捷徑

```python
from presentation_tts import quick_synthesize

async def quick_synthesize(text: str, output_file: str,
                          voice: str = "zh-TW-HsiaoHsiaoNeural") -> str
```

**參數:**
| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| text | str | - | 要合成的文字 |
| output_file | str | - | 輸出檔案路徑 |
| voice | str | "zh-TW-HsiaoHsiaoNeural" | 音色 |

**回傳:** `str` - 輸出檔案路徑

---

## 3. 使用範例

### 完整範例

```python
import asyncio
from presentation_tts import PresentationTTS
from config_manager import TTSConfig

async def main():
    # 1. 建立配置
    config = TTSConfig(
        voice="zh-TW-HsiaoHsiaoNeural",
        rate="+0%",
        volume="+0%",
        chunk_size=500,
        retry_count=3
    )
    
    # 2. 建立實例
    tts = PresentationTTS(config)
    
    # 3. 合成
    text = """
    這是一段測試文字。
    會自動進行分段處理。
    輸出為 MP3 格式。
    """
    
    result = await tts.synthesize(text, "output.mp3")
    print(f"完成: {result}")

asyncio.run(main())
```

---

*Generated by TTS Project v574 - 2026-03-28*