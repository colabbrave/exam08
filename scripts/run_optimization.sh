#!/bin/bash

# 設置腳本目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 設置日誌文件
timestamp=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/optimization_${timestamp}.log"
mkdir -p "$LOG_DIR"

# 初始化日誌
log() {
    local timestamp=$(date +'[%Y-%m-%d %H:%M:%S]')
    echo "$timestamp [INFO] $1" | tee -a "$LOG_FILE"
}

log "=== 會議記錄優化與評估系統 - 依據 act.md 流程 ==="
log "日誌已初始化，日誌文件: $SCRIPT_DIR/$LOG_FILE"
log "執行命令: $0 $*"
log "工作目錄: $SCRIPT_DIR"

# 解析命令行參數
MODEL="cwchang/llama3-taide-lx-8b-chat-alpha1:latest"
OPTIMIZATION_MODEL="gemma3:12b"
MAX_ITERATIONS=5
QUALITY_THRESHOLD=0.8
TRANSCRIPT_DIR="data/transcript"
REFERENCE_DIR="data/reference"
DISABLE_EARLY_STOPPING=false
ENABLE_SEMANTIC_SEGMENTATION=true
SEMANTIC_MODEL="gemma3:12b"
MAX_SEGMENT_LENGTH=4000

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --optimization-model)
            OPTIMIZATION_MODEL="$2"
            shift 2
            ;;
        --max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --quality-threshold)
            QUALITY_THRESHOLD="$2"
            shift 2
            ;;
        --transcript-dir)
            TRANSCRIPT_DIR="$2"
            shift 2
            ;;
        --disable-early-stopping)
            DISABLE_EARLY_STOPPING=true
            shift
            ;;
        --disable-semantic-segmentation)
            ENABLE_SEMANTIC_SEGMENTATION=false
            shift
            ;;
        --semantic-model)
            SEMANTIC_MODEL="$2"
            shift 2
            ;;
        --max-segment-length)
            MAX_SEGMENT_LENGTH="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法: $0 [選項]"
            echo "選項:"
            echo "  --model MODEL                  生成模型 (預設: cwchang/llama3-taide-lx-8b-chat-alpha1:latest)"
            echo "  --optimization-model MODEL     策略優化模型 (預設: gemma3:12b)"
            echo "  --max-iterations N             最大疊代次數 (預設: 5)"
            echo "  --quality-threshold N          品質閾值 (預設: 0.8)"
            echo "  --transcript-dir DIR           逐字稿目錄 (預設: data/transcript)"
            echo "  --disable-early-stopping       禁用提前停止"
            echo "  --disable-semantic-segmentation 禁用語意分段功能"
            echo "  --semantic-model MODEL         語意分段模型 (預設: gemma3:12b)"
            echo "  --max-segment-length N         最大分段長度 (預設: 4000)"
            echo "  -h, --help                     顯示此幫助信息"
            exit 0
            ;;
        *)
            echo "未知選項: $1"
            echo "使用 $0 --help 查看可用選項"
            exit 1
            ;;
    esac
done

# 設置環境變量
export TRANSCRIPT_DIR="$TRANSCRIPT_DIR"
export REFERENCE_DIR="$REFERENCE_DIR"
export OUTPUT_DIR="results"

# 創建必要的目錄
mkdir -p "$TRANSCRIPT_DIR" "$REFERENCE_DIR" "$OUTPUT_DIR" "results/optimized" "results/iterations"

log "設置環境..."
log "檢查系統依賴..."
log "啟動虛擬環境..."

# 檢查並創建虛擬環境
if [ ! -d ".venv" ]; then
    log "創建虛擬環境..."
    python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip

# 安裝依賴
log "安裝 Python 依賴..."
pip install -r requirements.txt

# 安裝額外套件
log "安裝額外套件..."
pip install rouge ollama

log "環境設置完成"
log "使用生成模型: $MODEL"
log "使用策略優化模型: $OPTIMIZATION_MODEL"
log "最大疊代次數: $MAX_ITERATIONS"
log "品質閾值: $QUALITY_THRESHOLD"
log "逐字稿目錄: $SCRIPT_DIR/$TRANSCRIPT_DIR"
log "參考目錄: $SCRIPT_DIR/$REFERENCE_DIR"
log "語意分段功能: $ENABLE_SEMANTIC_SEGMENTATION"
if [ "$ENABLE_SEMANTIC_SEGMENTATION" = true ]; then
    log "語意分段模型: $SEMANTIC_MODEL"
    log "最大分段長度: $MAX_SEGMENT_LENGTH"
fi

# 檢查 Ollama 服務
log "檢查 Ollama 服務狀態..."
if pgrep -x "ollama" > /dev/null; then
    OLLAMA_PID=$(pgrep -x "ollama")
    log "Ollama 已在運行 (PID: $OLLAMA_PID)，等待服務就緒..."
    sleep 2
    log "Ollama 服務已就緒"
else
    log "Ollama 未運行，正在啟動..."
    ollama serve > /dev/null 2>&1 &
    sleep 5
    log "Ollama 服務已啟動"
fi

# 檢查模型是否已下載
log "檢查模型可用性..."
MODELS_TO_CHECK=("$MODEL" "$OPTIMIZATION_MODEL")

if [ "$ENABLE_SEMANTIC_SEGMENTATION" = true ]; then
    MODELS_TO_CHECK+=("$SEMANTIC_MODEL")
fi

for model in "${MODELS_TO_CHECK[@]}"; do
    log "檢查模型 $model 是否已下載..."
    if ! ollama list | grep -q "$model"; then
        log "模型 $model 未找到，正在下載..."
        ollama pull "$model"
        if [ $? -eq 0 ]; then
            log "模型 $model 下載成功"
        else
            log "錯誤: 模型 $model 下載失敗"
            exit 1
        fi
    else
        log "模型 $model 已存在"
    fi
done

# 檢查逐字稿文件
if [ ! -d "$TRANSCRIPT_DIR" ] || [ -z "$(ls -A $TRANSCRIPT_DIR 2>/dev/null)" ]; then
    log "錯誤: 逐字稿目錄 $TRANSCRIPT_DIR 不存在或為空"
    log "請將逐字稿文件放入 $TRANSCRIPT_DIR 目錄中"
    exit 1
fi

transcript_count=$(ls "$TRANSCRIPT_DIR"/*.txt 2>/dev/null | wc -l)
log "找到 $transcript_count 個逐字稿文件"

# 語意分段預處理步驟
if [ "$ENABLE_SEMANTIC_SEGMENTATION" = true ]; then
    log "=== 開始語意分段預處理 ==="
    log "執行語意分段與品質檢查..."
    
    # 創建語意分段輸出目錄
    SEMANTIC_OUTPUT_DIR="output/semantic_segmentation"
    mkdir -p "$SEMANTIC_OUTPUT_DIR"
    
    # 執行批次語意分段處理
    python3 scripts/batch_semantic_processor.py \
        --input-dir "$TRANSCRIPT_DIR" \
        --output-dir "$SEMANTIC_OUTPUT_DIR" \
        --segmentation-model "$SEMANTIC_MODEL" \
        --evaluation-model "$SEMANTIC_MODEL"
    
    if [ $? -eq 0 ]; then
        log "語意分段預處理完成"
        log "分段結果已儲存至: $SEMANTIC_OUTPUT_DIR"
        
        # 檢查是否有品質檢查報告
        LATEST_SUMMARY=$(ls -t "$SEMANTIC_OUTPUT_DIR"/batch_summary_*.json 2>/dev/null | head -1)
        if [ -n "$LATEST_SUMMARY" ]; then
            log "品質檢查報告: $LATEST_SUMMARY"
            
            # 顯示簡要統計
            if command -v jq >/dev/null 2>&1; then
                log "=== 語意分段品質統計 ==="
                jq -r '.statistics | to_entries[] | "\(.key): \(.value)"' "$LATEST_SUMMARY" 2>/dev/null || log "無法解析統計資料"
                
                AVG_QUALITY=$(jq -r '.quality_analysis.average_quality_score' "$LATEST_SUMMARY" 2>/dev/null)
                if [ "$AVG_QUALITY" != "null" ] && [ -n "$AVG_QUALITY" ]; then
                    log "平均品質分數: $AVG_QUALITY"
                fi
            fi
        fi
    else
        log "警告: 語意分段預處理失敗，將繼續使用標準處理模式"
    fi
    log "=== 語意分段預處理完成 ==="
fi

# 開始批次優化流程
log "=== 開始執行完整的疊代優化流程 ==="
log "流程包含: 自動 reference 配對 → minutes 生成 → 多指標評分 → 策略優化 → 疊代與 early stopping → 結果儲存"

# 構建執行參數
PYTHON_ARGS="--max-iterations $MAX_ITERATIONS --quality-threshold $QUALITY_THRESHOLD --model '$MODEL' --optimization-model '$OPTIMIZATION_MODEL'"

if [ "$DISABLE_EARLY_STOPPING" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --disable-early-stopping"
fi

if [ "$ENABLE_SEMANTIC_SEGMENTATION" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --enable-semantic-segmentation --semantic-model '$SEMANTIC_MODEL' --max-segment-length $MAX_SEGMENT_LENGTH"
fi

# 執行優化
log "執行命令: python scripts/iterative_optimizer.py $PYTHON_ARGS"
eval "python scripts/iterative_optimizer.py $PYTHON_ARGS" 2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log "=== 優化流程執行完成 ==="
    log "結果已保存到 results/ 目錄"
    log "- results/optimized/     : 最佳會議記錄與評分報告"
    log "- results/iterations/    : 各輪疊代結果"
    log "- logs/                  : 執行日誌"
    
    # 顯示結果統計
    optimized_count=$(ls results/optimized/*_best.md 2>/dev/null | wc -l)
    report_count=$(ls results/optimized/*_report.json 2>/dev/null | wc -l)
    log "已產生 $optimized_count 份最佳會議記錄和 $report_count 份評分報告"
else
    log "錯誤: 優化流程執行失敗，請檢查日誌"
    exit 1
fi