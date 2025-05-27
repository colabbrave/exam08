#!/bin/bash

# 設置腳本在遇到錯誤時終止執行
set -e

# 顯示歡迎訊息
echo "=== 會議記錄AI優化系統 - 環境設置腳本 ==="
echo "此腳本將幫助您設置開發環境。"

# 檢查是否以 root 身份執行
if [ "$(id -u)" -eq 0 ]; then
    echo "錯誤：請勿使用 root 權限執行此腳本。"
    exit 1
fi

# 檢查是否已安裝 Python 3.8+
if ! command -v python3 &> /dev/null; then
    echo "錯誤：未檢測到 Python 3。請先安裝 Python 3.8 或更高版本。"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "錯誤：需要 Python 3.8 或更高版本，當前版本為 $PYTHON_VERSION"
    exit 1
fi

echo "✓ 檢測到 Python $PYTHON_VERSION"

# 檢查是否已安裝 virtualenv
if ! command -v virtualenv &> /dev/null; then
    echo "未找到 virtualenv，正在安裝..."
    pip3 install --user virtualenv
    export PATH="$HOME/.local/bin:$PATH"
fi

# 創建虛擬環境
VENV_NAME="venv"
if [ ! -d "$VENV_NAME" ]; then
    echo "創建虛擬環境..."
    python3 -m venv $VENV_NAME
    echo "✓ 虛擬環境已創建於 $VENV_NAME/"
else
    echo "✓ 虛擬環境已存在於 $VENV_NAME/"
fi

# 激活虛擬環境
echo "激活虛擬環境..."
source "$VENV_NAME/bin/activate"

# 升級 pip
echo "升級 pip..."
pip install --upgrade pip

# 安裝依賴
echo "安裝 Python 依賴..."
pip install -r requirements.txt

# 安裝開發依賴（如果存在）
if [ -f "requirements-dev.txt" ]; then
    echo "安裝開發依賴..."
    pip install -r requirements-dev.txt
fi

# 創建必要的目錄
echo "創建必要的目錄..."
mkdir -p data/reference
mkdir -p results/optimized
mkdir -p results/evaluation_reports

# 檢查 Ollama 是否已安裝
if ! command -v ollama &> /dev/null; then
    echo "警告：未檢測到 Ollama。"
    echo "請從 https://ollama.ai/ 下載並安裝 Ollama。"
    echo "安裝完成後，請執行 'ollama pull gemma:2b' 下載模型。"
else
    echo "✓ 檢測到 Ollama"
    
    # 檢查是否已下載常用模型
    echo "檢查常用模型..."
    if ! ollama list | grep -q "gemma"; then
        echo "提示：建議下載 gemma 模型以獲得最佳體驗"
        echo "  執行: ollama pull gemma:2b"
    fi
fi

# 設置完成
echo "\n=== 環境設置完成 ==="
echo "1. 每次開始工作前，請先執行: source $VENV_NAME/bin/activate"
echo "2. 運行優化腳本: ./run_optimization.sh"
echo "3. 運行評估腳本: python scripts/evaluate.py"
echo "\n祝您使用愉快！"

exit 0
