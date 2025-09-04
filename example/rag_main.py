#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from typing import List, Dict
from document_processor import DocumentProcessor
from vector_store import VectorStore
from rag_client import VLLMClient

class RAGSystem:
    """RAG 系統主類別"""
    
    def __init__(self, pdf_dir: str = "pdfs", vector_db_path: str = "vector_db"):
        self.pdf_dir = pdf_dir
        self.vector_db_path = vector_db_path
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.vllm_client = VLLMClient()
        self.is_initialized = False
    
    def initialize(self, force_rebuild: bool = False):
        """初始化 RAG 系統"""
        print("=== RAG 系統初始化 ===")
        
        # 檢查是否需要重建向量資料庫
        if not force_rebuild and os.path.exists(f"{self.vector_db_path}.faiss"):
            print("載入現有向量資料庫...")
            if self.vector_store.load(self.vector_db_path):
                self.is_initialized = True
                stats = self.vector_store.get_stats()
                print(f"載入完成！包含 {stats['total_documents']} 個文件塊")
                return
        
        print("建立新的向量資料庫...")
        
        # 處理 PDF 文件
        print(f"處理 PDF 目錄: {self.pdf_dir}")
        documents = self.doc_processor.process_pdf_directory(self.pdf_dir)
        
        if not documents:
            print("沒有找到可處理的文件！")
            return
        
        # 創建嵌入向量
        print("創建嵌入向量...")
        texts = [doc['content'] for doc in documents]
        embeddings = self.doc_processor.create_embeddings(texts)
        
        if embeddings.size == 0:
            print("創建嵌入向量失敗！")
            return
        
        # 建立向量資料庫
        self.vector_store.add_documents(documents, embeddings)
        
        # 保存向量資料庫
        self.vector_store.save(self.vector_db_path)
        
        self.is_initialized = True
        print("RAG 系統初始化完成！")
    
    def search_relevant_documents(self, query: str, k: int = 3) -> List[Dict]:
        """搜尋相關文件"""
        if not self.is_initialized:
            return []
        
        # 創建查詢嵌入向量
        query_embedding = self.doc_processor.create_embeddings([query])
        if query_embedding.size == 0:
            return []
        
        # 搜尋相似文件
        results = self.vector_store.search(query_embedding, k)
        
        relevant_docs = []
        for doc, score in results:
            relevant_docs.append({
                'content': doc['content'],
                'source': doc['source'],
                'score': score
            })
        
        return relevant_docs
    
    def generate_answer(self, question: str, context_docs: List[Dict]) -> str:
        """基於上下文生成答案"""
        if not context_docs:
            return "抱歉，我沒有找到相關的資訊來回答您的問題。"
        
        # 構建上下文
        context = "\n\n".join([
            f"文件來源: {doc['source']}\n內容: {doc['content']}"
            for doc in context_docs
        ])
        
        # 構建提示詞
        prompt = f"""基於以下文件內容，請回答用戶的問題。如果文件中沒有相關資訊，請誠實地說明。

文件內容:
{context}

用戶問題: {question}

請提供準確、有幫助的回答:"""
        
        # 使用聊天完成 API
        messages = [
            {"role": "system", "content": "你是一個有幫助的助手，會基於提供的文件內容來回答問題。"},
            {"role": "user", "content": prompt}
        ]
        
        return self.vllm_client.chat_completion(messages, max_tokens=512, temperature=0.3)
    
    def ask_question(self, question: str) -> Dict:
        """處理用戶問題"""
        if not self.is_initialized:
            return {
                'answer': "系統尚未初始化，請先初始化系統。",
                'sources': []
            }
        
        print(f"\n搜尋相關文件...")
        relevant_docs = self.search_relevant_documents(question, k=3)
        
        if relevant_docs:
            print(f"找到 {len(relevant_docs)} 個相關文件")
            for i, doc in enumerate(relevant_docs, 1):
                print(f"  {i}. {doc['source']} (相似度: {doc['score']:.3f})")
        
        print("生成回答...")
        answer = self.generate_answer(question, relevant_docs)
        
        return {
            'answer': answer,
            'sources': [doc['source'] for doc in relevant_docs]
        }

def main():
    """主程式"""
    print("=== RAG 問答系統 ===")
    print("這個系統會基於 PDF 文件來回答您的問題")
    
    # 初始化系統
    rag_system = RAGSystem()
    
    # 檢查 PDF 目錄
    if not os.path.exists("pdfs"):
        print("錯誤: 找不到 'pdfs' 目錄")
        print("請創建 'pdfs' 目錄並放入您要查詢的 PDF 文件")
        return
    
    pdf_files = [f for f in os.listdir("pdfs") if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("錯誤: 'pdfs' 目錄中沒有 PDF 文件")
        print("請將您要查詢的 PDF 文件放入 'pdfs' 目錄")
        return
    
    print(f"找到 {len(pdf_files)} 個 PDF 文件:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    
    # 詢問是否重建向量資料庫
    rebuild = input("\n是否重建向量資料庫？(y/N): ").lower().strip() == 'y'
    
    # 初始化系統
    rag_system.initialize(force_rebuild=rebuild)
    
    if not rag_system.is_initialized:
        print("系統初始化失敗！")
        return
    
    print("\n=== 開始問答 ===")
    print("輸入您的問題，輸入 'quit' 或 'exit' 結束程式")
    
    while True:
        try:
            question = input("\n請輸入您的問題: ").strip()
            
            if question.lower() in ['quit', 'exit', '退出', '結束']:
                print("感謝使用！再見！")
                break
            
            if not question:
                print("請輸入有效的問題")
                continue
            
            # 處理問題
            result = rag_system.ask_question(question)
            
            print(f"\n回答:")
            print(result['answer'])
            
            if result['sources']:
                print(f"\n參考來源:")
                for source in set(result['sources']):
                    print(f"  - {source}")
        
        except KeyboardInterrupt:
            print("\n\n程式被中斷，再見！")
            break
        except Exception as e:
            print(f"發生錯誤: {e}")

if __name__ == "__main__":
    main()