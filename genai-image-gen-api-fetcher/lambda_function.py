import json
import boto3
from os import environ

from constants import *
from utils.s3 import presigned_url
from utils.dynamo import check_request_status


S3_BUCKET = environ.get('S3_BUCKET')
REQUEST_TABLE_NAME = environ.get('REQUEST_TABLE_NAME') 
SERVICE_TABLE_NAME = environ.get('SERVICE_TABLE_NAME') 
QUEUE_URL = environ.get('SQS_QUEUE_URL')

s3_client = boto3.client("s3")
sqs_client = boto3.client('sqs')
dynamodb_client = boto3.client('dynamodb')


def lambda_handler(event, context):
    try:
        print(event)
        params = event.get('queryStringParameters', None)
        if(params is None):
            return {
                "statusCode": 400,
                "body": json.dumps({'message': 'Query params missing'})
            }
        request_id = params.get('request_id')
        
        status=check_request_status(dynamodb_client,REQUEST_TABLE_NAME,request_id)
        if status == queuedstatus:
            return {
                "statusCode": 202,
                "body": json.dumps({'request_id': request_id, 'status': status})
            }
        elif status == inprogressstatus:
            return {
                "statusCode": 202,
                "body": json.dumps({'request_id': request_id, 'status': status})
            }
        elif status == completedstatus:
            key = request_id + ".jpg"
            image_url = presigned_url(s3_client,S3_BUCKET,key)
            print(image_url)
            return {
                "statusCode": 200,
                "body": json.dumps({'request_id': request_id, 'status': status, 'url': image_url })
            }
        else:
            return {
                "statusCode": 500,
                "body": json.dumps({'request_id': request_id, 'status': status })
            }
    except Exception as e:
        print(e)
        return {
                "statusCode": 500,
                "body": json.dumps({'status': f"{e}" })
        }