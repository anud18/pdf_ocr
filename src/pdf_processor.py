# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import os
import base64
from PIL import Image
import io
from typing import List, Dict, Tuple
from pathlib import Path
import logging
from font_utils import font_manager

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict]:
        """從 PDF 中提取圖片及其位置信息"""
        doc = fitz.open(pdf_path)
        images_info = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # 獲取圖片數據
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # 確保不是 CMYK
                        # 轉換為 PIL Image
                        img_data = pix.tobytes("png")
                        
                        # 驗證圖片數據
                        if len(img_data) == 0:
                            logger.warning(f"頁面 {page_num+1} 圖片 {img_index+1} 數據為空，跳過")
                            pix = None
                            continue
                        
                        try:
                            pil_image = Image.open(io.BytesIO(img_data))
                            
                            # 驗證圖片是否有效
                            if pil_image.size[0] <= 0 or pil_image.size[1] <= 0:
                                logger.warning(f"頁面 {page_num+1} 圖片 {img_index+1} 尺寸無效: {pil_image.size}")
                                pix = None
                                continue
                            
                            # 嘗試驗證圖片數據完整性
                            pil_image.verify()
                            # 重新加載圖片（verify 後需要重新加載）
                            pil_image = Image.open(io.BytesIO(img_data))
                            
                        except Exception as e:
                            logger.warning(f"頁面 {page_num+1} 圖片 {img_index+1} 無法解析: {str(e)}")
                            pix = None
                            continue
                        
                        # 獲取圖片在頁面中的位置
                        img_rects = page.get_image_rects(xref)
                        
                        for rect in img_rects:
                            images_info.append({
                                'page_num': page_num,
                                'image': pil_image,
                                'rect': rect,
                                'xref': xref,
                                'img_index': img_index
                            })
                    
                    pix = None
                    
                except Exception as e:
                    logger.error(f"處理頁面 {page_num+1} 圖片 {img_index+1} 時發生錯誤: {str(e)}")
                    continue
        
        doc.close()
        return images_info
    
    def image_to_base64(self, image: Image.Image) -> str:
        """將 PIL Image 轉換為 base64 字符串"""
        if image is None:
            logger.error("收到空的圖片對象")
            return ""
        
        try:
            # 驗證圖片尺寸
            if image.size[0] <= 0 or image.size[1] <= 0:
                logger.error(f"無效的圖片尺寸: {image.size}")
                return ""
            
            buffer = io.BytesIO()
            
            # 確保圖片格式兼容
            if image.mode in ('RGBA', 'LA', 'P'):
                # 轉換為 RGB 格式以確保兼容性
                image = image.convert('RGB')
            elif image.mode == 'L':
                # 灰度圖片轉為 RGB
                image = image.convert('RGB')
            
            image.save(buffer, format='PNG')
            buffer_data = buffer.getvalue()
            
            # 驗證生成的數據
            if len(buffer_data) == 0:
                logger.error("圖片轉換後數據為空")
                return ""
            
            img_str = base64.b64encode(buffer_data).decode()
            logger.debug(f"圖片轉換為 base64，大小: {len(img_str)} 字符")
            return img_str
            
        except Exception as e:
            logger.error(f"圖片轉換為 base64 失敗: {str(e)}")
            return ""
    
    def convert_pages_to_images(self, pdf_path: str, dpi: int = 150) -> List[Dict]:
        """將 PDF 頁面轉換為圖片"""
        doc = fitz.open(pdf_path)
        pages_info = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 設置縮放比例以控制圖片質量
            zoom = dpi / 72  # 72 是 PDF 的默認 DPI
            mat = fitz.Matrix(zoom, zoom)
            
            # 渲染頁面為圖片
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            
            pages_info.append({
                'page_num': page_num,
                'image': pil_image,
                'width': pil_image.size[0],
                'height': pil_image.size[1]
            })
            
            pix = None
        
        doc.close()
        return pages_info
    
    def save_pages_as_images(self, pdf_path: str, output_dir: str, dpi: int = 150) -> str:
        """將 PDF 頁面保存為圖片文件"""
        pdf_name = Path(pdf_path).stem
        pages_dir = Path(output_dir) / f"{pdf_name}_pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        pages_info = self.convert_pages_to_images(pdf_path, dpi)
        
        for page_info in pages_info:
            page_num = page_info['page_num'] + 1
            filename = f"page_{page_num:03d}.png"
            image_path = pages_dir / filename
            page_info['image'].save(image_path, 'PNG')
        
        logger.info(f"✅ 所有頁面已保存到: {pages_dir}")
        return str(pages_dir)

    def create_enhanced_pdf(self, original_pdf_path: str, images_descriptions: List[Dict], output_path: str):
        """創建包含圖片描述的增強 PDF"""
        doc = fitz.open(original_pdf_path)
        
        for img_desc in images_descriptions:
            page_num = img_desc['page_num']
            page = doc[page_num]
            rect = img_desc['rect']
            description = img_desc['description']
            ocr_text = img_desc.get('ocr_text', '')
            
            # 在圖片下方添加描述文字
            text_rect = fitz.Rect(
                rect.x0, 
                rect.y1 + 5, 
                rect.x1, 
                rect.y1 + 50
            )
            
            # 添加描述文字
            full_text = f"圖片描述: {description}"
            if ocr_text:
                full_text += f"\n文字內容: {ocr_text}"
            
            # 使用字體管理器插入文字
            font_manager.insert_text_with_font(
                page,
                text_rect,
                full_text,
                fontsize=8,
                color=(0, 0, 1)  # 藍色
            )
        
        doc.save(output_path)
        doc.close()
        logger.info(f"增強的 PDF 已保存到: {output_path}")
    
    def create_enhanced_pdf_from_pages(self, original_pdf_path: str, pages_ocr_results: List[Dict], output_path: str):
        """從頁面 OCR 結果創建增強的 PDF"""
        doc = fitz.open(original_pdf_path)
        
        for page_result in pages_ocr_results:
            page_num = page_result['page_num']
            page = doc[page_num]
            ocr_text = page_result.get('ocr_text', '')
            
            if ocr_text and ocr_text != "無文字內容":
                # 在頁面底部添加 OCR 結果
                page_rect = page.rect
                text_rect = fitz.Rect(
                    page_rect.x0 + 50,
                    page_rect.y1 - 100,
                    page_rect.x1 - 50,
                    page_rect.y1 - 20
                )
                
                # 使用字體管理器插入文字
                font_manager.insert_text_with_font(
                    page,
                    text_rect,
                    f"頁面 OCR 結果: {ocr_text}",
                    fontsize=8,
                    color=(0, 0, 1)  # 藍色
                )
        
        doc.save(output_path)
        doc.close()
        logger.info(f"增強的 PDF 已保存到: {output_path}")