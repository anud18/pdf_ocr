# RAG 測試範例

這個資料夾包含了 RAG (Retrieval-Augmented Generation) 測試的範例程式，使用 vLLM API 來回答基於 PDF 文件的問題。

## 結構說明

- `rag_main.py` - 主程式，提供使用者介面來輸入問題
- `rag_client.py` - vLLM API 客戶端
- `document_processor.py` - 文件處理和向量化
- `vector_store.py` - 向量資料庫管理
- `pdfs/` - 存放要做 RAG 的 PDF 文件
- `requirements.txt` - 相依套件

## 使用方法

1. 將 PDF 文件放入 `pdfs/` 資料夾
2. 安裝相依套件：`pip install -r requirements.txt`
3. 執行主程式：`python rag_main.py`
4. 輸入問題，系統會基於 PDF 內容回答