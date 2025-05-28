#!/bin/bash

# 設置錯誤處理
set -euo pipefail
trap 'handle_error $? $LINENO' ERR

# 基礎配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
PYTHON_DEPS=(
    "scikit-learn>=1.0.2"
    "evaluate>=0.4.0"
    "rouge-score>=0.1.2"
    "bert-score>=0.3.13"
    "numpy>=1.19.5"
    "pandas>=1.3.0"
    "torch>=1.10.0"
    "transformers>=4.18.0"
    "tqdm>=4.62.0"
    "requests>=2.25.1"
)

# 優化參數 - 設置默認值
STABILITY_THRESHOLD=0.7
QUALITY_THRESHOLD=0.6
MAX_ITERATIONS=10
BATCH_SIZE=3
WARMUP_ITERATIONS=2
EARLY_STOPPING=5
MIN_IMPROVEMENT=0.01

# 輸入輸出設置
TRANSCRIPT_DIR="${SCRIPT_DIR}/data/transcript"  # 逐字稿目錄
REFERENCE_DIR="${SCRIPT_DIR}/data/reference"    # 參考會議記錄目錄
OUTPUT_DIR="${SCRIPT_DIR}/optimized_results"     # 輸出目錄
LOG_FILE="${SCRIPT_DIR}/logs/optimization_$(date +%Y%m%d_%H%M%S).log"
MODEL="gemma3:12b"  # 默認使用 Gemma 3 12B 模型
SKIP_MODEL_CHECK=0  # 啟用模型檢查
INTERACTIVE=1       # 預設啟用交互模式

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
    --input-dir)
      INPUT_DIR="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --stability-threshold)
      STABILITY_THRESHOLD="$2"
      shift 2
      ;;
    --quality-threshold)
      QUALITY_THRESHOLD="$2"
      shift 2
      ;;
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --batch-size)
      BATCH_SIZE="$2"
      shift 2
      ;;
    --warmup-iterations)
      WARMUP_ITERATIONS="$2"
      shift 2
      ;;
    --early-stopping)
      EARLY_STOPPING="$2"
      shift 2
      ;;
    --min-improvement)
      MIN_IMPROVEMENT="$2"
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      # 為了向後兼容，將未識別的參數視為輸入目錄
      if [ -z "$INPUT_DIR" ] && [ -d "$1" ]; then
        INPUT_DIR="$1"
        shift
      else
        echo "未知選項: $1"
        show_help
        exit 1
      fi
      ;;
  esac
done

# 顯示幫助信息
show_help() {
  echo "用法: $0 [選項] [輸入目錄]"
  echo ""
  echo "選項:"
  echo "  --model MODEL_NAME          指定要使用的模型 (預設: $MODEL)"
  echo "                             支援的模型: gemma3:12b, gemma3:4b, llama3:latest, mistral:latest"
  echo "  --input-dir DIR            包含參考會議記錄的目錄 (預設: $TRANSCRIPT_DIR)"
  echo "  --output-dir DIR           輸出目錄 (預設: $OUTPUT_DIR)"
  echo "  --stability-threshold FLOAT 穩定性閾值 (0-1, 預設: $STABILITY_THRESHOLD)"
  echo "  --quality-threshold FLOAT   質量閾值 (0-1, 預設: $QUALITY_THRESHOLD)"
  echo "  --max-iterations INT       最大迭代次數 (預設: $MAX_ITERATIONS)"
  echo "  --batch-size INT           每批生成的樣本數 (預設: $BATCH_SIZE)"
  echo "  --warmup-iterations INT    預熱迭代次數 (預設: $WARMUP_ITERATIONS)"
  echo "  --early-stopping INT       早停輪數 (預設: $EARLY_STOPPING)"
  echo "  --min-improvement FLOAT    最小改進閾值 (預設: $MIN_IMPROVEMENT)"
  echo "  --non-interactive         非交互模式"
  echo "  -h, --help                顯示此幫助信息"
  echo ""
  echo "示例:"
  echo "  $0 --input-dir ./meeting_notes --model $MODEL"
  echo "  $0 --input-dir ./meeting_notes --output-dir ./results --stability-threshold 0.8"
  echo "  $0 --non-interactive --input-dir ./meeting_notes --batch-size 5 --max-iterations 20"
  echo "  $0 --help                 顯示完整幫助信息"
}

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

# 檢查並安裝系統依賴
install_system_deps() {
    log "檢查系統依賴..."
    
    # 檢查是否已安裝 Python 3
    if ! command -v python3 &> /dev/null; then
        log "錯誤: 未找到 Python 3，請先安裝 Python 3.8 或更高版本"
        exit 1
    fi
    
    # 檢查是否已安裝 pip
    if ! command -v pip3 &> /dev/null; then
        log "錯誤: 未找到 pip3，請先安裝 pip"
        exit 1
    fi
    
    # 檢查是否已安裝 virtualenv
    if ! command -v virtualenv &> /dev/null; then
        log "安裝 virtualenv..."
        pip3 install --user virtualenv
    fi
}

# 創建虛擬環境
create_virtualenv() {
    if [ ! -d "$VENV_DIR" ]; then
        log "創建虛擬環境..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # 啟動虛擬環境
    log "啟動虛擬環境..."
    source "${VENV_DIR}/bin/activate"
    
    # 升級 pip
    pip install --upgrade pip
}

# 安裝 Python 依賴
install_python_deps() {
    log "安裝 Python 依賴..."
    source "${VENV_DIR}/bin/activate"
    
    # 安裝 requirements.txt 中的依賴
    if [ -f "${REQUIREMENTS_FILE}" ]; then
        pip install -r "${REQUIREMENTS_FILE}" || {
            log "錯誤: 無法安裝 requirements.txt 中的依賴"
            exit 1
        }
    fi
    
    # 安裝其他必要的 Python 依賴
    for dep in "${PYTHON_DEPS[@]}"; do
        pip install "$dep" || {
            log "警告: 安裝 $dep 失敗，但繼續執行..."
        }
    done
    
    # 安裝 rouge 套件
    log "安裝 rouge 套件..."
    pip install rouge || {
        log "警告: 安裝 rouge 套件失敗，但繼續執行..."
    }
    
    # 安裝 ollama 套件
    log "安裝 ollama 套件..."
    pip install ollama >> "${LOG_FILE}" 2>&1 || {
        log "錯誤: 安裝 ollama 套件失敗"
        exit 1
    }
}

# 檢查並設置環境
setup_environment() {
    log "設置環境..."
    
    # 安裝系統依賴
    install_system_deps
    
    # 創建並啟動虛擬環境
    create_virtualenv
    
    # 安裝 Python 依賴
    install_python_deps
    
    log "環境設置完成"
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
                # 跳過模型下載檢查
                log "跳過模型下載檢查，直接使用模型"
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
                # 跳過模型下載檢查
                log "跳過模型下載檢查，直接使用模型"
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

# 檢查並下載模型
check_and_pull_model() {
    # 如果設置了跳過模型檢查，則直接返回
    if [ "${SKIP_MODEL_CHECK:-0}" = "1" ]; then
        log "跳過模型檢查，直接使用模型: $MODEL"
        return 0
    fi
    
    local model_name=${MODEL:-cwchang/llama3-taide-lx-8b-chat-alpha1:latest}  # 使用指定的模型或默認值
    log "檢查模型 $model_name 是否已下載..."
    
    # 檢查模型是否已存在
    if ollama list | grep -q "$model_name"; then
        log "模型 $model_name 已下載"
    else
        log "模型 $model_name 未找到，正在下載..."
        if ollama pull "$model_name"; then
            log "模型 $model_name 下載成功"
        else
            log "錯誤: 無法下載模型 $model_name"
            exit 1
        fi
    fi
}

# 清理函數
cleanup() {
    if [ "${OLLAMA_STARTED_BY_SCRIPT:-0}" = "1" ]; then
        log "正在停止 Ollama 服務..."
        pkill -f "ollama serve" || true
    fi
    log "腳本執行完成"
}

# 初始化日誌
init_logging() {
    LOG_DIR="${SCRIPT_DIR}/logs"
    mkdir -p "${LOG_DIR}"
    LOG_FILE="${LOG_DIR}/optimization_$(date +%Y%m%d_%H%M%S).log"
    exec > >(tee -a "${LOG_FILE}") 2>&1
    log "日誌已初始化，日誌文件: ${LOG_FILE}"
}

# 主函數
main() {
    # 初始化日誌
    init_logging
    
    log "=== 開始執行會議記錄優化流程 ==="
    log "執行命令: $0 $*"
    log "工作目錄: $(pwd)"
    log "腳本目錄: ${SCRIPT_DIR}"
    
    # 設置環境
    setup_environment
    
    # 檢查目錄是否存在
    for dir_var in "TRANSCRIPT_DIR" "REFERENCE_DIR"; do
        dir_path=$(eval echo "\$$dir_var")
        if [ ! -d "$dir_path" ]; then
            log "錯誤: 目錄不存在 ($dir_var): $dir_path"
            exit 1
        fi
        log "使用 $dir_var: $dir_path"
    done
    
    # 創建輸出目錄
    mkdir -p "$OUTPUT_DIR"
    
    # 檢查並啟動 Ollama 服務
    setup_ollama
    
    # 檢查並下載模型
    check_and_pull_model "$MODEL"
    
    # 檢查參考目錄是否存在
    if [ ! -d "$REFERENCE_DIR" ]; then
        log "錯誤: 參考會議記錄目錄不存在: $REFERENCE_DIR"
        exit 1
    fi
    
    # 創建輸出目錄
    mkdir -p "$OUTPUT_DIR"
    
    # 構建優化命令
    CMD=(
        "${SCRIPT_DIR}/scripts/optimization/stability_optimizer.py"
        "$REFERENCE_DIR"
        "--output-dir" "$OUTPUT_DIR"
        "--model" "$MODEL"
        "--stability-threshold" "$STABILITY_THRESHOLD"
        "--quality-threshold" "$QUALITY_THRESHOLD"
        "--max-iterations" "$MAX_ITERATIONS"
        "--batch-size" "$BATCH_SIZE"
        "--warmup-iterations" "$WARMUP_ITERATIONS"
        "--early-stopping" "$EARLY_STOPPING"
        "--min-improvement" "$MIN_IMPROVEMENT"
    )
    
    # 如果是非交互模式，添加 --non-interactive 參數
    [ "$INTERACTIVE" -eq 0 ] && CMD+=( "--non-interactive" )
    
    log "優化參數:"
    log "  - 模型: $MODEL"
    log "  - 參考目錄: $REFERENCE_DIR"
    log "  - 輸出目錄: $OUTPUT_DIR"
    log "  - 穩定性閾值: $STABILITY_THRESHOLD"
    log "  - 質量閾值: $QUALITY_THRESHOLD"
    log "  - 最大迭代次數: $MAX_ITERATIONS"
    log "  - 批次大小: $BATCH_SIZE"
    log "  - 預熱迭代: $WARMUP_ITERATIONS"
    log "  - 早停輪數: $EARLY_STOPPING"
    log "  - 最小改進: $MIN_IMPROVEMENT"
    
    # 執行優化
    log "開始執行優化流程..."
    log "命令: ${CMD[*]}"
    
    # 添加項目根目錄到 PYTHONPATH
    export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"
    
    # 切換到項目根目錄執行腳本
    cd "${SCRIPT_DIR}" && \
    if ! python "${CMD[0]}" "${CMD[@]:1}"; then
        log "錯誤: 優化流程失敗"
        exit 1
    fi
    
    log "優化完成，結果已保存到: $OUTPUT_DIR"
    
    # 顯示結果文件路徑
    if [ -d "$OUTPUT_DIR" ]; then
        log "\n=== 結果文件 ==="
        find "$OUTPUT_DIR" -type f | while read -r file; do
            log "- $file"
            
            # 如果是文本文件，顯示前幾行
            if [[ "$file" == *.txt || "$file" == *.log ]]; then
                log "  內容預覽:"
                head -n 10 "$file" | while IFS= read -r line; do
                    log "  $line"
                done
                [ $(wc -l < "$file") -gt 10 ] && log "  ... (更多內容請查看文件)"
            fi
        done
    fi
    
    log "\n=== 會議記錄優化流程完成 ==="
    log "最佳模板路徑: $OUTPUT_DIR/optimized_template.txt"
    log "日誌文件: $LOG_FILE"
    log ""
    log "使用範例:"
    log "  $0 --input-dir ./meeting_notes --model gemma3:4b"
    log "  $0 --input-dir ./meeting_notes --output-dir ./results --stability-threshold 0.8"
}

# 執行主函數
trap cleanup EXIT
main "$@"