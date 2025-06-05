#!/bin/bash
# 深度整理腳本 - 根據PROJECT_ORGANIZATION_PRINCIPLES.md執行完整整理
# 基於專案整理原則 v1.0

echo "🔄 開始深度整理流程..."
echo "========================================"

# 創建完整的archive目錄結構
echo "📁 創建archive目錄結構..."
mkdir -p archive/{temp_files,old_versions,historical_data,deprecated_files,test_files}
mkdir -p archive/temp_files/{output_legacy,results_legacy,config_legacy,logs_legacy,scripts_legacy}
mkdir -p archive/by_date/$(date +%Y)/$(date +%m)

# 備份當前狀態
echo "💾 備份當前專案狀態..."
tar -czf "archive/by_date/$(date +%Y)/$(date +%m)/project_backup_$(date +%Y%m%d_%H%M).tar.gz" \
    --exclude='archive' \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.git' \
    . 2>/dev/null || echo "⚠️  備份過程中遇到部分檔案問題，但繼續執行..."

# 根目錄深度清理
echo "🏠 清理根目錄..."
echo "移動非核心檔案到archive..."

# 移動測試檔案
find . -maxdepth 1 -name "*test*" -not -name "*.md" -exec mv {} archive/test_files/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*tmp*" -exec mv {} archive/temp_files/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*copy*" -exec mv {} archive/temp_files/ \; 2>/dev/null || true
find . -maxdepth 1 -name "untitled*" -exec mv {} archive/temp_files/ \; 2>/dev/null || true
find . -maxdepth 1 -name "new_*" -exec mv {} archive/temp_files/ \; 2>/dev/null || true

# 移動歷史檔案（含日期的檔案）
find . -maxdepth 1 -name "*_20*" -exec mv {} archive/historical_data/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*-20*" -exec mv {} archive/historical_data/ \; 2>/dev/null || true

# scripts目錄整理
if [ -d "scripts" ]; then
    echo "📜 整理scripts目錄..."
    
    # 移動測試腳本
    find scripts/ -name "test_*.py" -exec mv {} archive/test_files/ \; 2>/dev/null || true
    find scripts/ -name "*_test.py" -exec mv {} archive/test_files/ \; 2>/dev/null || true
    find scripts/ -name "experimental_*.py" -exec mv {} archive/test_files/ \; 2>/dev/null || true
    
    # 移動備份檔案
    find scripts/ -name "*.bak" -exec mv {} archive/old_versions/ \; 2>/dev/null || true
    find scripts/ -name "*.backup" -exec mv {} archive/old_versions/ \; 2>/dev/null || true
    find scripts/ -name "*_old.py" -exec mv {} archive/old_versions/ \; 2>/dev/null || true
    
    # 移動重複檔案
    find scripts/ -name "*_copy*.py" -exec mv {} archive/temp_files/scripts_legacy/ \; 2>/dev/null || true
    find scripts/ -name "*副本*.py" -exec mv {} archive/temp_files/scripts_legacy/ \; 2>/dev/null || true
fi

# config目錄整理
if [ -d "config" ]; then
    echo "⚙️  整理config目錄..."
    
    # 移動備份配置檔案
    find config/ -name "*.backup" -exec mv {} archive/old_versions/ \; 2>/dev/null || true
    find config/ -name "*_backup.*" -exec mv {} archive/old_versions/ \; 2>/dev/null || true
    
    # 移動測試配置檔案
    find config/ -name "*test*" -exec mv {} archive/test_files/ \; 2>/dev/null || true
    find config/ -name "*demo*" -exec mv {} archive/test_files/ \; 2>/dev/null || true
fi

# output目錄整理
if [ -d "output" ]; then
    echo "📤 整理output目錄..."
    
    # 移動優化測試檔案（超過7天）
    find output/ -name "optimized_*" -mtime +7 -exec mv {} archive/temp_files/output_legacy/ \; 2>/dev/null || true
    
    # 移動臨時輸出檔案
    find output/ -name "*tmp*" -exec mv {} archive/temp_files/output_legacy/ \; 2>/dev/null || true
    find output/ -name "*temp*" -exec mv {} archive/temp_files/output_legacy/ \; 2>/dev/null || true
    
    # 移動歷史輸出檔案
    find output/ -name "*_20*" -mtime +30 -exec mv {} archive/historical_data/ \; 2>/dev/null || true
fi

# results目錄整理
if [ -d "results" ]; then
    echo "📊 整理results目錄..."
    
    # 移動臨時結果檔案
    find results/ -name "tmp*" -exec mv {} archive/temp_files/results_legacy/ \; 2>/dev/null || true
    
    # 移動超過20個的評估報告（保留最新20個）
    eval_files=$(find results/ -name "*評估*" -type f | wc -l)
    if [ $eval_files -gt 20 ]; then
        find results/ -name "*評估*" -type f -printf '%T@ %p\n' | sort -n | head -n $((eval_files - 20)) | cut -d' ' -f2- | xargs -I {} mv {} archive/temp_files/results_legacy/ 2>/dev/null || true
    fi
    
    # 移動測試結果檔案
    find results/ -name "*test*" -exec mv {} archive/test_files/ \; 2>/dev/null || true
fi

# logs目錄整理
if [ -d "logs" ]; then
    echo "📋 整理logs目錄..."
    
    # 移動30天以上的日誌
    find logs/ -name "*.log" -mtime +30 -exec mv {} archive/temp_files/logs_legacy/ \; 2>/dev/null || true
    
    # 移動調試日誌
    find logs/ -name "*debug*" -exec mv {} archive/temp_files/logs_legacy/ \; 2>/dev/null || true
    find logs/ -name "*test*" -exec mv {} archive/test_files/ \; 2>/dev/null || true
fi

# 清理空檔案和空目錄
echo "🗑️  清理空檔案和空目錄..."
find . -name "*.json" -size 0 -delete 2>/dev/null || true
find . -name "*.py" -size 0 -delete 2>/dev/null || true
find . -name "*.md" -size 0 -delete 2>/dev/null || true
find . -name "*.txt" -size 0 -delete 2>/dev/null || true

# 清理空目錄（除了archive）
find . -type d -empty -not -path "./archive*" -delete 2>/dev/null || true

# 統計整理效果
echo "========================================"
echo "📊 深度整理完成統計："

# 計算各archive子目錄的檔案數量
temp_files=$(find archive/temp_files/ -type f 2>/dev/null | wc -l)
old_versions=$(find archive/old_versions/ -type f 2>/dev/null | wc -l)
test_files=$(find archive/test_files/ -type f 2>/dev/null | wc -l)
historical_data=$(find archive/historical_data/ -type f 2>/dev/null | wc -l)

echo "   臨時檔案: $temp_files 個"
echo "   歷史版本: $old_versions 個"
echo "   測試檔案: $test_files 個"
echo "   歷史資料: $historical_data 個"

# 檢查根目錄檔案數量
root_items=$(ls -1 | wc -l)
echo "   根目錄項目: $root_items 個"

if [ $root_items -le 15 ]; then
    echo "✅ 根目錄已符合極簡原則（≤15個項目）"
else
    echo "⚠️  根目錄仍有 $root_items 個項目，建議手動檢查"
fi

# 生成整理報告
report_file="PROJECT_DEEP_CLEANUP_REPORT_$(date +%Y%m%d_%H%M).md"
cat > "$report_file" << EOF
# 深度整理報告

## 整理時間
$(date '+%Y年%m月%d日 %H:%M:%S')

## 整理統計
- 臨時檔案: $temp_files 個
- 歷史版本: $old_versions 個  
- 測試檔案: $test_files 個
- 歷史資料: $historical_data 個
- 根目錄項目: $root_items 個

## 整理效果
$(if [ $root_items -le 15 ]; then echo "✅ 根目錄符合極簡原則"; else echo "⚠️ 根目錄需要進一步檢查"; fi)

## 備份位置
- 完整備份: archive/by_date/$(date +%Y)/$(date +%m)/project_backup_$(date +%Y%m%d_%H%M).tar.gz
- 分類備份: archive/各子目錄

## 後續建議
1. 檢查根目錄剩餘檔案是否都是必要檔案
2. 驗證功能目錄結構是否合理
3. 定期執行 verify_structure.sh 檢查結構
EOF

echo "📋 整理報告已生成: $report_file"
echo "✨ 深度整理完成！"
