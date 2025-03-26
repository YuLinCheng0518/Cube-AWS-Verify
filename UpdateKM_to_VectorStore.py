import json
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import requests
import time
from datetime import datetime
import pytz
import boto3
from botocore.exceptions import ClientError

# ======================== 基本設定 ========================
OPENAI_API_BASE = 'https://api.openai.com/v1'

# ======================== aws取得google credential ========================
# 目前不需要這樣用，先把檔案傳在這邊就好，直接呼叫
# def get_secret():
#     return json.loads(secret_str)
#  ======================== get_google_sheet, delete_all_vs_files, upload_vs_files ========================
def get_google_sheet(url: str, sheet_name: str):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credential.json", scope)
    client_gs  = gspread.authorize(creds)
    spreadsheet = client_gs.open_by_url(url)
    worksheet = spreadsheet.worksheet(sheet_name)
    sheet_data = worksheet.get_all_values()
    if not sheet_data:
        raise ValueError(f"No data found in sheet: {sheet_name}")
    else:
        return sheet_data

def delete_all_vs_files(vector_store_id, api_key:str):
    """
    刪除指定 VectorStore 內的所有檔案。這邊沒放assistant id其實不重要，因為request的url裡面用不到。
    """
    base_url = f"{OPENAI_API_BASE}/vector_stores"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # 取得 VectorStore 內的所有檔案
    list_url = f"{base_url}/{vector_store_id}/files"
    response = requests.get(list_url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to retrieve files:", response.text)
        return
    
    files = response.json().get("data", [])
    
    if len(files) == 0:
        print("There are no files to delete")
        return True
    else:
        print(f"There are {len(files)} files, starting deletion...")
    
    for file in files:
        file_id = file.get("id")
        delete_url = f"{base_url}/{vector_store_id}/files/{file_id}"
        try:
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code == 200 and delete_response.json().get("deleted"):
                print(f"Successfully deleted file: {file_id}")
            else:
                print(f"Failed to delete file: {file_id}")
        except Exception as e:
            print(f"Error deleting file {file_id}: {e}")
    time.sleep(5)
    
    
    # 再次確認是否成功刪除
    response = requests.get(list_url, headers=headers)
    print(response.text)
    if json.loads(response.text)['data'][0]['status'] == "failed":
        raise Exception(f"{json.loads(response.text)['data'][0]['last_error']}")
        # raise Exception(f"response.text.json()['data']['status']")
    elif response.status_code == 200 and len(response.json().get("data", [])) == 0:
        print("We have successfully deleted all files")
        return True
    else:
        print("Some files were not deleted")
        raise Exception("Some files were not deleted")
def upload_vs_files(platform, api_key, vector_store_id, assistant_id):
    """
    上傳最新檔案到指定 VectorStore（AWS Lambda 版本）
    """
    base_url = f"{OPENAI_API_BASE}/vector_stores"
    headers = {"Authorization": f"Bearer {api_key}", 'OpenAI-Beta': 'assistants=v2'}

    history_path = "/tmp/history"
    os.makedirs(history_path, exist_ok=True)  # 確保目錄存在

    files = [f for f in os.listdir(history_path) if platform in f]
    files.sort(reverse=True, key=lambda x: x.split("_")[-1].split(".")[0])
    filename = files[0] if files else None

    if not filename:
        print(f"No files found to upload for platform {platform}.")
        return None

    try:
        file_path = os.path.join(history_path, filename)

        # 上傳最新檔名的檔案
        upload_url = f"{OPENAI_API_BASE}/files"
        with open(file_path, "rb") as file:
            response = requests.post(upload_url, headers=headers, files={"file": file}, data={"purpose": "assistants"})

        if response.status_code != 200:
            print("Failed to upload file:", response.text)
            return None

        new_file_id = response.json().get("id")
        print(f"Created file and file ID is {new_file_id} for {filename}")

        # 將新檔案放入對應的 Vector Store
        add_file_url = f"{base_url}/{vector_store_id}/files"
        file_data = {"file_id": new_file_id}
        upload_response = requests.post(add_file_url, headers=headers, json=file_data)

        if upload_response.status_code != 200:
            print("Failed to add file to Vector Store:", upload_response.text)
            return None

        # 等待上傳完成
        while True:
            retrieve_url = f"{base_url}/{vector_store_id}/files/{new_file_id}"
            retrieve_response = requests.get(retrieve_url, headers=headers)

            if retrieve_response.status_code != 200:
                print("Failed to retrieve file status:", retrieve_response.text)
                return None

            status = retrieve_response.json().get("status")
            if status == "completed":
                break
            time.sleep(1)

        # 更新 Assistant 設定
        update_url = f"{OPENAI_API_BASE}/assistants/{assistant_id}"
        update_data = {"tool_resources": {"file_search": {"vector_store_ids": [vector_store_id]}}}
        update_response = requests.post(update_url, headers=headers, json=update_data)

        if update_response.status_code != 200:
            print("Failed to update assistant:", update_response.text)
            return None

        time.sleep(4)

        # 確認列表是否已經只有一個成功上傳的檔案
        list_url = f"{base_url}/{vector_store_id}/files"
        list_response = requests.get(list_url, headers=headers)

        if list_response.status_code == 200:
            files = list_response.json().get("data", [])
            print(f"Successfully uploaded files! There are {len(files)} files in the Vector Store")
        else:
            print("Failed to retrieve file list:", list_response.text)

    except Exception as e:
        print(f"Failed to upload files to OpenAI assistant: {e}")

#  ======================== Lambda Function ========================
def lambda_handler(event, context):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_URL = os.getenv("GOOGLE_URL")
    try:
        # 解析輸入參數
        print(f"Received event: {event}")
        body = event['body']
        assistant_id = body.get('assistant_id', 'None')  # 未使用，但保留
        vector_store_id = body.get('vector_store_id', 'None')
        sheet_name = body.get('sheet_name', 'Sheet1')  # 預設工作表名稱
        google_sheet_url = body.get('sheet_url', 'https://docs.google.com/spreadsheets/d/1-C4OwDPhBGIlxFwtRFNp6qAKcT6pJ6x_jVa8cVg6AZQ/edit?usp=sharing')
        if "ios" in sheet_name.lower():
            platform = 'ios'
        elif "android" in sheet_name.lower():
            platform = 'android'
        else:
            platform = 'others'

        if not vector_store_id:
            raise ValueError("Missing vector_store_id")
        if not OPENAI_API_KEY:
            raise ValueError("Missing OPENAI_API_KEY environment variable")
        
        # 1. 讀google sheet
        sheet_data = get_google_sheet(url=GOOGLE_URL,
                                      sheet_name=sheet_name)
        
        # 2. 另存新檔
        now = datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d-%H-%M-%S")
        history_path = "/tmp/history"
        os.makedirs(history_path, exist_ok=True)  # Lambda 環境可能沒有這個目錄

        temp_file = os.path.join(history_path, f"{platform}_sheet_data_{now}.txt")

        # 產生檔案並寫入內容
        content = "\n".join(["\t".join(row) for row in sheet_data])
        with open(temp_file, 'w') as f:
            f.write(content)
        
        # 3. 刪掉vector store的所有檔案
        deleted_all_files = delete_all_vs_files(vector_store_id=vector_store_id, api_key=OPENAI_API_KEY)
        if not deleted_all_files:
            raise Exception("Failed to delete all files in vector store")
        
        # 4. 上傳新檔案
        upload_vs_files(platform=platform, api_key=OPENAI_API_KEY, vector_store_id=vector_store_id, assistant_id=assistant_id)
        
        # 成功回應
        return {
            "statusCode": 200,
            "body": {
                "message": "Successfully processed Google Sheet and updated Vector Store",
                "platform": platform,
                "sheet_name": sheet_name,
                "vector_store_id": vector_store_id,
                "assistant_id": assistant_id,
                "timestamp": now
            }
        }

    except Exception as e:
        # 錯誤回應
        return {
            "statusCode": 500,
            "body": {
                "message": "Error processing request",
                "error": str(e)
            }
        }

# 測試事件
event = {
    "body": {
        "assistant_id": "asst_QscR1FtW0Mt3ZfilgdtL2Zgp",
        "vector_store_id": "vs_67c51534ade8819194dadbbd759ca71d",
        "sheet_name": "Temp_IOS_KM",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1-C4OwDPhBGIlxFwtRFNp6qAKcT6pJ6x_jVa8cVg6AZQ/edit?usp=sharing"
    }
}

print(lambda_handler(event=event, context = None))
