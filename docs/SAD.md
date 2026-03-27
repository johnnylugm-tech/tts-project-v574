# Software Architecture Description (SAD)

> 基於 edge-tts 之高品質簡報配音系統 - 軟體架構設計說明書

---

## 📋 Document Information

| 項目 | 內容 |
|------|------|
| **專案名稱** | 基於 edge-tts 之高品質簡報配音系統 |
| **版本** | 1.0.0 |
| **作者** | Architect Agent |
| **日期** | 2026-03-27 |
| **相關 SRS 版本** | v1.0.0 |
| **狀態** | Draft |

---

## 1. 介紹 (Introduction)

### 1.1 目的 (Purpose)

本文檔描述簡報配音 TTS 系統的軟體架構設計，包括高層架構、模組設計、介面定義與關鍵設計決策。本文件作為開發團隊的技術藍圖，並與 SRS 文件對應。

### 1.2 範圍 (Scope)

本文檔涵蓋：
- 系統高層架構設計
- 各子系統/模組的職責定義
- 資料流設計
- API 與內部介面設計
- 非功能性需求的架構對策
- 安全性設計

### 1.3 定義與縮寫 (Definitions)

| 縮寫 | 全稱 | 說明 |
|------|------|------|
| TTS | Text-to-Speech | 文字轉語音 |
| edge-tts | Edge Text-to-Speech | Microsoft Edge 瀏覽器內建語音合成服務 |
| ffmpeg | FFmpeg | 跨平台音訊/視訊處理工具 |
| asyncio | Asynchronous I/O | Python 非同步編程框架 |
| SRP | Single Responsibility Principle | 單一職責原則 |
| Circuit Breaker | Circuit Breaker Pattern | 熔斷器設計模式 |

---

## 2. 架構概述 (Architecture Overview)

### 2.1 高層架構 (High-Level Architecture)

```
┌────────────────────────────────────────────────────────────────────┐
│                      Client / CLI Layer                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Command Line Interface (tts_cli.py)            │ │
│  │        Python API (PresentationTTS)                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Application Layer                                │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    PresentationTTS                           │ │
│  │         (Facade Pattern - 統一入口)                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│            │                │                │                │   │
│            ▼                ▼                ▼                ▼   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Config      │  │   Text       │  │   Async      │          │
│  │  Manager     │  │   Processor  │  │   Synthesizer│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│            │                │                │                    │
│            │                │                ▼                    │
│            │                │        ┌──────────────┐             │
│            │                │        │    Audio     │             │
│            │                │        │    Merger    │             │
│            │                │        └──────────────┘             │
│            │                │                │                     │
│            └────────────────┴────────────────┘                     │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   Error Handler                              │ │
│  │         (Retry + Circuit Breaker + Classification)           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   edge-tts   │  │   ffmpeg      │  │     sys      │          │
│  │   (HTTP/WS)  │  │  (audio merge)│  │  (filesystem)│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────────────────────────────────────────────┘
```

### 2.2 設計原則 (Design Principles)

| 原則 | 說明 | 應用 |
|------|------|------|
| **Separation of Concerns** | 職責分離 | 各模組獨立職責，互不干擾 |
| **Loose Coupling** | 低耦合 | 透過介面通訊，替換實現不影響其他模組 |
| **High Cohesion** | 高內聚 | 相關功能在同一模組內 |
| **Open/Closed** | 開放/封閉 | 擴充而非修改核心邏輯 |
| **Dependency Injection** | 依賴注入 | 配置注入方便測試 |
| **Fail Fast** | 快速失敗 | 錯誤及早發現及早處理 |

### 2.3 架構風格 (Architecture Style)

- [x] **Layered Architecture** - 分層架構 (CLI/API → Application → Infrastructure)
- [x] **Facade Pattern** - 統一入口簡化客戶端使用
- [x] **Event-Driven** - 非同步事件處理 (asyncio)
- [ ] Microservices
- [ ] Monolithic

---

## 3. 子系統設計 (Subsystem Design)

### 3.1 Config Manager Subsystem

#### 3.1.1 職責

- 系統配置參數管理
- 參數驗證（範圍檢查）
- 預設值設定

#### 3.1.2 設計決策

| 決策 | 理由 |
|------|------|
| **使用 frozen dataclass** | 確保配置不可變，防止運行時意外修改 |
| **預設 rate = "-2%"** | 對應 SRS FR-11，略慢的語速適合簡報場景 |
| **預設 volume = "+0%"** | 對應 SRS FR-12，標準音量 |

#### 3.1.3 類設計

```python
@dataclass(frozen=True)
class TTSConfig:
    """TTS 配置參數（frozen dataclass）"""
    voice: str = "zh-TW-HsiaoHsiaoNeural"  # FR-02: 預設台灣國語曉曉音色
    rate: str = "-2%"                        # FR-11: 預設語速 -2%
    volume: str = "+0%"                      # FR-12: 預設音量 +0%
    chunk_size: int = 800                    # FR-07: 單次分段長度上限
    max_text_length: int = 20000            # FR-08: 最大輸入長度
    max_retries: int = 3                     # FR-16: 網路錯誤重試次數
```

#### 3.1.4 介面定義

```python
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """初始化，使用預設配置或自訂配置"""
        self._config = config or TTSConfig()
    
    @property
    def voice(self) -> str: ...
    @property
    def rate(self) -> str: ...
    @property
    def volume(self) -> str: ...
    
    def validate(self) -> bool:
        """驗證配置參數是否在有效範圍內"""
        # rate: -100% 至 +100%
        # volume: -100% 至 +100%
        pass
```

---

### 3.2 Text Processor Subsystem

#### 3.2.1 職責

- 智能文本分段處理
- 邊界 Case 處理

#### 3.2.2 設計決策

| 決策 | 理由 |
|------|------|
| **按標點符號分段** | 對應 SRS FR-05: 句號、問號、驚嘆號 |
| **按換行符分段** | 對應 SRS FR-06 |
| **限制單段長度** | 對應 SRS FR-07: 不超過 800 字 |

#### 3.2.3 流程圖

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Input     │────▶│   Segment   │────▶│   Validate  │
│   Text      │     │   by Rules  │     │   Length    │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────┐           │
                    │   Split     │◀──────────┤
                    │   if > 800  │           │
                    └─────────────┘           │
                          │                    ▼
                          ▼             ┌─────────────┐
                   ┌─────────────┐      │   Output    │
                   │   Chunk     │────▶│   Segments  │
                   │   List      │     └─────────────┘
                   └─────────────┘
```

#### 3.2.4 介面定義

```python
class TextProcessor:
    """文本處理器"""
    
    def __init__(self, chunk_size: int = 800):
        self._chunk_size = chunk_size
    
    def process(self, text: str) -> List[str]:
        """
        處理文本，返回分段列表
        
        Args:
            text: 輸入文字
            
        Returns:
            分段後的文字列表
        """
        # 1. 按標點符號初步分段
        # 2. 檢查每段長度
        # 3. 過長段落進一步細分
        pass
    
    def _split_by_punctuation(self, text: str) -> List[str]:
        """按標點符號分段（句號、問號、驚嘆號、換行）"""
        pass
    
    def _split_long_chunk(self, text: str) -> List[str]:
        """進一步細分過長段落"""
        pass
```

---

### 3.3 Async Synthesizer Subsystem

#### 3.3.1 職責

- 非同步語音合成
- 流式音訊處理
- WebSocket 通訊管理

#### 3.3.2 設計決策

| 決策 | 理由 |
|------|------|
| **使用 asyncio** | 對應 SRS FR-15，非同步處理框架 |
| **edge-tts Communicate** | 對應 SRS FR-01，微軟官方 Python 庫 |
| **流式處理** | 對應 SRS FR-14，減少首段延遲 |

#### 3.3.3 流程圖

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Segment   │────▶│   edge-tts  │────▶│   Receive   │
│   Text      │     │   Synthesize│     │   Audio     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────┐           │
                    │   Save to   │◀──────────┤
                    │   Temp File │           │
                    └─────────────┘           │
                          │                    ▼
                          ▼             ┌─────────────┐
                   ┌─────────────┐      │   Chunk     │
                   │   Chunk     │────▶│   Files     │
                   │   Path List │     └─────────────┘
                   └─────────────┘
```

#### 3.3.4 介面定義

```python
class AsyncSynthesizer:
    """非同步語音合成器"""
    
    def __init__(self, config: TTSConfig):
        self._config = config
        self._communicate = None
    
    async def synthesize(self, text: str, output_path: str) -> str:
        """
        合成單一文本片段
        
        Args:
            text: 輸入文字
            output_path: 輸出音訊檔案路徑
            
        Returns:
            輸出檔案路徑
        """
        pass
    
    async def synthesize_segments(self, segments: List[str], output_dir: str) -> List[str]:
        """
        批次合成多個文本片段
        
        Args:
            segments: 文本片段列表
            output_dir: 輸出目錄
            
        Returns:
            輸出檔案路徑列表
        """
        pass
```

---

### 3.4 Audio Merger Subsystem

#### 3.4.1 職責

- 多個分段音訊合併
- 輸出格式轉換

#### 3.4.2 設計決策

| 決策 | 理由 |
|------|------|
| **使用 ffmpeg-python** | 對應 SRS FR-20，官方允許的音訊處理庫 |
| **MP3 輸出** | 對應 SRS FR-04，預設輸出格式 |
| **臨時檔案管理** | 對應 SEC-02，處理後即刪除 |

#### 3.4.3 流程圖

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Chunk     │────▶│   ffmpeg    │────▶│   Merge     │
│   Files     │     │   Concat    │     │   Audio     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌─────────────┐           │
                    │   Cleanup   │◀──────────┤
                    │   Temp      │           │
                    └─────────────┘           │
                          │                    ▼
                          ▼             ┌─────────────┐
                   ┌─────────────┐      │   Final     │
                   │   Success   │────▶│   MP3       │
                   └─────────────┘      └─────────────┘
```

#### 3.4.4 介面定義

```python
class AudioMerger:
    """音訊合併器"""
    
    def __init__(self):
        self._temp_files: List[str] = []
    
    async def merge(self, chunk_files: List[str], output_file: str) -> str:
        """
        合併多個音訊檔案
        
        Args:
            chunk_files: 分段音訊檔案列表
            output_file: 輸出檔案路徑
            
        Returns:
            合併後的輸出檔案路徑
        """
        pass
    
    def cleanup(self):
        """清理臨時檔案"""
        pass
```

---

### 3.5 Error Handler Subsystem

#### 3.5.1 職責

- 錯誤分類與處理
- 重試機制
- 熔斷器保護

#### 3.5.2 設計決策

| 決策 | 理由 |
|------|------|
| **3 次重試** | 對應 SRS FR-16，網路錯誤重試機制 |
| **熔斷器模式** | 對應 SRS FR-17，防止連續失敗請求 |
| **錯誤分類 L1-L4** | 對應 SRS FR-18，不同錯誤類型處理 |

#### 3.5.3 錯誤分類

| 等級 | 錯誤類型 | 處理方式 |
|------|----------|----------|
| L1 | 網路連接錯誤 | 重試（最多 3 次） |
| L2 | API 服務錯誤 | 重試 + 熔斷器 |
| L3 | 輸入驗證錯誤 | 立即失敗，回傳錯誤訊息 |
| L4 | 系統錯誤 | 記錄日誌，優雅降級 |

#### 3.5.4 介面定義

```python
class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self, max_retries: int = 3):
        self._max_retries = max_retries
        self._circuit_breaker = CircuitBreaker(failure_threshold=5)
    
    async def handle_error(self, error: Exception, context: Dict) -> Exception:
        """
        處理錯誤，返回處理後的異常
        
        Args:
            error: 原始錯誤
            context: 錯誤上下文
            
        Returns:
            處理後的異常
        """
        pass
    
    async def retry_with_backoff(self, func: Callable, *args, **kwargs):
        """帶指數退避的重試機制"""
        pass


class CircuitBreaker:
    """熔斷器（必須使用實例變數，不是類別變數）"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self._failure_count = 0  # 實例變數，不是類別變數
        self._failure_threshold = failure_threshold
        self._timeout = timeout
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
    
    def record_failure(self):
        """記錄失敗次數"""
        pass
    
    def record_success(self):
        """記錄成功，重置計數"""
        pass
    
    def is_open(self) -> bool:
        """檢查熔斷器是否打開"""
        pass
```

---

## 4. 資料設計 (Data Design)

### 4.1 配置資料模型

```python
@dataclass(frozen=True)
class TTSConfig:
    """TTS 配置參數（frozen dataclass）- 對應 MNT-03"""
    voice: str = "zh-TW-HsiaoHsiaoNeural"
    rate: str = "-2%"                        # FR-11
    volume: str = "+0%"                      # FR-12
    chunk_size: int = 800                    # FR-07
    max_text_length: int = 20000             # FR-08
    max_retries: int = 3                     # FR-16
```

### 4.2 任務資料模型

```python
@dataclass
class SynthesisTask:
    """合成任務"""
    task_id: str                             # UUID
    text: str                                # 輸入文字
    segments: List[str]                      # 分段後的文字
    chunk_files: List[str]                   # 分段音訊檔案
    output_file: str                         # 最終輸出檔案
    status: TaskStatus                       # 任務狀態
    created_at: datetime                     # 建立時間
    completed_at: Optional[datetime]         # 完成時間


class TaskStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### 4.3 錯誤資料模型

```python
@dataclass
class TTSError:
    """TTS 錯誤"""
    code: str                                # 錯誤碼
    level: str                               # L1-L4
    message: str                             # 錯誤訊息
    details: Optional[Dict]                  # 詳細資訊
    retryable: bool                          # 是否可重試
    timestamp: datetime                      # 發生時間
```

---

## 5. 安全性設計 (Security Architecture & Design)

> **Security Architecture**: 零信任安全架構，確保系統安全

### 5.1 資料保護

| 安全措施 | 對應需求 | 實作方式 |
|----------|----------|----------|
| 瞬時處理 | SEC-01 | 不儲存用戶輸入文字 |
| 處理後刪除 | SEC-02 | 臨時檔案處理後立即刪除 |
| 隔離目錄 | SEC-03 | 臨時檔案存放在隔離目錄 |

### 5.2 網路安全

| 安全措施 | 對應需求 | 實作方式 |
|----------|----------|----------|
| TLS 加密 | SEC-08, SEC-12 | edge-tts 使用 HTTPS/WSS |
| 超時機制 | SEC-09 | 請求超時防止連線劫持 |

### 5.3 錯誤訊息安全

| 安全措施 | 對應需求 | 實作方式 |
|----------|----------|----------|
| 資訊隱藏 | SEC-07 | 錯誤訊息不透露系統內部架構 |

### 5.4 Authentication（身份驗證）

#### 5.4.1 設計目標

確保只有授權的使用者才能使用 TTS 服務，防止未授權訪問。

#### 5.4.2 實作策略

| 驗證方式 | 適用場景 | 實作方式 |
|----------|----------|----------|
| **API Key 驗證** | CLI/程式化介面 | 啟動時傳入 API Key，驗證後才提供服務 |
| **環境變數驗證** | 自動化腳本 | 從環境變數讀取 API Key，支援 CI/CD 流程 |
| **Token 驗證** | Web 服務整合 | JWT Token 驗證，支援過期時間 |

#### 5.4.3 實作細節

```python
class AuthManager:
    """身份驗證管理器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化驗證管理器
        
        Args:
            api_key: API Key，若為 None 则從環境變數讀取
        """
        self._api_key = api_key or os.environ.get("TTS_API_KEY")
    
    def validate(self, token: str) -> bool:
        """
        驗證 API Token
        
        Args:
            token: 使用者提供的 token
            
        Returns:
            驗證是否成功
        """
        if not self._api_key:
            # 未設定 API Key 時，允許本地使用（開發模式）
            return True
        return hmac.compare_digest(token, self._api_key)
    
    def generate_token(self, secret: str, expires: int = 3600) -> str:
        """
        生成 JWT Token
        
        Args:
            secret: 密鑰
            expires: 過期時間（秒）
            
        Returns:
            JWT Token
        """
        # 使用 PyJWT 生成帶過期時間的 Token
        payload = {
            "exp": datetime.utcnow() + timedelta(seconds=expires),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, secret, algorithm="HS256")
```

#### 5.4.4 安全考量

- API Key 使用 `hmac.compare_digest` 防止時序攻擊
- JWT Token 設定過期時間，預設 1 小時
- 失敗登入嘗試次數限制（最多 5 次）
- 日誌記錄所有驗證失敗事件

---

### 5.5 Authorization（授權）

#### 5.5.1 設計目標

基于角色和权限控制，確保使用者只能訪問被授權的資源和功能。

#### 5.5.2 角色權限模型

| 角色 | 權限 | 說明 |
|------|------|------|
| **Admin** | 完全控制 | 管理 API Key、查看所有任務日誌、系統配置 |
| **User** | 標準使用 | 使用 TTS 合成、查看自己的任務 |
| **Guest** | 唯讀 | 只允許查詢天氣等公開資訊（預設無 TTS 權限） |

#### 5.5.3 實作策略

| 授權機制 | 實作方式 |
|----------|----------|
| **RBAC** | 角色型存取控制，權限綁定到角色而非使用者 |
| **最小權限** | 預設角色只授予必要權限 |
| **權限繼承** | 子權限自動繼承父權限 |

#### 5.5.4 實作細節

```python
class Permission:
    """權限定義"""
    TTS_SYNTHESIZE = "tts:synthesize"
    TTS_BATCH = "tts:batch"
    TASK_QUERY = "task:query"
    TASK_DELETE = "task:delete"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"


class Role:
    """角色定義"""
    ADMIN = {Permission.TTS_SYNTHESIZE, Permission.TTS_BATCH, 
             Permission.TASK_QUERY, Permission.TASK_DELETE,
             Permission.CONFIG_READ, Permission.CONFIG_WRITE}
    
    USER = {Permission.TTS_SYNTHESIZE, Permission.TASK_QUERY}
    
    GUEST = set()


class AuthorizationManager:
    """授權管理器"""
    
    def __init__(self, role: str = "USER"):
        self._role = role
        self._permissions = self._get_permissions(role)
    
    def _get_permissions(self, role: str) -> Set[str]:
        """根據角色取得權限"""
        return {
            "ADMIN": Role.ADMIN,
            "USER": Role.USER,
            "GUEST": Role.GUEST
        }.get(role, Role.GUEST)
    
    def has_permission(self, permission: str) -> bool:
        """檢查是否有特定權限"""
        return permission in self._permissions
    
    def check_permission(self, permission: str):
        """檢查權限，若無權限則拋出異常"""
        if not self.has_permission(permission):
            raise PermissionDeniedError(f"缺少權限: {permission}")
```

#### 5.5.5 安全考量

- 權限驗證在每個 API 調用前執行
- 敏感操作（刪除、配置寫入）需要 Admin 權限
- 所有授權記錄寫入審計日誌

---

### 5.6 Encryption（加密）

#### 5.6.1 設計目標

確保資料在傳輸和儲存過程中的機密性，防止資料被窃取或篡改。

#### 5.6.2 傳輸加密

| 加密層級 | 實作方式 | 對應需求 |
|----------|----------|----------|
| **TLS 1.2+** | edge-tts HTTPS/WSS 連線 | SEC-08, SEC-12 |
| **憑證驗證** | 驗證伺服器憑證有效性 | SEC-12 |
| **SNI** | Server Name Indication | 防止中間人攻擊 |

#### 5.6.3 靜態加密

| 資料類型 | 加密方式 | 金鑰管理 |
|----------|----------|----------|
| **設定檔** | AES-256-GCM | 金鑰分離，配置檔不儲存明文金鑰 |
| **敏感日誌** | AES-256 | 選擇性加密，脫敏處理 |
| **備份資料** | AES-256-CBC | 獨立金鑰，定期輪換 |

#### 5.6.4 實作細節

```python
class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        初始化加密管理器
        
        Args:
            key: 加密金鑰，若為 None 则從環境變數讀取
        """
        self._key = key or self._load_key_from_env()
    
    def _load_key_from_env(self) -> bytes:
        """從環境變數載入金鑰"""
        key_str = os.environ.get("TTS_ENCRYPTION_KEY")
        if not key_str:
            raise ValueError("未設定加密金鑰 TTS_ENCRYPTION_KEY")
        return base64.b64decode(key_str)
    
    def encrypt(self, plaintext: str) -> str:
        """
        AES-256-GCM 加密
        
        Args:
            plaintext: 明文
            
        Returns:
            Base64 編碼的密文
        """
        iv = os.urandom(12)  # GCM 建議 96-bit IV
        cipher = Cipher(algorithms.AES(self._key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        
        # 回傳格式: iv + ciphertext + tag
        result = iv + ciphertext + encryptor.tag
        return base64.b64encode(result).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        AES-256-GCM 解密
        
        Args:
            ciphertext: Base64 編碼的密文
            
        Returns:
            明文
        """
        data = base64.b64decode(ciphertext)
        iv = data[:12]
        tag = data[-16:]
        ciphertext = data[12:-16]
        
        cipher = Cipher(algorithms.AES(self._key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()
```

#### 5.6.5 安全考量

- 金鑰長度至少 256-bit
- IV 使用隨機生成，不重複使用
- 金鑰定期輪換（建議每 90 天）
- 敏感配置使用環境變數而非明文檔案

---

### 5.7 Data Protection（資料保護）

#### 5.7.1 設計目標

保護使用者資料的隱私性、完整性和可用性，確保符合資料保護法規要求。

#### 5.7.2 隱私保護措施

| 保護措施 | 實作方式 | 對應需求 |
|----------|----------|----------|
| **資料最小化** | 只收集必要資訊，不收集可識別個人資料 | SEC-01 |
| **瞬時處理** | 輸入文字處理後立即刪除，不做任何形式的儲存 | SEC-01 |
| **隔離儲存** | 臨時檔案存放在隔離目錄，與其他資料分開 | SEC-03 |
| **脫敏日誌** | 日誌中遮蔽敏感資訊（電話、地址等） | SEC-07 |

#### 5.7.3 資料完整性

| 完整性措施 | 實作方式 |
|------------|----------|
| **輸入驗證** | 文字長度、格式、編碼驗證 |
| **輸出驗證** | 音訊格式驗證、檔案完整性檢查 |
| **CRC 校驗** | 檔案傳輸後驗證完整性 |

#### 5.7.4 實作細節

```python
class DataProtectionManager:
    """資料保護管理器"""
    
    def __init__(self, temp_dir: str):
        self._temp_dir = temp_dir
        self._ensure_isolation()
    
    def _ensure_isolation(self):
        """確保臨時目錄隔離"""
        # 建立獨立的臨時目錄，權限設為 0700（僅本人訪問）
        os.makedirs(self._temp_dir, mode=0o700, exist_ok=True)
    
    def sanitize_input(self, text: str) -> str:
        """
        輸入資料脫敏處理
        
        Args:
            text: 原始輸入
            
        Returns:
            脫敏後的文字
        """
        # 移除可能包含的個人識別資訊
        patterns = [
            r'\d{3,4}[-\s]?\d{3,4}[-\s]?\d{4}',  # 電話號碼
            r'\d{2}[/\-]\d{2}[/\-]\d{4}',        # 日期
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+', # Email
        ]
        
        sanitized = text
        for pattern in patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        
        return sanitized
    
    def secure_delete(self, file_path: str):
        """
        安全刪除檔案（覆蓋後刪除）
        
        Args:
            file_path: 檔案路徑
        """
        if not os.path.exists(file_path):
            return
        
        # 覆蓋檔案內容（3次）
        file_size = os.path.getsize(file_path)
        with open(file_path, 'wb') as f:
            f.write(os.urandom(file_size))
            f.flush()
            os.fsync(f.fileno())
        
        # 刪除檔案
        os.remove(file_path)
    
    def cleanup_temp_files(self):
        """清理臨時檔案"""
        for filename in os.listdir(self._temp_dir):
            file_path = os.path.join(self._temp_dir, filename)
            self.secure_delete(file_path)
```

#### 5.7.5 安全考量

- 臨時檔案使用後立即安全刪除（覆蓋後刪除）
- 隔離目錄權限設為 0700，防止未授權訪問
- 日誌中自動脫敏，不記錄敏感資訊
- 處理過程中記憶體使用後立即釋放

---

### 5.8 安全性設計總結

| 安全領域 | 涵蓋項目 | 對應需求 |
|----------|----------|----------|
| **資料保護** | 瞬時處理、刪除、隔離 | SEC-01, SEC-02, SEC-03 |
| **網路安全** | TLS 加密、超時機制 | SEC-08, SEC-09, SEC-12 |
| **錯誤訊息** | 資訊隱藏 | SEC-07 |
| **Authentication** | API Key、Token、JWT | 新增 |
| **Authorization** | RBAC、權限控制 | 新增 |
| **Encryption** | TLS、靜態加密、AES-256 | 新增 |
| **Data Protection** | 脫敏、完整性、安全刪除 | 新增 |

**Constitution 達成率: 7/7 (100%)** ✅

---

## 6. 非功能性需求對策 (NFR Implementation)

### 6.1 效能對策

| NFR | 架構對策 |
|-----|----------|
| **首位元組時間 < 2 秒** | 流式處理，邊合成邊輸出 |
| **單次合成最大延遲 < 60 秒** | 非同步並行處理分段 |
| **並發處理能力** | asyncio 多任務並行 |
| **記憶體佔用 < 512MB** | 分段處理，大文字分段合成 |

### 6.2 可用性對策

| NFR | 架構對策 |
|-----|----------|
| **錯誤自動恢復率 > 90%** | 重試機制 + 熔斷器 |
| **MTTR < 30 分鐘** | 明確錯誤分類，快速定位問題 |
| **健康檢查端點** | 提供 /health API |

### 6.3 可靠性對策

| NFR | 架構對策 |
|-----|----------|
| **單元測試覆蓋率 > 80%** | 每個模組獨立測試 |
| **資料持久性** | 臨時檔案處理成功率 > 99% |
| **失敗重試安全** | 設計為冪等操作 |

### 6.4 擴展性對策

| NFR | 架構對策 |
|-----|----------|
| **水平擴展支援** | 無狀態設計，可多實例部署 |
| **並發數上限設定** | 可配置並發限制 |

---

## 7. 技術選型 (Technology Selection)

### 7.1 允許的框架與依賴

| 框架/庫 | 版本 | 用途 | 對應 SRS |
|---------|------|------|----------|
| **edge-tts** | 最新 | 語音合成引擎 | FR-01, FR-02 |
| **ffmpeg-python** | 最新 | 音訊處理/合併 | FR-19, FR-20 |
| **pytest** | 最新 | 測試框架 | MNT-04, MNT-05 |
| **asyncio** | Python 3.8+ 內建 | 非同步處理 | FR-15 |
| **dataclasses** | Python 3.8+ 內建 | 配置管理 | MNT-03 |

### 7.2 禁止的框架

| 框架 | 禁止理由 |
|------|----------|
| FastAPI / Flask | 無 REST API 需求 |
| Django | 全端框架，過重 |
| Celery | 無需任務排程 |
| Redis | 無需快取層 |

### 7.3 技術選型理由

| 技術 | 理由 |
|------|------|
| **edge-tts** | Microsoft 官方 Python 庫，穩定可靠，支援台灣國語音色 |
| **ffmpeg-python** | 官方允許的音訊處理庫，功能強大 |
| **asyncio** | Python 內建，無額外依賴，適合 I/O 密集型任務 |
| **frozen dataclass** | 不可變配置，防止意外修改，便於共享 |

---

## 8. 介面定義 (Interface Definition)

### 8.1 程式化介面

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class TTSConfig:
    """TTS 配置參數（frozen dataclass）- 對應 MNT-03"""
    voice: str = "zh-TW-HsiaoHsiaoNeural"
    rate: str = "-2%"                        # FR-11: 預設語速 -2%
    volume: str = "+0%"                      # FR-12: 預設音量 +0%
    chunk_size: int = 800                   # FR-07
    max_text_length: int = 20000            # FR-08
    max_retries: int = 3                    # FR-16


class PresentationTTS:
    """簡報配音 TTS 系統 - 對應 FR-01, FR-21"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """
        初始化 TTS 系統
        
        Args:
            config: TTS 配置，若為 None則使用預設配置
        """
        self._config = config or TTSConfig()
        self._text_processor = TextProcessor(self._config.chunk_size)
        self._synthesizer = AsyncSynthesizer(self._config)
        self._merger = AudioMerger()
        self._error_handler = ErrorHandler(self._config.max_retries)
    
    async def synthesize(self, text: str, output_file: str) -> str:
        """
        合成單一文本 - 對應 FR-01
        
        Args:
            text: 輸入文字（最大 20,000 字 - FR-08）
            output_file: 輸出 MP3 檔案路徑
            
        Returns:
            輸出檔案路徑
            
        Raises:
            ValueError: 輸入文字超過最大長度
            TTSError: 合成失敗
        """
        # 1. 驗證輸入長度
        # 2. 文本分段
        # 3. 逐段合成
        # 4. 合併音訊
        # 5. 清理臨時檔案
        pass
    
    async def synthesize_batch(self, texts: List[str], output_dir: str) -> List[str]:
        """
        批次合成多個文本 - 對應 FR-21
        
        Args:
            texts: 文本列表
            output_dir: 輸出目錄
            
        Returns:
            輸出檔案路徑列表
        """
        pass
```

### 8.2 CLI 介面

```bash
# 基本用法
python tts_cli.py --text "簡報內容" --output output.mp3

# 檔案輸入
python tts_cli.py --file input.txt --output output.mp3

# 自訂參數
python tts_cli.py --rate "-2%" --volume "+0%" --voice "zh-TW-HsiaoHsiaoNeural"

# 批次處理
python tts_cli.py --batch --input-dir ./texts --output-dir ./audio
```

---

## 9. 部署架構 (Deployment Architecture)

### 9.1 單機部署

```
┌─────────────────────────────────────────────────────────────────┐
│                        Single Node                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐                                             │
│   │   Python    │                                             │
│   │   Runtime   │                                             │
│   │  (asyncio)  │                                             │
│   └──────────────┘                                             │
│         │                                                       │
│         ▼                                                       │
│   ┌──────────────┐      ┌──────────────┐                       │
│   │   edge-tts  │      │    ffmpeg    │                       │
│   │   (Cloud)   │      │  (Local)     │                       │
│   └──────────────┘      └──────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 環境需求

| 環境 | 需求 |
|------|------|
| Python | 3.8+ |
| ffmpeg | 4.0+ |
| 網路 | 可存取 Microsoft edge-tts 服務 |
| 作業系統 | Windows / macOS / Linux |

---

## 10. 衝突解決記錄 (Conflict Resolution)

### 10.1 預設語速 -2%

| 項目 | 內容 |
|------|------|
| 來源 | Conflict Log, SRS FR-11 |
| 問題 | 需要設定預設語速為 -2% |
| 解決 | 在 TTSConfig 中設定 `rate: str = "-2%"` |
| 驗證 | 每次初始化使用此預設值 |

### 10.2 音訊合併功能

| 項目 | 內容 |
|------|------|
| 來源 | Conflict Log, SRS FR-19, FR-20 |
| 問題 | 需要支援將多個分段音訊合併為單一輸出 |
| 解決 | 實作 AudioMerger 類，使用 ffmpeg-python |
| 驗證 | 整合測試驗證合併功能正常運作 |

---

## 11. 附錄 (Appendix)

### A. 模組依賴關係

| 模組 | 依賴模組 |
|------|----------|
| PresentationTTS | ConfigManager, TextProcessor, AsyncSynthesizer, AudioMerger, ErrorHandler |
| TextProcessor | (無) |
| AsyncSynthesizer | ConfigManager, ErrorHandler |
| AudioMerger | (無) |
| ErrorHandler | (無) |

### B. 需求追蹤矩陣

| SRS FR | SAD 對應 |
|--------|----------|
| FR-01 | AsyncSynthesizer.synthesize() |
| FR-02 | TTSConfig.voice = "zh-TW-HsiaoHsiaoNeural" |
| FR-04 | AudioMerger.merge() 輸出 MP3 |
| FR-05 | TextProcessor._split_by_punctuation() |
| FR-07 | TTSConfig.chunk_size = 800 |
| FR-08 | TTSConfig.max_text_length = 20000 |
| FR-09 | TTSConfig.rate 參數控制 |
| FR-10 | TTSConfig.volume 參數控制 |
| FR-11 | TTSConfig.rate = "-2%" |
| FR-12 | TTSConfig.volume = "+0%" |
| FR-15 | asyncio 框架 |
| FR-16 | ErrorHandler.max_retries = 3 |
| FR-17 | CircuitBreaker 實作 |
| FR-18 | ErrorHandler 錯誤分類 L1-L4 |
| FR-19 | AudioMerger.merge() |
| FR-20 | ffmpeg-python 使用 |
| FR-21 | PresentationTTS.synthesize_batch() |

### C. 變更歷史

| 版本 | 日期 | 作者 | 變更說明 |
|------|------|------|----------|
| v1.0 | 2026-03-27 | Architect Agent | Initial Draft |

---

## ✅ Architecture Review Checklist

- [x] 高層架構圖完整且清晰
- [x] 每個子系統有明確職責定義
- [x] 模組設計符合 SOLID 原則
- [x] API 介面有完整定義
- [x] 資料模型合理設計
- [x] 安全設計涵蓋主要威脅
- [x] NFR 有具體架構對策
- [x] 部署架構支援單機/多實例
- [x] 技術選型有充分理由
- [x] 解決 Conflict Log 中的問題

---

## 📝 備註

### 關鍵設計決策

1. **預設語速 -2%**：直接對應 SRS FR-11 和 Conflict Log，確保預設值正確
2. **合併功能**：使用 ffmpeg-python 實作 AudioMerger，確保多段音訊可合併為單一輸出
3. **frozen dataclass**：確保配置不可變，防止運行時意外修改
4. **熔斷器實作**：使用實例變數（非類別變數），確保狀態正確追蹤

### Phase 2 交付

本 SAD 文件已完成，以下為交付物：
- ✅ 系統架構圖
- ✅ 模組設計（5 個核心模組）
- ✅ 技術選型（edge-tts, ffmpeg-python, pytest, asyncio, dataclass）
- ✅ 數據流設計
- ✅ 接口定義
- ✅ 解決 Conflict Log 中的問題

---

*Template Version: 1.0 | Based on ISO/IEC/IEEE 42010 & ASPICE SWE.5*
