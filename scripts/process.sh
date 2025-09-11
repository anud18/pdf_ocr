#!/bin/bash

# PDF 處理腳本

echo "🔄 開始處理 PDF 文件..."

# 檢查 input 目錄是否有 PDF 文件
if [ ! "$(ls -A input/*.pdf 2>/dev/null)" ]; then
    echo "❌ input 目錄中沒有找到 PDF 文件"
    echo "請將要處理的 PDF 文件放入 input/ 目錄"
    exit 1
fi

# 檢查 vLLM 服務是否運行
if ! docker compose ps vllm-qwen | grep -q "Up"; then
    echo "🚀 啟動 vLLM 服務..."
    docker compose up -d vllm-qwen
    
    echo "⏳ 等待服務啟動（這可能需要幾分鐘）..."
    sleep 30
fi

# 運行處理程序
echo "🖼️ 開始圖片分析和 OCR 處理..."
docker compose run --rm pdf-processor

echo "✅ 處理完成！"
echo "📄 結果文件保存在 output/ 目錄中"