"""
TextProcessor 測試
"""

import pytest
from text_processor import TextProcessor


class TestTextProcessor:
    def test_init_default(self):
        processor = TextProcessor()
        assert processor.chunk_size == 800
    
    def test_init_custom_chunk_size(self):
        processor = TextProcessor(chunk_size=500)
        assert processor.chunk_size == 500


class TestSplitByPunctuation:
    def test_split_by_period(self):
        processor = TextProcessor()
        text = "第一句。第二句。第三句"
        result = processor.split_by_punctuation(text)
        assert len(result) == 3
    
    def test_split_by_question_mark(self):
        processor = TextProcessor()
        text = "這是問題嗎？這是陳述"
        result = processor.split_by_punctuation(text)
        assert len(result) == 2
    
    def test_split_by_exclamation(self):
        processor = TextProcessor()
        text = "太棒了！真的很棒"
        result = processor.split_by_punctuation(text)
        assert len(result) == 2
    
    def test_split_by_mixed_punctuation(self):
        processor = TextProcessor()
        text = "你好！最近好嗎？不錯"
        result = processor.split_by_punctuation(text)
        assert len(result) == 3
    
    def test_split_empty_text(self):
        processor = TextProcessor()
        result = processor.split_by_punctuation("")
        assert result == []


class TestSplitByNewline:
    def test_split_by_newline(self):
        processor = TextProcessor()
        text = "第一行\n第二行\n第三行"
        result = processor.split_by_newline(text)
        assert result == ["第一行", "第二行", "第三行"]
    
    def test_split_by_multiple_newlines(self):
        processor = TextProcessor()
        text = "第一行\n\n\n第二行"
        result = processor.split_by_newline(text)
        assert result == ["第一行", "第二行"]
    
    def test_split_newline_empty(self):
        processor = TextProcessor()
        result = processor.split_by_newline("")
        assert result == []


class TestChunkByLength:
    def test_chunk_small_text(self):
        processor = TextProcessor()
        text = "短文字"
        result = processor.chunk_by_length(text)
        assert result == ["短文字"]
    
    def test_chunk_long_text(self):
        processor = TextProcessor(chunk_size=5)
        text = "這是一個很長的文字需要被分塊"
        result = processor.chunk_by_length(text)
        assert len(result[0]) <= 5
    
    def test_chunk_with_custom_max_length(self):
        processor = TextProcessor()
        result = processor.chunk_by_length("測試文字", max_length=3)
        for chunk in result:
            assert len(chunk) <= 3


class TestValidateInput:
    def test_validate_valid_text(self):
        processor = TextProcessor()
        result = processor.validate_input("這是有效文字")
        assert result == True
    
    def test_validate_empty_text(self):
        processor = TextProcessor()
        result = processor.validate_input("")
        assert result == False
    
    def test_validate_too_long_text(self):
        processor = TextProcessor()
        long_text = "a" * 20001
        result = processor.validate_input(long_text)
        assert result == False
    
    def test_validate_non_string(self):
        processor = TextProcessor()
        result = processor.validate_input(123)
        assert result == False


class TestSmartSplit:
    def test_split_simple_text(self):
        processor = TextProcessor()
        result = processor.split("簡單文字測試")
        assert len(result) >= 1
    
    def test_split_with_newlines(self):
        processor = TextProcessor()
        text = "第一行\n第二行\n第三行"
        result = processor.split(text)
        assert len(result) >= 1
    
    def test_split_empty(self):
        processor = TextProcessor()
        result = processor.split("")
        assert result == []
    
    def test_split_respects_chunk_size(self):
        processor = TextProcessor(chunk_size=50)
        text = "a" * 100
        result = processor.split(text)
        for chunk in result:
            assert len(chunk) <= 50


class TestGetTextInfo:
    def test_get_info_valid_text(self):
        processor = TextProcessor()
        info = processor.get_text_info("Hello World")
        assert "char_count" in info
        assert info["char_count"] == 11
    
    def test_get_info_empty_text(self):
        processor = TextProcessor()
        info = processor.get_text_info("")
        assert info["char_count"] == 0


class TestSplitIntegration:
    def test_split_full_text(self):
        processor = TextProcessor(chunk_size=10)
        text = "這是一個很長的測試文字，需要被正確分段"
        result = processor.split(text)
        assert len(result) > 0
    
    def test_validate_with_custom_max(self):
        processor = TextProcessor()
        result = processor.validate_input("test", max_length=100)
        assert result == True