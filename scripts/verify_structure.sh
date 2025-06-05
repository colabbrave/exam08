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
            
            # 檢查各目錄的內容
            case $dir in
                "scripts")
                    check_scripts_directory
                    ;;
                "config")
                    check_config_directory
                    ;;
                "output")
                    check_output_directory
                    ;;
                "results")
                    check_results_directory
                    ;;
                "logs")
                    check_logs_directory
                    ;;
                "archive")
                    check_archive_structure
                    ;;
            esac
        else
            echo "⚠️  建議創建 $dir/ 目錄"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
    done
}

check_scripts_directory() {
    if [ -d "scripts" ]; then
        # 檢查測試檔案
        test_files=$(find scripts/ -name "*test*.py" -o -name "experimental_*.py" 2>/dev/null)
        if [ -n "$test_files" ]; then
            echo "   ⚠️  scripts/中發現測試檔案，建議移至archive/"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 檢查備份檔案
        backup_files=$(find scripts/ -name "*.bak" -o -name "*.backup" -o -name "*_old.*" 2>/dev/null)
        if [ -n "$backup_files" ]; then
            echo "   ⚠️  scripts/中發現備份檔案，建議移至archive/"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 統計主要腳本數量
        main_scripts=$(find scripts/ -name "*.py" -not -name "*test*" -not -name "experimental_*" 2>/dev/null | wc -l)
        echo "   📊 主要腳本數量: $main_scripts"
    fi
}

check_config_directory() {
    if [ -d "config" ]; then
        # 檢查備份配置檔案
        backup_configs=$(find config/ -name "*.backup" -o -name "*_backup.*" 2>/dev/null)
        if [ -n "$backup_configs" ]; then
            echo "   ⚠️  config/中發現備份檔案，建議移至archive/"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 檢查測試配置檔案
        test_configs=$(find config/ -name "*test*" -o -name "*demo*" 2>/dev/null)
        if [ -n "$test_configs" ]; then
            echo "   ⚠️  config/中發現測試檔案，建議移至archive/"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 統計配置檔案數量
        config_files=$(find config/ -type f 2>/dev/null | wc -l)
        echo "   📊 配置檔案數量: $config_files"
    fi
}

check_output_directory() {
    if [ -d "output" ]; then
        # 檢查優化測試檔案
        optimized_files=$(find output/ -name "optimized_*" -mtime +7 2>/dev/null)
        if [ -n "$optimized_files" ]; then
            echo "   ⚠️  output/中發現超過7天的優化檔案，建議清理"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 檢查臨時檔案
        temp_files=$(find output/ -name "*tmp*" -o -name "*temp*" 2>/dev/null)
        if [ -n "$temp_files" ]; then
            echo "   ⚠️  output/中發現臨時檔案，建議清理"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 統計輸出檔案數量
        output_files=$(find output/ -type f 2>/dev/null | wc -l)
        echo "   📊 輸出檔案數量: $output_files"
    fi
}

check_results_directory() {
    if [ -d "results" ]; then
        # 檢查臨時結果檔案
        temp_results=$(find results/ -name "tmp*" 2>/dev/null)
        if [ -n "$temp_results" ]; then
            echo "   ⚠️  results/中發現臨時檔案，建議清理"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 檢查評估報告數量
        eval_reports=$(find results/ -name "*評估*" -type f 2>/dev/null | wc -l)
        echo "   📊 評估報告數量: $eval_reports"
        if [ $eval_reports -gt 20 ]; then
            echo "   ⚠️  評估報告超過20個，建議歸檔舊報告"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 檢查測試結果檔案
        test_results=$(find results/ -name "*test*" 2>/dev/null)
        if [ -n "$test_results" ]; then
            echo "   ⚠️  results/中發現測試檔案，建議移至archive/"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
    fi
}

check_logs_directory() {
    if [ -d "logs" ]; then
        # 檢查30天以上的日誌
        old_logs=$(find logs/ -name "*.log" -mtime +30 2>/dev/null)
        if [ -n "$old_logs" ]; then
            echo "   ⚠️  logs/中發現30天以上的日誌，建議歸檔"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 檢查調試日誌
        debug_logs=$(find logs/ -name "*debug*" 2>/dev/null)
        if [ -n "$debug_logs" ]; then
            echo "   ⚠️  logs/中發現調試日誌，建議歸檔"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
        
        # 統計日誌檔案數量
        log_files=$(find logs/ -name "*.log" 2>/dev/null | wc -l)
        echo "   📊 日誌檔案數量: $log_files"
    fi
}

check_archive_structure() {
    if [ -d "archive" ]; then
        echo "   ✅ archive/目錄存在"
        
        # 檢查archive子目錄結構
        archive_subdirs=("temp_files" "old_versions" "historical_data" "test_files" "by_date")
        
        for subdir in "${archive_subdirs[@]}"; do
            if [ -d "archive/$subdir" ]; then
                echo "   ✅ archive/$subdir/ 存在"
            else
                echo "   ⚠️  建議創建 archive/$subdir/ 目錄"
                WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
            fi
        done
        
        # 統計archive內容
        archived_files=$(find archive/ -type f 2>/dev/null | wc -l)
        echo "   📊 已歸檔檔案數量: $archived_files"
    else
        echo "   ❌ 缺少archive/目錄"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        SUGGESTIONS+=("創建archive目錄結構: mkdir -p archive/{temp_files,old_versions,historical_data,test_files,by_date}")
    fi
}

check_file_naming_conventions() {
    echo "📝 檢查檔案命名規範..."
    
    # 檢查重要文件是否存在
    important_files=("README.md" "PROJECT_ORGANIZATION_PRINCIPLES.md")
    
    for file in "${important_files[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ $file 存在"
        else
            echo "   ⚠️  建議創建 $file"
            WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
        fi
    done
    
    # 檢查腳本執行權限
    echo "   檢查腳本執行權限..."
    for script in *.sh; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                echo "   ✅ $script 有執行權限"
            else
                echo "   ⚠️  $script 缺少執行權限"
                WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
                SUGGESTIONS+=("設置執行權限: chmod +x $script")
            fi
        fi
    done
}

# 執行所有檢查
check_root_directory
echo ""
check_directory_structure  
echo ""
check_file_naming_conventions

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

# 生成詳細報告
report_file="PROJECT_STRUCTURE_CHECK_$(date +%Y%m%d_%H%M).md"
cat > "$report_file" << EOF
# 專案結構檢查報告

## 檢查時間
$(date '+%Y年%m月%d日 %H:%M:%S')

## 檢查結果總覽
- 問題數量: $ISSUES_FOUND
- 警告數量: $WARNINGS_FOUND
- 整體狀態: $(if [ $ISSUES_FOUND -eq 0 ] && [ $WARNINGS_FOUND -eq 0 ]; then echo "✅ 完全符合"; elif [ $ISSUES_FOUND -eq 0 ]; then echo "⚠️ 基本符合"; else echo "❌ 需要改進"; fi)

## 改進建議
$(if [ ${#SUGGESTIONS[@]} -gt 0 ]; then 
    for suggestion in "${SUGGESTIONS[@]}"; do
        echo "- $suggestion"
    done
else
    echo "無特別建議"
fi)

## 下次檢查建議
- 建議檢查頻率: 每週一次
- 下次檢查時間: $(date -v+7d '+%Y年%m月%d日')

## 維護腳本
- 快速清理: \`./quick_cleanup.sh\`
- 深度整理: \`./deep_cleanup.sh\`
- 結構檢查: \`./verify_structure.sh\`
EOF

echo ""
echo "📋 詳細報告已生成: $report_file"
echo "🔄 建議定期執行此檢查 (建議頻率: 每週)"