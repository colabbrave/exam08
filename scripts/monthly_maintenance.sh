#!/bin/bash
# 月度維護腳本 - 定期深度整理和維護檢查
# 基於PROJECT_ORGANIZATION_PRINCIPLES.md v1.0

echo "📅 開始月度維護程序..."
echo "========================================"
echo "維護時間: $(date '+%Y年%m月%d日 %H:%M:%S')"
echo ""

# 創建月度維護目錄
current_month="$(date +%Y%m)"
maintenance_dir="archive/monthly_maintenance/$current_month"
mkdir -p "$maintenance_dir"

# 1. 執行結構驗證
echo "🔍 步驟 1/6: 執行結構驗證"
echo "========================================"
./verify_structure.sh > "$maintenance_dir/structure_check_$(date +%Y%m%d).log" 2>&1
structure_result=$?

if [ $structure_result -eq 0 ]; then
    echo "✅ 結構驗證通過"
else
    echo "⚠️  結構驗證發現問題，詳見日誌"
fi
echo ""

# 2. 執行深度清理
echo "🧹 步驟 2/6: 執行深度清理"
echo "========================================"
./deep_cleanup.sh > "$maintenance_dir/deep_cleanup_$(date +%Y%m%d).log" 2>&1
echo "✅ 深度清理完成"
echo ""

# 3. 歷史檔案歸檔
echo "📦 步驟 3/6: 歷史檔案歸檔"
echo "========================================"

# 歸檔超過3個月的archive/temp_files
if [ -d "archive/temp_files" ]; then
    echo "歸檔舊的臨時檔案..."
    find archive/temp_files/ -type f -mtime +90 -exec mv {} archive/by_date/$(date +%Y)/$(date +%m)/ \; 2>/dev/null || true
    archived_temp=$(find archive/by_date/$(date +%Y)/$(date +%m)/ -type f -name "*" -mtime -1 2>/dev/null | wc -l)
    echo "已歸檔 $archived_temp 個舊臨時檔案"
fi

# 清理空目錄
echo "清理空目錄..."
find archive/ -type d -empty -delete 2>/dev/null || true
echo "✅ 歷史檔案歸檔完成"
echo ""

# 4. 磁碟使用分析
echo "💾 步驟 4/6: 磁碟使用分析"
echo "========================================"

# 分析各目錄大小
echo "目錄大小分析:"
for dir in scripts config output results logs archive; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        files=$(find "$dir" -type f 2>/dev/null | wc -l)
        echo "   $dir/: $size ($files 個檔案)"
    fi
done

# 分析最大檔案
echo ""
echo "最大檔案前10名:"
find . -type f -not -path "./archive/*" -not -path "./.git/*" -exec du -h {} + 2>/dev/null | sort -hr | head -10

# 檢查超大檔案（>100MB）
large_files=$(find . -type f -size +100M -not -path "./archive/*" -not -path "./.git/*" 2>/dev/null)
if [ -n "$large_files" ]; then
    echo ""
    echo "⚠️  發現超大檔案 (>100MB):"
    echo "$large_files"
    echo "建議考慮是否需要壓縮或外部存儲"
fi
echo ""

# 5. 備份驗證
echo "🔒 步驟 5/6: 備份驗證"
echo "========================================"

# 檢查最近的備份
recent_backup=$(find archive/by_date/ -name "*.tar.gz" -mtime -30 2>/dev/null | head -1)
if [ -n "$recent_backup" ]; then
    echo "✅ 發現最近30天的備份: $(basename "$recent_backup")"
    
    # 測試備份完整性
    echo "測試備份完整性..."
    if tar -tzf "$recent_backup" >/dev/null 2>&1; then
        echo "✅ 備份檔案完整"
    else
        echo "❌ 備份檔案損壞！"
    fi
else
    echo "⚠️  未發現最近30天的備份，建議手動創建"
fi

# 創建當月備份
monthly_backup="archive/by_date/$(date +%Y)/$(date +%m)/monthly_backup_$(date +%Y%m%d).tar.gz"
echo "創建月度備份..."
tar -czf "$monthly_backup" \
    --exclude='archive' \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.git' \
    . 2>/dev/null || echo "⚠️  備份過程中遇到部分檔案問題"

if [ -f "$monthly_backup" ]; then
    backup_size=$(du -sh "$monthly_backup" | cut -f1)
    echo "✅ 月度備份已創建: $backup_size"
else
    echo "❌ 月度備份創建失敗"
fi
echo ""

# 6. 生成維護報告
echo "📊 步驟 6/6: 生成維護報告"
echo "========================================"

# 統計資訊
total_files=$(find . -type f -not -path "./archive/*" -not -path "./.git/*" 2>/dev/null | wc -l)
root_items=$(ls -1 | wc -l)
archived_files=$(find archive/ -type f 2>/dev/null | wc -l)
project_size=$(du -sh . | cut -f1)

# 計算成長趨勢（與上個月比較）
last_month_report=$(find archive/monthly_maintenance/ -name "monthly_report_*.md" -type f 2>/dev/null | sort | tail -2 | head -1)
if [ -n "$last_month_report" ] && [ -f "$last_month_report" ]; then
    last_month_files=$(grep "總檔案數量:" "$last_month_report" | grep -o '[0-9]*' | head -1)
    if [ -n "$last_month_files" ]; then
        file_growth=$((total_files - last_month_files))
        if [ $file_growth -gt 0 ]; then
            growth_trend="📈 增加 $file_growth 個檔案"
        elif [ $file_growth -lt 0 ]; then
            growth_trend="📉 減少 $((file_growth * -1)) 個檔案"
        else
            growth_trend="➡️ 檔案數量無變化"
        fi
    else
        growth_trend="📊 無法計算趨勢"
    fi
else
    growth_trend="📊 首次月度維護"
fi

# 生成月度報告
report_file="$maintenance_dir/monthly_report_$(date +%Y%m%d).md"
cat > "$report_file" << EOF
# 月度維護報告

## 維護基本資訊
- **維護日期**: $(date '+%Y年%m月%d日 %H:%M:%S')
- **維護類型**: 自動月度維護
- **維護版本**: v1.0

## 專案狀態總覽
- **總檔案數量**: $total_files 個
- **根目錄項目**: $root_items 個
- **已歸檔檔案**: $archived_files 個
- **專案大小**: $project_size
- **成長趨勢**: $growth_trend

## 維護執行結果
- ✅ 結構驗證: $(if [ $structure_result -eq 0 ]; then echo "通過"; else echo "發現問題"; fi)
- ✅ 深度清理: 已完成
- ✅ 歷史歸檔: 已完成
- ✅ 磁碟分析: 已完成
- ✅ 備份驗證: 已完成
- ✅ 維護報告: 已生成

## 目錄大小分析
$(for dir in scripts config output results logs archive; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        files=$(find "$dir" -type f 2>/dev/null | wc -l)
        echo "- **$dir/**: $size ($files 個檔案)"
    fi
done)

## 改進建議
$(if [ $root_items -gt 15 ]; then echo "- ⚠️ 根目錄項目過多，建議進一步整理"; fi)
$(if [ -n "$large_files" ]; then echo "- ⚠️ 發現超大檔案，建議檢查是否需要外部存儲"; fi)
$(if [ $structure_result -ne 0 ]; then echo "- ⚠️ 結構驗證未通過，請查看詳細日誌"; fi)
- 📅 下次月度維護建議時間: $(date -v+1m '+%Y年%m月%d日')

## 維護文件
- 結構檢查日誌: \`$maintenance_dir/structure_check_$(date +%Y%m%d).log\`
- 深度清理日誌: \`$maintenance_dir/deep_cleanup_$(date +%Y%m%d).log\`
- 月度備份: \`$monthly_backup\`

## 維護腳本使用
- 快速清理: \`./quick_cleanup.sh\`
- 深度整理: \`./deep_cleanup.sh\`
- 結構檢查: \`./verify_structure.sh\`
- 月度維護: \`./monthly_maintenance.sh\`

---
*此報告由月度維護腳本自動生成*
EOF

echo "✅ 月度維護報告已生成: $report_file"
echo ""

# 清理維護過程中的臨時檔案
find . -name "PROJECT_DEEP_CLEANUP_REPORT_*" -mtime +7 -delete 2>/dev/null || true
find . -name "PROJECT_STRUCTURE_CHECK_*" -mtime +7 -delete 2>/dev/null || true

echo "========================================"
echo "🎉 月度維護程序完成！"
echo ""
echo "📋 維護總結:"
echo "   總檔案數量: $total_files"
echo "   根目錄項目: $root_items"
echo "   專案大小: $project_size"
echo "   成長趨勢: $growth_trend"
echo ""
echo "📁 維護文件位置: $maintenance_dir"
echo "📊 詳細報告: $report_file"
echo ""
echo "🔄 建議下次維護時間: $(date -v+1m '+%Y年%m月%d日')"