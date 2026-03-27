"""
ErrorHandler 測試
Phase 3 實作 - 單元測試

對應規範:
- SRS.md: FR-16, FR-17, FR-18
- NFR-04: 99.5% 可用率
- NFR-05: 錯誤自動恢復 > 90%
- SEC-07: 錯誤訊息不透露架構
- MNT-04: 每個核心模組單元測試
"""

import pytest
import time
from tts_project_v574_03_implementation.error_handler import (
    TTSError, NetworkError, ServiceError, InputError, SystemError,
    ErrorLevel, CircuitBreaker, RetryPolicy, ErrorHandler
)


class TestTTSErrorHierarchy:
    """測試錯誤類別階層"""
    
    def test_error_levels(self):
        """測試錯誤等級"""
        assert NetworkError.level == ErrorLevel.L1
        assert ServiceError.level == ErrorLevel.L2
        assert InputError.level == ErrorLevel.L3
        assert SystemError.level == ErrorLevel.L4
    
    def test_recoverable_flags(self):
        """測試可恢復標記"""
        assert NetworkError.recoverable is True
        assert ServiceError.recoverable is True
        assert InputError.recoverable is False
        assert SystemError.recoverable is False
    
    def test_error_messages(self):
        """測試錯誤訊息（SEC-07: 不透露架構）"""
        e = NetworkError("test")
        assert "網路" in str(e) or "連線" in str(e)
        
        e = ServiceError("test")
        assert "服務" in str(e) or "不可用" in str(e)
        
        e = InputError("test")
        assert "輸入" in str(e) or "格式" in str(e)
        
        e = SystemError("test")
        assert "系統" in str(e) or "錯誤" in str(e)
    
    def test_error_to_dict(self):
        """測試錯誤轉換為字典"""
        e = NetworkError("test error")
        d = e.to_dict()
        
        assert d['level'] == 'L1'
        assert d['type'] == 'NetworkError'
        assert d['recoverable'] is True


class TestCircuitBreaker:
    """測試熔斷器（FR-17）"""
    
    def test_init_default(self):
        """測試初始化預設值"""
        cb = CircuitBreaker()
        assert cb.state == "CLOSED"
    
    def test_init_custom(self):
        """測試自訂初始化"""
        cb = CircuitBreaker(
            failure_threshold=3,
            success_threshold=2,
            recovery_timeout=30
        )
        assert cb._state.failure_threshold == 3
        assert cb._state.success_threshold == 2
        assert cb._state.recovery_timeout == 30
    
    def test_can_execute_closed_state(self):
        """測試 CLOSED 狀態可以執行"""
        cb = CircuitBreaker()
        assert cb.can_execute() is True
    
    def test_can_execute_open_state(self):
        """測試 OPEN 狀態不可執行"""
        cb = CircuitBreaker(failure_threshold=1)
        
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.can_execute() is False
    
    def test_record_success(self):
        """測試記錄成功"""
        cb = CircuitBreaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        
        assert cb._state.failure_count == 3
        
        cb.record_success()
        assert cb._state.failure_count == 0
    
    def test_record_failure(self):
        """測試記錄失敗"""
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        assert cb._state.failure_count == 1
        assert cb.state == "CLOSED"
        
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
    
    def test_recovery_timeout(self):
        """測試恢復超時"""
        cb = CircuitBreaker(recovery_timeout=1, failure_threshold=1)
        
        cb.record_failure()
        assert cb.state == "OPEN"
        
        time.sleep(1.1)
        assert cb.can_execute() is True
        assert cb.state == "HALF_OPEN"
    
    def test_get_status(self):
        """測試取得狀態"""
        cb = CircuitBreaker(failure_threshold=5)
        status = cb.get_status()
        
        assert 'state' in status
        assert 'failure_count' in status
        assert 'failure_threshold' in status
        assert 'recovery_timeout' in status
    
    def test_reset(self):
        """測試重置"""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.state == "OPEN"
        
        cb.reset()
        assert cb.state == "CLOSED"
        assert cb._state.failure_count == 0


class TestRetryPolicy:
    """測試重試策略（FR-16）"""
    
    def test_init_default(self):
        """測試初始化預設值"""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 30.0
        assert policy.multiplier == 2.0
    
    def test_calculate_delay(self):
        """測試計算延遲"""
        policy = RetryPolicy(base_delay=1.0, multiplier=2.0, max_delay=30.0)
        
        assert policy.calculate_delay(0) == 1.0
        assert policy.calculate_delay(1) == 2.0
        assert policy.calculate_delay(2) == 4.0
        assert policy.calculate_delay(3) == 8.0
        assert policy.calculate_delay(10) == 30.0  # 不超過 max_delay
    
    def test_is_retryable(self):
        """測試判斷是否可重試"""
        assert RetryPolicy.is_retryable(NetworkError("test")) is True
        assert RetryPolicy.is_retryable(ServiceError("test")) is True
        assert RetryPolicy.is_retryable(InputError("test")) is False
        assert RetryPolicy.is_retryable(SystemError("test")) is False


class TestErrorHandler:
    """測試 ErrorHandler"""
    
    def test_init(self):
        """測試初始化"""
        handler = ErrorHandler(max_retries=3)
        assert handler.retry_policy.max_retries == 3
        assert handler.circuit_breaker is not None
    
    def test_classify_network_error(self):
        """測試分類網路錯誤"""
        handler = ErrorHandler()
        
        error = ConnectionError("connection failed")
        classified = handler.classify_error(error)
        
        assert isinstance(classified, NetworkError)
    
    def test_classify_timeout_error(self):
        """測試分類超時錯誤"""
        handler = ErrorHandler()
        
        error = TimeoutError("timeout")
        classified = handler.classify_error(error)
        
        assert isinstance(classified, NetworkError)
    
    def test_classify_value_error(self):
        """測試分類值錯誤"""
        handler = ErrorHandler()
        
        error = ValueError("invalid value")
        classified = handler.classify_error(error)
        
        assert isinstance(classified, InputError)
    
    def test_classify_tts_error(self):
        """測試分類已分類的 TTSError"""
        handler = ErrorHandler()
        
        original = NetworkError("original")
        classified = handler.classify_error(original)
        
        assert isinstance(classified, NetworkError)
    
    def test_get_error_stats(self):
        """測試取得錯誤統計"""
        handler = ErrorHandler()
        stats = handler.get_error_stats()
        
        assert 'circuit_breaker' in stats
        assert 'retry_policy' in stats
    
    def test_reset_circuit_breaker(self):
        """測試重置熔斷器"""
        handler = ErrorHandler()
        
        handler.circuit_breaker.record_failure()
        handler.circuit_breaker.record_failure()
        
        handler.reset_circuit_breaker()
        
        assert handler.circuit_breaker.state == "CLOSED"
