# 會議記錄AI優化系統

## 專案概述
這是一個基於AI的會議記錄優化系統，使用開源大語言模型（如Gemma）將原始會議逐字稿轉換為結構化、易讀的正式會議記錄。系統支持多種優化策略，可根據需求調整輸出格式和風格。

## 功能特點

- **多種優化策略**：支持精簡冗詞、結構化摘要、發言者標註等多種優化方式
- **模型管理**：支持多種Ollama模型，可靈活切換不同規模的語言模型
- **自動評估**：提供優化結果與參考標準的相似度評估
- **資源監控**：實時監控系統資源使用情況，確保穩定運行
- **可擴展架構**：模塊化設計，易於添加新的優化策略和評估指標

## 系統要求

- Python 3.8+
- Ollama (運行開源大語言模型)
- 推薦至少16GB內存（運行較大模型時）

## 安裝步驟

### 1. 克隆代碼庫
```bash
git clone [https://github.com/colabbrave/exam08.git](https://github.com/colabbrave/exam08.git)
cd exam08_提示詞練習重啟
```

2. **設置虛擬環境**
   ```bash
   # 使用 Python 內建 venv
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .venv\Scripts\activate    # Windows
   
   # 或使用 uv（更快）
   # pip install uv
   # uv venv
   # source .venv/bin/activate
   ```

3. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

## 🛠 使用方法

### 基本用法

```bash
# 使用預設設置運行
./run_optimization.sh

# 使用非互動模式（自動選擇第一個可用模型）
./run_optimization.sh --non-interactive

# 指定要使用的模型
./run_optimization.sh --model gemma:4b

# 查看幫助
./run_optimization.sh --help
```

### 命令選項

| 選項 | 說明 | 預設值 |
|------|------|--------|
| `--interactive` | 啟用互動模式 | 是 |
| `--non-interactive` | 使用非互動模式 | 否 |
| `--model <名稱>` | 指定要使用的模型 | 無 |

## 🔧 配置

### 模型選擇

工具支援多種 AI 模型，包括：
- Gemma 系列
- LLaMA 系列
- 其他 Ollama 支援的模型

### 日誌

日誌文件保存在 `logs/` 目錄下，格式為：
```
optimization_YYYYMMDD_HHMMSS.log
```

## 🤝 貢獻

歡迎提交 Pull Request 或報告問題。請確保：

1. 遵循現有代碼風格
2. 添加適當的測試
3. 更新相關文檔

## 📄 授權

本專案採用 [MIT 授權](LICENSE)。

---

💡 提示：使用前請確保已下載所需的 AI 模型（使用 `ollama pull <模型名稱>`）

📧 如有問題或建議，請提交 [Issue](https://github.com/colabbrave/exam08/issues) 或聯繫維護者。

## 未來改進

- [ ] 實現更精細的評估指標
- [ ] 添加圖形用戶界面
- [ ] 支持並行處理多個文件
- [ ] 完善API文檔
- [ ] 添加單元測試和集成測試

## 目錄結構說明

- `/config`: 配置文件和優化策略定義
- `/data`: 原始逐字稿和參考會議記錄
  - `/transcript`: 原始會議逐字稿
  - `/reference`: 標準會議記錄（參考答案）
- `/prompts`: 提示詞模板和組件
- `/results`: 優化結果和評估報告
- `/scripts`: 核心處理腳本

## 優化策略

系統支持以下優化策略（定義於`/config/improvement_strategies.json`）：

- 精簡冗詞
- 結構化摘要
- 明確標註發言者
- 補充省略資訊
- 轉換為正式書面語
- 強化邏輯連貫性
- 統一專有名詞
- 刪除無關閒聊
- 明確標示決議事項
- 補充會議背景

## 使用Docker運行

1. 構建Docker鏡像
   ```bash
   docker build -t meeting-minutes-optimizer .
   ```

2. 運行容器
   ```bash
   docker run -it --rm -v $(pwd):/app meeting-minutes-optimizer
   ```

## 常見問題

### 1. 優化結果不理想
- 嘗試使用更大的模型（如gemma:7b）
- 調整提示詞模板
- 檢查原始逐字稿的格式是否正確

### 2. 內存不足
- 使用較小的模型（如gemma:2b）
- 關閉其他內存密集型應用
- 增加系統交換空間

## 貢獻指南

我們歡迎貢獻！請遵循以下步驟：

1. Fork 本專案
2. 創建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 授權

本專案採用 [MIT 授權](LICENSE)。

## 未來改進

- [ ] 實現更精細的評估指標
- [ ] 添加圖形用戶界面
- [ ] 支持並行處理多個文件
- [ ] 完善API文檔
- [ ] 添加單元測試和集成測試

---
