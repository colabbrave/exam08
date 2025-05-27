# 會議記錄優化與評估系統

## 專案概述

本專案旨在利用大型語言模型（LLM）來自動優化會議記錄，提高其結構化程度、完整性和可讀性。系統支援多種優化策略，並提供全面的評估框架來衡量優化效果。

## 主要功能

- **多策略優化**：支援多種會議記錄優化策略
- **多模型支援**：可與多種開源和商業語言模型整合
- **自動化評估**：提供多種評估指標來衡量優化效果
- **可擴展架構**：易於添加新的優化策略和評估指標

## 快速開始

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 基本用法

```bash
# 優化單個會議記錄
python scripts/optimize_meeting_minutes.py data/examples/meeting1.txt

# 評估優化效果
python scripts/test_optimization.py --test-dir data/test --output-dir results/evaluation
```

## 專案結構

```
.
├── data/                    # 數據目錄
│   ├── examples/            # 範例數據
│   ├── test/                # 測試數據
│   └── references/          # 參考記錄
├── results/                 # 結果輸出
│   ├── evaluation/          # 評估結果
│   └── optimized/           # 優化後的記錄
├── scripts/                 # 腳本文件
│   ├── optimize_meeting_minutes.py  # 優化腳本
│   └── test_optimization.py         # 測試腳本
├── .gitignore
├── README.md
├── requirements.txt
└── INSTALL.md
```

## 評估結果

### 最佳表現模型
1. **模型**: cwchang_llama3-taide-lx-8b-chat-alpha1_latest
   - 策略: 補充省略資訊
   - 加權分數: 0.4115
   - BERTScore F1: 0.6814

2. **模型**: jcai_llama3-taide-lx-8b-chat-alpha1_Q4_K_M
   - 策略: 專業術語標準化
   - 加權分數: 0.4060
   - BERTScore F1: 0.6632

### 策略表現排名
1. 補充省略資訊 (0.3861)
2. 明確標註發言者 (0.3833)
3. 結構化摘要 (0.3830)
4. 專業術語標準化 (0.3806)
5. 標準格式模板 (0.3806)

詳細評估報告請參考: [results/evaluation_reports/summary_report.md](results/evaluation_reports/summary_report.md)

## 貢獻指南

歡迎提交問題和拉取請求！請確保：

1. 遵循現有的代碼風格
2. 為新功能添加測試
3. 更新相關文檔

## 專案進度

### 完成情況

1. **基本架構建立** ✅ 已完成
   - 專案目錄結構
   - 基礎優化流程
   - 多模型支援

2. **評估系統實現** 🔄 部分完成
   - ✅ 基本評估框架
   - ✅ BERTScore 實現
   - ✅ ROUGE 實現
   - ❌ 多指標整合
   - ❌ 評估報告可視化

### 後續計劃

3. **提示工程優化** 🔜 下一階段
   - 提示詞模板重構
   - 動態範例載入
   - 思維鏈提示

4. **效能優化** ⏳ 未開始
   - 並行處理
   - 快取機制
   - 資源監控

5. **文檔與部署** ⏳ 未開始
   - 使用文檔
   - API 文檔
   - 部署指南

## 最近更新

### 2025-05-27
- 新增模型執行時間統計功能
- 新增策略執行時間統計功能
- 改進模型名稱處理邏輯
- 優化錯誤處理和重試機制
- 添加 `run_all_models.sh` 腳本用於批量運行多個模型

### 2025-05-26
- 實現模型響應時間追蹤
- 優化模型調用過程中的錯誤處理
- 改進重試機制，提高穩定性

### 2025-05-25
- 修復 `time` 模組導入問題
- 修正 `model_timings` 和 `strategy_timings` 變數作用域問題
- 更新評估結果和改進策略

## 授權

[在此添加授權信息]
