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

def process_pdf_with_vlm(input_pdf_path: str, output_pdf_path: str):
    """處理 PDF 文件，提取圖片並使用 VLM 分析"""
    
    # 初始化組件
    pdf_processor = PDFProcessor()
    vlm_client = QwenVLMClient(os.getenv("VLLM_API_URL", "http://localhost:8000"))
    
    # 等待 vLLM 服務準備就緒
    if not wait_for_vllm_ready(vlm_client):
        logger.error("無法連接到 vLLM 服務")
        return False
    
    try:
        logger.info(f"開始處理 PDF: {input_pdf_path}")
        
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
        
        for i, img_info in enumerate(images_info):
            logger.info(f"分析第 {i+1}/{len(images_info)} 張圖片...")
            
            # 轉換為 base64
            image_base64 = pdf_processor.image_to_base64(img_info['image'])
            
            # 使用 VLM 分析
            analysis_result = vlm_client.get_image_description_and_ocr(image_base64)
            
            images_descriptions.append({
                'page_num': img_info['page_num'],
                'rect': img_info['rect'],
                'description': analysis_result['description'],
                'ocr_text': analysis_result['ocr_text']
            })
            
            logger.info(f"圖片 {i+1} 分析完成")
        
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
        output_file = output_dir / f"enhanced_{pdf_file.name}"
        logger.info(f"處理文件: {pdf_file.name}")
        
        success = process_pdf_with_vlm(str(pdf_file), str(output_file))
        
        if success:
            logger.info(f"✅ {pdf_file.name} 處理成功")
        else:
            logger.error(f"❌ {pdf_file.name} 處理失敗")

if __name__ == "__main__":
    main()