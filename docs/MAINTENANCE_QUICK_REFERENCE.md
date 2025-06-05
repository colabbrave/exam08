# 專案整理維護快速參考指南

## 🎯 整理原則摘要

### 核心理念
- **三層架構**：核心功能區 → 功能分類區 → 歷史備份區
- **根目錄極簡**：保持 ≤15 個項目
- **定期維護**：週檢查 + 月整理 + 季度評估

### 保留標準
✅ **保留**：正在使用、近期需要、核心功能  
📦 **歸檔**：測試完成、歷史版本、臨時檔案  
🗑️ **刪除**：完全空白、損壞檔案、明確無用  

---

## 🛠️ 維護腳本使用

### 日常維護
```bash
# 快速清理（每週）
./quick_cleanup.sh

# 結構檢查（每週）
./verify_structure.sh
```

### 深度維護
```bash
# 深度整理（當根目錄 >15 項目時）
./deep_cleanup.sh

# 月度維護（每月執行）
./monthly_maintenance.sh
```

### 腳本說明
| 腳本 | 用途 | 頻率 | 效果 |
|------|------|------|------|
| `quick_cleanup.sh` | 清理臨時檔案 | 每週 | 輕量級清理 |
| `verify_structure.sh` | 檢查專案結構 | 每週 | 生成檢查報告 |
| `deep_cleanup.sh` | 深度整理 | 需要時 | 全面整理歸檔 |
| `monthly_maintenance.sh` | 月度維護 | 每月 | 完整維護週期 |

---

## 📁 目錄整理標準

### 根目錄 (極簡原則)
**保留**：README.md, 執行腳本(*.sh), requirements.txt, 重要報告(≤3個)  
**禁止**：測試檔案、臨時檔案、歷史版本、詳細日誌

### 功能目錄
```
scripts/     → 主要腳本 (測試腳本→archive/)
config/      → 當前配置 (備份檔案→archive/)
output/      → 當前輸出 (優化檔案→archive/ 7天後)
results/     → 正式結果 (評估報告保留20個)
logs/        → 近期日誌 (30天以上→archive/)
archive/     → 統一備份區
```

### Archive 目錄結構
```
archive/
├── temp_files/          # 臨時檔案
├── old_versions/        # 歷史版本
├── historical_data/     # 歷史資料
├── test_files/          # 測試檔案
├── by_date/            # 按日期備份
└── monthly_maintenance/ # 月度維護記錄
```

---

## 🚨 警告信號與處理

### 根目錄過多項目 (>15)
```bash
# 立即執行深度整理
./deep_cleanup.sh
```

### 發現禁用命名檔案
- `tmp*`, `untitled*`, `new_*`, `copy_*`, `*副本*`
```bash
# 快速清理
./quick_cleanup.sh
```

### 超大檔案 (>100MB)
- 考慮外部存儲或壓縮
- 檢查是否為必要檔案

### 備份檔案積累
- config/*.backup → archive/old_versions/
- scripts/*.bak → archive/old_versions/

---

## 常見維護問題
- 根目錄項目過多：請優先執行 `deep_cleanup.sh`
- 發現禁用命名檔案：請手動更名或歸檔
- archive 子目錄缺失：可手動建立或執行 `deep_cleanup.sh`
- 檔案權限不足：`chmod +x *.sh`

## 報告與紀錄
- 結構檢查報告：`PROJECT_STRUCTURE_CHECK_*.md`
- 深度整理報告：`PROJECT_DEEP_CLEANUP_REPORT_*.md`
- 月度維護報告：`archive/monthly_maintenance/YYYYMM/monthly_report_YYYYMMDD.md`

## 重要原則摘要
- 根目錄項目建議 ≤ 15
- 禁用命名：tmp*、untitled*、new_*、copy_*
- scripts/、config/、output/、results/、logs/、archive/ 目錄需齊全
- 定期備份與歸檔，維護報告需留存

---
如遇異常，請參考 `PROJECT_ORGANIZATION_PRINCIPLES.md` 或聯絡專案維護人員。

## 📊 效果評估指標

### 結構健康度
- **優秀** ✅：根目錄 ≤10 項目，無警告
- **良好** 👍：根目錄 ≤15 項目，少量警告
- **需改進** ⚠️：根目錄 >15 項目，多個警告
- **需重整** ❌：根目錄 >20 項目，結構混亂

### 維護頻率建議
- **每週**：quick_cleanup.sh + verify_structure.sh
- **每月**：monthly_maintenance.sh
- **需要時**：deep_cleanup.sh (當根目錄 >15 項目)

---

## 🔄 標準維護流程

### 週度檢查流程
1. `./verify_structure.sh` - 檢查結構狀態
2. `./quick_cleanup.sh` - 清理臨時檔案
3. 檢查根目錄項目數量
4. 如果 >15 項目，執行深度整理

### 月度維護流程
1. `./monthly_maintenance.sh` - 執行完整維護
2. 檢查生成的維護報告
3. 處理報告中的改進建議
4. 驗證備份完整性

### 季度評估流程
1. 回顧過去3個月的維護報告
2. 評估專案成長趨勢
3. 調整整理策略和保留標準
4. 更新整理原則文檔

---

## 💡 最佳實踐提醒

### 檔案命名
- ✅ 使用描述性名稱：`semantic_analysis_report.md`
- ✅ 包含日期版本：`backup_20250605.tar.gz`
- ❌ 避免通用名稱：`new_file.py`, `tmp_data.json`

### 目錄管理
- 🎯 保持根目錄簡潔
- 📦 定期歸檔歷史檔案
- 🔍 使用結構檢查腳本監控狀態

### 備份策略
- 💾 月度完整備份
- 📁 分類歸檔到archive/
- 🔒 定期驗證備份完整性

---

*基於 PROJECT_ORGANIZATION_PRINCIPLES.md v1.0 | 更新日期：2025年6月5日*
