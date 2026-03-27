"""
PresentationTTS - 簡報配音 TTS 系統主入口
Phase 3 實作 - SKILL.md Phase 3: 程式碼實現

對應規範:
- SRS.md: FR-21（批次處理多個文本）
- SKILL.md: 整合所有模組
- MNT-01: 單一職責原則
- MNT-05: 整合測試
"""

import asyncio
import os
import tempfile
import shutil
from typing import List, Optional, Dict

from config_manager import ConfigManager, TTSConfig
from text_processor import TextProcessor
from async_synthesizer import AsyncSynthesizer
from audio_merger import AudioMerger
from error_handler import (
    ErrorHandler, 
    TTSError, 
    InputError, 
    NetworkError,
    ServiceError
)


class PresentationTTS:
    """
    簡報配音 TTS 系統 - 主入口
    
    職責: 協調所有模組，提供完整的 TTS 流程
    
    規範對應:
    - FR-21: 批次處理多個文本
    - NFR-01: 首位元組時間 < 2秒
    - NFR-02: 10,000字 < 60秒
    - MNT-05: 整合測試
    """
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """
        初始化 PresentationTTS
        
        參數:
            config: TTSConfig 物件（可選）
        """
        self.config = config or ConfigManager.create_default()
        
        if not ConfigManager.validate(self.config):
            raise InputError("配置參數無效")
        
        self.text_processor = TextProcessor(self.config.chunk_size)
        self.synthesizer = AsyncSynthesizer(self.config)
        self.audio_merger = AudioMerger()
        self.error_handler = ErrorHandler(
            max_retries=self.config.retry_count,
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=60
        )
        
        self._temp_dir: Optional[str] = None
    
    async def synthesize(self, text: str, output_file: str,
                        voice: Optional[str] = None) -> str:
        """
        完整合成流程：text → MP3
        
        流程:
        1. 驗證輸入
        2. 文本分段
        3. 批次合成
        4. 音訊合併
        5. 清理臨時檔案
        """
        if not self.text_processor.validate_input(
            text, self.config.max_text_length
        ):
            raise InputError(
                f"文字長度需在 1-{self.config.max_text_length} 字之間"
            )
        
        chunks = self.text_processor.split(text)
        
        if not chunks:
            raise InputError("文本分段失敗")
        
        self._temp_dir = tempfile.mkdtemp(prefix="tts_")
        
        try:
            temp_files = await self._synthesize_with_retry(chunks, voice)
            result = self.audio_merger.merge(temp_files, output_file)
            
            if not self.audio_merger.validate_output(result):
                raise TTSError("輸出音訊驗證失敗")
            
            return result
        finally:
            self._cleanup_temp()
    
    async def synthesize_stream(self, text: str,
                               voice: Optional[str] = None) -> bytes:
        """流式合成"""
        if not self.text_processor.validate_input(
            text, self.config.max_text_length
        ):
            raise InputError(
                f"文字長度需在 1-{self.config.max_text_length} 字之間"
            )
        
        audio_chunks = []
        async for chunk in self.synthesizer.synthesize_stream(text, voice):
            audio_chunks.append(chunk)
        
        return b''.join(audio_chunks)
    
    async def synthesize_batch(self, texts: List[str], output_dir: str,
                             voice: Optional[str] = None) -> List[str]:
        """批次合成多個文本"""
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for i, text in enumerate(texts):
            output_path = os.path.join(output_dir, f"output_{i}.mp3")
            try:
                result = await self.synthesize(text, output_path, voice)
                results.append(result)
            except TTSError as e:
                results.append(str(e))
        
        return results
    
    def get_text_info(self, text: str) -> Dict:
        """取得文本資訊"""
        return self.text_processor.get_text_info(text)
    
    async def get_available_voices(self) -> List[str]:
        """取得所有可用音色"""
        return await AsyncSynthesizer.get_chinese_voices()
    
    async def _synthesize_with_retry(self, chunks: List[str],
                                    voice: Optional[str] = None) -> List[str]:
        """帶重試的合成"""
        last_error = None
        
        for attempt in range(self.config.retry_count):
            try:
                return await self.synthesizer.synthesize_chunks(
                    chunks, self._temp_dir
                )
            except (NetworkError, ServiceError) as e:
                last_error = e
                if attempt < self.config.retry_count - 1:
                    delay = 2 ** attempt
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
        
        raise last_error
    
    def _cleanup_temp(self) -> None:
        """清理臨時目錄"""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except Exception:
                pass
            finally:
                self._temp_dir = None
    
    def __del__(self):
        self._cleanup_temp()
    
    @classmethod
    def from_file(cls, config_path: str) -> 'PresentationTTS':
        """從檔案建立實例"""
        config = ConfigManager.from_file(config_path)
        return cls(config)
    
    @staticmethod
    async def list_all_voices() -> List[dict]:
        """列出所有可用音色"""
        voices = await AsyncSynthesizer.list_voices()
        return [
            {
                "name": v["Name"],
                "locale": v["Locale"],
                "gender": v.get("Gender", "Unknown"),
                "short_name": v.get("ShortName", "")
            }
            for v in voices
        ]


async def quick_synthesize(text: str, output_file: str,
                           voice: str = "zh-TW-HsiaoHsiaoNeural") -> str:
    """快速合成"""
    config = TTSConfig(voice=voice)
    tts = PresentationTTS(config)
    return await tts.synthesize(text, output_file)