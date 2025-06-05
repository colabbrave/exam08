# 會議記錄優化系統 - 快速使用指南

## 🚀 一鍵開始

```bash
# 測試系統是否正常
python3 test_system.py

# 優化單個逐字稿 (2輪疊代)
python3 scripts/iterative_optimizer.py "data/transcript/會議逐字稿.txt" --max-iterations 2

# 批次優化所有逐字稿
./run_optimization.sh
```

## 📊 系統測試結果

```text
=== 會議記錄優化系統測試 ===

✓ 文件結構檢查 通過
✓ 策略配置載入 通過 (30種策略)
✓ 優化器創建 通過
✓ 策略選擇邏輯 通過
✓ 提示詞生成 通過

🎉 所有測試通過！系統已準備就緒。
```

## 💡 核心功能

### 30種策略 × 6大維度

```text
🎭 角色 (5種)    🏗️ 結構 (5種)    📝 內容 (5種)
📋 格式 (5種)    🗣️ 語言 (5種)    ✨ 品質 (5種)
```

### 智能優化流程

```text
選擇策略 → 生成提示詞 → LLM生成 → 多指標評估 → 策略調整 → 重複疊代
```

## 📁 系統架構

```text
會議記錄優化系統/
├── scripts/iterative_optimizer.py  # 核心引擎
├── scripts/evaluation/              # 評估模組
├── config/improvement_strategies.json  # 30種策略
├── test_system.py                   # 系統測試
└── run_optimization.sh              # 一鍵執行
```

## ⚙️ 命令參數

```bash
python3 scripts/iterative_optimizer.py [檔案] [選項]

選項:
  --max-iterations N         最大疊代次數 (預設: 5)
  --quality-threshold 0.8    品質閾值 (預設: 0.8)
  --model MODEL_NAME         生成模型
  --optimization-model MODEL 策略優化模型
  --disable-early-stopping   禁用提前停止
```

## 📈 效果展示

### 策略組合範例

| 組合 | 角色 | 結構 | 內容 | 效果 |
|------|------|------|------|------|
| A | 專業記錄員 | 標準議程 | 摘要提煉 | 簡潔正式 |
| B | 主持人視角 | 決策導向 | 行動重點 | 決策清晰 |
| C | 技術專家 | 時間順序 | 詳細記錄 | 技術精確 |

### 多指標評估

- **結構性** (0-1): 章節完整度、格式規範性
- **完整性** (0-1): 議題覆蓋度、信息保留度  
- **準確性** (0-1): 事實正確性、數據精確性
- **可讀性** (0-1): 語言流暢度、邏輯清晰度
- **一致性** (0-1): 風格統一性、術語一致性

## 🔧 環境需求

- **Python**: 3.8+
- **Ollama**: 本地 LLM 服務
- **模型**: `cwchang/llama3-taide-lx-8b-chat-alpha1:latest`、`gemma3:12b`

## 💎 系統優勢

✅ **自動化**: 無需人工干預的端到端優化  
✅ **智能化**: 基於評估結果自動調整策略  
✅ **可擴展**: 易於新增策略和評估指標  
✅ **高效率**: Early stopping 節省計算資源  
✅ **高品質**: 多維度評估確保輸出品質  

---

**開始使用**: `python3 test_system.py && ./run_optimization.sh` 🎯
