"""
TextProcessor - 文本處理器
Phase 3 實作 - SKILL.md Phase 3: 程式碼實現

對應規範:
- SRS.md: FR-05, FR-06, FR-07, FR-08
- SKILL.md: 文本處理模組化
- MNT-08: 文本分段邏輯模組化
"""

import re
from typing import List


class TextProcessor:
    """
    文本處理器
    
    職責: 將輸入文本智慧分段為適合合成的長度
    
    規範對應:
    - FR-05: 根據句號、問號、驚嘆號智能分段
    - FR-06: 根據換行符進行分段
    - FR-07: 限制單次分段長度不超過 800 字
    - FR-08: 支援最大 20,000 字的單次輸入
    - MNT-08: 文本分段邏輯模組化
    """
    
    def __init__(self, chunk_size: int = 800):
        """
        初始化文本處理器
        
        規範對應: FR-07（限制單次分段長度）
        
        參數:
            chunk_size: 分段大小，預設 800 字
        """
        self.chunk_size = chunk_size
    
    def split(self, text: str) -> List[str]:
        """
        智慧分段：按標點和換行分段
        
        規範對應: FR-05, FR-06
        
        演算法:
        1. 先按句尾標點（。？！）分割
        2. 依據 chunk_size 進一步合併
        
        參數:
            text: 輸入文本
        
        返回:
            List[str]: 分段後的文本列表
        """
        if not text:
            return []
        
        # 移除空白字元
        text = text.strip()
        
        # Step 1: 按句尾標點和換行符分割
        # 使用正則表達式: [。？！\n]+
        sentences = re.split(r'[。？！\n]+', text)
        
        # 過濾空字串
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Step 2: 依據 chunk_size 合併
        return self._merge_chunks(sentences)
    
    def split_by_punctuation(self, text: str) -> List[str]:
        """
        按標點符號分段（僅句尾）
        
        規範對應: FR-05
        
        參數:
            text: 輸入文本
        
        返回:
            List[str]: 按標點分割的文本列表
        """
        if not text:
            return []
        
        sentences = re.split(r'[。？！]+', text.strip())
        return [s.strip() for s in sentences if s.strip()]
    
    def split_by_newline(self, text: str) -> List[str]:
        """
        按換行符分段
        
        規範對應: FR-06
        
        參數:
            text: 輸入文本
        
        返回:
            List[str]: 按換行分割的文本列表
        """
        if not text:
            return []
        
        lines = re.split(r'\n+', text.strip())
        return [line.strip() for line in lines if line.strip()]
    
    def chunk_by_length(self, text: str, max_length: int = None) -> List[str]:
        """
        按長度分塊
        
        規範對應: FR-07
        
        參數:
            text: 輸入文本
            max_length: 最大長度，預設使用 self.chunk_size
        
        返回:
            List[str]: 分塊後的文本列表
        """
        max_len = max_length or self.chunk_size
        
        if not text:
            return []
        
        if len(text) <= max_len:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_len
            
            # 嘗試在 word boundary 處切斷
            if end < len(text):
                # 找最後一個空白或標點
                last_space = max(text.rfind(' ', start, end),
                                 text.rfind('，', start, end),
                                 text.rfind('。', start, end))
                if last_space > start:
                    end = last_space
            
            chunks.append(text[start:end].strip())
            start = end
        
        return chunks
    
    def validate_input(self, text: str, max_length: int = 20000) -> bool:
        """
        驗證輸入文本
        
        規範對應: FR-08
        
        參數:
            text: 輸入文本
            max_length: 最大長度，預設 20000
        
        返回:
            bool: 驗證是否通過
        """
        # 檢查是否為空
        if not text or not isinstance(text, str):
            return False
        
        # 檢查長度
        text_length = len(text.strip())
        if text_length <= 0 or text_length > max_length:
            return False
        
        return True
    
    def _merge_chunks(self, sentences: List[str]) -> List[str]:
        """
        將短句合併為不超過 chunk_size 的段落
        
        規範對應: FR-07
        
        參數:
            sentences: 句子列表
        
        返回:
            List[str]: 合併後的段落列表
        
        修復記錄 (2026-03-28):
        - 移除多餘句號插入：原程式會在句子的開頭插入「。」，
          這會導致合成時產生不應該有的停頓。
        - 修正邏輯：只在句子本身有句號時才保留，合併時不額外插入標點
        """
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 檢查加上這個句子是否超過限制
            # 修正：移除多餘的句號插入，保持原始標點
            test_chunk = current_chunk + sentence if not current_chunk else current_chunk + sentence
            
            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # 先保存當前 chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果單一句子超過限制，則強制分割
                if len(sentence) > self.chunk_size:
                    # 遞迴分割長句子
                    sub_chunks = self.chunk_by_length(sentence)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = sentence
        
        # 保存最後一個 chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def get_text_info(self, text: str) -> dict:
        """
        取得文本資訊
        
        參數:
            text: 輸入文本
        
        返回:
            dict: 包含字數、句數、分段數等資訊
        """
        if not text:
            return {
                'char_count': 0,
                'sentence_count': 0,
                'chunk_count': 0,
                'is_valid': False
            }
        
        char_count = len(text.strip())
        sentences = self.split_by_punctuation(text)
        sentence_count = len(sentences)
        chunks = self.split(text)
        chunk_count = len(chunks)
        
        return {
            'char_count': char_count,
            'sentence_count': sentence_count,
            'chunk_count': chunk_count,
            'is_valid': self.validate_input(text)
        }