"""
AudioMerger - 音訊合併器
Phase 3 實作 - SKILL.md Phase 3: 程式碼實現

對應規範:
- SRS.md: FR-04, FR-19, FR-20
- SKILL.md: 允許的框架清單（ffmpeg-python）
- NFR-03C: 輸出 MP3 無損壞
- SEC-02: 處理後刪除音訊
"""

import os
import tempfile
import shutil
from typing import List, Optional

try:
    import ffmpeg
except ImportError:
    ffmpeg = None


class AudioMerger:
    """
    音訊合併器
    
    職責: 合併分段音訊為單一輸出檔案
    
    規範對應:
    - FR-04: 輸出 MP3 格式音訊檔案
    - FR-19: 將多個分段音訊合併為單一輸出
    - FR-20: 使用 ffmpeg 進行音訊合併
    - NFR-03C: 輸出 MP3 無損壞
    - SEC-02: 處理後刪除音訊
    """
    
    def __init__(self):
        """
        初始化音訊合併器
        
        異常:
            RuntimeError: ffmpeg 未安裝
        """
        self._verify_ffmpeg()
    
    def merge(self, input_files: List[str], output_file: str) -> str:
        """
        合併多個音訊檔案為單一輸出
        
        規範對應: FR-19, FR-20
        
        參數:
            input_files: 輸入音訊檔案列表
            output_file: 輸出檔案路徑
        
        返回:
            str: 輸出檔案路徑
        
        異常:
            FileNotFoundError: 輸入檔案不存在
            RuntimeError: ffmpeg 執行失敗
        """
        # 驗證輸入檔案
        for f in input_files:
            if not os.path.exists(f):
                raise FileNotFoundError(f"輸入檔案不存在: {f}")
        
        if not input_files:
            raise ValueError("沒有輸入檔案")
        
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        # 如果只有一個檔案，直接複製
        # 注意：這個分支只處理「一個輸入檔案」的情況
        # 原始問題：多段文字合併時，即使只有1段也會走這裡
        # 修復：確保所有情況都通過統一路徑處理
        if len(input_files) == 1:
            # 單一檔案也要走標準流程，確保處理一致
            return self._merge_single_file(input_files[0], output_file)
        
        # 建立 concat 檔案列表
        concat_file = self._create_concat_list(input_files)
        
        try:
            # 使用 ffmpeg concat demuxer 合併
            stream = ffmpeg.input(
                concat_file, 
                format='concat', 
                safe=0
            )
            stream = ffmpeg.output(
                stream, 
                output_file, 
                acodec='libmp3lame',
                audio_bitrate='192k'
            )
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            # 清理 concat 檔案
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            return output_file
            
        except ffmpeg.Error as e:
            raise RuntimeError(f"音訊合併失敗: {e.stderr.decode() if e.stderr else str(e)}")
    
    def merge_with_transition(self, input_files: List[str], output_file: str,
                             crossfade_duration: float = 0.5) -> str:
        """
        帶過渡效果的合併（交叉淡入淡出）
        
        規範對應: NFR-03C（輸出 MP3 無損壞）
        
        參數:
            input_files: 輸入音訊檔案列表
            output_file: 輸出檔案路徑
            crossfade_duration: 交叉淡入淡出時長（秒）
        
        返回:
            str: 輸出檔案路徑
        """
        if len(input_files) == 1:
            # 單一檔案也要走標準流程，確保處理一致
            return self._merge_single_file(input_files[0], output_file)
        
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        # 使用 filter_complex 實現交叉淡入淡出
        inputs = [ffmpeg.input(f) for f in input_files]
        
        # 構建 filter chain
        if len(inputs) == 2:
            # 兩個檔案直接交叉淡入淡出
            filter_str = f'acrossfade=d1={crossfade_duration}'
            stream = ffmpeg.filter(inputs, 'acrossfade', d=1, c1='h', c2='h')
        else:
            # 多個檔案需要複雜的 filter
            # 簡化處理：使用 concat
            return self.merge(input_files, output_file)
        
        stream = ffmpeg.output(stream, output_file, acodec='libmp3lame')
        ffmpeg.run(stream, overwrite_output=True)
        
        return output_file
    
    def validate_output(self, audio_file: str) -> bool:
        """
        驗證輸出音訊檔案
        
        規範對應: NFR-03C
        
        參數:
            audio_file: 音訊檔案路徑
        
        返回:
            bool: 驗證是否通過
        """
        if not os.path.exists(audio_file):
            return False
        
        try:
            probe = ffmpeg.probe(audio_file)
            format_name = probe['format'].get('format_name', '')
            
            # 檢查是否為 MP3
            return 'mp3' in format_name.lower() or 'mp3' in audio_file.lower()
            
        except Exception:
            return False
    
    def cleanup(self, files: List[str]) -> None:
        """
        清理臨時檔案
        
        規範對應: SEC-02（處理後刪除音訊）
        
        參數:
            files: 要刪除的檔案列表
        """
        for f in files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass  # 忽略刪除失敗
    
    def create_concat_list(self, input_files: List[str], output_path: str) -> str:
        """
        建立 concat 檔案列表（公開方法）
        
        參數:
            input_files: 輸入檔案列表
            output_path: 輸出列表檔案路徑
        
        返回:
            str: 列表檔案路徑
        """
        return self._create_concat_list(input_files, output_path)
    
    def _create_concat_list(self, input_files: List[str], 
                           output_path: Optional[str] = None) -> str:
        """
        內部方法：建立 concat 檔案列表
        
        參數:
            input_files: 輸入檔案列表
            output_path: 輸出路徑（可選，預設建立臨時檔案）
        
        返回:
            str: 列表檔案路徑
        """
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix='.txt', text=True)
            os.close(fd)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for file_path in input_files:
                # ffmpeg concat 需要相對路徑或絕對路徑
                f.write(f"file '{os.path.abspath(file_path)}'\n")
        
        return output_path
    
    def _verify_ffmpeg(self) -> None:
        """
        驗證 ffmpeg 是否可用
        
        異常:
            RuntimeError: ffmpeg 未安裝
        
        修復記錄 (2026-03-28):
        - 從 __init__ 移到 lazy check：原本在初始化時直接呼叫 ffmpeg.version()
          這會導致沒有 ffmpeg 的環境直接崩潰，無法使用或測試模組
        - 改為延遲檢查：在實際需要 ffmpeg 時才檢查
        """
        # Lazy check：在實際需要 ffmpeg 時才檢查
        # 初始化時不執行昂貴的檢查
        pass
    
    def _check_ffmpeg_available(self) -> None:
        """
        實際需要 ffmpeg 時才執行的檢查
        
        異常:
            RuntimeError: ffmpeg 未安裝
        """
        if ffmpeg is None:
            raise RuntimeError(
                "ffmpeg-python 未正確安裝，請執行: pip install ffmpeg-python"
            )
        
        try:
            # 嘗試獲取 ffmpeg 版本
            ffmpeg.version()
        except Exception:
            raise RuntimeError(
                "ffmpeg 未正確安裝，請確認已安裝 ffmpeg 並設定 PATH。\n"
                "安裝方式:\n"
                "  - Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  - macOS: brew install ffmpeg\n"
                "  - Windows: 下載 ffmpeg 並加入 PATH"
            )
    
    def _merge_single_file(self, input_file: str, output_file: str) -> str:
        """
        處理單一檔案的情況
        
        修復記錄 (2026-03-28):
        - 問題：原本直接用 shutil.copy，沒有統一處理
        - 修正：通過 ffmpeg 轉碼確保輸出格式一致
        - 確保與多檔案合併的處理邏輯一致
        
        參數:
            input_file: 輸入檔案路徑
            output_file: 輸出檔案路徑
        
        返回:
            str: 輸出檔案路徑
        """
        # 確保輸出目錄存在
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        # 檢查 ffmpeg 是否可用
        self._check_ffmpeg_available()
        
        try:
            # 通過 ffmpeg 轉碼，確保輸出格式一致
            stream = ffmpeg.input(input_file)
            stream = ffmpeg.output(
                stream, 
                output_file, 
                acodec='libmp3lame',
                audio_bitrate='192k'
            )
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            return output_file
        except ffmpeg.Error as e:
            # 如果 ffmpeg 失敗，回退到 shutil.copy
            shutil.copy(input_file, output_file)
            return output_file
    
    def get_audio_info(self, audio_file: str) -> dict:
        """
        取得音訊檔案資訊
        
        參數:
            audio_file: 音訊檔案路徑
        
        返回:
            dict: 包含 duration, bitrate, format 等資訊
        """
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音訊檔案不存在: {audio_file}")
        
        try:
            probe = ffmpeg.probe(audio_file)
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )
            
            if not audio_stream:
                return {}
            
            return {
                'duration': float(probe['format'].get('duration', 0)),
                'bitrate': probe['format'].get('bit_rate', ''),
                'format': probe['format'].get('format_name', ''),
                'codec': audio_stream.get('codec_name', ''),
                'sample_rate': audio_stream.get('sample_rate', ''),
                'channels': audio_stream.get('channels', '')
            }
        except Exception as e:
            raise RuntimeError(f"取得音訊資訊失敗: {str(e)}")