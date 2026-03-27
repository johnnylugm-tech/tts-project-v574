"""
ConfigManager 測試
Phase 3 實作 - 單元測試

對應規範:
- SRS.md: FR-09, FR-10, FR-11, FR-12
- MNT-03: frozen dataclass 配置
- MNT-04: 每個核心模組單元測試

**模組標註**：SKILL.md - Phase 3: 代碼實現 (SWE.3) - 測試
"""

import pytest
import json
import tempfile

import sys


# 修正 import 路徑

from config_manager import ConfigManager, TTSConfig


class TestTTSConfig:
    """測試 TTSConfig frozen dataclass"""
    
    def test_default_values(self):
        """測試預設值（FR-11, FR-12）"""
        config = TTSConfig()
        
        assert config.voice == "zh-TW-HsiaoHsiaoNeural"
        assert config.rate == "-2%"
        assert config.volume == "+0%"
        assert config.chunk_size == 800
        assert config.max_text_length == 20000
        assert config.retry_count == 3
        assert config.timeout == 60
    
    def test_frozen_immutability(self):
        """測試 frozen 不可變性（MNT-03）"""
        config = TTSConfig()
        
        with pytest.raises(Exception):
            config.voice = "zh-TW-YunJiaNeural"
    
    def test_custom_values(self):
        """測試自訂值"""
        config = TTSConfig(
            voice="zh-TW-YunJiaNeural",
            rate="+10%",
            volume="+20%",
            chunk_size=1000,
            max_text_length=30000,
            retry_count=5,
            timeout=120
        )
        
        assert config.voice == "zh-TW-YunJiaNeural"
        assert config.rate == "+10%"
        assert config.volume == "+20%"
        assert config.chunk_size == 1000
        assert config.max_text_length == 30000
        assert config.retry_count == 5
        assert config.timeout == 120


class TestConfigManager:
    """測試 ConfigManager"""
    
    def test_create_default(self):
        """測試建立預設配置"""
        config = ConfigManager.create_default()
        
        assert isinstance(config, TTSConfig)
        assert config.voice == "zh-TW-HsiaoHsiaoNeural"
    
    def test_validate_valid_config(self):
        """測試驗證有效配置"""
        config = TTSConfig()
        assert ConfigManager.validate(config) is True
    
    def test_validate_invalid_voice(self):
        """測試無效音色"""
        config = TTSConfig(voice="")
        assert ConfigManager.validate(config) is False
    
    def test_validate_invalid_rate(self):
        """測試無效 rate 格式"""
        config = TTSConfig(rate="invalid")
        assert ConfigManager.validate(config) is False
    
    def test_validate_invalid_chunk_size(self):
        """測試無效 chunk_size"""
        config = TTSConfig(chunk_size=0)
        assert ConfigManager.validate(config) is False
        
        config = TTSConfig(chunk_size=20000)
        assert ConfigManager.validate(config) is False
    
    def test_validate_invalid_max_text_length(self):
        """測試無效 max_text_length"""
        config = TTSConfig(max_text_length=0)
        assert ConfigManager.validate(config) is False
    
    def test_validate_invalid_retry_count(self):
        """測試無效 retry_count"""
        config = TTSConfig(retry_count=-1)
        assert ConfigManager.validate(config) is False
        
        config = TTSConfig(retry_count=20)
        assert ConfigManager.validate(config) is False
    
    def test_validate_invalid_timeout(self):
        """測試無效 timeout"""
        config = TTSConfig(timeout=0)
        assert ConfigManager.validate(config) is False
        
        config = TTSConfig(timeout=500)
        assert ConfigManager.validate(config) is False
    
    def test_from_file(self):
        """測試從檔案載入配置"""
        config_data = {
            "voice": "zh-TW-YunJiaNeural",
            "rate": "+5%",
            "volume": "+10%",
            "chunk_size": 500,
            "max_text_length": 15000,
            "retry_count": 2,
            "timeout": 30
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigManager.from_file(temp_path)
            
            assert config.voice == "zh-TW-YunJiaNeural"
            assert config.rate == "+5%"
            assert config.volume == "+10%"
            assert config.chunk_size == 500
            assert config.max_text_length == 15000
            assert config.retry_count == 2
            assert config.timeout == 30
        finally:
            os.unlink(temp_path)
    
    def test_from_file_not_found(self):
        """測試檔案不存在"""
        with pytest.raises(FileNotFoundError):
            ConfigManager.from_file("/nonexistent/config.json")
    
    def test_from_file_invalid_format(self):
        """測試檔案格式錯誤"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                ConfigManager.from_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_to_file(self):
        """測試寫入配置到檔案"""
        config = TTSConfig(
            voice="zh-TW-YunJiaNeural",
            rate="+10%"
        )
        
        temp_path = tempfile.mktemp(suffix='.json')
        
        try:
            ConfigManager.to_file(config, temp_path)
            
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data['voice'] == "zh-TW-YunJiaNeural"
            assert data['rate'] == "+10%"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_merge_configs(self):
        """測試合併配置（FR-03）"""
        base = TTSConfig(
            voice="zh-TW-HsiaoHsiaoNeural",
            rate="-2%",
            volume="+0%"
        )
        
        merged = ConfigManager.merge_configs(
            base,
            voice="zh-TW-YunJiaNeural",
            rate="+10%"
        )
        
        assert merged.voice == "zh-TW-YunJiaNeural"
        assert merged.rate == "+10%"
        assert merged.volume == "+0%"  # 保持不變
    
    def test_merge_configs_ignore_none(self):
        """測試合併時忽略 None 值"""
        base = TTSConfig(chunk_size=800)
        
        merged = ConfigManager.merge_configs(
            base,
            chunk_size=None
        )
        
        assert merged.chunk_size == 800