#!/bin/bash
# UTF-8 測試運行腳本

echo "=== 開始 UTF-8 編碼測試 ==="

# 設置環境變數
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONIOENCODING=utf-8

# 顯示當前環境
echo "當前環境設置："
echo "LANG: $LANG"
echo "LC_ALL: $LC_ALL"
echo "PYTHONIOENCODING: $PYTHONIOENCODING"
echo ""

# 運行 Python UTF-8 測試
echo "運行 Python UTF-8 測試..."
python3 test_utf8.py

echo ""
echo "=== UTF-8 編碼測試完成 ==="