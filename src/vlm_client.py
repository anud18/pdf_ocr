# -*- coding: utf-8 -*-
import requests
import base64
import json
from typing import Dict, Optional, List
import logging
import asyncio
import aiohttp
import concurrent.futures
from functools import partial

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
        
        # 驗證 base64 圖片數據
        if not image_base64 or not image_base64.strip():
            logger.error("收到空的 base64 圖片數據")
            return {"success": False, "error": "圖片數據為空"}
        
        # 驗證 base64 數據格式
        try:
            # 嘗試解碼 base64 以驗證格式
            import base64 as b64
            decoded_data = b64.b64decode(image_base64)
            logger.info(f"圖片數據大小: {len(decoded_data)} 字節")
            if len(decoded_data) < 20:  # 只有極小的數據才拒絕
                logger.error(f"圖片數據太小: {len(decoded_data)} 字節，可能無效")
                return {"success": False, "error": "圖片數據太小，可能無效"}
        except Exception as e:
            logger.error(f"無效的 base64 數據: {str(e)}")
            return {"success": False, "error": "無效的 base64 圖片數據"}
        
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

請保持原始的格式和結構，用繁體中文輸出。如果沒有文字，請回答「無文字內容」。
只需要輸出圖片裡的文字
"""
            
            user_prompt = "請提取這張圖片中的所有文字內容。"
        
        else:
            system_prompt = "請分析這張圖片並提供相關信息。"
            user_prompt = "請分析這張圖片。"
        
        payload = {
            "model": "Qwen/Qwen2.5-VL-32B-Instruct",
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
                timeout=1200
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
    
    async def analyze_image_async(self, session: aiohttp.ClientSession, image_base64: str, prompt_type: str = "ocr", image_index: int = 0) -> Dict[str, any]:
        """
        異步分析單張圖片
        
        Args:
            session: aiohttp 會話
            image_base64: base64 編碼的圖片
            prompt_type: 分析類型 ("description" 或 "ocr")
            image_index: 圖片索引
        
        Returns:
            包含分析結果的字典
        """
        
        # 驗證 base64 圖片數據
        if not image_base64 or not image_base64.strip():
            logger.error(f"圖片 {image_index + 1}: 收到空的 base64 圖片數據")
            return {"success": False, "error": "圖片數據為空", "index": image_index}
        
        # 驗證 base64 數據格式
        try:
            import base64 as b64
            decoded_data = b64.b64decode(image_base64)
            if len(decoded_data) < 20:
                logger.error(f"圖片 {image_index + 1}: 圖片數據太小: {len(decoded_data)} 字節")
                return {"success": False, "error": "圖片數據太小，可能無效", "index": image_index}
        except Exception as e:
            logger.error(f"圖片 {image_index + 1}: 無效的 base64 數據: {str(e)}")
            return {"success": False, "error": "無效的 base64 圖片數據", "index": image_index}
        
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

請保持原始的格式和結構，用繁體中文輸出。如果沒有文字，請回答「無文字內容」。
只需要輸出圖片裡的文字"""
            
            user_prompt = "請提取這張圖片中的所有文字內容。"
        
        else:
            system_prompt = "請分析這張圖片並提供相關信息。"
            user_prompt = "請分析這張圖片。"
        
        payload = {
            "model": "Qwen/Qwen2.5-VL-32B-Instruct",
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
            logger.info(f"開始分析圖片 {image_index + 1}")
            
            async with session.post(
                f"{self.api_url}/v1/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    logger.info(f"圖片 {image_index + 1} 分析完成")
                    return {"success": True, "content": content, "index": image_index}
                else:
                    error_text = await response.text()
                    logger.error(f"圖片 {image_index + 1} API 請求失敗: {response.status}, {error_text}")
                    return {"success": False, "error": f"API 錯誤: {response.status}", "index": image_index}
                    
        except Exception as e:
            logger.error(f"圖片 {image_index + 1} VLM 分析失敗: {str(e)}")
            return {"success": False, "error": str(e), "index": image_index}
    
    async def analyze_images_concurrent(self, images_base64_list: List[str], prompt_type: str = "ocr", max_concurrent: int = 5) -> List[Dict[str, any]]:
        """
        並發分析多張圖片
        
        Args:
            images_base64_list: base64 編碼的圖片列表
            prompt_type: 分析類型 ("description" 或 "ocr")
            max_concurrent: 最大並發數
        
        Returns:
            所有圖片分析結果的列表
        """
        
        if not images_base64_list:
            logger.error("沒有提供圖片數據")
            return []
        
        logger.info(f"開始並發分析 {len(images_base64_list)} 張圖片，最大並發數: {max_concurrent}")
        
        # 創建 aiohttp 會話
        connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=max_concurrent)
        timeout = aiohttp.ClientTimeout(total=300)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 創建信號量來控制並發數
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def analyze_with_semaphore(image_base64: str, index: int):
                async with semaphore:
                    return await self.analyze_image_async(session, image_base64, prompt_type, index)
            
            # 創建所有任務
            tasks = [
                analyze_with_semaphore(image_base64, i) 
                for i, image_base64 in enumerate(images_base64_list)
            ]
            
            # 並發執行所有任務
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理異常結果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"圖片 {i + 1} 處理異常: {str(result)}")
                    processed_results.append({
                        "success": False, 
                        "error": str(result), 
                        "index": i
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"並發分析完成，成功: {sum(1 for r in processed_results if r.get('success', False))} 張，失敗: {sum(1 for r in processed_results if not r.get('success', False))} 張")
            
            return processed_results
    
    def analyze_images_concurrent_sync(self, images_base64_list: List[str], prompt_type: str = "ocr", max_concurrent: int = 5) -> List[Dict[str, any]]:
        """
        並發分析多張圖片的同步包裝器
        
        Args:
            images_base64_list: base64 編碼的圖片列表
            prompt_type: 分析類型 ("description" 或 "ocr")
            max_concurrent: 最大並發數
        
        Returns:
            所有圖片分析結果的列表
        """
        
        # 檢查是否已經在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 如果已經在事件循環中，使用線程池執行
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    self.analyze_images_concurrent(images_base64_list, prompt_type, max_concurrent)
                )
                return future.result()
        except RuntimeError:
            # 沒有運行的事件循環，直接運行
            return asyncio.run(
                self.analyze_images_concurrent(images_base64_list, prompt_type, max_concurrent)
            )
