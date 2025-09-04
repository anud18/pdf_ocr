# PDF 圖片轉文字處理系統

使用 Qwen2.5-VL 模型和 vLLM 進行 PDF 中圖片的 OCR 和描述生成。

## 功能特色

- 🖼️ 自動提取 PDF 中的圖片
- 🤖 使用 Qwen2.5-VL-72B 模型進行圖片分析
- 📝 生成圖片描述和 OCR 文字識別
- 📄 輸出增強版 PDF（包含圖片描述）
- 🐳 完整的 Docker 容器化解決方案

## 系統需求

- Docker 和 Docker Compose
- NVIDIA GPU（建議 24GB+ VRAM）
- NVIDIA Container Toolkit

## 快速開始

### 1. 啟動服務

```bash
# 啟動 vLLM 服務和處理器
docker-compose up -d vllm-qwen

# 等待模型加載完成（首次啟動需要下載模型，可能需要較長時間）
docker-compose logs -f vllm-qwen
```

### 2. 處理 PDF 文件

```bash
# 將要處理的 PDF 文件放入 input 目錄
mkdir -p input output

# 複製你的 PDF 文件到 input 目錄
cp your_document.pdf input/

# 運行處理程序
docker-compose run --rm pdf-processor
```

### 3. 查看結果

處理完成的 PDF 文件會保存在 `output` 目錄中，文件名前綴為 `enhanced_`。

## 目錄結構

```
.
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile             # PDF 處理器容器配置
├── requirements.txt       # Python 依賴
├── main.py               # 主程序
├── src/
│   ├── pdf_processor.py  # PDF 處理邏輯
│   └── vlm_client.py     # VLM API 客戶端
├── input/                # 輸入 PDF 文件目錄
├── output/               # 輸出結果目錄
└── temp/                 # 臨時文件目錄
```

## 配置選項

### 模型配置

在 `docker-compose.yml` 中可以調整：

- `--model`: 模型名稱（預設使用 72B AWQ 量化版本）
- `--max-model-len`: 最大序列長度
- `--gpu-memory-utilization`: GPU 記憶體使用率

### 支援的模型

- `Qwen/Qwen2.5-VL-72B-Instruct-AWQ` (推薦，4bit 量化)
- `Qwen/Qwen2.5-VL-32B-Instruct-AWQ`
- `Qwen/Qwen2.5-VL-7B-Instruct`

## 使用說明

### 圖片分析功能

系統會對每張圖片進行兩種分析：

1. **圖片描述**: 詳細描述圖片內容、場景、物體等
2. **OCR 文字識別**: 提取圖片中的文字內容

### 輸出格式

增強版 PDF 會在原始圖片下方添加：
- 藍色文字的圖片描述
- 識別出的文字內容

## 故障排除

### 常見問題

1. **GPU 記憶體不足**
   ```bash
   # 使用較小的模型
   # 在 docker-compose.yml 中修改為 32B 或 7B 版本
   ```

2. **模型下載緩慢**
   ```bash
   # 可以預先下載模型到 ./models 目錄
   # 並在 docker-compose.yml 中指定本地路徑
   ```

3. **處理大型 PDF 文件**
   ```bash
   # 增加容器記憶體限制
   # 調整 --max-model-len 參數
   ```

### 日誌查看

```bash
# 查看 vLLM 服務日誌
docker-compose logs vllm-qwen

# 查看處理器日誌
docker-compose logs pdf-processor
```

## 效能優化

- 使用 AWQ 4bit 量化模型可大幅降低 VRAM 需求
- 批次處理多個 PDF 文件
- 根據 GPU 記憶體調整 `gpu-memory-utilization` 參數


## 遇到的問題
1. 原先想說直接抓頁面的每一張的圖片做 ocr，但發現項流程圖的圖片可能會是有幾百張圖片組成
<img width="743" height="810" alt="image" src="https://github.com/user-attachments/assets/8b2c955b-9f0d-4853-ae5a-e9f941c9f329" />


2. 改為將頁面轉為圖片，丟給 VLM 做 OCR


## 授權

本專案使用 MIT 授權條款。# pdf_ocr
