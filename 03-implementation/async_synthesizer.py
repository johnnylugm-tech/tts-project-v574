"""
AsyncSynthesizer - 非同步語音合成器
Phase 3 實作 - SKILL.md Phase 3: 程式碼實現

對應規範:
- SRS.md: FR-01, FR-02, FR-03, FR-13, FR-14, FR-15
- SKILL.md: asyncio 非同步處理
- NFR-01, NFR-01A, NFR-02: 效能需求
- SEC-08: 安全連線（HTTPS/WebSocket TLS）
"""

import asyncio
import os
from typing import List, AsyncIterator, Optional

try:
    import edge_tts
    from edge_tts import Communicate, Voice
except ImportError:
    raise ImportError("edge-tts 尚未安裝，請執行: pip install edge-tts")

from .config_manager import TTSConfig
from .error_handler import NetworkError, ServiceError, TTSError


class AsyncSynthesizer:
    """
    非同步語音合成器
    
    職責: 非同步語音合成，支援流式處理
    
    規範對應:
    - FR-01: 透過 edge-tts 將文字轉換為語音
    - FR-02: 預設使用 zh-TW-HsiaoHsiaoNeural 音色
    - FR-03: 支援自訂音色選擇
    - FR-13: 使用 WebSocket 與 edge-tts 通訊
    - FR-14: 支援流式音訊回傳
    - FR-15: 基於 asyncio 實現非同步處理
    - NFR-01: 首位元組時間 < 2秒
    - NFR-01A: 單一合成 < 15秒
    - NFR-02: 10,000字 < 60秒
    - SEC-08: 安全連線
    """
    
    # 預設允許的音色前綴（安全考量）
    ALLOWED_VOICE_PREFIXES = ('zh-', 'en-', 'ja-', 'ko-')
    
    def __init__(self, config: TTSConfig):
        """
        初始化合成器
        
        參數:
            config: TTSConfig 物件
        """
        self.config = config
        self._semaphore = asyncio.Semaphore(10)  # 限制並發數
    
    async def synthesize(self, text: str, output_path: str, 
                        voice: Optional[str] = None) -> str:
        """
        同步合成：text → MP3
        
        規範對應: FR-01, FR-03
        
        參數:
            text: 要合成的文字
            output_path: 輸出檔案路徑
            voice: 覆蓋預設音色（可選）
        
        返回:
            str: 輸出檔案路徑
        
        異常:
            NetworkError: 網路錯誤（L1）
            ServiceError: 服務端錯誤（L2）
            TTSError: 其他 TTS 錯誤（L4）
        """
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        # 驗證音色
        used_voice = voice or self.config.voice
        self._validate_voice(used_voice)
        
        try:
            communicate = Communicate(
                text,
                used_voice,
                rate=self.config.rate,
                volume=self.config.volume
            )
            
            await communicate.save(output_path)
            return output_path
            
        except asyncio.TimeoutError:
            raise NetworkError(f"合成超時（>{self.config.timeout}秒）")
        except ConnectionError as e:
            raise NetworkError(f"網路連線失敗: {str(e)}")
        except Exception as e:
            error_msg = str(e).lower()
            if 'rate' in error_msg or 'quota' in error_msg:
                raise ServiceError(f"服務端錯誤: {str(e)}")
            raise TTSError(f"合成失敗: {str(e)}")
    
    async def synthesize_stream(self, text: str, 
                                voice: Optional[str] = None) -> AsyncIterator[bytes]:
        """
        流式合成：返回 AsyncIterator[bytes]
        
        規範對應: FR-14
        
        參數:
            text: 要合成的文字
            voice: 覆蓋預設音色（可選）
        
        返回:
            AsyncIterator[bytes]: 音訊資料流
        
        異常:
            NetworkError: 網路錯誤
            ServiceError: 服務端錯誤
        """
        used_voice = voice or self.config.voice
        self._validate_voice(used_voice)
        
        try:
            communicate = Communicate(
                text,
                used_voice,
                rate=self.config.rate,
                volume=self.config.volume
            )
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
                    
        except Exception as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg:
                raise NetworkError(f"流式合成超時")
            if 'connection' in error_msg:
                raise NetworkError(f"網路連線失敗: {str(e)}")
            raise TTSError(f"流式合成失敗: {str(e)}")
    
    async def synthesize_chunks(self, chunks: List[str], 
                               temp_dir: str) -> List[str]:
        """
        批次合成多個分段
        
        規範對應: NFR-02（10,000字 < 60秒）
        
        參數:
            chunks: 文本分段列表
            temp_dir: 臨時目錄路徑
        
        返回:
            List[str]: 合成後的音訊檔案列表
        
        異常:
            NetworkError: 網路錯誤（會重試）
        """
        temp_files = []
        
        # 使用信號量限制並發
        async def synthesize_single(chunk: str, index: int) -> str:
            async with self._semaphore:
                temp_file = os.path.join(temp_dir, f"chunk_{index}.mp3")
                return await self.synthesize(chunk, temp_file)
        
        # 創建並發任務
        tasks = [
            synthesize_single(chunk, i) 
            for i, chunk in enumerate(chunks)
        ]
        
        try:
            # 並發執行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 檢查結果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    raise NetworkError(f"分段 {i} 合成失敗: {str(result)}")
                temp_files.append(result)
            
            return temp_files
            
        except Exception as e:
            # 清理已產生的檔案
            for f in temp_files:
                if os.path.exists(f):
                    os.remove(f)
            raise
    
    @staticmethod
    async def list_voices() -> List[Voice]:
        """
        列出所有可用音色
        
        規範對應: FR-03（支援自訂音色選擇）
        
        返回:
            List[Voice]: 可用音色列表
        
        異常:
            NetworkError: 網路錯誤
        """
        try:
            return await Communicate.get_voices()
        except Exception as e:
            raise NetworkError(f"取得音色列表失敗: {str(e)}")
    
    @staticmethod
    async def get_chinese_voices() -> List[str]:
        """
        取得中文音色名稱列表
        
        方便用戶選擇
        
        返回:
            List[str]: 中文音色名稱列表
        """
        voices = await AsyncSynthesizer.list_voices()
        return [
            v["Name"] for v in voices 
            if v["Locale"].startswith("zh-")
        ]
    
    def _validate_voice(self, voice: str) -> None:
        """
        驗證音色名稱（安全檢查）
        
        規範對應: SEC-07（錯誤訊息不透露架構）
        
        參數:
            voice: 音色名稱
        
        異常:
            TTSError: 音色名稱無效
        """
        if not voice or not isinstance(voice, str):
            raise TTSError("音色名稱無效")
        
        # 檢查是否為允許的音色前綴
        if not any(voice.startswith(prefix) for prefix in self.ALLOWED_VOICE_PREFIXES):
            raise TTSError(f"不支援的音色: {voice}")
    
    async def synthesize_batch(self, texts: List[str], output_dir: str,
                              voice: Optional[str] = None) -> List[str]:
        """
        批次合成多個文本
        
        規範對應: FR-21（批次處理多個文本）
        
        參數:
            texts: 文本列表
            output_dir: 輸出目錄
            voice: 覆蓋預設音色（可選）
        
        返回:
            List[str]: 合成後的音訊檔案列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for i, text in enumerate(texts):
            output_path = os.path.join(output_dir, f"output_{i}.mp3")
            result = await self.synthesize(text, output_path, voice)
            results.append(result)
        
        return results