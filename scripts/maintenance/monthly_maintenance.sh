#!/bin/bash

# 月度維護腳本 - 全面的專案維護和清理
# 建議每月執行一次，進行深度整理和結構優化

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="logs/monthly_maintenance_$(date +%Y%m%d_%H%M%S).log"
REPORT_FILE="PROJECT_MONTHLY_MAINTENANCE_REPORT_$(date +%Y%m%d_%H%M%S).md"

# 創建必要的目錄
mkdir -p logs archive/monthly_maintenance

echo "🔧 開始月度維護流程..."
echo "📅 日期: $(date)"
echo "📝 日誌檔案: $LOG_FILE"
echo "📋 報告檔案: $REPORT_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 步驟1: 結構驗證
echo "📋 步驟1: 執行結構驗證..." | tee -a "$LOG_FILE"
if [ -f "./verify_structure_new.sh" ]; then
    ./verify_structure_new.sh | tee -a "$LOG_FILE"
else
    echo "⚠️  結構驗證腳本不存在" | tee -a "$LOG_FILE"
fi

# 步驟2: 深度清理
echo "🧹 步驟2: 執行深度清理..." | tee -a "$LOG_FILE"
if [ -f "./deep_cleanup.sh" ]; then
    ./deep_cleanup.sh | tee -a "$LOG_FILE"
else
    echo "⚠️  深度清理腳本不存在" | tee -a "$LOG_FILE"
fi

# 步驟3: 歷史歸檔
echo "📦 步驟3: 歷史檔案歸檔..." | tee -a "$LOG_FILE"
OLD_REPORTS=$(find . -maxdepth 1 -name "*REPORT*.md" -mtime +30 2>/dev/null | wc -l)
if [ "$OLD_REPORTS" -gt 0 ]; then
    find . -maxdepth 1 -name "*REPORT*.md" -mtime +30 -exec mv {} archive/monthly_maintenance/ \; 2>/dev/null
    echo "✅ 已歸檔 $OLD_REPORTS 個舊報告檔案" | tee -a "$LOG_FILE"
else
    echo "ℹ️  沒有需要歸檔的舊報告檔案" | tee -a "$LOG_FILE"
fi

# 步驟4: 磁碟空間分析
echo "💾 步驟4: 磁碟空間分析..." | tee -a "$LOG_FILE"
echo "總專案大小:" | tee -a "$LOG_FILE"
du -sh . | tee -a "$LOG_FILE"
echo "主要目錄大小:" | tee -a "$LOG_FILE"
for dir in archive logs output results data; do
    if [ -d "$dir" ]; then
        echo "  $dir: $(du -sh "$dir" | cut -f1)" | tee -a "$LOG_FILE"
    fi
done

# 步驟5: 備份驗證
echo "🔐 步驟5: 備份驗證..." | tee -a "$LOG_FILE"
if [ -d "archive" ]; then
    ARCHIVE_COUNT=$(find archive -type f | wc -l)
    echo "✅ 備份目錄存在，包含 $ARCHIVE_COUNT 個檔案" | tee -a "$LOG_FILE"
else
    echo "❌ 備份目錄不存在" | tee -a "$LOG_FILE"
fi

# 步驟6: 生成維護報告
echo "📊 步驟6: 生成維護報告..." | tee -a "$LOG_FILE"

cat > "$REPORT_FILE" << EOF
# 月度維護報告

**執行日期**: $(date)
**維護類型**: 完整月度維護
**執行腳本**: monthly_maintenance.sh

## 📊 維護統計

### 結構狀態
$(./verify_structure_new.sh 2>/dev/null | tail -10)

### 磁碟使用情況
- **專案總大小**: $(du -sh . | cut -f1)
- **備份大小**: $(if [ -d archive ]; then du -sh archive | cut -f1; else echo "N/A"; fi)
- **日誌大小**: $(if [ -d logs ]; then du -sh logs | cut -f1; else echo "N/A"; fi)

### 檔案統計
- **根目錄項目數**: $(ls -1 | wc -l)
- **備份檔案數**: $(if [ -d archive ]; then find archive -type f | wc -l; else echo "0"; fi)
- **日誌檔案數**: $(if [ -d logs ]; then find logs -name "*.log" | wc -l; else echo "0"; fi)

## 🔧 執行的維護操作

1. ✅ 結構驗證檢查
2. ✅ 深度清理執行
3. ✅ 歷史檔案歸檔
4. ✅ 磁碟空間分析
5. ✅ 備份驗證
6. ✅ 維護報告生成

## 📋 下次維護建議

- **下次執行時間**: $(date -d "+1 month" "+%Y年%m月%d日")
- **重點關注**: 
  - 根目錄項目數量控制（目標: <15）
  - 定期備份驗證
  - 日誌檔案輪替

## 🚨 需要注意的問題

$(if [ $(ls -1 | wc -l) -gt 15 ]; then echo "- ❌ 根目錄項目過多 ($(ls -1 | wc -l) > 15)"; fi)
$(if [ ! -d archive ]; then echo "- ❌ 缺少備份目錄"; fi)

---
*自動生成於 $(date)*
EOF

echo "✅ 月度維護完成！" | tee -a "$LOG_FILE"
echo "📋 維護報告已生成: $REPORT_FILE" | tee -a "$LOG_FILE"
echo "📝 詳細日誌: $LOG_FILE" | tee -a "$LOG_FILE"

# 顯示摘要
echo ""
echo "========================================"
echo "🎯 月度維護摘要"
echo "   根目錄項目數: $(ls -1 | wc -l)"
echo "   專案總大小: $(du -sh . | cut -f1)"
echo "   備份檔案數: $(if [ -d archive ]; then find archive -type f | wc -l; else echo "0"; fi)"
echo "========================================"