#!/bin/bash

# 深度清理腳本 - 專案檔案歸檔和整理
# 將根目錄過多的檔案歸檔到相應目錄

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="archive/deep_cleanup_$TIMESTAMP"
REPORT_FILE="PROJECT_DEEP_CLEANUP_REPORT_$TIMESTAMP.md"
LOG_FILE="logs/deep_cleanup_$TIMESTAMP.log"

# 創建必要目錄
mkdir -p "$BACKUP_DIR" logs archive/temp_files archive/old_versions

echo "🧹 開始深度清理..." | tee -a "$LOG_FILE"
echo "📅 時間: $(date)" | tee -a "$LOG_FILE"
echo "📁 備份目錄: $BACKUP_DIR" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"

# 統計初始狀態
INITIAL_ROOT_COUNT=$(ls -1 | wc -l | tr -d ' ')
echo "📊 清理前根目錄項目數: $INITIAL_ROOT_COUNT" | tee -a "$LOG_FILE"

# 歸檔計數器
ARCHIVED_COUNT=0

# 1. 移動文檔檔案到 docs/
echo "📚 整理文檔檔案..." | tee -a "$LOG_FILE"
mkdir -p docs
for file in *.md; do
    if [ -f "$file" ] && [ "$file" != "README.md" ]; then
        # 檢查docs/目錄是否已有同名檔案
        if [ -f "docs/$file" ]; then
            mv "$file" "$BACKUP_DIR/" && echo "  備份重複檔案: $file" | tee -a "$LOG_FILE"
        else
            mv "$file" docs/ && echo "  移動文檔: $file → docs/" | tee -a "$LOG_FILE"
        fi
        ((ARCHIVED_COUNT++))
    fi
done

# 2. 移動測試檔案到 tests/
echo "🧪 整理測試檔案..." | tee -a "$LOG_FILE"
mkdir -p tests
for file in test_*.py; do
    if [ -f "$file" ]; then
        if [ -f "tests/$file" ]; then
            mv "$file" "$BACKUP_DIR/" && echo "  備份重複測試檔案: $file" | tee -a "$LOG_FILE"
        else
            mv "$file" tests/ && echo "  移動測試檔案: $file → tests/" | tee -a "$LOG_FILE"
        fi
        ((ARCHIVED_COUNT++))
    fi
done

# 3. 移動分析腳本到 scripts/
echo "📊 整理分析腳本..." | tee -a "$LOG_FILE"
mkdir -p scripts
for file in analyze_*.py; do
    if [ -f "$file" ]; then
        if [ -f "scripts/$file" ]; then
            mv "$file" "$BACKUP_DIR/" && echo "  備份重複腳本: $file" | tee -a "$LOG_FILE"
        else
            mv "$file" scripts/ && echo "  移動分析腳本: $file → scripts/" | tee -a "$LOG_FILE"
        fi
        ((ARCHIVED_COUNT++))
    fi
done

# 4. 歸檔執行腳本中的舊版本
echo "🗂️ 整理執行腳本..." | tee -a "$LOG_FILE"
for file in run_*.sh; do
    if [ -f "$file" ]; then
        # 保留最新的，舊版本移到backup
        if [[ "$file" =~ run_(all_models|optimization)\.sh$ ]]; then
            echo "  保留執行腳本: $file" | tee -a "$LOG_FILE"
        else
            mv "$file" "$BACKUP_DIR/" && echo "  歸檔舊執行腳本: $file" | tee -a "$LOG_FILE"
            ((ARCHIVED_COUNT++))
        fi
    fi
done

# 5. 清理空檔案
echo "🗑️ 清理空檔案..." | tee -a "$LOG_FILE"
EMPTY_FILES=$(find . -maxdepth 1 -type f -empty)
if [ -n "$EMPTY_FILES" ]; then
    echo "$EMPTY_FILES" | while read empty_file; do
        if [ -f "$empty_file" ]; then
            rm "$empty_file" && echo "  刪除空檔案: $empty_file" | tee -a "$LOG_FILE"
            ((ARCHIVED_COUNT++))
        fi
    done
else
    echo "  沒有發現空檔案" | tee -a "$LOG_FILE"
fi

# 6. 歸檔臨時和快取檔案
echo "💾 清理臨時檔案..." | tee -a "$LOG_FILE"
for pattern in "*.tmp" "*.cache" "*.pyc" "__pycache__" ".coverage"; do
    find . -maxdepth 1 -name "$pattern" -exec mv {} archive/temp_files/ \; 2>/dev/null && \
    echo "  清理: $pattern" | tee -a "$LOG_FILE"
done

# 7. 歸檔舊的腳本檔案
echo "📜 整理腳本檔案..." | tee -a "$LOG_FILE"
for file in verify_structure.sh; do
    if [ -f "$file" ]; then
        mv "$file" archive/old_versions/ && echo "  歸檔舊腳本: $file" | tee -a "$LOG_FILE"
        ((ARCHIVED_COUNT++))
    fi
done

# 統計最終狀態
FINAL_ROOT_COUNT=$(ls -1 | wc -l | tr -d ' ')
REDUCTION=$((INITIAL_ROOT_COUNT - FINAL_ROOT_COUNT))

echo "======================================" | tee -a "$LOG_FILE"
echo "📊 清理統計:" | tee -a "$LOG_FILE"
echo "   清理前項目數: $INITIAL_ROOT_COUNT" | tee -a "$LOG_FILE"
echo "   清理後項目數: $FINAL_ROOT_COUNT" | tee -a "$LOG_FILE"
echo "   減少項目數: $REDUCTION" | tee -a "$LOG_FILE"
echo "   歸檔檔案數: $ARCHIVED_COUNT" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"

# 生成清理報告
cat > "$REPORT_FILE" << EOF
# 深度清理報告

**執行時間**: $(date)
**清理類型**: 深度檔案整理和歸檔
**執行腳本**: deep_cleanup.sh

## 📊 清理統計

| 項目 | 數值 |
|------|------|
| 清理前根目錄項目數 | $INITIAL_ROOT_COUNT |
| 清理後根目錄項目數 | $FINAL_ROOT_COUNT |
| 減少項目數 | $REDUCTION |
| 歸檔檔案數 | $ARCHIVED_COUNT |

## 🗂️ 整理操作

### 文檔整理
- 移動 *.md 檔案到 docs/ 目錄
- 保留 README.md 在根目錄

### 測試檔案整理
- 移動 test_*.py 檔案到 tests/ 目錄
- 保持測試結構完整性

### 腳本整理
- 移動 analyze_*.py 檔案到 scripts/ 目錄
- 歸檔舊版本執行腳本

### 清理操作
- 刪除空檔案
- 清理臨時檔案和快取
- 歸檔過時腳本

## 📁 目錄結構

清理後的根目錄應包含：
- 核心配置檔案 (README.md, LICENSE, pyproject.toml)
- 主要執行腳本 (*.sh)
- Makefile
- 功能目錄 (scripts/, tests/, docs/, data/, config/)

## 🎯 達成效果

$(if [ $FINAL_ROOT_COUNT -le 15 ]; then echo "✅ 根目錄項目數已達到目標 (<15)"; else echo "⚠️ 根目錄項目數仍需進一步精簡 ($FINAL_ROOT_COUNT > 15)"; fi)

## 🔄 後續建議

- 定期執行結構驗證: \`./verify_structure_new.sh\`
- 保持根目錄簡潔，新檔案及時分類
- 每週執行快速清理: \`./quick_cleanup.sh\`

---
*清理報告生成於 $(date)*
EOF

echo "✅ 深度清理完成！" | tee -a "$LOG_FILE"
echo "📋 清理報告: $REPORT_FILE" | tee -a "$LOG_FILE"
echo "📝 詳細日誌: $LOG_FILE" | tee -a "$LOG_FILE"

# 顯示當前根目錄狀態
echo ""
echo "📁 當前根目錄內容 ($FINAL_ROOT_COUNT 項):"
ls -1 | head -20
if [ $FINAL_ROOT_COUNT -gt 20 ]; then
    echo "... (還有 $((FINAL_ROOT_COUNT - 20)) 項)"
fi