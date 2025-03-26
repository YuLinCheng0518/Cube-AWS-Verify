import json
import os
from complementary_class import ReportGenerator, EmailSender

def lambda_handler(event, context):
    """
    AWS Lambda handler function that processes an input event, generates a report,
    sends it via email, and returns a JSON response.
    
    Parameters:
    - event: Dict containing 'data' (list of dicts) and 'receiver' (email recipient)
    - context: AWS Lambda context object (unused here)
    
    Returns:
    - Dict with statusCode and body as per AWS Lambda response format
    """
    try:
        # Extract data from event
        if 'data' not in event or not isinstance(event['data'], list):
            raise ValueError("Event must contain 'data' key with a list of dictionaries")
        data = event['data']
        
        # Initialize ReportGenerator (root_path set to /tmp, though not used for saving here)
        report_gen = ReportGenerator(root_path='/tmp')
        
        # Get email credentials from environment variables and receiver from event
        sender = os.environ.get('SENDER_EMAIL')
        password = os.environ.get('PASSWORD')
        receiver = event.get('receiver')
        
        if not sender:
            raise ValueError("Missing email sender")
        if not password:
            raise ValueError("Missing email password")
        if not receiver:
            raise ValueError("Missing email receiver")
        
        # Initialize EmailSender
        email_sender = EmailSender()
        
        # Send email with the report
        success = email_sender.send_email(sender, receiver, password, data, report_gen)
        
        # Check email sending result and prepare response
        if success:
            success_count = len(data)
            return {
                "statusCode": 200,
                "body": {
                    "returnCode": "0000",
                    "message": f"Successfully sent an email to {receiver} containing {len(data)} issues."
                }
            }
        else:
            return {
                "statusCode": 500,
                "body": {
                    "returnCode": "9999",
                    "message": "Failed to send email"
                }
            }
            
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "returnCode": "9999",
                "message": f"Error: {str(e)}"
            }
        }

# Test event for local testing
if __name__ == "__main__":
    test_event = {
        "data": [
            {
                "original_index": 1,
                "Title": "Issue with Login",
                "Comment": "Cannot login to app",
                "Platform": "iOS",
                "UserReply": "Please check your credentials",
                "Reformulated_Reply": ["Check username", "Reset password"],
                "YesNoList": ["Yes", "No"]
            },
            {
                "original_index": 2,
                "Title": "Payment Failure",
                "Comment": "Payment not processing",
                "Platform": "Android",
                "UserReply": "Contact support",
                "Reformulated_Reply": ["Verify card details"],
                "YesNoList": ["No"]
            }
        ],
        "receiver": "mmbcolab@gmail.com"
    }
    # 模擬 Lambda 環境變數
    os.environ['SENDER_EMAIL'] = ''
    os.environ['PASSWORD'] = ''  # 請替換為實際密碼
    print(lambda_handler(test_event, None))
