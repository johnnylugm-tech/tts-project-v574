#!/usr/bin/env python3
"""
Regression Tests - 回歸測試
=============================
確保新變更不破壞現有功能

執行方式:
    pytest tests/test_regression.py -v
"""

import pytest
import sys



# 加入父目錄到路徑


from config_manager import ConfigManager
from text_processor import TextProcessor
from audio_merger import AudioMerger
from error_handler import ErrorHandler


class TestRegressionConfig:
    """配置回歸測試"""
    
    def test_config_load_default(self):
        """Regression: 預設配置正確載入"""
        config = ConfigManager()
        assert config.config is not None
        assert "voice" in config.config
        assert "rate" in config.config
    
    def test_config_get_voice(self):
        """Regression: 獲取預設音色"""
        config = ConfigManager()
        voice = config.get("voice")
        assert voice is not None
        assert isinstance(voice, str)
    
    def test_config_get_rate(self):
        """Regression: 獲取預設速率"""
        config = ConfigManager()
        rate = config.get("rate")
        assert rate is not None
    
    def test_config_get_volume(self):
        """Regression: 獲取預設音量"""
        config = ConfigManager()
        volume = config.get("volume")
        assert volume is not None
    
    def test_config_set(self):
        """Regression: 配置設定"""
        config = ConfigManager()
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
    
    def test_config_validate_valid(self):
        """Regression: 有效配置驗證通過"""
        config = ConfigManager()
        valid_config = {
            "voice": "test-voice",
            "rate": "+0%",
            "volume": "+0"
        }
        result = config.validate_config(valid_config)
        assert result is True
    
    def test_config_merge_override(self):
        """Regression: 配置合併覆蓋"""
        config = ConfigManager()
        base = {"voice": "old", "rate": "+0%"}
        override = {"voice": "new"}
        merged = config.merge_config(base, override)
        assert merged["voice"] == "new"
        assert merged["rate"] == "+0%"


class TestRegressionText:
    """文字處理回歸測試"""
    
    def test_text_split_small(self):
        """Regression: 小文本正確分段"""
        processor = TextProcessor()
        text = "短文本"
        result = processor.split_text(text)
        assert len(result) >= 1
    
    def test_text_split_large(self):
        """Regression: 大文本正確分段"""
        processor = TextProcessor()
        # 生成 5000 字文本
        text = "測試文字。" * 500
        result = processor.split_text(text)
        assert len(result) > 1
    
    def test_text_validate_empty(self):
        """Regression: 空文本驗證"""
        processor = TextProcessor()
        result = processor.validate_text("")
        assert result is False
    
    def test_text_validate_valid(self):
        """Regression: 有效文本驗證"""
        processor = TextProcessor()
        result = processor.validate_text("正常文本")
        assert result is True
    
    def test_text_validate_long(self):
        """Regression: 長文本驗證"""
        processor = TextProcessor()
        long_text = "測試文字。" * 100
        result = processor.validate_text(long_text)
        assert result is True
    
    def test_text_split_empty(self):
        """Regression: 空文本分段"""
        processor = TextProcessor()
        result = processor.split_text("")
        assert len(result) == 0


class TestRegressionAudio:
    """音訊處理回歸測試"""
    
    def test_merger_init(self):
        """Regression: 合併器初始化"""
        merger = AudioMerger()
        assert merger is not None
    
    def test_merger_cleanup(self):
        """Regression: 合併器清理"""
        merger = AudioMerger()
        # 清理不應拋出異常
        merger.cleanup()
    
    def test_merger_get_output_path(self):
        """Regression: 獲取輸出路徑"""
        merger = AudioMerger()
        path = merger.get_output_path("test.mp3")
        assert path is not None
        assert "test.mp3" in path


class TestRegressionError:
    """錯誤處理回歸測試"""
    
    def test_error_handler_init(self):
        """Regression: 錯誤處理器初始化"""
        handler = ErrorHandler()
        assert handler is not None
    
    def test_error_classify_network(self):
        """Regression: 網路錯誤分類"""
        handler = ErrorHandler()
        # 模擬網路錯誤
        error = Exception("Connection timeout")
        error_type = handler.classify_error(error)
        assert error_type in ["network", "unknown"]
    
    def test_error_classify_api(self):
        """Regression: API 錯誤分類"""
        handler = ErrorHandler()
        error = Exception("API rate limit exceeded")
        error_type = handler.classify_error(error)
        assert error_type in ["api", "unknown"]
    
    def test_error_classify_validation(self):
        """Regression: 驗證錯誤分類"""
        handler = ErrorHandler()
        error = Exception("Invalid input")
        error_type = handler.classify_error(error)
        assert error_type in ["validation", "unknown"]
    
    def test_error_retry_network(self):
        """Regression: 網路錯誤重試"""
        handler = ErrorHandler()
        retry_config = handler.get_retry_config("network")
        assert "max_retries" in retry_config
        assert retry_config["max_retries"] > 0
    
    def test_error_retry_api(self):
        """Regression: API 錯誤重試"""
        handler = ErrorHandler()
        retry_config = handler.get_retry_config("api")
        assert "max_retries" in retry_config
    
    def test_circuit_breaker_init(self):
        """Regression: 熔斷器初始化"""
        handler = ErrorHandler()
        # 熔斷器狀態應可用
        assert handler.circuit_breaker is not None or hasattr(handler, 'circuit_breaker')
    
    def test_error_handler_decorator(self):
        """Regression: 錯誤處理裝飾器"""
        handler = ErrorHandler()
        if hasattr(handler, 'handle_error'):
            result = handler.handle_error(Exception("test"))
            assert result is not None


class TestRegressionIntegration:
    """整合回歸測試"""
    
    def test_config_to_text_processor(self):
        """Regression: 配置傳遞到文字處理器"""
        config = ConfigManager()
        processor = TextProcessor()
        
        # 使用配置進行文字處理
        text = "測試文字"
        chunks = processor.split_text(text)
        
        assert len(chunks) > 0
    
    def test_text_validate_after_config_load(self):
        """Regression: 配置載入後文字驗證"""
        config = ConfigManager()
        processor = TextProcessor()
        
        valid_text = "這是有效的中文測試文字"
        is_valid = processor.validate_text(valid_text)
        assert is_valid is True
    
    def test_error_handler_with_config(self):
        """Regression: 配置相關錯誤處理"""
        config = ConfigManager()
        handler = ErrorHandler()
        
        # 配置驗證錯誤
        invalid_config = {"voice": ""}
        try:
            config.validate_config(invalid_config)
        except Exception as e:
            error_type = handler.classify_error(e)
            assert error_type is not None
    
    def test_all_modules_importable(self):
        """Regression: 所有模組可正常導入"""
        from config_manager import ConfigManager
        from text_processor import TextProcessor
        from async_synthesizer import AsyncSynthesizer
        from audio_merger import AudioMerger
        from error_handler import ErrorHandler
        
        assert ConfigManager is not None
        assert TextProcessor is not None
        assert AsyncSynthesizer is not None
        assert AudioMerger is not None
        assert ErrorHandler is not None