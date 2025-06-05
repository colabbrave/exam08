#!/bin/bash
# 快速清理腳本 - 清理明顯的臨時檔案
# 基於專案整理原則 v1.0

echo "🧹 開始快速清理..."

# 創建必要的archive目錄結構
mkdir -p archive/temp_files/{output_legacy,results_legacy,config_legacy,logs_legacy}

# 清理根目錄臨時檔案
echo "清理根目錄臨時檔案..."
find . -maxdepth 1 -name "*tmp*" -exec mv {} archive/temp_files/ \; 2>/dev/null || true
find . -maxdepth 1 -name "optimization_result_*" -exec mv {} archive/temp_files/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_test_*" -exec mv {} archive/temp_files/ \; 2>/dev/null || true

# 清理空檔案
echo "清理空檔案..."
find . -name "*.json" -size 0 -delete 2>/dev/null || true
find . -name "*.md" -size 0 -delete 2>/dev/null || true
find . -name "*.py" -size 0 -delete 2>/dev/null || true

# 清理output目錄中的臨時檔案
echo "清理output目錄..."
find output/ -name "optimized_*" -mtime +7 -exec mv {} archive/temp_files/output_legacy/ \; 2>/dev/null || true
find output/ -name "*tmp*" -exec mv {} archive/temp_files/output_legacy/ \; 2>/dev/null || true

# 清理重複的備份檔案
echo "清理重複備份檔案..."
find config/ -name "*.backup" -mtime +30 -exec mv {} archive/temp_files/config_legacy/ \; 2>/dev/null || true

# 統計清理效果
moved_files=$(find archive/temp_files/ -type f -newer archive/temp_files 2>/dev/null | wc -l)
echo "✅ 快速清理完成"
echo "📊 移動了 $moved_files 個檔案到archive"

# 檢查根目錄檔案數量
root_files=$(ls -1 | wc -l)
echo "📁 根目錄現有 $root_files 個項目"
if [ $root_files -gt 15 ]; then
    echo "⚠️  建議進行深度整理（根目錄項目過多）"
fi