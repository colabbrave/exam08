# 會議記錄優化工具安裝與使用指南

## 會議標題：優化工具安裝與使用指南

## 與會人員：[待定 - 記錄使用者]

## 討論事項：
- 介紹優化工具的功能和使用方法。
- 詳細說明安裝步驟、環境要求、使用方法、疑難排解和貢獻指南。
- 提供優化結果的評估方法。

## 決議事項：
- 採納優化工具以提升會議記錄的質量和效率。
- 鼓勵使用者參與工具的開發和完善。

## 待辦事項：
- 完善工具文檔，提供更清晰的使用說明。
- 增加工具的自動化功能，例如批量處理和自動評估。
- 建立完善的測試套件，確保工具的穩定性和可靠性。

## 環境要求

本工具的正常運行需要滿足以下環境要求：

*   **作業系統：** Windows, Linux, macOS
*   **Python 版本：** 3.8 或更高版本
*   **CUDA 版本：** 11.7 或更高版本（若需 GPU 加速）
*   **系統記憶體：** 至少 16GB (建議 32GB 或更多)
*   **磁碟空間：** 至少 20GB (用於模型快取)

## 安裝步驟

1.  **克隆代碼庫：**
    使用 Git 複製代碼庫：
    ```bash
    git clone <repository-url>
    cd exam08_提示詞練習重啟
    ```
2.  **創建並啟動虛擬環境（建議）：**
    *   **Linux/Mac:**
        ```bash
        python -m venv venv
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
3.  **安裝依賴：**
    使用 pip 安裝依賴包：
    ```bash
    pip install -r requirements.txt
    ```
4.  **安裝 PyTorch (若需 GPU 支援):**
    根據您的 CUDA 版本選擇合適的安裝命令。 例如， CUDA 11.8：
    ```bash
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    ```

## 模型下載

本工具支援多種語言模型。 預設使用 `cwchang/llama3-taide-lx-8b-chat-alpha1_latest`。 首次運行時，工具會自動下載模型（約 15GB）。 請確保您擁有足夠的磁碟空間和穩定的網路連接。

## 使用方法

1.  **優化單個會議記錄：**
    ```bash
    python scripts/optimize_meeting_minutes.py path/to/your/meeting.txt
    ```

2.  **批量處理多個會議記錄：**
    *   **創建輸出目錄：**
        ```bash
        mkdir -p optimized_meetings
        ```
    *   **執行批次處理：**
        ```bash
        for f in data/meetings/*.txt; do
            python scripts/optimize_meeting_minutes.py "$f" -o optimized_meetings
        done
        ```

3.  **評估優化效果：**
    *   **單個優化結果評估：**
        ```bash
        python scripts/test_optimization.py --test-dir path/to/test/files --output-dir results/evaluation
        ```
    *   **查看評估報告：**
        ```bash
        cat results/evaluation/optimization_evaluation.json
        ```

## 進階選項

1.  **使用不同的模型：**
    ```bash
    python scripts/optimize_meeting_minutes.py meeting.txt --model "jcai/llama3-taide-lx-8b-chat-alpha1_Q4_K_M"
    ```

2.  **調整生成長度：**
    ```bash
    # 增加生成長度限制
    python scripts/optimize_meeting_minutes.py meeting.txt --max-length 4096
    ```

## 疑難排解

1.  **記憶體不足錯誤：**
    *   嘗試減少生成長度 (`--max-length`)。
    *   使用較小的模型。
    *   增加系統交換空間。
    *   避免使用 CPU 模式（速度較慢）。

2.  **模型下載問題：**
    *   檢查網路連接。
    *   確保有足夠的磁碟空間。
    *   手動下載模型並指定本地路徑。

## 貢獻指南

歡迎提交問題和拉取請求！請確保：

*   遵循現有的代碼風格。
*   為新功能添加測試。
*   更新相關文檔。

## 授權

[在此添加授權信息]
