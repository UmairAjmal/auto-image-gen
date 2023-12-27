import json
import time
import boto3
import base64
from PIL import Image
from os import environ
from io import BytesIO
from datetime import datetime

from utils.dynamo import update_service_status, update_request_record, get_inference_endpoint
from utils.comprehend import is_prompt_positive
from utils.functions import get_prompt
from utils.s3 import store_image_in_s3 
from utils.sqs import get_messages_count, set_sqs_delay
from utils.sagemaker import create_inference_endpoint, get_inference_endpoint_status


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



def generate_image(request_id, prompt, endpoint_name):
    print("Generate Image")
    payload = {
        "cfg_scale": CFG_SCALE,
        "height": HEIGHT,
        "width": WIDTH,
        "steps": STEPS,
        "seed": SEED,
        "sampler": SAMPLER,
        "text_prompts": [
            {
                "text": prompt,
                "weight": WEIGHT
            }
        ],
        "samples": SAMPLES  # Set samples to 1 for a single image
    }
    
    print("Prompt ", prompt)

    try:
        print("Invoking endpoint")
        status="inprogress"
        update_request_record(dynamodb_client, REQUEST_TABLE_NAME,request_id,status)
        response = sagemaker_runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType=CONTENT_TYPE,
            Body=json.dumps(payload)
        )
        print(" RESPONSE OF generate image is ", response)
        return 200, response
    except Exception as excp:
        status="failed"
        update_request_record(dynamodb_client, REQUEST_TABLE_NAME, request_id, status)
        print("Exception ", excp)
        return 500, json.dumps({"error": str(excp)})



def lambda_handler(event, context):
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
                update_service_status(dynamodb_client, SERVICE_TABLE_NAME, 'inference_endpoint', None, endpoint_name)
                create_inference_endpoint(sagemaker_client, ENDPOINT_CONFIG_NAME, endpoint_name)
                set_sqs_delay(sqs_client, SQS_NEW_DELAY_TIME, QUEUE_URL)
                raise Exception('Endpoint not present, creation in progress')
            
            # Check for endpoint status, if not inservice raise error
            status = get_inference_endpoint_status(sagemaker_client,endpoint_name)
            if(status != 'InService'):
                raise Exception('Endpoint not in service')
            
            set_sqs_delay(sqs_client, SQS_DEFAULT_DELAY_TIME,QUEUE_URL)
            statusCode, response = generate_image(request_id, prompt, endpoint_name)
            
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
                    status="completed"
                    update_request_record(dynamodb_client, REQUEST_TABLE_NAME, request_id,status, s3_key)
                    # delete_from_sqs(QUEUE_URL, ReceiptHandle)
                    messages_in_queue = get_messages_count(sqs_client, QUEUE_URL)
                    print(messages_in_queue)
                    if messages_in_queue <= 1:
                        print("reached on this body")
                        status = 'empty'
                        update_service_status(dynamodb_client, SERVICE_TABLE_NAME, 'queue', status)
                    # update_request_record(request_id,status, s3_key)
                    return {
                        'statusCode': 200,
                        "body" : json.dumps({"Processed Request": request_id})
                    }
        
    except Exception as excp:
        print("Exception ", excp)
        raise excp
