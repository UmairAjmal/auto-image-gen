import boto3
import json
import time
import uuid
from os import environ
from datetime import datetime

from utils.dynamo import record_request,update_queue_service_status
from utils.sqs import save_message_in_sqs, get_messages_count , calculate_remaining_time


dynamodb_client = boto3.client('dynamodb')
sqs_client = boto3.client(service_name='sqs')

QUEUE_URL = environ.get('SQS_QUEUE_URL')
REQUEST_TABLE_NAME = environ.get('REQUEST_TABLE_NAME') 
SERVICE_TABLE_NAME = environ.get('SERVICE_TABLE_NAME') 
DEFAULT_EXECUTION_TIME = int(environ.get('DEFAULT_EXECUTION_TIME'))
    
    
def lambda_handler(event, context):
    """
        Takes an API request, Extract Prompt, Stores in SQS queue, generate UUID
        Returns message_id and the queue number
    """
    
    try:
        body = json.loads(event['body'])
        prompt = body.get('prompt')
        creation_time = datetime.now().isoformat()
        request_id = str(uuid.uuid4())
        if not prompt or len(prompt) > 500 :
            return {
                "statusCode": 400,
                "body" : json.dumps({"error": "Prompt must be provided and be less than 500 characters"})
                }
        
        message_id = save_message_in_sqs(sqs_client,prompt, request_id,QUEUE_URL)
        update_queue_service_status(dynamodb_client, SERVICE_TABLE_NAME, creation_time)
        record_request(dynamodb_client,REQUEST_TABLE_NAME,message_id, prompt, creation_time)
        
        messages_in_queue = get_messages_count(sqs_client,QUEUE_URL)
        time_remaining = calculate_remaining_time(messages_in_queue,DEFAULT_EXECUTION_TIME)
        return {
            "statusCode": 200,
            "body": json.dumps({
                'message_id': message_id,
                'queue_number':messages_in_queue,
                'expected_time_remaining': time_remaining
            })
        }
    except Exception as excp:
        print(excp)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(excp)})
        }