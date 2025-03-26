## 串接aws lambda api
import json
import requests
import pandas as pd
from datetime import datetime

data = pd.read_excel('/Users/twinb00551636/Downloads/StoreAI問與答.xlsx')
df = data.dropna(subset=['Platform', 'Comment', 'UserReply'])
data_dict = df.to_dict(orient='records')
summarized_list = []

def TextToList(text):
    return text.strip("[]").replace(" ", "").replace("'", "").split(',')

def PostRequest(url, payload):
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise Exception(json.loads(response.text))

# ======================設置 assistant_id======================
assistant_mapping = {
    "temp_ios": "asst_QscR1FtW0Mt3ZfilgdtL2Zgp",
    "temp_android": "asst_hYOY7EJGv2hTafJfnwtFrIYk",
    'ios': 'asst_IyjSSXcjHziraJnjUtMux4H8',
    'android': 'asst_tbypxTVefe86nkLiI0pkyptC'}

vector_mapping = {'temp_android':'vs_67c51734e9e481919e0eb0bb8ecf9cb4',
               'temp_ios': 'vs_67c51534ade8819194dadbbd759ca71d'}

KM_mapping = {'temp_ios': 'Temp_IOS_KM',
              'temp_android': 'Temp_Android_KM'}
# ====================url=============================
url_storeai_query_assistants = "/StroeAI_query_TempAssistant"
url_completion = '/ChatGPT-Completion' 
url_add_kms_temp = '/AddKMS_Temp'
url_send_mail = '/Send_Mail'
url_update_to_db = '/update_KM_to_DB'


for index, row in enumerate(data_dict[1:5]):
    # 動態設置 assistant_id
    platform = row["Platform"].lower()
    assistant_id = assistant_mapping.get(f"{platform}")
    if assistant_id is None:
        print(f"Error Platform Format:{platform}")
        continue

# ======================生成回覆======================
    original_comment = row['Title'] + row['Comment']
    query_org_reply = {
        "headers": {
            "apikey": "550e8400-e29b-41d4-a716-446655440000" 
        },
        "body": {
            "asst": assistant_id,
            "query": original_comment
        }
    }
    try:
        body = PostRequest(url_storeai_query_assistants, query_org_reply)
        data = body['body']['data']
    
        # body_json = json.loads(body)  # 解析 body 為 Python 字典
        # data = json.loads(body_json['body'])['data']
        print(f"DB1.0正式版回覆: {data}")
    except Exception as e:
        print(f"Error: {e}")

# ======================判斷矛盾======================
    conflict_warning_prompt = """
    請以專業的角度分析 **「主體的回覆」** 與 **「生成的回覆」**，的關係為以下四種的何種類型。
    1. **「主體的回覆」** 與 **「生成的回覆」** 文意相同且完整度雷同
    2. **「主體的回覆」** 比 **「生成的回覆」** 明顯還更完整且文意相同
    3. **「主體的回覆」** 比 **「生成的回覆」** 明顯還更不完整且文意相同
    4. **「主體的回覆」** 有回答到 **「主體的評論」**  ，並且 **「生成的回覆」** 沒有回答到 **「主體的評論」**(答非所問)

    請務必 **只輸出 JSON 格式的內容，不要額外加上任何文字或 `json` 標籤**。
    回傳的格式：
    {"Conflict_Type": , "Reason": "判定原因"}
    ex : {"Conflict_Type": 2, "Reason": "因為..."}
    """
    conflict_user_prompt = f"主體的評論：{original_comment}\n主體的回覆：{row['UserReply']}\n生成的回覆：{data} ，請幫我注意一定要以json格式回覆"

    conflict = {
            "message": {
            "sys_prompt" : conflict_warning_prompt,
            "model" : "o3-mini",
            "prompt" : conflict_user_prompt
        }}
    try:
        response = PostRequest(url_completion, conflict)
        data = response['body']['data']
        # body_json = json.loads(response)  # 解析 body 為 Python 字典
        # data = json.loads(body_json['body'])['data']
        conflict_type = json.loads(data)['Conflict_Type']
        print(f"Type: {conflict_type}")
    except Exception as e:
        print(f"Error: {e}")

    if conflict_type in [1, 3]:
        print('「匯入的」回覆 與 生成的回覆 文意相同且完整度雷同')
        print('-' * 100)
        continue
    elif conflict_type in [2, 4]:
        print('「匯入的」回覆 比 生成的回覆 明顯還更完整且文意相同')
# ======================匯入至Google Sheet======================
        Body = {
            "body": {
                "datas": [
                    {
                        "id": row["ReviewID"],
                        "title": row["Title"],
                        "quest": row["Comment"],
                        "response": row["UserReply"],
                        "platform": platform,
                        "datetime": str(datetime.now()), # 先以現在匯入評論時的時間當作datetime <- 未來可以修改
                        "rank": row["Rating"]
                    }
                ]}}
        try:
            response = PostRequest(url_add_kms_temp, Body)
            print("API 回應：", response)
        except Exception as e:
            print(f"API 請求錯誤：{e}")
        print('-' * 100)

    else:
        print('Conflict_Type Error')

# ======================匯入至DB======================
    assistant_id = assistant_mapping.get(f"temp_{platform}", 'None')
    vector_id = vector_mapping.get(f"temp_{platform}", 'None')
    sheet_name = KM_mapping.get(f"temp_{platform}", 'None')

    event = {
        "body": {
            "assistant_id": assistant_id,
            "vector_store_id": vector_id,
            "sheet_name": sheet_name,
            "sheet_url": "https://docs.google.com/spreadsheets/d/1-C4OwDPhBGIlxFwtRFNp6qAKcT6pJ6x_jVa8cVg6AZQ/edit?usp=sharing"
        }
    }
    response = PostRequest(url_update_to_db, event)
    if response['statusCode'] != 200:
        print(f"API 匯入錯誤：{response}")
        print('-' * 100)
        continue
    else:
        print(f"API 回應: {response}")
#====================換句話說五次======================
        change_prompt = "請用中文把這句話換句話說5次(請盡量還原這句話的語氣)："
        change_system_prompt = 'You are a helpful assistant. The reply should be in Python list format, e.g., ["Response1", "Response2", ..., "Response5"](We want to apply json loads on this reply)'
        change = {
                "message": {
                "sys_prompt" : change_system_prompt,
                "model" : "gpt-4o",
                "prompt" : change_prompt + original_comment
            }}
        try:
            response = PostRequest(url_completion, change)
            # body_json = json.loads(response)  # 解析 body 為 Python list
            reformulated_list = json.loads(response['body']['data'])
            # reformulated_list = TextToList(reformulated_list)
        except Exception as e:
            print(f"Error: {e}")
        
    # ======================利用新的temp assistant回覆======================
        responses_list = []
        temp_assistant_id = assistant_mapping.get(f"temp_{platform}")

        for i, sentence in enumerate(reformulated_list):
            query_temp_reply = {
                "headers": {
                    "apikey": "550e8400-e29b-41d4-a716-446655440000" #固定住的
                },
                "body": {
                    "asst": temp_assistant_id,
                    "query": sentence
                }}
            try:
                response = PostRequest(url_storeai_query_assistants, query_temp_reply)
                # body_json = json.loads(response)  # 解析 body 為 Python 字典
                data = response['body']['data']
                print(f"DB1.1 UAT 第{i+1}筆回應: {data}"+ "\n")
            except Exception as e:
                print(f"Error: {response}")
            responses_list.append(data)

    # ======================檢查與原始回覆的衝突======================
        check_system_prompt = 'You are a helpful assistant. The reply should be only in Python list format, e.g., ["yes", "no", ..., "yes"], len(list) == 5. please use the Double quotation marks to wrap the "yes" or "no".'
        check_prompt = "分析 **「reformulate_reply」的資訊 ** 是否有包含 **「主體的回覆」** 的關鍵資訊"
        chck_prompt = check_prompt + "「reformulate_reply」 : " + str(responses_list) + "「主體的回覆」 : " + row["UserReply"]
        check = {
                "message": {
                "sys_prompt" : check_system_prompt,
                "model" : "o3-mini",
                "prompt" : chck_prompt
            }}
        try:
            response = PostRequest(url_completion, check)
            yes_no = json.loads(response['body']['data'])
            yes_times = yes_no.count('yes')
            no_times = yes_no.count('no')
            summarized_list.append(
                {
                    "original_index": index,
                    "Title": row["Title"],
                    "Comment": row["Comment"],
                    "Platform": row["Platform"],
                    "UserReply": row["UserReply"],
                    "Reformulated_Reply": responses_list,
                    "YesNoList": yes_no,
                    "Yes_times": yes_times,
                    "No_times": no_times
                })    
            print('-' * 100)
            
        except Exception as e:
            print(f"處理評論失敗: {response}")
            continue

    # ======================生成報表======================
        if summarized_list:
            summarized_df = pd.DataFrame(summarized_list)
            issue_df = summarized_df[summarized_df["Yes_times"] != 5]
            want_to_export = summarized_df[summarized_df["Yes_times"] == 5]["original_index"].tolist()
            
            print(f"需要匯出的數據索引: {want_to_export}")
            issue_dict = issue_df.to_dict(orient='records')
        
            # 組合成 API 需要的格式
            data_dict = {
                "data": [item for item in issue_dict],  # 修正此處
                "receiver": "mmbcolab@gmail.com"  # 確保 receiver 有值
            }
            try:
                response = PostRequest(url_send_mail, data_dict)
                print(f"API 回應: {response}")
            except Exception as e:
                print(f"API 請求錯誤：{e}")



