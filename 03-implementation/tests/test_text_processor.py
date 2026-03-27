"""
TextProcessor 測試
Phase 3 實作 - 單元測試

對應規範:
- SRS.md: FR-05, FR-06, FR-07, FR-08
- MNT-08: 文本分段邏輯模組化
- MNT-04: 每個核心模組單元測試
"""

import pytest
import sys
import os

# 修正 import 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from text_processor import TextProcessor


class TestTextProcessor:
    """測試 TextProcessor"""
    
    def test_init_default(self):
        """測試初始化預設值"""
        processor = TextProcessor()
        assert processor.chunk_size == 800
    
    def test_init_custom_chunk_size(self):
        """測試自訂 chunk_size"""
        processor = TextProcessor(chunk_size=500)
        assert processor.chunk_size == 500


class TestSplitByPunctuation:
    """測試按標點分段（FR-05）"""
    
    def test_split_by_period(self):
        """測試句號分段"""
        processor = TextProcessor()
        text = "這是第一句。這是第二句。這是第三句。"
        
        result = processor.split_by_punctuation(text)
        
        assert len(result) == 3
        assert result[0] == "這是第一句"
        assert result[1] == "這是第二句"
        assert result[2] == "這是第三句"
    
    def test_split_by_question_mark(self):
        """測試問號分段"""
        processor = TextProcessor()
        text = "這是問題嗎？這是另一個問題？"
        
        result = processor.split_by_punctuation(text)
        
        assert len(result) == 2
    
    def test_split_by_exclamation(self):
        """測試驚嘆號分段"""
        processor = TextProcessor()
        text = "太棒了！真的太好了！"
        
        result = processor.split_by_punctuation(text)
        
        assert len(result) == 2
    
    def test_split_by_mixed_punctuation(self):
        """測試混合標點"""
        processor = TextProcessor()
        text = "你好！世界。怎麼樣？"
        
        result = processor.split_by_punctuation(text)
        
        assert len(result) == 3
    
    def test_split_empty_text(self):
        """測試空文字"""
        processor = TextProcessor()
        result = processor.split_by_punctuation("")
        
        assert result == []
    
    def test_split_text_with_only_punctuation(self):
        """測試只有標點的文字"""
        processor = TextProcessor()
        result = processor.split_by_punctuation("。？！")
        
        assert result == []


class TestSplitByNewline:
    """測試按換行分段（FR-06）"""
    
    def test_split_by_newline(self):
        """測試換行分段"""
        processor = TextProcessor()
        text = "第一行\n第二行\n第三行"
        
        result = processor.split_by_newline(text)
        
        assert len(result) == 3
        assert result[0] == "第一行"
        assert result[1] == "第二行"
        assert result[2] == "第三行"
    
    def test_split_by_multiple_newlines(self):
        """測試多個連續換行"""
        processor = TextProcessor()
        text = "第一行\n\n\n第二行\n\n第三行"
        
        result = processor.split_by_newline(text)
        
        assert len(result) == 3
    
    def test_split_newline_empty(self):
        """測試空文字"""
        processor = TextProcessor()
        result = processor.split_by_newline("")
        
        assert result == []


class TestChunkByLength:
    """測試按長度分塊（FR-07）"""
    
    def test_chunk_small_text(self):
        """測試小於限制的文字"""
        processor = TextProcessor(chunk_size=800)
        text = "短文字"
        
        result = processor.chunk_by_length(text)
        
        assert len(result) == 1
        assert result[0] == "短文字"
    
    def test_chunk_long_text(self):
        """測試大於限制的文字"""
        processor = TextProcessor(chunk_size=10)
        text = "這是一個很長的文字需要被分割"
        
        result = processor.chunk_by_length(text)
        
        # 應該被分割成多個 chunk
        assert len(result) > 1
        # 驗證每個 chunk 不超過限制
        for chunk in result:
            assert len(chunk) <= 10
    
    def test_chunk_with_custom_max_length(self):
        """測試自訂最大長度"""
        processor = TextProcessor(chunk_size=800)
        text = "a" * 100
        
        result = processor.chunk_by_length(text, max_length=50)
        
        assert len(result[0]) <= 50


class TestValidateInput:
    """測試輸入驗證（FR-08）"""
    
    def test_validate_valid_text(self):
        """測試有效文字"""
        processor = TextProcessor()
        text = "這是有效的輸入文字"
        
        assert processor.validate_input(text) is True
    
    def test_validate_empty_text(self):
        """測試空文字"""
        processor = TextProcessor()
        
        assert processor.validate_input("") is False
        assert processor.validate_input("   ") is False
    
    def test_validate_too_long_text(self):
        """測試過長文字"""
        processor = TextProcessor()
        text = "a" * 25000
        
        assert processor.validate_input(text, max_length=20000) is False
    
    def test_validate_max_length_boundary(self):
        """測試最大長度邊界"""
        processor = TextProcessor()
        text = "a" * 20000
        
        assert processor.validate_input(text, max_length=20000) is True
        
        text = "a" * 20001
        assert processor.validate_input(text, max_length=20000) is False
    
    def test_validate_non_string(self):
        """測試非字串"""
        processor = TextProcessor()
        
        assert processor.validate_input(None) is False
        assert processor.validate_input(123) is False


class TestSmartSplit:
    """測試智慧分段"""
    
    def test_split_simple_text(self):
        """測試簡單文字"""
        processor = TextProcessor()
        text = "這是一句話。這是另一句。"
        
        result = processor.split(text)
        
        assert len(result) >= 1
        assert "這是一句話" in result[0]
    
    def test_split_with_newlines(self):
        """測試帶換行的文字"""
        processor = TextProcessor()
        text = "第一句。第二句\n第三句。第四句"
        
        result = processor.split(text)
        
        assert len(result) >= 1
    
    def test_split_empty(self):
        """測試空文字"""
        processor = TextProcessor()
        
        result = processor.split("")
        
        assert result == []
    
    def test_split_respects_chunk_size(self):
        """測試遵守 chunk_size 限制"""
        processor = TextProcessor(chunk_size=10)
        text = "這是一個很長的文字會被分割。" * 10
        
        result = processor.split(text)
        
        # 每個 chunk 不應超過 chunk_size
        for chunk in result:
            assert len(chunk) <= 10


class TestGetTextInfo:
    """測試取得文本資訊"""
    
    def test_get_info_valid_text(self):
        """測試有效文字"""
        processor = TextProcessor()
        text = "這是一個測試。"
        
        info = processor.get_text_info(text)
        
        assert info['char_count'] == len("這是一個測試")
        assert info['sentence_count'] >= 1
        assert info['chunk_count'] >= 1
        assert info['is_valid'] is True
    
    def test_get_info_empty_text(self):
        """測試空文字"""
        processor = TextProcessor()
        
        info = processor.get_text_info("")
        
        assert info['char_count'] == 0
        assert info['is_valid'] is False