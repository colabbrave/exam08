# 貢獻指南

感謝您對本專案的關注！我們歡迎各種形式的貢獻。本文件將指導您如何參與專案開發。

## 開發環境設置

1. 克隆專案

   ```bash
   git clone [專案網址]
   cd exam08_提示詞練習重啟
   ```

2. 建立虛擬環境

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .venv\Scripts\activate  # Windows
   ```

3. 安裝開發依賴

   ```bash
   make install
   ```

4. 設置 pre-commit hooks

   ```bash
   pre-commit install
   ```

## 開發流程

1. 建立新分支

   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

2. 進行開發
   - 遵循程式碼風格指南
   - 撰寫測試
   - 更新文件

3. 提交變更

   ```bash
   git add .
   git commit -m "描述你的變更"
   ```

4. 推送到遠端

   ```bash
   git push origin feature/your-feature-name
   ```

5. 建立 Pull Request
   - 使用 GitHub 的 Pull Request 功能
   - 填寫 PR 描述
   - 等待審查

## 程式碼風格

1. Python 程式碼
   - 使用 Black 進行格式化
   - 使用 isort 排序 imports
   - 使用 Flake8 進行程式碼檢查
   - 使用 MyPy 進行型別檢查

2. 文件
   - 使用 Markdown 格式
   - 遵循現有的文件結構
   - 保持文件的一致性

3. 測試
   - 撰寫單元測試
   - 確保測試覆蓋率
   - 測試應該獨立且可重複執行

## 提交規範

提交訊息應遵循以下格式：

```
<類型>: <描述>

[可選的詳細描述]

[可選的相關問題編號]
```

類型包括：

- feat: 新功能
- fix: 錯誤修復
- docs: 文件更新
- style: 程式碼風格變更
- refactor: 程式碼重構
- test: 測試相關
- chore: 建置過程或輔助工具的變更

## 審查流程

1. 程式碼審查
   - 確保程式碼品質
   - 檢查測試覆蓋率
   - 驗證文件更新

2. 功能審查
   - 確認功能符合需求
   - 檢查效能影響
   - 驗證整合測試

3. 文件審查
   - 確保文件準確性
   - 檢查文件完整性
   - 驗證範例程式碼

## 問題回報

回報問題時，請包含以下資訊：

1. 問題描述
2. 重現步驟
3. 預期行為
4. 實際行為
5. 環境資訊
6. 相關日誌或截圖

## 功能建議

提出新功能建議時，請考慮：

1. 功能的目的和價值
2. 可能的實現方案
3. 與現有功能的整合方式
4. 潛在的影響和限制

## 聯絡方式

如有任何問題，請透過以下方式聯絡：

- GitHub Issues
- 電子郵件
- 專案討論區

感謝您的貢獻！
