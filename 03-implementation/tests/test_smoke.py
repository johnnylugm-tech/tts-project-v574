"""
Smoke Tests
"""

import pytest
from config_manager import ConfigManager, TTSConfig
from text_processor import TextProcessor
from audio_merger import AudioMerger
from error_handler import ErrorHandler


class TestSmokeBasicSynthesize:
    def test_config_init(self):
        config = ConfigManager()
        assert config is not None
    
    def test_config_create_default(self):
        config = ConfigManager.create_default()
        assert isinstance(config, TTSConfig)
        assert config.voice == "zh-TW-HsiaoHsiaoNeural"
    
    def test_text_processor_init(self):
        processor = TextProcessor()
        assert processor.chunk_size == 800
    
    def test_text_split_basic(self):
        processor = TextProcessor()
        result = processor.split_by_punctuation("第一句。第二句")
        assert len(result) == 2
    
    def test_audio_merger_init(self):
        merger = AudioMerger()
        assert merger is not None
    
    def test_error_handler_init(self):
        handler = ErrorHandler()
        assert handler is not None
    
    def test_error_classification(self):
        handler = ErrorHandler()
        error_type = handler.classify_error(Exception("Network error"))
        assert error_type is not None


class TestSmokeCoreFeatures:
    def test_config_validation(self):
        config = ConfigManager.create_default()
        result = ConfigManager.validate(config)
        assert result == True
    
    def test_text_validate(self):
        processor = TextProcessor()
        assert processor.validate_input("valid text") == True
    
    def test_config_merge(self):
        config = ConfigManager.create_default()
        result = ConfigManager.merge_configs(config)
        assert isinstance(result, TTSConfig)
    
    def test_error_retry_config(self):
        config = ConfigManager.create_default()
        assert config.retry_count == 3