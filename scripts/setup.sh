#!/bin/bash

# PDF 圖片轉文字處理系統設置腳本

echo "🚀 設置 PDF 圖片轉文字處理系統..."

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

# 檢查 Docker Compose 是否安裝
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

# 檢查 NVIDIA Docker 是否可用
if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo "⚠️  警告: NVIDIA Docker 支援可能未正確配置"
    echo "   請確保已安裝 NVIDIA Container Toolkit"
fi

# 創建必要的目錄
echo "📁 創建目錄結構..."
mkdir -p input output temp models

# 設置權限
chmod +x scripts/*.sh

# 複製環境變數文件
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 已創建 .env 文件，請根據需要修改配置"
fi

echo "✅ 設置完成！"
echo ""
echo "📋 下一步："
echo "1. 將要處理的 PDF 文件放入 input/ 目錄"
echo "2. 運行: docker-compose up -d vllm-qwen"
echo "3. 等待模型加載完成"
echo "4. 運行: docker-compose run --rm pdf-processor"
echo ""
echo "📖 更多信息請查看 README.md"