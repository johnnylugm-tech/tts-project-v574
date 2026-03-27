"""
ErrorHandler - 錯誤處理器
Phase 3 實作 - SKILL.md Phase 3: 程式碼實現

對應規範:
- SRS.md: FR-16, FR-17, FR-18
- SKILL.md: 錯誤處理分層
- NFR-04: 99.5% 可用率
- NFR-05: 錯誤自動恢復 > 90%
- SEC-07: 錯誤訊息不透露架構
"""

import time
import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorLevel(Enum):
    """錯誤等級枚舉"""
    L1 = "L1"  # 暫時性網路錯誤（可重試）
    L2 = "L2"  # 服務端錯誤（熔斷）
    L3 = "L3"  # 用戶輸入錯誤（需修正）
    L4 = "L4"  # 系統錯誤（僅記錄）


class TTSError(Exception):
    """
    TTS 基底例外
    
    規範對應: FR-18（錯誤分類）
    
    屬性:
        level: 錯誤等級（L1-L4）
        message: 錯誤訊息（不透露架構）
        recoverable: 是否可恢復
    """
    level = ErrorLevel.L4
    message = "TTS 發生錯誤"
    recoverable = False
    
    def __init__(self, message: str = None, original_error: Exception = None):
        self.original_error = original_error
        user_message = message or self.message
        
        # SEC-07: 錯誤訊息不透露架構
        # 只返回通用訊息，不透露技術細節
        super().__init__(user_message)
    
    def to_dict(self) -> dict:
        """轉換為字典格式（安全的日誌記錄）"""
        return {
            "level": self.level.value,
            "type": self.__class__.__name__,
            "recoverable": self.recoverable
        }


class NetworkError(TTSError):
    """
    L1: 網路錯誤（可重試）
    
    規範對應: FR-16
    
    場景:
    - 網路連線失敗
    - DNS 解析失敗
    - 連線超時
    - 暫時性連線中斷
    """
    level = ErrorLevel.L1
    message = "網路連線不穩定，請稍後重試"
    recoverable = True
    
    def __init__(self, message: str = None, original_error: Exception = None):
        super().__init__(message, original_error)
        logger.warning(f"L1 網路錯誤: {message}", extra=self.to_dict())


class ServiceError(TTSError):
    """
    L2: 服務端錯誤（熔斷）
    
    規範對應: FR-17
    
    場景:
    - 服務端返回錯誤（如 500 錯誤）
    - 配額超限
    - 速率限制
    - 服務維護中
    """
    level = ErrorLevel.L2
    message = "服務暫時不可用，請稍後再試"
    recoverable = True
    
    def __init__(self, message: str = None, original_error: Exception = None):
        super().__init__(message, original_error)
        logger.warning(f"L2 服務端錯誤: {message}", extra=self.to_dict())


class InputError(TTSError):
    """
    L3: 用戶輸入錯誤（需修正）
    
    規範對應: FR-18
    
    場景:
    - 文字長度超過限制
    - 文字為空
    - 音色名稱無效
    - 參數格式錯誤
    """
    level = ErrorLevel.L3
    message = "輸入資料格式錯誤，請檢查後重新輸入"
    recoverable = False
    
    def __init__(self, message: str = None, original_error: Exception = None):
        super().__init__(message, original_error)
        logger.info(f"L3 用戶輸入錯誤: {message}", extra=self.to_dict())


class SystemError(TTSError):
    """
    L4: 系統錯誤（僅記錄）
    
    規範對應: FR-18
    
    場景:
    - 檔案系統錯誤
    - 記憶體不足
    - 程式邏輯錯誤
    - 未預期的例外
    """
    level = ErrorLevel.L4
    message = "系統發生錯誤，請聯絡支援團隊"
    recoverable = False
    
    def __init__(self, message: str = None, original_error: Exception = None):
        super().__init__(message, original_error)
        logger.error(f"L4 系統錯誤: {message}", extra=self.to_dict())


@dataclass
class CircuitBreakerState:
    """熔斷器狀態"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    # 設定參數
    failure_threshold: int = 5
    success_threshold: int = 3
    recovery_timeout: int = 60  # 秒


class CircuitBreaker:
    """
    熔斷器
    
    規範對應: FR-17（熔斷器機制）
    實現方式: 參考 Martin Fowler 的 Circuit Breaker 模式
    
    狀態:
    - CLOSED: 正常狀態，可執行
    - OPEN: 熔斷狀態，禁止執行
    - HALF_OPEN: 半開狀態，嘗試執行
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 success_threshold: int = 3,
                 recovery_timeout: int = 60):
        """
        初始化熔斷器
        
        參數:
            failure_threshold: 失敗次數閾值，達到此值則打開熔斷
            success_threshold: 成功次數閾值，達到此值則關閉熔斷
            recovery_timeout: 恢復超時（秒），超過此時間後進入半開狀態
        """
        self._state = CircuitBreakerState(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            recovery_timeout=recovery_timeout
        )
        logger.info(f"CircuitBreaker 初始化: failure_threshold={failure_threshold}, "
                   f"recovery_timeout={recovery_timeout}")
    
    @property
    def state(self) -> str:
        """取得當前狀態"""
        self._check_recovery()
        return self._state.state
    
    def can_execute(self) -> bool:
        """
        檢查是否可以執行
        
        返回:
            bool: 是否可以執行
        """
        self._check_recovery()
        return self._state.state != "OPEN"
    
    def record_success(self) -> None:
        """
        記錄成功
        
        規範對應: NFR-04（99.5% 可用率）
        """
        self._state.success_count += 1
        self._state.failure_count = 0
        
        if self._state.state == "HALF_OPEN":
            if self._state.success_count >= self._state.success_threshold:
                self._state.state = "CLOSED"
                logger.info("CircuitBreaker: 狀態變更 CLOSED → CLOSED (成功)")
        
        logger.debug(f"CircuitBreaker 記錄成功: success_count={self._state.success_count}")
    
    def record_failure(self) -> None:
        """
        記錄失敗
        
        規範對應: NFR-04
        """
        self._state.failure_count += 1
        self._state.success_count = 0
        self._state.last_failure_time = time.time()
        
        if self._state.state == "CLOSED":
            if self._state.failure_count >= self._state.failure_threshold:
                self._state.state = "OPEN"
                logger.warning(
                    f"CircuitBreaker: 狀態變更 CLOSED → OPEN "
                    f"(failure_count={self._state.failure_count})"
                )
        
        elif self._state.state == "HALF_OPEN":
            # 半開狀態下失敗，重新打開熔斷
            self._state.state = "OPEN"
            logger.warning("CircuitBreaker: HALF_OPEN → OPEN (半開狀態下失敗)")
    
    def _check_recovery(self) -> None:
        """檢查是否應該進入半開狀態"""
        if self._state.state == "OPEN":
            elapsed = time.time() - self._state.last_failure_time
            if elapsed >= self._state.recovery_timeout:
                self._state.state = "HALF_OPEN"
                self._state.success_count = 0
                logger.info(
                    f"CircuitBreaker: OPEN → HALF_OPEN "
                    f"(recovery_timeout={self._state.recovery_timeout}s 経過)"
                )
    
    def get_status(self) -> dict:
        """取得熔斷器狀態"""
        self._check_recovery()
        return {
            "state": self._state.state,
            "failure_count": self._state.failure_count,
            "success_count": self._state.success_count,
            "failure_threshold": self._state.failure_threshold,
            "recovery_timeout": self._state.recovery_timeout
        }
    
    def reset(self) -> None:
        """重置熔斷器"""
        self._state = CircuitBreakerState(
            failure_threshold=self._state.failure_threshold,
            success_threshold=self._state.success_threshold,
            recovery_timeout=self._state.recovery_timeout
        )
        logger.info("CircuitBreaker 已重置")


class RetryPolicy:
    """
    重試策略
    
    規範對應: FR-16（網路錯誤重試機制）
    
    實現:
    - 指數退避（Exponential Backoff）
    - 最大重試次數限制
    - 可重試錯誤過濾
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 30.0,
                 multiplier: float = 2.0):
        """
        初始化重試策略
        
        參數:
            max_retries: 最大重試次數
            base_delay: 基礎延遲（秒）
            max_delay: 最大延遲（秒）
            multiplier: 退避倍率
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
    
    def calculate_delay(self, attempt: int) -> float:
        """
        計算延遲時間（指數退避）
        
        公式: min(base_delay * (multiplier ^ attempt), max_delay)
        
        參數:
            attempt: 重試次數（從 0 開始）
        
        返回:
            float: 延遲秒數
        """
        delay = self.base_delay * (self.multiplier ** attempt)
        return min(delay, self.max_delay)
    
    @staticmethod
    def is_retryable(error: TTSError) -> bool:
        """
        判斷錯誤是否可重試
        
        參數:
            error: TTSError 例外
        
        返回:
            bool: 是否可重試
        """
        return error.recoverable and error.level in [ErrorLevel.L1, ErrorLevel.L2]
    
    async def execute_with_retry(self, 
                                 func: Callable, 
                                 *args, 
                                 **kwargs) -> Any:
        """
        執行帶重試的函式
        
        參數:
            func: 要執行的非同步函式
            *args, **kwargs: 函式參數
        
        返回:
            Any: 函式返回值
        
        異常:
            TTSError: 所有重試失敗後的最後一個錯誤
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                return result
            except TTSError as e:
                last_error = e
                
                if not self.is_retryable(e):
                    # 不可重試的錯誤直接拋出
                    raise
                
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.info(
                        f"重試 {attempt + 1}/{self.max_retries}，"
                        f"等待 {delay:.1f} 秒... ({e.level.value})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"重試次數用盡 ({self.max_retries + 1} 次)")
        
        raise last_error


# 避免 asyncio 未定義的問題
import asyncio


class ErrorHandler:
    """
    錯誤處理器
    
    職責: 統一管理錯誤分類、重試機制、熔斷保護
    
    規範對應:
    - FR-16: 網路錯誤重試機制
    - FR-17: 熔斷器機制
    - FR-18: 錯誤分類（L1-L4）
    - NFR-04: 99.5% 可用率
    - NFR-05: 錯誤自動恢復 > 90%
    - SEC-07: 錯誤訊息不透露架構
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 circuit_breaker_threshold: int = 5,
                 circuit_breaker_timeout: int = 60):
        """
        初始化錯誤處理器
        
        參數:
            max_retries: 最大重試次數
            circuit_breaker_threshold: 熔斷器失敗閾值
            circuit_breaker_timeout: 熔斷器恢復超時
        """
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_timeout
        )
        self.retry_policy = RetryPolicy(max_retries=max_retries)
        logger.info(f"ErrorHandler 初始化: max_retries={max_retries}")
    
    def classify_error(self, error: Exception) -> TTSError:
        """
        分類錯誤
        
        規範對應: FR-18
        
        參數:
            error: 原始例外
        
        返回:
            TTSError: 分類後的錯誤
        """
        # 如果已經是 TTSError，直接返回
        if isinstance(error, TTSError):
            return error
        
        # 根據錯誤類型分類
        error_msg = str(error).lower()
        
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return NetworkError(str(error), error)
        
        elif 'timeout' in error_msg or 'connect' in error_msg:
            return NetworkError(str(error), error)
        
        elif 'quota' in error_msg or 'rate limit' in error_msg or '429' in error_msg:
            return ServiceError(str(error), error)
        
        elif '500' in error_msg or '502' in error_msg or '503' in error_msg:
            return ServiceError(str(error), error)
        
        elif isinstance(error, (ValueError, TypeError)):
            return InputError(str(error), error)
        
        else:
            return SystemError(str(error), error)
    
    async def execute_with_protection(self, 
                                      func: Callable, 
                                      *args, 
                                      **kwargs) -> Any:
        """
        執行帶保護的函式
        
        實現:
        1. 熔斷器檢查
        2. 重試機制
        3. 錯誤分類
        
        參數:
            func: 要執行的非同步函式
            *args, **kwargs: 函式參數
        
        返回:
            Any: 函式返回值
        """
        # 檢查熔斷器
        if not self.circuit_breaker.can_execute():
            status = self.circuit_breaker.get_status()
            logger.warning(f"熔斷器打開中: {status}")
            raise ServiceError("服務熔斷中，請稍後再試")
        
        try:
            # 執行函式
            result = await self.retry_policy.execute_with_retry(func, *args, **kwargs)
            
            # 記錄成功
            self.circuit_breaker.record_success()
            return result
            
        except TTSError as e:
            # 記錄失敗
            self.circuit_breaker.record_failure()
            
            # 分類錯誤
            classified_error = self.classify_error(e)
            raise classified_error
    
    def get_error_stats(self) -> dict:
        """取得錯誤統計"""
        return {
            "circuit_breaker": self.circuit_breaker.get_status(),
            "retry_policy": {
                "max_retries": self.retry_policy.max_retries,
                "base_delay": self.retry_policy.base_delay
            }
        }
    
    def reset_circuit_breaker(self) -> None:
        """重置熔斷器"""
        self.circuit_breaker.reset()
        logger.info("ErrorHandler: 熔斷器已重置")