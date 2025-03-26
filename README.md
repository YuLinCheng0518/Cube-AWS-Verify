# StoreAI 評論處理系統

這個項目是一個自動化評論處理系統，旨在從 Excel 文件中讀取用戶評論數據，通過串接多個 AWS Lambda API 進行數據處理、回覆生成、衝突分析，並將結果匯入 Google Sheet 和資料庫，最終生成報表並發送郵件通知。項目使用 Python 編寫，適用於處理來自不同平台的評論數據，例如 iOS 和 Android。

---

## 依賴和安裝

項目依賴以下 Python 庫：

- **pandas**：用於數據處理和報表生成。
- **requests**：用於發送 HTTP 請求與 AWS Lambda API 交互。
- **json**：用於處理 API 回應數據。
- **datetime**：用於記錄數據處理時間。

您可以使用以下命令安裝依賴：

```bash
pip install pandas requests
