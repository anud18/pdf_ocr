# -*- coding: utf-8 -*-
"""
字體工具模組
處理中文字體相關功能
"""

import fitz
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FontManager:
    """字體管理器"""
    
    def __init__(self):
        self.available_fonts = self._get_available_fonts()
        self.chinese_font = self._find_chinese_font()
    
    def _get_available_fonts(self):
        """獲取可用字體列表"""
        try:
            # 獲取 PyMuPDF 支持的字體
            fonts = fitz.fitz_fontdescriptors
            return [font['name'] for font in fonts.values()]
        except Exception as e:
            logger.warning(f"無法獲取字體列表: {str(e)}")
            return []
    
    def _find_chinese_font(self):
        """尋找支持中文的字體"""
        # 優先順序的中文字體列表
        chinese_fonts = [
            "cjk",           # PyMuPDF 內建 CJK 字體
            "china-s",       # 簡體中文
            "china-t",       # 繁體中文
            "japan",         # 日文（也支持中文）
            "korea",         # 韓文（也支持中文）
            "noto-cjk",      # Noto CJK 字體
            "simsun",        # 宋體
            "simhei",        # 黑體
            "kaiti",         # 楷體
            "fangsong",      # 仿宋
        ]
        
        # 檢查哪些字體可用
        for font in chinese_fonts:
            if self._test_font(font):
                logger.info(f"找到可用的中文字體: {font}")
                return font
        
        logger.warning("未找到專用的中文字體，將使用默認字體")
        return "helv"  # 回退到默認字體
    
    def _test_font(self, font_name):
        """測試字體是否可用"""
        try:
            # 創建一個臨時文檔來測試字體
            doc = fitz.open()
            page = doc.new_page()
            
            # 嘗試使用字體插入中文文字
            test_text = "測試中文字體"
            rect = fitz.Rect(0, 0, 100, 50)
            
            page.insert_textbox(
                rect,
                test_text,
                fontsize=12,
                fontname=font_name
            )
            
            doc.close()
            return True
            
        except Exception as e:
            logger.debug(f"字體 {font_name} 測試失敗: {str(e)}")
            return False
    
    def get_best_font_for_text(self, text):
        """根據文字內容獲取最佳字體"""
        # 檢查是否包含中文字符
        if self._contains_chinese(text):
            return self.chinese_font
        else:
            return "helv"  # 英文使用默認字體
    
    def _contains_chinese(self, text):
        """檢查文字是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符範圍
                return True
        return False
    
    def insert_text_with_font(self, page, rect, text, fontsize=8, color=(0, 0, 1)):
        """使用適當的字體插入文字"""
        font_name = self.get_best_font_for_text(text)
        
        try:
            page.insert_textbox(
                rect,
                text,
                fontsize=fontsize,
                color=color,
                fontname=font_name
            )
            logger.info(f"使用字體 {font_name} 插入文字成功: {text[:30]}...")
            return True
            
        except Exception as e:
            logger.warning(f"使用字體 {font_name} 插入文字失敗: {str(e)}")
            
            # 回退到默認字體
            try:
                page.insert_textbox(
                    rect,
                    text,
                    fontsize=fontsize,
                    color=color,
                    fontname="helv"
                )
                logger.info(f"回退到默認字體插入文字成功: {text[:30]}...")
                return True
                
            except Exception as e2:
                logger.error(f"插入文字完全失敗: {str(e2)}")
                return False

# 全局字體管理器實例
font_manager = FontManager()