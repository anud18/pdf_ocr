import requests
import json
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class VLLMClient:
    """vLLM API 客戶端"""
    
    def __init__(self, base_url: str = None, model_name: str = None):
        self.base_url = base_url or os.getenv('VLLM_BASE_URL', 'http://localhost:8000')
        self.model_name = model_name or os.getenv('VLLM_MODEL_NAME', 'default')
        self.api_key = os.getenv('VLLM_API_KEY', '')
        
    def generate_response(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """生成回應"""
        url = f"{self.base_url}/v1/completions"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": ["Human:", "Assistant:"]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['text'].strip()
            
        except requests.exceptions.RequestException as e:
            print(f"API 請求錯誤: {e}")
            return "抱歉，無法連接到 vLLM 服務。"
        except KeyError as e:
            print(f"回應格式錯誤: {e}")
            return "抱歉，服務回應格式異常。"
    
    def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> str:
        """聊天完成 API"""
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.RequestException as e:
            print(f"API 請求錯誤: {e}")
            return "抱歉，無法連接到 vLLM 服務。"
        except KeyError as e:
            print(f"回應格式錯誤: {e}")
            return "抱歉，服務回應格式異常。"