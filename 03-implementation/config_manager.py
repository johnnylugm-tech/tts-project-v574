"""
ConfigManager - 配置管理器
Phase 3 實作 - SKILL.md Phase 3: 程式碼實現

對應規範:
- SRS.md: FR-09, FR-10, FR-11, FR-12
- SKILL.md: frozen dataclass
- MNT-03: 必須使用 frozen dataclass 配置
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import os


@dataclass(frozen=True)
class TTSConfig:
    """
    TTS 配置參數（frozen dataclass）
    
    規範對應:
    - FR-11: 預設語速為 -2%（略慢）
    - FR-12: 預設音量為 +0%（標準）
    - MNT-03: 必須使用 frozen dataclass 配置
    
    屬性:
        voice: 音色名稱，預設 zh-TW-HsiaoHsiaoNeural
        rate: 語速調整，範圍 -100% ~ +100%
        volume: 音量調整，範圍 -100% ~ +100%
        chunk_size: 分段大小，預設 800 字
        max_text_length: 最大文字長度，預設 20000 字
        retry_count: 重試次數，預設 3 次
        timeout: 請求超時秒數，預設 60 秒
    """
    voice: str = "zh-TW-HsiaoHsiaoNeural"
    rate: str = "-2%"
    volume: str = "+0%"
    chunk_size: int = 800
    max_text_length: int = 20000
    retry_count: int = 3
    timeout: int = 60


class ConfigManager:
    """
    配置管理器
    
    職責: 統一管理所有配置參數，確保不可變性
    
    規範對應:
    - FR-09: 支援語速參數調整
    - FR-10: 支援音量參數調整
    - MNT-07: 新增音色只需修改配置
    """
    
    @staticmethod
    def create_default() -> TTSConfig:
        """
        建立預設配置
        
        規範對應: FR-11, FR-12
        
        返回:
            TTSConfig: 預設配置物件
        """
        return TTSConfig()
    
    @staticmethod
    def from_file(config_path: str) -> TTSConfig:
        """
        從檔案載入配置
        
        規範對應: NFR-05D（音色版本穩定性）
        
        參數:
            config_path: 配置文件路徑（JSON 格式）
        
        返回:
            TTSConfig: 從檔案載入的配置
        
        異常:
            FileNotFoundError: 檔案不存在
            ValueError: 配置格式錯誤
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 驗證必要欄位
        valid_fields = {'voice', 'rate', 'volume', 'chunk_size', 
                        'max_text_length', 'retry_count', 'timeout'}
        
        # 只提取有效欄位
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        try:
            return TTSConfig(**filtered_data)
        except TypeError as e:
            raise ValueError(f"配置格式錯誤: {e}")
    
    @staticmethod
    def to_file(config: TTSConfig, config_path: str) -> None:
        """
        將配置寫入檔案
        
        參數:
            config: TTSConfig 物件
            config_path: 目標檔案路徑
        """
        data = {
            'voice': config.voice,
            'rate': config.rate,
            'volume': config.volume,
            'chunk_size': config.chunk_size,
            'max_text_length': config.max_text_length,
            'retry_count': config.retry_count,
            'timeout': config.timeout
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def validate(config: TTSConfig) -> bool:
        """
        驗證配置參數
        
        規範對應: NFR-09（依賴邊界清晰）
        
        參數:
            config: TTSConfig 物件
        
        返回:
            bool: 驗證是否通過
        """
        # 驗證音色（非空）
        if not config.voice or not isinstance(config.voice, str):
            return False
        
        # 驗證 rate 格式（百分比）
        if not isinstance(config.rate, str) or not config.rate.endswith('%'):
            return False
        
        # 驗證 volume 格式
        if not isinstance(config.volume, str) or not config.volume.endswith('%'):
            return False
        
        # 驗證數值範圍
        if config.chunk_size <= 0 or config.chunk_size > 10000:
            return False
        if config.max_text_length <= 0 or config.max_text_length > 100000:
            return False
        if config.retry_count < 0 or config.retry_count > 10:
            return False
        if config.timeout <= 0 or config.timeout > 300:
            return False
        
        return True
    
    @staticmethod
    def merge_configs(base: TTSConfig, **overrides) -> TTSConfig:
        """
        合併配置（基礎配置 + 覆蓋值）
        
        規範對應: FR-03（支援自訂音色選擇）
        
        參數:
            base: 基礎配置
            **overrides: 覆蓋的參數
        
        返回:
            TTSConfig: 合併後的配置
        """
        base_dict = {
            'voice': base.voice,
            'rate': base.rate,
            'volume': base.volume,
            'chunk_size': base.chunk_size,
            'max_text_length': base.max_text_length,
            'retry_count': base.retry_count,
            'timeout': base.timeout
        }
        
        # 合併覆蓋值
        base_dict.update({k: v for k, v in overrides.items() 
                         if k in base_dict and v is not None})
        
        return TTSConfig(**base_dict)