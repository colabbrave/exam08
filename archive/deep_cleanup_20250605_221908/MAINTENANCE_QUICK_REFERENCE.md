# 專案維護快速參考指南

> 🎯 **目標**: 保持專案整潔、高效、可維護的狀態

## 🚀 快速操作

### 日常清理 (2-3分鐘)

```bash
./quick_cleanup.sh
```

- 清理臨時檔案
- 移除空檔案
- 整理快取

### 結構檢查 (1分鐘)

```bash
./verify_structure_new.sh
```

- 檢查目錄結構
- 驗證檔案組織
- 識別問題

### 深度整理 (5-10分鐘)

```bash
./deep_cleanup.sh
```

- 歸檔舊檔案
- 分類整理
- 生成報告

### 月度維護 (15-20分鐘)

```bash
./monthly_maintenance.sh
```

- 完整結構檢查
- 歷史檔案歸檔
- 磁碟分析
- 維護報告

## 📋 維護檢查清單

### 每週檢查 ✅

- [ ] 執行 `./quick_cleanup.sh`
- [ ] 執行 `./verify_structure_new.sh`
- [ ] 檢查根目錄項目數 (目標: <15)
- [ ] 清理不需要的測試檔案

### 每月檢查 ✅

- [ ] 執行 `./monthly_maintenance.sh`
- [ ] 檢查專案總大小
- [ ] 備份重要檔案
- [ ] 更新文檔

### 季度檢查 ✅

- [ ] 檢討整理原則
- [ ] 優化自動化腳本
- [ ] 清理過時的依賴
- [ ] 更新配置檔案

## 🎯 目標指標

| 指標 | 目標值 | 檢查方式 |
|------|--------|----------|
| 根目錄項目數 | <15 | `ls -1 \| wc -l` |
| 空檔案數量 | 0 | `find . -empty -type f` |
| 專案總大小 | <500MB | `du -sh .` |
| 備份完整性 | 100% | 檢查 archive/ 目錄 |

## 🗂️ 檔案分類規則

### 保留在根目錄

- `README.md` - 專案說明
- `LICENSE` - 授權檔案
- `pyproject.toml` - Python 專案配置
- `Makefile` - 建置腳本
- 主要執行腳本 (*.sh)

### 移動到 docs/

- 所有 *.md 文檔檔案
- 報告檔案 (*REPORT*.md)
- 指南檔案 (*GUIDE*.md)

### 移動到 tests/

- 所有測試檔案 (test_*.py)
- 測試數據檔案

### 移動到 scripts/

- 分析腳本 (analyze_*.py)
- 工具腳本

### 歸檔到 archive/

- 超過30天的報告檔案
- 舊版本檔案
- 臨時測試檔案

## 🔧 常用命令

### 檢查專案狀態

```bash
# 根目錄項目數
ls -1 | wc -l

# 專案總大小
du -sh .

# 找出最大的目錄
du -sh */ | sort -hr | head -5

# 找出空檔案
find . -empty -type f

# 找出大檔案 (>10MB)
find . -size +10M -type f
```

### 手動整理命令

```bash
# 移動所有測試檔案到 tests/
mv test_*.py tests/

# 移動所有文檔到 docs/
mv *.md docs/

# 清理空檔案
find . -empty -type f -delete

# 清理臨時檔案
find . -name "*.tmp" -delete
find . -name "*.cache" -delete
```

## 🚨 警告信號

### 立即處理

- ❌ 根目錄項目數 >25
- ❌ 專案大小 >1GB
- ❌ 發現重複檔案
- ❌ 備份目錄缺失

### 需要關注

- ⚠️ 根目錄項目數 >15
- ⚠️ 空檔案 >5個
- ⚠️ 測試檔案在根目錄
- ⚠️ 報告檔案堆積

## 📞 故障排除

### 腳本執行失敗

```bash
# 檢查權限
ls -la *.sh

# 設置執行權限
chmod +x *.sh

# 檢查語法
bash -n script_name.sh
```

### 檔案無法移動

```bash
# 檢查檔案是否存在
ls -la filename

# 檢查目標目錄
ls -ld target_directory/

# 強制移動
mv filename target_directory/ 2>/dev/null || echo "移動失敗"
```

## 📈 效果追蹤

### 維護前後對比

- 記錄維護前的項目數、檔案大小
- 執行維護操作
- 記錄維護後的改善情況
- 更新維護日誌

### 維護日誌範例

```
2025-06-05: 月度維護
- 根目錄項目: 57→25 (-32)
- 歸檔檔案: 301個
- 專案大小: 1.2GB→800MB
- 耗時: 15分鐘
```

---

**💡 提示**: 定期維護是保持專案健康的關鍵。建議設置日曆提醒，每週執行快速清理，每月執行深度維護。

**📖 相關文檔**:

- [PROJECT_ORGANIZATION_PRINCIPLES.md](PROJECT_ORGANIZATION_PRINCIPLES.md) - 詳細組織原則
- [SEMANTIC_SEGMENTATION_GUIDE.md](SEMANTIC_SEGMENTATION_GUIDE.md) - 語意分段指南

*最後更新: 2025年6月5日*
