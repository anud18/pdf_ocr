import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple

class VectorStore:
    """向量資料庫管理器"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # 使用內積相似度
        self.documents = []
        self.is_built = False
    
    def add_documents(self, documents: List[Dict], embeddings: np.ndarray):
        """添加文件和對應的嵌入向量"""
        if embeddings.shape[0] != len(documents):
            raise ValueError("文件數量和嵌入向量數量不匹配")
        
        # 正規化嵌入向量（用於內積相似度）
        faiss.normalize_L2(embeddings)
        
        self.index.add(embeddings.astype('float32'))
        self.documents.extend(documents)
        self.is_built = True
        
        print(f"已添加 {len(documents)} 個文件到向量資料庫")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[Dict, float]]:
        """搜尋最相似的文件"""
        if not self.is_built:
            return []
        
        # 正規化查詢向量
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        
        return results
    
    def save(self, filepath: str):
        """保存向量資料庫"""
        try:
            # 保存 FAISS 索引
            faiss.write_index(self.index, f"{filepath}.faiss")
            
            # 保存文件資料
            with open(f"{filepath}.pkl", 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'dimension': self.dimension,
                    'is_built': self.is_built
                }, f)
            
            print(f"向量資料庫已保存到 {filepath}")
        except Exception as e:
            print(f"保存向量資料庫錯誤: {e}")
    
    def load(self, filepath: str) -> bool:
        """載入向量資料庫"""
        try:
            # 載入 FAISS 索引
            if os.path.exists(f"{filepath}.faiss"):
                self.index = faiss.read_index(f"{filepath}.faiss")
            else:
                print(f"找不到索引文件: {filepath}.faiss")
                return False
            
            # 載入文件資料
            if os.path.exists(f"{filepath}.pkl"):
                with open(f"{filepath}.pkl", 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data['documents']
                    self.dimension = data['dimension']
                    self.is_built = data['is_built']
            else:
                print(f"找不到文件資料: {filepath}.pkl")
                return False
            
            print(f"向量資料庫已從 {filepath} 載入，包含 {len(self.documents)} 個文件")
            return True
        except Exception as e:
            print(f"載入向量資料庫錯誤: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """獲取資料庫統計資訊"""
        return {
            'total_documents': len(self.documents),
            'dimension': self.dimension,
            'is_built': self.is_built,
            'index_size': self.index.ntotal if self.is_built else 0
        }