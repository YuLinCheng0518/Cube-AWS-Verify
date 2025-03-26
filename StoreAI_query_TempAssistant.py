import json
import time
import urllib.request
import os
import hashlib

# Lambda function: query assistant via OpenAI API
def lambda_handler(event, context):
    """
    AWS Lambda handler to interact with OpenAI Assistant APIs using assistants=v2.
    """
    # Step 1: Validate API Key
    headers = event.get("headers") or {}
    apikey = headers.get("apikey")

    if not apikey:
        return generate_response(401, "401", "Missing API key")

    if not validate_apikey(apikey):
        return generate_response(403, "403", "Invalid API key")

    try:
        # Step 2: Retrieve parameters from event
        body = event.get("body", "{}")
        assistant_id = body.get("asst")
        query_content = body.get("query")

        if not assistant_id or not query_content:
            return generate_response(400, "Missing required parameters: asst, query")

        # Step 3: Retrieve OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return generate_response(500, "Server configuration error: Missing OpenAI API key in environment variables.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "assistants=v2"
        }

        # Step 4: Create thread
        thread_id = create_thread(headers)
        if not thread_id:
            return generate_response(500, "Failed to create thread.")

        # Step 5: Create message
        message_id = create_message(headers, thread_id, query_content)
        if not message_id:
            return generate_response(500, "Failed to create message.")

        # Step 6: Create run
        run_id = create_run(headers, thread_id, assistant_id)
        if not run_id:
            return generate_response(500, "Failed to create run.")

        # Step 7: Poll run status
        poll_run_status(headers, thread_id, run_id)

        # Step 8: Retrieve messages
        first_message_content = retrieve_first_message(headers, thread_id)

        # Response
        return generate_response(200, "0000", first_message_content)

    except Exception as e:
        return generate_response(500, str(e))


# Helper functions for API Key validation

def generate_apikey(timestamp=None):
    """
    Generate an API key based on a given timestamp.
    """
    if timestamp is None:
        timestamp = int(time.time()) // 60
    raw_string = f"cube{timestamp}"
    apikey = hashlib.sha256(raw_string.encode()).hexdigest()
    return apikey


def validate_apikey(apikey):
    """
    Validate the API key with a 60-second flexibility.
    """
    current_timestamp = int(time.time()) // 60
    # Generate API keys for the current, previous, and next minute
    expected_apikeys = [
        generate_apikey(current_timestamp),        # Current minute
        generate_apikey(current_timestamp - 1),    # Previous minute
        generate_apikey(current_timestamp + 1),    # Next minute
        "testtt"     # Testing fixed UUID
    ]
    return apikey in expected_apikeys


# OpenAI API integration functions
def create_thread(headers):
    """
    Create a thread using the OpenAI API.
    """
    url = "https://api.openai.com/v1/threads"
    request = urllib.request.Request(url, headers=headers, method="POST")
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data.get("id")


def create_message(headers, thread_id, query_content):
    """
    Create a message in the thread.
    """
    url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
    payload = json.dumps({"role": "user", "content": query_content}).encode('utf-8')
    request = urllib.request.Request(url, headers=headers, data=payload, method="POST")
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data.get("id")


def create_run(headers, thread_id, assistant_id):
    """
    Create a run in the thread.
    """
    url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
    payload = json.dumps({"assistant_id": assistant_id}).encode('utf-8')
    request = urllib.request.Request(url, headers=headers, data=payload, method="POST")
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data.get("id")


def poll_run_status(headers, thread_id, run_id):
    """
    Poll the run status until it is completed.
    """
    url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
    while True:
        request = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("status") == "completed":
                break
        time.sleep(0.5)  # Poll every 0.5 seconds


def retrieve_first_message(headers, thread_id):
    """
    Retrieve the first message in the thread.
    """
    url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
        first_message = data["data"][0]["content"][0]["text"]["value"]

        # Remove annotations
        annotations = data["data"][0]["content"][0]["text"].get("annotations", [])
        for annotation in annotations:
            text_to_remove = annotation["text"]
            first_message = first_message.replace(text_to_remove, "")

        # Remove Markdown
        first_message = remove_markdown(first_message)
        return first_message


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


# Local testing
if __name__ == "__main__":
    # Simulate an event for local testing
    test_event = {
        "headers": {
            "apikey": "550e8400-e29b-41d4-a716-446655440000"
        },
        "body": {
            "asst": "asst_IyjSSXcjHziraJnjUtMux4H8",
            "query": "我要轉帳不用手續費"
        }
    }

    # Run the Lambda function locally
    result = lambda_handler(test_event, None)
    print("Local Test Result:")
    print(json.dumps(json.loads(result["body"]), indent=4, ensure_ascii=False))
