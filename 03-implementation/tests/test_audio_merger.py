"""
AudioMerger 測試
Phase 3 實作 - 單元測試

對應規範:
- SRS.md: FR-04, FR-19, FR-20
- NFR-03C: 輸出 MP3 無損壞
- SEC-02: 處理後刪除音訊
- MNT-04: 每個核心模組單元測試
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import sys
sys.modules['ffmpeg'] = MagicMock()


class TestAudioMerger:
    """測試 AudioMerger"""
    
    def test_init(self):
        """測試初始化"""
        with patch.dict('sys.modules', {'ffmpeg': MagicMock()}):
            from tts_project_v574_03_implementation.audio_merger import AudioMerger
            merger = AudioMerger()
            assert merger is not None


class TestCleanup:
    """測試清理功能（SEC-02）"""
    
    def test_cleanup_existing_files(self):
        """測試清理存在的檔案"""
        from tts_project_v574_03_implementation.audio_merger import AudioMerger
        merger = AudioMerger()
        temp_files = []
        for i in range(3):
            fd, path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            temp_files.append(path)
        merger.cleanup(temp_files)
        for f in temp_files:
            assert not os.path.exists(f)
    
    def test_cleanup_nonexistent_files(self):
        """測試清理不存在的檔案"""
        from tts_project_v574_03_implementation.audio_merger import AudioMerger
        merger = AudioMerger()
        merger.cleanup(['/nonexistent/file1.mp3', '/nonexistent/file2.mp3'])


class TestCreateConcatList:
    """測試建立 concat 列表"""
    
    def test_create_concat_list(self):
        """測試建立 concat 檔案列表"""
        from tts_project_v574_03_implementation.audio_merger import AudioMerger
        merger = AudioMerger()
        temp_files = []
        for i in range(3):
            fd, path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            temp_files.append(path)
        try:
            concat_path = merger.create_concat_list(temp_files)
            assert os.path.exists(concat_path)
            with open(concat_path, 'r') as f:
                content = f.read()
                assert 'file' in content
            os.unlink(concat_path)
        finally:
            for f in temp_files:
                if os.path.exists(f):
                    os.unlink(f)


class TestMerge:
    """測試合併功能"""
    
    @patch('tts_project_v574_03_implementation.audio_merger.ffmpeg')
    def test_merge_single_file(self, mock_ffmpeg):
        """測試單一檔案合併"""
        from tts_project_v574_03_implementation.audio_merger import AudioMerger
        merger = AudioMerger()
        fd, input_path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)
        output_path = tempfile.mktemp(suffix='.mp3')
        try:
            result = merger.merge([input_path], output_path)
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_merge_empty_list(self):
        """測試空列表合併"""
        from tts_project_v574_03_implementation.audio_merger import AudioMerger
        merger = AudioMerger()
        with pytest.raises(ValueError):
            merger.merge([], "output.mp3")
    
    def test_merge_nonexistent_input(self):
        """測試不存在的輸入檔案"""
        from tts_project_v574_03_implementation.audio_merger import AudioMerger
        merger = AudioMerger()
        with pytest.raises(FileNotFoundError):
            merger.merge(["/nonexistent/file.mp3"], "output.mp3")
