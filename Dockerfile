FROM python:3.11-slim

# 設置 UTF-8 環境變數
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libxml2-dev \
    libxslt-dev \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8

# 複製需求文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY src/ ./src/
COPY main.py .

# 創建必要的目錄
RUN mkdir -p input output temp

CMD ["python", "main.py"]