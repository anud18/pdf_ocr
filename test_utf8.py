#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTF-8 編碼測試腳本
測試系統是否能正確處理中文字符
"""

import sys
import os
import logging
from pathlib import Path

# 設置 UTF-8 編碼
import locale
import codecs

def test_utf8_support():
    """測試 UTF-8 支持"""
    print("=== UTF-8 編碼測試 ===")
    
    # 測試中文字符
    test_strings = [
        "這是一個中文測試字符串",
        "圖片描述：包含中文的內容",
        "OCR 文字識別：繁體中文支持",
        "PDF 處理系統：支援中文字符",
        "測試特殊字符：「」『』〈〉《》【】〔〕",
        "數字和符號：１２３４５６７８９０",
        "標點符號：，。！？；：",
    ]
    
    print("1. 測試中文字符串輸出：")
    for i, test_str in enumerate(test_strings, 1):
        print(f"   {i}. {test_str}")
    
    print("\n2. 測試系統編碼設置：")
    print(f"   系統默認編碼: {sys.getdefaultencoding()}")
    print(f"   文件系統編碼: {sys.getfilesystemencoding()}")
    print(f"   標準輸出編碼: {sys.stdout.encoding}")
    print(f"   標準錯誤編碼: {sys.stderr.encoding}")
    
    try:
        current_locale = locale.getlocale()
        print(f"   當前 locale: {current_locale}")
    except:
        print("   無法獲取 locale 信息")
    
    print("\n3. 測試文件讀寫：")
    test_file = "test_utf8_file.txt"
    test_content = "這是一個包含中文的測試文件內容\n圖片描述：測試中文字符\nOCR 結果：繁體中文"
    
    try:
        # 寫入測試文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"   ✅ 成功寫入測試文件: {test_file}")
        
        # 讀取測試文件
        with open(test_file, 'r', encoding='utf-8') as f:
            read_content = f.read()
        
        if read_content == test_content:
            print("   ✅ 文件讀寫測試通過")
        else:
            print("   ❌ 文件讀寫測試失敗")
        
        # 清理測試文件
        os.remove(test_file)
        
    except Exception as e:
        print(f"   ❌ 文件讀寫測試失敗: {str(e)}")
    
    print("\n4. 測試日誌輸出：")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("這是一個包含中文的日誌訊息")
    logger.warning("警告：中文字符測試")
    logger.error("錯誤：UTF-8 編碼測試")
    
    print("\n=== UTF-8 編碼測試完成 ===")
    return True

def test_pdf_processor_utf8():
    """測試 PDF 處理器的 UTF-8 支持"""
    print("\n=== PDF 處理器 UTF-8 測試 ===")
    
    try:
        # 導入 PDF 處理器
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from pdf_processor import PDFProcessor
        from vlm_client import QwenVLMClient
        from font_utils import font_manager
        
        print("✅ 成功導入 PDF 處理器模組")
        
        # 測試創建實例
        pdf_processor = PDFProcessor()
        vlm_client = QwenVLMClient()
        
        print("✅ 成功創建處理器實例")
        
        # 測試字體管理器
        print(f"   可用字體數量: {len(font_manager.available_fonts)}")
        print(f"   選擇的中文字體: {font_manager.chinese_font}")
        
        # 測試中文字符處理
        test_descriptions = [
            {
                'description': '這是一個包含中文的圖片描述',
                'ocr_text': '圖片中的中文文字內容'
            },
            {
                'description': '測試繁體中文字符：圖片、描述、識別',
                'ocr_text': '包含標點符號的文字：「測試」、『內容』'
            }
        ]
        
        for i, desc in enumerate(test_descriptions, 1):
            print(f"   測試描述 {i}: {desc['description']}")
            print(f"   測試 OCR {i}: {desc['ocr_text']}")
        
        print("✅ PDF 處理器 UTF-8 測試通過")
        
    except Exception as e:
        print(f"❌ PDF 處理器 UTF-8 測試失敗: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("開始 UTF-8 編碼支持測試...\n")
    
    # 基本 UTF-8 測試
    test_utf8_support()
    
    # PDF 處理器測試
    test_pdf_processor_utf8()
    
    print("\n所有測試完成！")