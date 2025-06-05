# 會議記錄優化工具安裝與使用指南

## 會議標題：優化工具安裝與使用指南

## 與會人員：[請在此填寫與會人員列表]

## 討論事項：
- 介紹優化工具的功能與使用方法
- 詳細說明安裝步驟、環境要求、使用方法、疑難排解及貢獻指南。

## 決議事項：
- 採購並安裝優化工具，以提升會議記錄優化效率。
- 鼓勵團隊成員積極參與工具的使用及貢獻。

## 待辦事項：
- 完善工具文檔，提供更詳細的使用說明。
- 建立測試用例，確保工具的穩定性和可靠性。
- 建立問題追蹤系統，方便使用者提交問題及建議。


## 環境要求

本優化工具依賴於以下環境配置：

*   **Python 版本:** 3.8 或更高版本
*   **CUDA 版本:** 11.7 或更高版本 (若需 GPU 加速)
*   **系統記憶體:** 至少 16GB (建議 32GB 或更多)
*   **磁碟空間:** 至少 20GB (用於模型快取)

## 安裝步驟

1.  **克隆代碼庫:** 使用 Git 複製程式碼庫至本地環境。
    ```bash
    git clone <repository-url>
    cd exam08_提示詞練習重啟
    ```

2.  **創建並啟動虛擬環境 (建議):**  建立並啟用一個隔離的 Python 虛擬環境，以管理專案依賴。
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # 或
    .\venv\Scripts\activate  # Windows
    ```

3.  **安裝依賴:**  使用 `pip` 依賴管理工具安裝程式碼庫中的所有依賴元件。
    ```bash
    pip install -r requirements.txt
    ```

4.  **安裝 PyTorch (若需 GPU 支援):**  根據您的 CUDA 版本選擇合適的 PyTorch 安裝命令。
    ```bash
    # 例如，CUDA 11.8：
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    ```

## 模型下載

本工具支援多種語言模型。預設使用 `cwchang/llama3-taide-lx-8b-chat-alpha1_latest`。首次運行時，工具會自動下載模型 (約 15GB)。請確保您有足夠的磁碟空間和穩定的網路連接。

## 使用方法

### 1. 優化單個會議記錄

```bash
python scripts/optimize_meeting_minutes.py path/to/your/meeting.txt
```

### 2. 批量處理多個會議記錄

```bash
# 創建輸出目錄
mkdir -p optimized_meetings

# 處理目錄中的所有 .txt 文件
for f in data/meetings/*.txt; do
    python scripts/optimize_meeting_minutes.py "$f" -o optimized_meetings
done
```

### 3. 評估優化效果

```bash
# 評估單個優化結果
python scripts/test_optimization.py --test-dir path/to/test/files --output-dir results/evaluation

# 查看評估報告
cat results/evaluation/optimization_evaluation.json
```

## 進階選項

### 使用不同的模型

```bash
python scripts/optimize_meeting_minutes.py meeting.txt --model "jcai/llama3-taide-lx-8b-chat-alpha1_Q4_K_M"
```

### 調整生成長度

```bash
# 增加生成長度限制
python scripts/optimize_meeting_minutes.py meeting.txt --max-length 4096
```

## 疑難排解

### 記憶體不足

如果遇到記憶體不足錯誤，請嘗試：

1.  減少生成長度 (`--max-length`)
2.  使用較小的模型
3.  增加系統交換空間
4.  使用 CPU 模式（不推薦，速度較慢）

### 模型下載問題

如果模型下載失敗：

1.  檢查網路連接
2.  確保有足夠的磁碟空間
3.  手動下載模型並指定本地路徑

## 貢獻指南

歡迎提交問題和拉取請求！請確保：

1.  遵循現有的代碼風格
2.  為新功能添加測試
3.  更新相關文檔

## 授權

[在此添加授權信息]
