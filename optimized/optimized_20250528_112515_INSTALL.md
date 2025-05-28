# 會議記錄優化工具安裝與使用指南

## 會議標題：優化工具安裝與使用指南

## 與會人員：開發團隊

## 討論事項：
- 說明優化工具的安裝步驟、環境要求、使用方法及疑難排解。
- 提供批量處理會議記錄的範例。
- 介紹進階選項及評估優化效果的方法。

## 決議事項：
- 建立標準化安裝與使用指南，以方便使用者。
- 提供詳細的疑難排解方法，提升使用者體驗。
- 鼓勵使用者提交問題和拉取請求，共同完善工具。

## 待辦事項：
- 完善疑難排解部分，增加更多常見問題及解決方案。
- 撰寫更詳細的授權文件，並更新相關資訊。
- 建立使用者文件，包含常見問題解答 (FAQ)。

## 環境要求

本工具的正常運作需要滿足以下環境要求：

- 作業系統：Windows, Linux, macOS
- Python 版本：3.8 或更高版本
- GPU 加速 (建議)：
    - CUDA 11.7 或更高版本
    - 至少 16GB 系統記憶體 (建議 32GB 或更多)
    - 至少 20GB 可用磁碟空間 (用於模型快取)
- 支援的語言模型：預設使用 `cwchang/llama3-taide-lx-8b-chat-alpha1_latest`，支援多種語言模型，使用者可選擇其他模型。

## 安裝步驟

1. **克隆代碼庫：**
   使用 Git 複製程式碼庫：
   ```bash
   git clone <repository-url>
   cd exam08_提示詞練習重啟
   ```
2. **創建並啟動虛擬環境（建議）：**
   建立一個隔離的 Python 虛擬環境，以避免與系統環境衝突：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   .\venv\Scripts\activate  # Windows
   ```
3. **安裝依賴：**
   使用 pip 安裝程式碼庫所需的依賴套件：
   ```bash
   pip install -r requirements.txt
   ```
4. **安裝 PyTorch（如需 GPU 支援）：**
   根據您的 CUDA 版本選擇合適的 PyTorch 安裝命令：
   ```bash
   # 例如，CUDA 11.8：
   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
   **注意：** 請務必選擇與您的 CUDA 版本相符的 PyTorch 版本。

## 下載模型

首次運行工具時，系統會自動下載預設模型 `cwchang/llama3-taide-lx-8b-chat-alpha1_latest` (約 15GB)。 請確保您有足夠的磁碟空間和穩定的網路連接。 您也可以手動下載模型並指定本地路徑。

## 使用方法

### 1. 優化單個會議記錄

使用以下命令優化單個會議記錄檔案：
```bash
python scripts/optimize_meeting_minutes.py path/to/your/meeting.txt
```
將 `path/to/your/meeting.txt` 替換為會議記錄檔案的實際路徑。

### 2. 批量處理多個會議記錄

使用以下命令批量處理目錄中的所有 `.txt` 檔案：

```bash
# 創建輸出目錄
mkdir -p optimized_meetings

# 處理目錄中的所有 .txt 文件
for f in data/meetings/*.txt; do
    python scripts/optimize_meeting_minutes.py "$f" -o optimized_meetings
done
```
將 `data/meetings/` 替換為包含會議記錄檔案的目錄路徑，`optimized_meetings` 為輸出目錄。

### 3. 評估優化效果

使用以下命令評估單個優化結果：

```bash
# 評估單個優化結果
python scripts/test_optimization.py --test-dir path/to/test/files --output-dir results/evaluation

# 查看評估報告
cat results/evaluation/optimization_evaluation.json
```
將 `path/to/test/files` 替換為測試檔案目錄路徑，`results/evaluation` 為輸出評估結果目錄。

## 進階選項

### 使用不同的模型

可以使用以下命令指定使用其他模型：

```bash
python scripts/optimize_meeting_minutes.py meeting.txt --model "jcai/llama3-taide-lx-8b-chat-alpha1_Q4_K_M"
```
將 `meeting.txt` 替換為會議記錄檔案，`jcai/llama3-taide-lx-8b-chat-alpha1_Q4_K_M` 為目標模型名稱。

### 調整生成長度

可以使用 `--max-length` 參數調整生成長度：

```bash
# 增加生成長度限制
python scripts/optimize_meeting_minutes.py meeting.txt --max-length 4096
```
將 `4096` 替換為所需的最大生成長度 (字數)。

## 疑難排解

### 記憶體不足

如果遇到記憶體不足錯誤，請嘗試：

1. 減少生成長度 (`--max-length`)
2. 使用較小的模型
3. 增加系統交換空間
4. 使用 CPU 模式（不推薦，速度較慢）

### 模型下載問題

如果模型下載失敗：

1. 檢查網路連接
2. 確保有足夠的磁碟空間
3. 手動下載模型並指定本地路徑

## 貢獻指南

歡迎提交問題和拉取請求！請確保：

1. 遵循現有的代碼風格
2. 為新功能添加測試
3. 更新相關文檔

## 授權

[在此添加授權信息]
