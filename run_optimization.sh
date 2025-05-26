#!/bin/bash

# 設置錯誤處理
set -euo pipefail
trap 'handle_error $? $LINENO' ERR

# 基礎配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/optimization_$(date +%Y%m%d_%H%M%S).log"
MAX_RETRIES=3
MODEL=""
INTERACTIVE=1  # 預設啟用交互模式

# 解析命令行參數
while [[ $# -gt 0 ]]; do
  case $1 in
    --non-interactive)
      INTERACTIVE=0  # 使用 --non-interactive 關閉交互模式
      shift
      ;;
    --interactive)
      INTERACTIVE=1  # 保留 --interactive 參數以保持向後兼容
      shift
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    *)
      echo "未知選項: $1"
      exit 1
      ;;
  esac
done

# 創建日誌目錄
mkdir -p "${SCRIPT_DIR}/logs"

# 錯誤處理函數
handle_error() {
    local exit_code=$1
    local line_no=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] 腳本在行 ${line_no} 出錯，退出碼: ${exit_code}" | tee -a "$LOG_FILE"
    
    # 清理資源
    if [ "${OLLAMA_STARTED_BY_SCRIPT:-0}" = "1" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] 清理 Ollama 服務..." | tee -a "$LOG_FILE"
        pkill -f "ollama serve" || true
    fi
    
    exit "$exit_code"
}

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" | tee -a "$LOG_FILE"
}

# 檢查並啟動虛擬環境
setup_environment() {
    if [ ! -f "${SCRIPT_DIR}/.venv/bin/activate" ]; then
        log "錯誤: 找不到虛擬環境，請先建立 .venv"
        exit 1
    fi
    
    log "啟動虛擬環境..."
    source "${SCRIPT_DIR}/.venv/bin/activate"
}

# 檢查並啟動 Ollama
setup_ollama() {
    local retries=0
    OLLAMA_STARTED_BY_SCRIPT=0
    
    # 檢查 Ollama 是否已經在運行
    OLLAMA_PID=$(pgrep -f "ollama serve" || true)
    if [ -n "$OLLAMA_PID" ]; then
        log "Ollama 已在運行 (PID: $OLLAMA_PID)，等待服務就緒..."
        # 等待 Ollama 服務就緒
        for i in {1..20}; do
            sleep 1
            if ollama list >/dev/null 2>&1; then
                log "Ollama 服務已就緒"
                OLLAMA_STARTED_BY_SCRIPT=0
                return 0
            fi
            log "等待 Ollama 服務就緒... ($i/20)"
        done
        log "警告: 無法連接到現有的 Ollama 服務，嘗試重啟..."
        pkill -f "ollama serve" || true
        sleep 2
    fi
    
    # 如果 Ollama 未運行，則啟動它
    while [ $retries -lt $MAX_RETRIES ]; do
        log "Ollama 未運行，正在啟動..."
        nohup ollama serve > "${SCRIPT_DIR}/logs/ollama.log" 2>&1 &
        OLLAMA_PID=$!
        OLLAMA_STARTED_BY_SCRIPT=1
        log "Ollama 已啟動 (PID: $OLLAMA_PID)"
        
        # 等待 Ollama 啟動
        for i in {1..20}; do
            sleep 1
            if ollama list >/dev/null 2>&1; then
                log "Ollama 服務已就緒"
                return 0
            fi
            log "等待 Ollama 服務啟動... ($i/20)"
        done
        
        # 如果 Ollama 啟動失敗，殺死可能殘留的進程
        if [ -n "$OLLAMA_PID" ]; then
            kill -9 "$OLLAMA_PID" 2>/dev/null || true
        fi
        
        retries=$((retries + 1))
        log "Ollama 啟動超時，重試 ($retries/$MAX_RETRIES)..."
    done
    
    log "錯誤: 無法啟動 Ollama 服務"
    exit 1
}

# 清理函數
cleanup() {
    if [ "${OLLAMA_STARTED_BY_SCRIPT:-0}" = "1" ]; then
        log "正在停止 Ollama 服務..."
        pkill -f "ollama serve" || true
    fi
    log "腳本執行完成"
}

# 主函數
main() {
    log "=== 開始執行會議記錄優化流程 ==="
    
    # 設置環境
    setup_environment
    setup_ollama
    
    # 選擇模型
    if [ -z "$MODEL" ]; then
    log "正在選擇模型..."
    
    # 根據 INTERACTIVE 變量決定是否使用交互模式
    if [ "$INTERACTIVE" -eq 1 ] && [ -t 0 ]; then
        log "使用交互模式選擇模型..."
        # 確保標準輸入來自終端
        MODEL=$(python "${SCRIPT_DIR}/scripts/select_model.py" < /dev/tty)
    else
        log "使用非交互模式，自動選擇第一個可用模型..."
        MODEL=$(python "${SCRIPT_DIR}/scripts/select_model.py" --non-interactive)
    fi
    
    if [ $? -ne 0 ] || [ -z "$MODEL" ]; then
        log "錯誤: 模型選擇失敗"
        exit 1
    fi
    fi
    log "已選擇模型: $MODEL"
    
    # 執行優化
    log "開始執行優化流程..."
    if ! python "${SCRIPT_DIR}/scripts/optimize.py" --model "$MODEL"; then
        log "錯誤: 優化流程失敗"
        exit 1
    fi
    
    # 執行評估
    log "開始執行評估流程..."
    if ! python "${SCRIPT_DIR}/scripts/evaluate.py"; then
        log "錯誤: 評估流程失敗"
        exit 1
    fi
    
    log "=== 會議記錄優化流程完成 ==="
}

# 執行主函數
trap cleanup EXIT
main "$@"