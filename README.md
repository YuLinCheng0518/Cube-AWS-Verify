# StoreAI 評論處理系統

這個項目是一個自動化的評論處理系統，目標是從 Excel 文件中讀取用戶評論，通過串接多個 AWS Lambda API 進行回覆生成、衝突分析，最後將結果匯入 Google Sheet 和資料庫，並生成報表與郵件通知。項目使用 Python 開發，展現了我對雲端架構、API 整合和自動化流程的掌握。

---

## 項目主要功能

- **自動化評論處理**：從數據讀取到回覆生成，再到結果匯出，全程自動化，減少人工操作。
- **雲端無伺服器設計**：基於 AWS Lambda 實現高可擴展性和彈性。
- **智能回覆生成與分析**：利用語言模型生成回覆並檢查一致性，提升回覆質量。
- **跨平台適配**：動態選擇助手 ID，處理 iOS 和 Android 的評論數據。
- **報表與通知**：生成處理結果報表並自動發送郵件。

---

## 使用的 AWS Lambda API

系統串接了以下關鍵 AWS Lambda API，實現了數據處理的完整流程：

1. **`/StroeAI_query_TempAssistant`**：根據評論內容生成回覆。
2. **`/ChatGPT-Completion`**：分析生成的回覆與原始評論的一致性。
3. **`/AddKMS_Temp`**：將處理結果匯入 Google Sheet。
4. **`/update_KM_to_DB`**：更新資料庫中的數據。
5. **`/Send_Mail`**：發送處理報表郵件。

---

## 技術

- **動態適配**：根據平台類型動態選擇助手 ID。
- **衝突分析**：設計提示模板，調用語言模型確保回覆一致性。
- **錯誤處理**：封裝 API 請求並加入異常處理。
- **性能優化**：批量處理數據，減少 API 調用次數。
