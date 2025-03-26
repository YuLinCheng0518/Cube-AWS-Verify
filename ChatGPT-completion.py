import json
import os
import requests
def remove_markdown(text):
    """
    Remove Markdown syntax from text.
    """
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
    return text

def generate_response(status_code, returnCode=None, message=""):
    """
    Generate a standard Lambda response.
    """
    if returnCode is None:
        returnCode = str(status_code)
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # 允许所有来源访问，也可以指定特定域名
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,apikey"
        },
        "body": {
            "returnCode": returnCode,
            "data": message
        }
    }

def lambda_handler(event, context):
    # 從環境變數取得 OpenAI API 金鑰
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {
            "statusCode": 500,
            "body": {"error": "Missing OpenAI API key"}
        }

    # API 端點
    url = "https://api.openai.com/v1/chat/completions"

    # 請求標頭
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        # 直接獲取消息內容
        message = event.get("message", "Hello!")

        # 請求體
        data = {
            "model": message["model"],
            "messages": [
                {"role": "system", "content": message["sys_prompt"]},
                {"role": "user", "content": message["prompt"]}
            ]
        }

        # 發送請求
        response = requests.post(url, headers=headers, json=data)

        # 檢查狀態碼並處理回應
        if response.status_code != 200:
            error_data = json.loads(response.text)  # 解析 API 錯誤
            error_code = error_data.get("error", {}).get("code", "unknown_error")
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            return generate_response(response.status_code, returnCode=error_code, message=error_message)

        # 成功情況
        result = response.json()
        return generate_response(200, "0000", result['choices'][0]['message']['content'])

    except Exception as e:
        return generate_response(500, "500", f"Error: {str(e)}")

if __name__ == '__main__':
    # 測試事件
    test_event = {
        "message": {
            "sys_prompt" : "記得在每一次的回覆最前面稱呼我帥哥",
            "model" : "gpt-4o",
            "prompt" : "我今天心情不好，安慰我一下"
        }
    }
    
    # 直接調用 lambda_handler
    response = lambda_handler(test_event, None)
    
    # 直接打印回應
    print(response)
