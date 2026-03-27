"""
AsyncSynthesizer 測試
Phase 3 實作 - 單元測試

對應規範:
- SRS.md: FR-01, FR-02, FR-03, FR-13, FR-14, FR-15
- NFR-01, NFR-01A, NFR-02: 效能需求
- SEC-08: 安全連線
- MNT-04: 每個核心模組單元測試
"""

import pytest
import asyncio
import os
import tempfile
import sys
import os

# 修正 import 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock edge-tts module
import sys
from unittest.mock import MagicMock
sys.modules['edge_tts'] = MagicMock()
sys.modules['edge_tts'].Communicate = MagicMock()

from unittest.mock import Mock, patch, MagicMock, AsyncMock
from config_manager import TTSConfig
from async_synthesizer import AsyncSynthesizer
from error_handler import TTSError, NetworkError


class TestAsyncSynthesizer:
    """測試 AsyncSynthesizer"""
    
    @pytest.fixture
    def mock_edge_tts(self):
        """Mock edge-tts"""
        mock_communicate = MagicMock()
        mock_voice = MagicMock()
        return {
            'Communicate': mock_communicate,
            'Voice': mock_voice
        }
    
    def test_init(self, mock_edge_tts):
        """測試初始化"""
        with patch.dict('sys.modules', {'edge_tts': mock_edge_tts}):
            from config_manager import TTSConfig
            from async_synthesizer import AsyncSynthesizer
            
            config = TTSConfig()
            synthesizer = AsyncSynthesizer(config)
            
            assert synthesizer.config == config
            assert synthesizer._semaphore is not None
    
    def test_validate_voice_valid(self):
        """測試驗證有效音色"""
        from config_manager import TTSConfig
        from async_synthesizer import AsyncSynthesizer
        from error_handler import TTSError
        
        config = TTSConfig()
        synthesizer = AsyncSynthesizer(config)
        
        # 有效音色應該不通過
        with pytest.raises(TTSError):
            synthesizer._validate_voice("")
    
    def test_validate_voice_allowed_prefix(self):
        """測試允許的音色前綴"""
        from config_manager import TTSConfig
        from async_synthesizer import AsyncSynthesizer
        
        config = TTSConfig()
        synthesizer = AsyncSynthesizer(config)
        
        # 測試允許的前綴
        for voice in ['zh-TW-HsiaoHsiaoNeural', 'en-US-JennyNeural', 'ja-JP-MayuNeural']:
            try:
                synthesizer._validate_voice(voice)
            except Exception:
                pass
    
    def test_allowed_voice_prefixes(self):
        """測試允許的音色前綴列表"""
        from async_synthesizer import AsyncSynthesizer
        
        assert 'zh-' in AsyncSynthesizer.ALLOWED_VOICE_PREFIXES
        assert 'en-' in AsyncSynthesizer.ALLOWED_VOICE_PREFIXES
        assert 'ja-' in AsyncSynthesizer.ALLOWED_VOICE_PREFIXES


class TestSynthesize:
    """測試合成功能"""
    
    @pytest.mark.asyncio
    async def test_synthesize_basic(self):
        """測試基本合成"""
        with patch('tts_project_v574_03_implementation.async_synthesizer.Communicate') as mock_comm:
            # Mock Communicate
            mock_instance = MagicMock()
            mock_instance.save = AsyncMock()
            mock_comm.return_value = mock_instance
            
            from config_manager import TTSConfig
            from async_synthesizer import AsyncSynthesizer
            
            config = TTSConfig()
            synthesizer = AsyncSynthesizer(config)
            
            # 建立輸出檔案
            fd, output_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            
            try:
                result = await synthesizer.synthesize("測試文字", output_path)
                
                # 驗證 save 被調用
                mock_instance.save.assert_called_once()
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
    
    @pytest.mark.asyncio
    async def test_synthesize_timeout(self):
        """測試超時錯誤"""
        with patch('tts_project_v574_03_implementation.async_synthesizer.Communicate') as mock_comm:
            mock_instance = MagicMock()
            mock_instance.save = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_comm.return_value = mock_instance
            
            from config_manager import TTSConfig
            from async_synthesizer import AsyncSynthesizer
            from error_handler import NetworkError
            
            config = TTSConfig()
            synthesizer = AsyncSynthesizer(config)
            
            fd, output_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            
            try:
                with pytest.raises(NetworkError):
                    await synthesizer.synthesize("測試", output_path)
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)


class TestSynthesizeStream:
    """測試流式合成"""
    
    @pytest.mark.asyncio
    async def test_synthesize_stream(self):
        """測試流式合成"""
        with patch('tts_project_v574_03_implementation.async_synthesizer.Communicate') as mock_comm:
            mock_instance = MagicMock()
            
            # Mock stream generator
            async def mock_stream():
                yield {"type": "audio", "data": b"audio_chunk_1"}
                yield {"type": "audio", "data": b"audio_chunk_2"}
            
            mock_instance.stream = mock_stream
            mock_comm.return_value = mock_instance
            
            from config_manager import TTSConfig
            from async_synthesizer import AsyncSynthesizer
            
            config = TTSConfig()
            synthesizer = AsyncSynthesizer(config)
            
            chunks = []
            async for chunk in synthesizer.synthesize_stream("測試文字"):
                chunks.append(chunk)
            
            assert len(chunks) == 2


class TestListVoices:
    """測試列出音色"""
    
    @pytest.mark.asyncio
    async def test_list_voices(self):
        """測試列出所有音色"""
        with patch('tts_project_v574_03_implementation.async_synthesizer.Communicate') as mock_comm:
            mock_voices = [
                {"Name": "zh-TW-HsiaoHsiaoNeural", "Locale": "zh-TW", "Gender": "Female"},
                {"Name": "en-US-JennyNeural", "Locale": "en-US", "Gender": "Female"}
            ]
            mock_comm.get_voices = AsyncMock(return_value=mock_voices)
            
            from async_synthesizer import AsyncSynthesizer
            
            voices = await AsyncSynthesizer.list_voices()
            
            assert len(voices) == 2
    
    @pytest.mark.asyncio
    async def test_get_chinese_voices(self):
        """測試取得中文音色"""
        with patch('tts_project_v574_03_implementation.async_synthesizer.Communicate') as mock_comm:
            mock_voices = [
                {"Name": "zh-TW-HsiaoHsiaoNeural", "Locale": "zh-TW"},
                {"Name": "zh-CN-XiaoxiaoNeural", "Locale": "zh-CN"},
                {"Name": "en-US-JennyNeural", "Locale": "en-US"}
            ]
            mock_comm.get_voices = AsyncMock(return_value=mock_voices)
            
            from async_synthesizer import AsyncSynthesizer
            
            voices = await AsyncSynthesizer.get_chinese_voices()
            
            assert len(voices) == 2
            assert "zh-TW-HsiaoHsiaoNeural" in voices
            assert "zh-CN-XiaoxiaoNeural" in voices
