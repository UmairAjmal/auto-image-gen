import os
import boto3
from datetime import datetime

from constants import *
from utils.functions import is_diff_10_min
from utils.sagemaker import get_inference_endpoint_status
from utils.dynamo import update_service_details, get_service_details

SERVICE_TABLE_NAME = os.environ.get('SERVICE_TABLE_NAME') 

dynamodb_client = boto3.client('dynamodb')
sagemaker_client=boto3.client('sagemaker')

def lambda_handler(event, context):
    """
        Invoked by Eventbridge after every 10 minutes, check queue status from dynamodb
        if the queue is empty and empty for more than 10 minutes,
        then deletes the endpoint
    """

    endpoint_details = get_service_details(dynamodb_client, SERVICE_TABLE_NAME,inference_endpoint_service_name)
    queue_details = get_service_details(dynamodb_client, SERVICE_TABLE_NAME, queue_service_name)
    
    print(endpoint_details)
    print(queue_details)
    queue_status=queue_details["service_status"]['S']

    # Process the item data if found
    time_updated=queue_details["updated_at"]['S']
    delete_endpoint = is_diff_10_min(time_updated)
    print({"Delete":delete_endpoint})
    endpoint_name =  endpoint_details['service_name']['S'] if 'service_name' in endpoint_details else None
    if  delete_endpoint == True and queue_status == empty_queue_status and endpoint_name != None:
        status = get_inference_endpoint_status(sagemaker_client, endpoint_name)
        if(status == endpoint_inservice_status):
            response = sagemaker_client.delete_endpoint(
                EndpointName=endpoint_details['service_name']['S']
            )
            update_service_details(dynamodb_client, SERVICE_TABLE_NAME, inference_endpoint_service_name)
            print("successfully deleted endpoint after 10 minutes")
        else:
            print("No endpoint exist for deletion")
    else:
        print('Condition for deletion not met')

