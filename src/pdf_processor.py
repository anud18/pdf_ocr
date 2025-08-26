import fitz  # PyMuPDF
import os
import base64
from PIL import Image
import io
from typing import List, Dict, Tuple
import logging

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
                # 獲取圖片數據
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # 確保不是 CMYK
                    # 轉換為 PIL Image
                    img_data = pix.tobytes("png")
                    pil_image = Image.open(io.BytesIO(img_data))
                    
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
        
        doc.close()
        return images_info
    
    def image_to_base64(self, image: Image.Image) -> str:
        """將 PIL Image 轉換為 base64 字符串"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
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
            
            page.insert_textbox(
                text_rect,
                full_text,
                fontsize=8,
                color=(0, 0, 1),  # 藍色
                fontname="helv"
            )
        
        doc.save(output_path)
        doc.close()
        logger.info(f"增強的 PDF 已保存到: {output_path}")