import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Initialize Google Sheets client
def initialize_gspread():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("googlesheet.json", scope)
    client = gspread.authorize(creds)
    return client

# Append data to the appropriate worksheet based on platform
def append_data_based_on_platform(spreadsheet, data):
    platform = data.get('platform', '').lower()
    if platform == 'ios':
        sheet = spreadsheet.worksheet('Temp_IOS_KM')
        data_to_append = [
            [data['title'], data['quest'], data['rank'], data['datetime'], data['response'], data['id']]
        ]
    elif platform == 'android':
        sheet = spreadsheet.worksheet('Temp_Android_KM')
        data_to_append = [
            [
                data['title'] + " " + data['quest'],
                data['rank'],
                data['datetime'],
                data['response'],
                data.get('appversion', ''),
                data.get('brand', ''),
                '',
                data['id']
            ]
        ]
    elif platform == 'test':
        sheet = spreadsheet.worksheet('test_KM')
        data_to_append = [
            [data['title'], data['quest'], data['rank'], data['datetime'], data['response'], data['id']]
        ]
    else:
        print(f"Unknown platform: {platform}")
        return False

    sheet.append_rows(data_to_append)
    return True

# Lambda handler
def lambda_handler(event, context):
    try:
        # Initialize Google Sheets client
        client_gs = initialize_gspread()

        # Open the spreadsheet
        spreadsheet = client_gs.open_by_url(
            'https://docs.google.com/spreadsheets/d/1-C4OwDPhBGIlxFwtRFNp6qAKcT6pJ6x_jVa8cVg6AZQ/edit?usp=sharing'
        )

        # Parse the request body
        datas = event["body"]["datas"]
        print(datas)
        success_count = 0
        for data in datas:
            success = append_data_based_on_platform(spreadsheet, data)
            if success:
                success_count += 1

        return {
            "statusCode": 200,
            "body": json.dumps({
                "returnCode": "0000",
                "message": f"add {success_count} items"
            })
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": {
                "returnCode": "9999",
                "message": str(e)
            }
        }

# Local testing
if __name__ == "__main__":
    test_event = {
        "body": {
            "datas": [
                {
                    "id": "00000016-432a-5902-c105-405a00000000",
                    "title": "Test Issue 1",
                    "quest": "Sample question for testing.",
                    "response": "Thank you for your feedback.",
                    "platform": "test",
                    "datetime": "2024/10/22 09:42:48",
                    "rank": "1",
                    "appversion": "",
                    "brand": "Apple"
                },
                {
                    "id": "00000016-432a-5902-c129-13e600000000",
                    "title": "Test Issue 2",
                    "quest": "Another test case question.",
                    "response": "We appreciate your input.",
                    "platform": "test",
                    "datetime": "2024/10/22 09:42:45",
                    "rank": "3",
                    "appversion": "",
                    "brand": "Samsung"
                }
            ]
        }
    }

    print(lambda_handler(test_event, None))

