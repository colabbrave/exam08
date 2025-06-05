# 專案檔案整理與維護原則

## 📋 整理原則總覽

基於今天的完整整理經驗（專案檔案整理 + 同類型檔案整併），建立這套可重複執行的整理原則。

---

## 🎯 核心整理理念

### 1. 三層架構原則
- **第一層：核心功能區** - 根目錄保持簡潔，只保留核心執行檔案
- **第二層：功能分類區** - 依功能分類的主要目錄（scripts/, config/, data/等）
- **第三層：歷史備份區** - archive/目錄統一管理所有歷史和臨時檔案

### 2. 保留與歸檔原則
- **保留標準**：正在使用、近期需要、核心功能
- **歸檔標準**：測試完成、歷史版本、臨時檔案、重複內容
- **刪除標準**：完全空白、損壞檔案、明確無用的檔案

---

## 📁 目錄整理規範

### 根目錄 (/) - 極簡原則
**保留檔案類型**：
- 📄 **說明文件**：README.md, INSTALL.md, QUICK_START.md
- 🔧 **執行腳本**：run_*.sh, setup.sh, *.sh（可執行）
- ⚙️ **配置檔案**：requirements.txt, Dockerfile
- 📊 **重要報告**：當前分析報告（最多3個）

**禁止保留**：
- 測試檔案、臨時檔案
- 歷史版本檔案
- 詳細日誌檔案
- 大量數據檔案

### 功能目錄整理標準

#### scripts/ - 程式碼目錄
```
保留：
- 主要功能腳本（*.py）
- 當前使用的工具腳本
- 核心執行檔案

歸檔：
- 測試腳本（test_*.py）
- 實驗性腳本（experimental_*.py）
- 備份腳本（*.py.bak）
```

#### config/ - 配置目錄
```
保留：
- 主要配置檔案（*.json, *.ini）
- 系統配置檔案
- 策略配置檔案（當前版本）

歸檔：
- 備份配置檔案（*.backup）
- 歷史配置版本
- 測試配置檔案
```

#### output/ - 輸出目錄
```
保留：
- 當前執行結果
- 功能性子目錄結構

歸檔：
- 歷史執行結果
- 優化測試檔案（optimized_*.*)
- 臨時輸出檔案
```

#### results/ - 結果目錄
```
保留：
- 正式會議記錄（第*次會議）
- 最新評估報告（最近20個）
- 核心分析結果

歸檔：
- 臨時結果檔案（tmp*）
- 老舊評估報告（超過20個）
- 測試結果檔案
```

#### logs/ - 日誌目錄
```
保留：
- 最近30天的日誌
- 重要執行記錄

歸檔：
- 30天以上的日誌
- 調試日誌（*debug*.log）
- 測試日誌
```

---

## 🏷️ 檔案命名規範

### 標準命名格式

#### 1. 日期時間格式
```
執行日誌：optimization_YYYYMMDD_HHMMSS.log
報告檔案：report_YYYYMMDD_主題.md
分析結果：analysis_YYYYMMDD_內容.json
```

#### 2. 版本控制格式
```
配置檔案：config_name.json / config_name.json.backup
策略檔案：strategies_v1.json / strategies_v2.json
優化結果：optimization_v1.md / optimization_v2.md
```

#### 3. 內容分類格式
```
會議記錄：第XXX次{會議類型}YYYY年MM月DD日逐字稿
分析報告：{日期描述}_{內容描述}_分析報告.md
測試檔案：test_{功能名稱}_{日期}.py
```

### 禁用命名模式
- ❌ `tmp*` - 長期保存的檔案不應使用tmp前綴
- ❌ `untitled*` - 應給予明確的檔案名稱
- ❌ `new_*` - 應使用版本號或日期
- ❌ `copy_*` - 應使用backup或v2等明確標示

---

## 🔄 定期維護計劃

### 每週維護（建議周日進行）
```bash
# 1. 清理臨時檔案
find . -name "tmp*" -type f -mtime +7 -exec mv {} archive/temp_files/ \;

# 2. 整理output目錄
cd output && ls -t *.* | tail -n +20 | xargs -I {} mv {} ../archive/temp_files/output_legacy/

# 3. 清理老舊日誌
cd logs && ls -t *.log | tail -n +30 | xargs -I {} mv {} ../archive/temp_files/logs_legacy/
```

### 每月維護（建議月初進行）
```bash
# 1. 壓縮archive歷史檔案
cd archive && tar -czf monthly_backup_$(date +%Y%m).tar.gz temp_files/

# 2. 清理超過6個月的備份
find archive/ -name "monthly_backup_*.tar.gz" -mtime +180 -delete

# 3. 生成維護報告
python scripts/generate_maintenance_report.py
```

### 季度維護（建議季末進行）
- 全面檢查目錄結構合規性
- 更新整理原則（如有需要）
- 進行完整的備份和清理
- 檢查檔案命名規範遵循情況

---

## 🤖 自動化腳本

### 快速清理腳本 (quick_cleanup.sh)
```bash
#!/bin/bash
# 快速清理腳本 - 清理明顯的臨時檔案

echo "🧹 開始快速清理..."

# 清理根目錄臨時檔案
mv ./*tmp* archive/temp_files/ 2>/dev/null || true
mv ./optimization_result_* archive/temp_files/ 2>/dev/null || true

# 清理空檔案
find . -name "*.json" -size 0 -exec rm {} \;
find . -name "*.md" -size 0 -exec rm {} \;

# 清理output臨時檔案
find output/ -name "optimized_*" -mtime +7 -exec mv {} archive/temp_files/output_legacy/ \;

echo "✅ 快速清理完成"
```

### 深度整理腳本 (deep_cleanup.sh)
```bash
#!/bin/bash
# 深度整理腳本 - 按整理原則進行完整整理

echo "🔍 開始深度整理..."

# 創建archive子目錄結構
mkdir -p archive/temp_files/{output_legacy,results_legacy,config_legacy,logs_legacy}

# 整理config目錄
cd config
ls *.backup 2>/dev/null | xargs -I {} mv {} ../archive/temp_files/config_legacy/
ls *_old* 2>/dev/null | xargs -I {} mv {} ../archive/temp_files/config_legacy/

# 整理results目錄
cd ../results
ls -t evaluation_reports/*.json | tail -n +21 | xargs -I {} mv {} ../archive/temp_files/results_legacy/

# 整理logs目錄
cd ../logs
ls -t *.log | tail -n +31 | xargs -I {} mv {} ../archive/temp_files/logs_legacy/

echo "✅ 深度整理完成"
```

### 維護檢查腳本 (verify_structure.sh)
```bash
#!/bin/bash
# 結構驗證腳本 - 檢查是否符合整理原則

echo "🔍 檢查專案結構合規性..."

# 檢查根目錄檔案數量
root_files=$(ls -1 | grep -v "^[a-z]" | wc -l)
if [ $root_files -gt 15 ]; then
    echo "⚠️  根目錄檔案過多：$root_files 個（建議<15個）"
fi

# 檢查是否有臨時檔案
temp_files=$(find . -maxdepth 1 -name "*tmp*" -o -name "*temp*" | wc -l)
if [ $temp_files -gt 0 ]; then
    echo "⚠️  發現 $temp_files 個臨時檔案需要清理"
fi

# 檢查archive目錄
if [ ! -d "archive" ]; then
    echo "❌ 缺少archive備份目錄"
else
    echo "✅ archive目錄存在"
fi

echo "🏁 結構檢查完成"
```

---

## 📊 效果評估標準

### 清理效果指標
```
根目錄簡潔度 = (根目錄檔案數 < 15) ? "優秀" : "需改善"
分類完整度 = (archive備份檔案數 / 總移動檔案數) × 100%
命名規範度 = (符合命名規範檔案數 / 總檔案數) × 100%
```

### 維護頻率評估
- **周維護執行率** > 80% = 良好
- **月維護執行率** > 90% = 優秀
- **季維護執行率** = 100% = 必須

---

## 🎯 整理檢查清單

### 整理前檢查
- [ ] 確認archive目錄結構存在
- [ ] 備份重要配置檔案
- [ ] 檢查當前執行狀態（避免中斷正在執行的任務）
- [ ] 確認磁碟空間充足

### 整理過程檢查
- [ ] 按分類移動檔案，不直接刪除
- [ ] 保持功能檔案完整性
- [ ] 記錄移動的檔案清單
- [ ] 驗證主要功能可正常執行

### 整理後檢查
- [ ] 執行結構驗證腳本
- [ ] 測試核心功能是否正常
- [ ] 生成整理報告
- [ ] 更新README.md中的目錄結構說明

---

## 📝 整理報告範本

每次整理後應生成報告，範本如下：

```markdown
# 專案整理報告 - YYYY-MM-DD

## 整理類型
- [ ] 週整理  - [ ] 月整理  - [ ] 季整理  - [x] 特殊整理

## 整理範圍
- [ ] 根目錄  - [ ] scripts/  - [ ] config/  - [ ] output/  - [ ] results/  - [ ] logs/

## 統計數據
- 移動檔案數：XX 個
- 刪除檔案數：XX 個
- 壓縮檔案數：XX 個
- 節省空間：XX MB

## 主要改善
- 描述主要的整理成果

## 發現問題
- 記錄發現的問題和改善建議

## 下次重點
- 下次整理的重點項目
```

---

## 🚀 快速執行指令

### 日常快速清理
```bash
./quick_cleanup.sh && ./verify_structure.sh
```

### 週度標準整理
```bash
./deep_cleanup.sh && python scripts/generate_maintenance_report.py
```

### 月度完整整理
```bash
./monthly_maintenance.sh && tar -czf archive/monthly_backup_$(date +%Y%m).tar.gz archive/temp_files/
```

---

**整理原則建立時間**：2025年6月5日  
**基於經驗**：203段異常修正 + 專案檔案整理 + 同類型檔案整併  
**適用範圍**：會議記錄優化系統及類似專案  
**更新週期**：季度檢視，年度更新