# PDF 圖片轉文字處理系統

使用 Qwen2.5-VL 模型和 vLLM 進行 PDF 中圖片的 OCR 和描述生成。

## 問題介紹
LLM 對 PDF 裡面的圖片無法解讀，或許可以透過 OCR 的技術讓 LLM 去讀圖片裡的文字來讓 LLM 理解圖片
<img width="766" height="838" alt="image" src="https://github.com/user-attachments/assets/0e8e7fa5-0cb2-4511-8372-150b3f275e7e" />

## 預期結果
LLM 可以回答出 按下正反轉按鍵後，下一步？ 這個問題

## 嘗試的解法
1. 將該頁面丟給 VLM 來回答
* Gemini2.5 pro

<img width="1092" height="429" alt="image" src="https://github.com/user-attachments/assets/cd9cfae3-7e60-49ad-97dc-3d632993bdf2" />

* Qwen2.5-VL-32B-Instruct

<img width="948" height="512" alt="image" src="https://github.com/user-attachments/assets/855bfb00-1985-4b1d-bc04-3047df39c107" />


2. 將 OCR 後的文字丟給 LLM

* GPT-OSS 20B
### 按下 **正/反轉鍵** 後會發生什麼？

根據您提供的「PM 馬達參數自動量測」流程圖文字說明，當您完成前面的設定（配線、馬達常數、05‑00(P.301) 參數等）後，**按下正/反轉鍵** 是啟動自動量測的關鍵動作。  

以下是 **按鍵之後的即時流程**：

| 步驟 | 內容 | 操作面板顯示 |
|------|------|--------------|
| 1️⃣ | **開始量測** – 變頻器（VFD）依照先前設定的參數，開始對馬達進行自動調校（Auto‑tuning）。 | **“TUN”**（Tuning） |
| 2️⃣ | **量測過程** – 變頻器會依序測量電阻、感抗、電感、磁極偏移角等參數，並即時調整控制參數。此階段不需要再操作任何按鍵，只要確保馬達可以自由轉動（或依設定做靜態量測）。 | 仍顯示 **“TUN”**，同時可能出現測量進度條或數值變化（依機型而異）。 |
| 3️⃣ | **量測結果判斷** – 完成後變頻器會自動判斷量測是否成功。 | - 成功 → 顯示 **“TEnd”**（Tuning End）<br>- 失敗 → 顯示 **“FAL”**（Fail） |

---

## 完整的後續流程（從「TUN」開始）

1. **量測成功（顯示 “TEnd”）**  
   - 若您 **需要自行微調** 參數：  
     - 進入手動輸入模式，調整 **05‑12(P.313) ~ 05‑16(P. 317)**（如電阻、感抗、磁極偏移角等）。  
     - 完成後，執行 **變頻器復歸（Reset）**，讓新參數生效。  
   - 若 **不需要微調**：直接結束，系統已完成自動量測。

2. **量測失敗（顯示 “FAL”）**  
   - 檢查以下可能的原因：  
     - 配線錯誤或接觸不良（參照 3.7 端子配線）。  
     - 先前設定的 **05‑00(P.301)**、**00‑21(P.300)**、**05‑02(P.303)** 等參數不符合實際馬達規格。  
     - 馬達被負載或機械卡住，無法自由轉動（尤其在 **動態量測** 模式下）。  
   - 修正後重新 **按正/反轉鍵** 再次嘗試。

3. **若流程圖中還有「磁極偏移角自動量測」**（在成功完成基本參數值量測後）  
   - 需要將 **05‑00(P.301) = 9**、**00‑21(P.300) = 5**，並正確設定 **09‑01(P.350)**、**09‑02(P.351)**。  
   - 再次 **按正/反轉鍵**，系統會進入磁極偏移角的自動量測，成功則顯示 “TEnd”，失敗則顯示 “FAL”。

---

## 小結：**按下正/反轉鍵的下一步是「開始自動量測」**，面板會顯示 **“TUN”**，接著系統自行完成測量並根據結果顯示 **“TEnd”**（成功）或 **“FAL”**（失敗），之後再依需求進行微調或結束。  

若在操作過程中遇到任何顯示異常或量測失敗，請回到前面的設定步驟檢查配線與參數，確保所有設定與實際馬達規格相符後再重新執行。祝您量測順利！

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
