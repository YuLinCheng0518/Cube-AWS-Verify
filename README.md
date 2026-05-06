# StoreAI 評論處理系統

[![OpenAI](https://img.shields.io/badge/OpenAI-Assistants_API-412991?style=flat-square&logo=openai)](https://platform.openai.com/docs/)
[![AWS](https://img.shields.io/badge/AWS-Lambda-FF9900?style=flat-square&logo=amazon-aws)](https://aws.amazon.com/lambda/)
[![Python](https://img.shields.io/badge/Python-Workflow-3776AB?style=flat-square&logo=python)](https://www.python.org/)

StoreAI 是一套以 Python 開發的自動化評論處理系統，目標是把「評論生成、回覆一致性驗證、知識同步更新、報表通知」串成可重複執行的工作流。系統透過 AWS Lambda 與 OpenAI API 完成主要 AI 能力，並將處理結果同步到 Google Sheet、資料庫與郵件報表中。

---

## 專案特色

- 自動化評論處理：從資料讀取、回覆生成到結果輸出，全流程自動化。
- 回覆一致性驗證：針對新增或更新知識，檢查模型回覆是否出現衝突或偏差。
- 多階段驗證流程：可疑案例會改寫 5 次再驗證，提升檢查可靠性。
- 雲端無伺服器設計：以 AWS Lambda 串接各模組，便於擴展與維護。
- 報表與通知：自動整理結果並寄送報表通知。

---

## 架構與流程

### 主要元件

1. 主流程入口 [main.py](main.py)
2. 回覆生成 [StoreAI_query_TempAssistant.py](StoreAI_query_TempAssistant.py)
3. 一致性驗證 [ChatGPT-completion.py](ChatGPT-completion.py)
4. 知識庫同步 [UpdateKM_to_VectorStore.py](UpdateKM_to_VectorStore.py)
5. 匯入 Google Sheet [storeai_addkms_temp.py](storeai_addkms_temp.py)
6. 報表通知 [Send_Mail.py](Send_Mail.py)

### 流程摘要

1. 讀取 Excel / 評論資料，依平台類型分派處理邏輯。
2. 透過 OpenAI Assistant 生成回覆。
3. 使用 LLM 檢查回覆是否與原始內容衝突。
4. 若判定可疑，將評論改寫 5 次並重新驗證。
5. 將結果寫回 Google Sheet，並同步更新資料庫 / 知識庫。
6. 產出報表並寄送通知信件。

---

## 專案目錄

```text
StoreAI/
├─ main.py
├─ StoreAI_query_TempAssistant.py
├─ ChatGPT-completion.py
├─ UpdateKM_to_VectorStore.py
├─ storeai_addkms_temp.py
├─ Send_Mail.py
└─ README.md
```

---

## 安裝與啟動

### 方式 A：AWS Lambda 部署（建議）

1. 建立並上傳各個 Lambda function。
2. 設定環境變數（見下方「環境設定」）。
3. 透過 API Gateway 建立對應的 API 路徑。
4. 由主流程或排程觸發處理流程。

### 方式 B：本機測試

1. 於各檔案的 `__main__` 測試區塊以測試事件呼叫 `lambda_handler`。
2. 驗證回覆生成、衝突檢查與匯入流程是否正確。

---

## 環境設定

請在 `.env` 設定下列關鍵值：

- `OPENAI_API_KEY`
- `GOOGLE_URL`
- `SENDER_EMAIL`
- `PASSWORD`

---

## 資料模式

### 評論來源

- 以 Excel 檔或批次資料作為輸入來源。

### 匯出結果

- 匯入至 Google Sheet。
- 同步更新資料庫或知識庫。
