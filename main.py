#!/usr/bin/env python3
import os
import sys
import logging
import time
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pdf_processor import PDFProcessor
from vlm_client import QwenVLMClient

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_vllm_ready(vlm_client: QwenVLMClient, max_retries: int = 30):
    """等待 vLLM 服務準備就緒"""
    logger.info("等待 vLLM 服務啟動...")
    
    for i in range(max_retries):
        try:
            # 嘗試發送一個簡單的測試請求
            test_result = vlm_client.analyze_image("", "description")
            if "error" not in test_result or "Connection" not in str(test_result.get("error", "")):
                logger.info("vLLM 服務已準備就緒")
                return True
        except Exception as e:
            logger.info(f"等待中... ({i+1}/{max_retries})")
            time.sleep(10)
    
    logger.error("vLLM 服務啟動超時")
    return False

def save_images_to_folder(input_pdf_path: str, images_info: list) -> str:
    """將圖片保存到資料夾"""
    # 創建圖片保存目錄
    pdf_name = Path(input_pdf_path).stem
    images_dir = Path("./extracted_images") / pdf_name
    images_dir.mkdir(parents=True, exist_ok=True)
    
    saved_images = []
    
    try:
        logger.info(f"開始保存 {len(images_info)} 張圖片到 {images_dir}")
        
        for i, img_info in enumerate(images_info):
            # 生成圖片文件名
            page_num = img_info['page_num'] + 1
            filename = f"page_{page_num:03d}_img_{i+1:03d}.png"
            image_path = images_dir / filename
            
            # 保存圖片
            img_info['image'].save(image_path, 'PNG')
            saved_images.append(str(image_path))
            
            if (i + 1) % 50 == 0:  # 每50張圖片顯示一次進度
                logger.info(f"已保存 {i+1}/{len(images_info)} 張圖片")
        
        logger.info(f"✅ 所有圖片已保存到: {images_dir}")
        return str(images_dir)
        
    except Exception as e:
        logger.error(f"保存圖片時發生錯誤: {str(e)}")
        return ""

def print_pdf_images_info(input_pdf_path: str):
    """打印 PDF 中的圖片信息"""
    pdf_processor = PDFProcessor()
    
    try:
        logger.info(f"分析 PDF 文件: {input_pdf_path}")
        
        # 提取圖片信息
        images_info = pdf_processor.extract_images_from_pdf(input_pdf_path)
        
        print(f"\n=== PDF 圖片信息 ===")
        print(f"文件: {input_pdf_path}")
        print(f"總共找到 {len(images_info)} 張圖片\n")
        
        if not images_info:
            print("此 PDF 中沒有找到任何圖片")
            return images_info
        
        for i, img_info in enumerate(images_info, 1):
            print(f"圖片 {i}:")
            print(f"  頁面: {img_info['page_num'] + 1}")
            print(f"  位置: x={img_info['rect'].x0:.1f}, y={img_info['rect'].y0:.1f}")
            print(f"  尺寸: 寬={img_info['rect'].width:.1f}, 高={img_info['rect'].height:.1f}")
            print(f"  圖片尺寸: {img_info['image'].size[0]}x{img_info['image'].size[1]} 像素")
            print(f"  圖片模式: {img_info['image'].mode}")
            print()
        
        print(f"=== 分析完成 ===\n")
        return images_info
        
    except Exception as e:
        logger.error(f"分析 PDF 圖片時發生錯誤: {str(e)}")
        return []

def process_pdf_with_vlm(input_pdf_path: str, output_pdf_path: str, use_page_mode: bool = False, test_mode: bool = False):
    """處理 PDF 文件，提取圖片並使用 VLM 分析"""
    
    # 初始化組件
    pdf_processor = PDFProcessor()
    vlm_client = QwenVLMClient(os.getenv("VLLM_API_URL", "http://localhost:8000"))
    
    # 測試模式跳過 VLM 服務檢查
    if not test_mode:
        # 等待 vLLM 服務準備就緒
        if not wait_for_vllm_ready(vlm_client):
            logger.error("無法連接到 vLLM 服務")
            return False
    
    try:
        logger.info(f"開始處理 PDF: {input_pdf_path}")
        
        if use_page_mode:
            # 頁面模式：將每頁轉換為圖片進行 OCR
            logger.info("使用頁面模式進行 OCR 處理...")
            
            # 將頁面轉換為圖片
            pages_info = pdf_processor.convert_pages_to_images(input_pdf_path)
            logger.info(f"轉換了 {len(pages_info)} 頁")
            
            # 保存頁面圖片
            pages_dir = pdf_processor.save_pages_as_images(input_pdf_path, "./extracted_pages")
            
            # 對每頁進行 OCR
            pages_ocr_results = []
            
            print(f"\n=== 頁面 OCR 結果 ===")
            print(f"文件: {input_pdf_path}")
            print(f"總共 {len(pages_info)} 頁\n")
            
            for i, page_info in enumerate(pages_info):
                logger.info(f"對第 {i+1}/{len(pages_info)} 頁進行 OCR...")
                
                # 轉換為 base64
                image_base64 = pdf_processor.image_to_base64(page_info['image'])
                
                # 使用 VLM 進行 OCR
                if test_mode:
                    # 測試模式：模擬 OCR 結果
                    ocr_text = f"第 {i+1} 頁的模擬 OCR 文字內容 - 這是一個測試結果"
                else:
                    ocr_result = vlm_client.analyze_image(image_base64, "ocr")
                    ocr_text = ocr_result.get("content", "無文字內容") if ocr_result["success"] else "OCR 分析失敗"
                
                pages_ocr_results.append({
                    'page_num': page_info['page_num'],
                    'ocr_text': ocr_text
                })
                
                # 打印 OCR 結果
                print(f"第 {i+1} 頁 OCR 結果:")
                print(f"  頁面尺寸: {page_info['width']}x{page_info['height']} 像素")
                if ocr_text and ocr_text != "無文字內容" and ocr_text != "OCR 分析失敗":
                    print(f"  識別文字: {ocr_text}")
                else:
                    print(f"  識別文字: {ocr_text}")
                print("-" * 50)
                
                logger.info(f"第 {i+1} 頁 OCR 完成")
            
            print(f"=== 頁面 OCR 完成 ===\n")
            
            # 創建增強的 PDF
            logger.info("創建增強的 PDF...")
            pdf_processor.create_enhanced_pdf_from_pages(input_pdf_path, pages_ocr_results, output_pdf_path)
            
        else:
            # 圖片模式：提取個別圖片進行分析
            logger.info("使用圖片模式進行處理...")
            
            # 提取圖片
            images_info = pdf_processor.extract_images_from_pdf(input_pdf_path)
            logger.info(f"找到 {len(images_info)} 張圖片")
            
            if not images_info:
                logger.info("PDF 中沒有找到圖片，直接複製原文件")
                import shutil
                shutil.copy2(input_pdf_path, output_pdf_path)
                return True
            
            # 分析每張圖片
            images_descriptions = []
            
            print(f"\n=== 圖片分析和 OCR 結果 ===")
            print(f"文件: {input_pdf_path}")
            print(f"總共 {len(images_info)} 張圖片\n")
            
            for i, img_info in enumerate(images_info):
                logger.info(f"分析第 {i+1}/{len(images_info)} 張圖片...")
                
                # 轉換為 base64
                image_base64 = pdf_processor.image_to_base64(img_info['image'])
                
                # 使用 VLM 分析
                if test_mode:
                    # 測試模式：模擬分析結果
                    analysis_result = {
                        'description': f"圖片 {i+1} 的模擬描述 - 這是一個測試圖片",
                        'ocr_text': f"圖片 {i+1} 的模擬 OCR 文字" if i % 3 == 0 else "無文字內容"
                    }
                else:
                    analysis_result = vlm_client.get_image_description_and_ocr(image_base64)
                
                images_descriptions.append({
                    'page_num': img_info['page_num'],
                    'rect': img_info['rect'],
                    'description': analysis_result['description'],
                    'ocr_text': analysis_result['ocr_text']
                })
                
                # 打印分析結果
                print(f"圖片 {i+1} 分析結果:")
                print(f"  頁面: {img_info['page_num'] + 1}")
                print(f"  位置: x={img_info['rect'].x0:.1f}, y={img_info['rect'].y0:.1f}")
                print(f"  尺寸: {img_info['image'].size[0]}x{img_info['image'].size[1]} 像素")
                print(f"  描述: {analysis_result['description']}")
                if analysis_result['ocr_text'] and analysis_result['ocr_text'] != "無文字內容":
                    print(f"  OCR 文字: {analysis_result['ocr_text']}")
                else:
                    print(f"  OCR 文字: 無文字內容")
                print("-" * 50)
                
                logger.info(f"圖片 {i+1} 分析完成")
            
            print(f"=== 圖片分析完成 ===\n")
            
            # 創建增強的 PDF
            logger.info("創建增強的 PDF...")
            pdf_processor.create_enhanced_pdf(input_pdf_path, images_descriptions, output_pdf_path)
        
        logger.info(f"處理完成！輸出文件: {output_pdf_path}")
        return True
        
    except Exception as e:
        logger.error(f"處理過程中發生錯誤: {str(e)}")
        return False

def main():
    """主函數"""
    input_dir = Path("./input")
    output_dir = Path("./output")
    
    # 確保目錄存在
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 查找輸入目錄中的 PDF 文件
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.info("在 input 目錄中沒有找到 PDF 文件")
        logger.info("請將要處理的 PDF 文件放入 ./input 目錄")
        return
    
    # 首先打印所有 PDF 文件中的圖片信息並保存圖片
    print("\n" + "="*50)
    print("開始分析 PDF 文件中的圖片...")
    print("="*50)
    
    pdf_images_data = {}  # 存儲每個PDF的圖片信息
    
    for pdf_file in pdf_files:
        images_info = print_pdf_images_info(str(pdf_file))
        pdf_images_data[str(pdf_file)] = images_info
        
        # 如果有圖片，保存到資料夾
        if images_info:
            print(f"正在保存 {pdf_file.name} 的圖片...")
            images_dir = save_images_to_folder(str(pdf_file), images_info)
            if images_dir:
                print(f"✅ 圖片已保存到: {images_dir}\n")
            else:
                print(f"❌ 保存圖片失敗\n")
        else:
            print(f"📝 {pdf_file.name} 中沒有圖片需要保存\n")
    
    # 詢問用戶是否要繼續處理
    print("圖片信息分析和保存完成！")
    user_input = input("是否要繼續使用 VLM 處理這些 PDF？(y/n): ").lower().strip()
    
    if user_input not in ['y', 'yes', '是']:
        print("已取消 VLM 處理，但圖片已保存完成")
        return
    
    # 處理每個 PDF 文件
    for pdf_file in pdf_files:
        images_info = pdf_images_data[str(pdf_file)]
        use_page_mode = False
        
        # 檢查圖片數量，如果超過 10 個則詢問用戶
        if len(images_info) > 10:
            print(f"\n📊 {pdf_file.name} 包含 {len(images_info)} 張圖片")
            print("由於圖片數量較多，建議使用以下處理方式：")
            print("1. 圖片模式：逐一分析每張圖片（較詳細但耗時）")
            print("2. 頁面模式：將每頁轉換為圖片進行 OCR（較快速）")
            
            mode_choice = input("請選擇處理模式 (1=圖片模式, 2=頁面模式): ").strip()
            
            if mode_choice == "2":
                use_page_mode = True
                print(f"✅ 選擇頁面模式處理 {pdf_file.name}")
            else:
                print(f"✅ 選擇圖片模式處理 {pdf_file.name}")
        else:
            print(f"\n📊 {pdf_file.name} 包含 {len(images_info)} 張圖片，使用圖片模式處理")
        
        output_file = output_dir / f"enhanced_{pdf_file.name}"
        logger.info(f"處理文件: {pdf_file.name}")
        
        # 檢查是否要使用測試模式
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        if test_mode:
            print("🧪 使用測試模式（模擬 OCR 結果）")
        
        success = process_pdf_with_vlm(str(pdf_file), str(output_file), use_page_mode, test_mode)
        
        if success:
            logger.info(f"✅ {pdf_file.name} 處理成功")
        else:
            logger.error(f"❌ {pdf_file.name} 處理失敗")

if __name__ == "__main__":
    main()