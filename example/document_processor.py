import os
import PyPDF2
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import numpy as np

class DocumentProcessor:
    """文件處理器，負責 PDF 解析和文本分塊"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """從 PDF 提取文本"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            print(f"讀取 PDF 錯誤 {pdf_path}: {e}")
            return ""
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """將文本分割成塊"""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 如果不是最後一塊，嘗試在句號或換行處分割
            if end < len(text):
                # 尋找最近的句號或換行
                for i in range(end, max(start + self.chunk_size - 100, start), -1):
                    if text[i] in '.。\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def process_pdf_directory(self, pdf_dir: str) -> List[Dict]:
        """處理目錄中的所有 PDF"""
        documents = []
        
        if not os.path.exists(pdf_dir):
            print(f"目錄不存在: {pdf_dir}")
            return documents
        
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"在 {pdf_dir} 中沒有找到 PDF 文件")
            return documents
        
        print(f"找到 {len(pdf_files)} 個 PDF 文件")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            print(f"處理: {pdf_file}")
            
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                continue
            
            chunks = self.split_text_into_chunks(text)
            print(f"  - 分割成 {len(chunks)} 個文本塊")
            
            for i, chunk in enumerate(chunks):
                documents.append({
                    'id': f"{pdf_file}_{i}",
                    'source': pdf_file,
                    'content': chunk,
                    'chunk_index': i
                })
        
        return documents
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """創建文本嵌入向量"""
        try:
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            return embeddings
        except Exception as e:
            print(f"創建嵌入向量錯誤: {e}")
            return np.array([])