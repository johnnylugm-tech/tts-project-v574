"""
TTS Package - 簡報配音系統
Phase 3 實作

模組:
- config_manager: 配置管理
- text_processor: 文本處理
- async_synthesizer: 非同步合成
- audio_merger: 音訊合併
- error_handler: 錯誤處理
- presentation_tts: 主入口
"""

from config_manager import ConfigManager, TTSConfig
from text_processor import TextProcessor
from async_synthesizer import AsyncSynthesizer
from audio_merger import AudioMerger
from error_handler import (
    ErrorHandler,
    TTSError,
    NetworkError,
    ServiceError,
    InputError,
    SystemError,
    CircuitBreaker,
    RetryPolicy
)
from presentation_tts import PresentationTTS, quick_synthesize

__version__ = "1.0.0"

__all__ = [
    # Config
    "ConfigManager",
    "TTSConfig",
    # Text Processing
    "TextProcessor",
    # Synthesis
    "AsyncSynthesizer",
    # Audio
    "AudioMerger",
    # Error Handling
    "ErrorHandler",
    "TTSError",
    "NetworkError",
    "ServiceError",
    "InputError",
    "SystemError",
    "CircuitBreaker",
    "RetryPolicy",
    # Main
    "PresentationTTS",
    "quick_synthesize",
]