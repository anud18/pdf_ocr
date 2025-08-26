import requests
import base64
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class QwenVLMClient:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def analyze_image(self, image_base64: str, prompt_type: str = "description") -> Dict[str, str]:
        """
        使用 Qwen2.5-VL 分析圖片
        
        Args:
            image_base64: base64 編碼的圖片
            prompt_type: 分析類型 ("description" 或 "ocr")
        
        Returns:
            包含分析結果的字典
        """
        
        if prompt_type == "description":
            system_prompt = """你是一個專業的圖片分析助手。請詳細描述這張圖片的內容，包括：
1. 主要物體和場景
2. 顏色和構圖
3. 重要的細節和特徵
4. 圖片的整體主題或用途

請用繁體中文回答，描述要準確且詳細。"""
            
            user_prompt = "請詳細描述這張圖片的內容。"
            
        elif prompt_type == "ocr":
            system_prompt = """你是一個專業的 OCR 助手。請識別並提取圖片中的所有文字內容，包括：
1. 標題和主要文字
2. 表格中的文字
3. 圖表中的標籤和數值
4. 任何其他可見的文字

請保持原始的格式和結構，用繁體中文輸出。如果沒有文字，請回答「無文字內容」。"""
            
            user_prompt = "請提取這張圖片中的所有文字內容。"
        
        else:
            system_prompt = "請分析這張圖片並提供相關信息。"
            user_prompt = "請分析這張圖片。"
        
        payload = {
            "model": "qwen2.5-vl",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return {"success": True, "content": content}
            else:
                logger.error(f"API 請求失敗: {response.status_code}, {response.text}")
                return {"success": False, "error": f"API 錯誤: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"VLM 分析失敗: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_image_description_and_ocr(self, image_base64: str) -> Dict[str, str]:
        """獲取圖片描述和 OCR 結果"""
        
        # 獲取圖片描述
        desc_result = self.analyze_image(image_base64, "description")
        description = desc_result.get("content", "無法獲取描述") if desc_result["success"] else "描述分析失敗"
        
        # 獲取 OCR 結果
        ocr_result = self.analyze_image(image_base64, "ocr")
        ocr_text = ocr_result.get("content", "無文字內容") if ocr_result["success"] else "OCR 分析失敗"
        
        return {
            "description": description,
            "ocr_text": ocr_text
        }