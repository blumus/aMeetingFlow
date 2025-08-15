import json
import sys

def handler(event, context):
    """
    This function is the main handler for the Lambda invocation.
    It is triggered by an SES event when a new email is received.

    Parameters:
    - event (dict): The SES event data.
    - context (object): The Lambda context object.

    Returns:
    - dict: A dictionary containing the status code and a body message.
    """
    # Print the entire event to CloudWatch for debugging purposes.
    # This will show you the structure of the SES event payload.
    print(f"Received event: {json.dumps(event, indent=2)}")

    try:
        # Access the email data from the SES event payload
        # Note: The raw email content can be quite large.
        ses_notification = event['Records'][0]['ses']
        mail = ses_notification['mail']
        common_headers = mail['commonHeaders']
        
        # Extract basic email information
        subject = common_headers['subject']
        from_address = common_headers['from'][0]
        
        # Log the extracted information to stdout.
        # This will appear in CloudWatch Logs.
        print(f"Successfully received email from: {from_address}")
        print(f"Subject: {subject}")
        
        # Placeholder for future email parsing logic
        # For now, we will simply log the information
        
        # Return a success response
        return {
            'statusCode': 200,
            'body': json.dumps('Email processed successfully!')
        }

    except Exception as e:
        # Log any errors to stderr. This will also appear in CloudWatch Logs.
        # This is a critical step for debugging and error handling.
        print(f"An error occurred: {str(e)}", file=sys.stderr)
        
        # Return an error response
        return {
            'statusCode': 500,
            'body': json.dumps('An error occurred during email processing.')
        }

# For local testing, you can provide a sample event here.
if __name__ == '__main__':
    # This is a sample SES event structure.
    sample_event = {
        "Records": [
            {
                "eventSource": "aws:ses",
                "eventVersion": "1.0",
                "ses": {
                    "mail": {
                        "commonHeaders": {
                            "subject": "Meeting Invitation",
                            "from": ["user@example.com"],
                            "to": ["parser@your-domain-here.com"]
                        },
                        "headers": [],
                        "source": "user@example.com",
                        "timestamp": "2023-08-15T12:00:00.000Z",
                        "messageId": "example-message-id",
                        "destination": ["parser@your-domain-here.com"],
                        "headersTruncated": False
                    }
                }
            }
        ]
    }
    
    # Call the handler with the sample event for testing
    handler(sample_event, {})
