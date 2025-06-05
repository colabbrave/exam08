#!/bin/bash
# 專案結構驗證腳本 - 檢查專案是否符合整理原則
# 基於PROJECT_ORGANIZATION_PRINCIPLES.md v1.0

echo "🔍 開始專案結構驗證..."
echo "========================================"

# 初始化檢查結果
ISSUES_FOUND=0
WARNINGS_FOUND=0
SUGGESTIONS=()

# 檢查函數
check_root_directory() {
    echo "🏠 檢查根目錄..."
    
    # 計算根目錄項目數量
    root_items=$(ls -1 | wc -l)
    echo "   根目錄項目數量: $root_items"
    
    if [ $root_items -gt 15 ]; then
        echo "❌ 根目錄項目過多 ($root_items > 15)"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        SUGGESTIONS+=("執行深度整理腳本: ./deep_cleanup.sh")
    else
        echo "✅ 根目錄項目數量符合極簡原則"
    fi
    
    # 檢查禁用命名模式
    echo "   檢查禁用檔案命名..."
    forbidden_patterns=("tmp*" "untitled*" "new_*" "copy_*" "*副本*" "*_test_*")
    
    for pattern in "${forbidden_patterns[@]}"; do
        found_files=$(find . -maxdepth 1 -name "$pattern" -type f 2>/dev/null)
        if [ -n "$found_files" ]; then
            echo "⚠️  發現禁用命名檔案: $pattern"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
            echo "$found_files"
        fi
    done
    
    # 檢查空檔案
    empty_files=$(find . -maxdepth 1 -size 0 -type f 2>/dev/null)
    if [ -n "$empty_files" ]; then
        echo "⚠️  發現空檔案:"
        echo "$empty_files"
        WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        SUGGESTIONS+=("執行快速清理: ./quick_cleanup.sh")
    fi
}

check_directory_structure() {
    echo "📁 檢查目錄結構..."
    
    # 檢查建議的目錄結構
    recommended_dirs=("scripts" "config" "output" "results" "logs" "archive")
    
    for dir in "${recommended_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "✅ $dir/ 目錄存在"
        else
            echo "⚠️  建議創建 $dir/ 目錄"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
    done
}

# 執行所有檢查
check_root_directory
echo ""
check_directory_structure

# 生成檢查報告
echo "========================================"
echo "📊 結構驗證總結:"
echo "   問題數量: $ISSUES_FOUND"
echo "   警告數量: $WARNINGS_FOUND"

if [ $ISSUES_FOUND -eq 0 ] && [ $WARNINGS_FOUND -eq 0 ]; then
    echo "✅ 專案結構完全符合整理原則！"
    exit 0
elif [ $ISSUES_FOUND -eq 0 ]; then
    echo "⚠️  專案結構基本符合原則，但有 $WARNINGS_FOUND 個改進建議"
else
    echo "❌ 發現 $ISSUES_FOUND 個結構問題需要修正"
fi

# 顯示建議
if [ ${#SUGGESTIONS[@]} -gt 0 ]; then
    echo ""
    echo "🔧 改進建議:"
    for suggestion in "${SUGGESTIONS[@]}"; do
        echo "   • $suggestion"
    done
fi

echo ""
echo "🔄 建議定期執行此檢查 (建議頻率: 每週)"
