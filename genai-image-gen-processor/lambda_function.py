import json
import time
import boto3
import base64
from PIL import Image
from os import environ
from io import BytesIO
from datetime import datetime

from constants import *
from utils.functions import get_prompt
from utils.s3 import store_image_in_s3 
from utils.comprehend import is_prompt_positive
from utils.sqs import get_messages_count, set_sqs_delay
from utils.dynamo import update_service_status, update_request_record, get_inference_endpoint
from utils.sagemaker import create_inference_endpoint, get_inference_endpoint_status, generate_image


s3_client = boto3.client("s3")
sqs_client = boto3.client('sqs')
dynamodb_client = boto3.client('dynamodb')
sagemaker_client = boto3.client('sagemaker')
comprehend_client = boto3.client('comprehend')
sagemaker_runtime_client = boto3.client("sagemaker-runtime")


SEED = int(environ.get('SEED'))
SAMPLER = environ.get('SAMPLER')
STEPS = int(environ.get("STEPS"))
WIDTH = int(environ.get('WIDTH')) 
WEIGHT = int(environ.get('WEIGHT'))
HEIGHT = int(environ.get('HEIGHT'))
S3_BUCKET = environ.get('S3_BUCKET')
SAMPLES = int(environ.get('SAMPLES'))
QUEUE_URL = environ.get('SQS_QUEUE_URL')
CFG_SCALE = int(environ.get('CFG_SCALE'))
LANGUAGE_CODE = environ.get('LANGUAGE_CODE')
CONTENT_TYPE = environ.get('CONTENT_TYPE')
REQUEST_TABLE_NAME = environ.get('REQUEST_TABLE_NAME') 
SERVICE_TABLE_NAME = environ.get('SERVICE_TABLE_NAME') 
ENDPOINT_CONFIG_NAME = environ.get('ENDPOINT_CONFIG_NAME')
SQS_NEW_DELAY_TIME = int(environ.get('SQS_NEW_DELAY_TIME'))
SQS_DEFAULT_DELAY_TIME = int(environ.get('SQS_DEFAULT_DELAY_TIME'))

def lambda_handler(event, context):
    """
        Poll message from queue, Extract Prompt, check if prompt is positive, check if enpoint is in service,
        if not then create the endpoint and  generate image, store image in s3 and store the status in dynamodb,
        also check if the queue is empty and update the queue status
    """
    print("EVENT ", event)
    record = event.get('Records')[0]
    try:
        # Get Prompt
        request_id, prompt = get_prompt(event)
        print("Prompt :: ", prompt)
        print("Request ID  :: ",  request_id )

        # Send Stable Diffusion Request for Image Generation
        if is_prompt_positive(comprehend_client, prompt, LANGUAGE_CODE):
            # Check for existing inference endpoint status
            endpoint_name = get_inference_endpoint(SERVICE_TABLE_NAME)

            if endpoint_name is None:
            # Create new endpoint if not present
                current_date = datetime.now().strftime("%Y-%m-%d-%H-%M")
                endpoint_name = f'genai-image-gen-{current_date}'
                update_service_status(dynamodb_client, SERVICE_TABLE_NAME, inference_endpoint_service_name, None, endpoint_name)
                create_inference_endpoint(sagemaker_client, ENDPOINT_CONFIG_NAME, endpoint_name)
                set_sqs_delay(sqs_client, SQS_NEW_DELAY_TIME, QUEUE_URL)
                raise Exception('Endpoint not present, creation in progress')
            
            # Check for endpoint status, if not inservice raise error
            status = get_inference_endpoint_status(sagemaker_client,endpoint_name)
            if(status != endpoint_inservice_status):
                raise Exception('Endpoint not in service')
            
            set_sqs_delay(sqs_client, SQS_DEFAULT_DELAY_TIME,QUEUE_URL)
            statusCode, response = generate_image(dynamodb_client, sagemaker_runtime_client, CONTENT_TYPE, REQUEST_TABLE_NAME, CFG_SCALE, HEIGHT, WIDTH, STEPS, SEED, SAMPLER, WEIGHT, SAMPLES, request_id, prompt, endpoint_name)
            
            print("Response of generate image ", response)
            print("status code of gen image : ",  statusCode )
            
            
            if statusCode == 500:
                return {
                    "statusCode": 500,
                    "body" : response
                    }
            else:               # store in S3
                statusCode, s3_key = store_image_in_s3(s3_client, dynamodb_client, S3_BUCKET, REQUEST_TABLE_NAME,request_id, response)
                
                print("Response of store image ", s3_key)
                print("status code of store image : ",  statusCode )
                
                if statusCode == 500:
                    
                    return {
                        "statusCode": 500,
                        "body" : response
                    }
                else: # Remove from SQS
                    status=completed_status
                    update_request_record(dynamodb_client, REQUEST_TABLE_NAME, request_id,status, s3_key)
                    # delete_from_sqs(QUEUE_URL, ReceiptHandle)
                    messages_in_queue = get_messages_count(sqs_client, QUEUE_URL)
                    if messages_in_queue <= 1:
                        status = empty_queue_status
                        update_service_status(dynamodb_client, SERVICE_TABLE_NAME, queue_service_name, status)
                    # update_request_record(request_id,status, s3_key)
                    return {
                        'statusCode': 200,
                        "body" : json.dumps({"Processed Request": request_id})
                    }
        
    except Exception as excp:
        print("Exception ", excp)
        raise excp
