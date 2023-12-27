import os
import boto3
from datetime import datetime

from utils.functions import is_diff_10_min
from utils.sagemaker import get_inference_endpoint_status
from utils.dynamo import update_service_details, get_service_details

SERVICE_TABLE_NAME = os.environ.get('SERVICE_TABLE_NAME', "genai-image-gen-service-table") 

dynamodb_client = boto3.client('dynamodb')
sagemaker_client=boto3.client('sagemaker')

def is_diff_10_min(last_updated):
    # Define reference time
    reference_time = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%S.%f")
    
    # Get current time
    current_time = datetime.now()
    
    # Calculate the time difference in seconds
    time_diff = (current_time - reference_time).total_seconds()

    # Check if the difference is 10 minutes (600 seconds)
    return True if time_diff >= 600 else False
    

def lambda_handler(event, context):
    
    endpoint_details = get_service_details(dynamodb_client, SERVICE_TABLE_NAME,'inference_endpoint')
    queue_details = get_service_details(dynamodb_client, SERVICE_TABLE_NAME, 'queue')
    
    print(endpoint_details)
    print(queue_details)
    queue_status=queue_details["service_status"]['S']

    # Process the item data if found
    time_updated=queue_details["updated_at"]['S']
    delete_endpoint = is_diff_10_min(time_updated)
    print({"Delete":delete_endpoint})
    endpoint_name =  endpoint_details['service_name']['S'] if 'service_name' in endpoint_details else None
    if  delete_endpoint == True and queue_status == 'empty' and endpoint_name != None:
        status = get_inference_endpoint_status(sagemaker_client, endpoint_name)
        if(status == 'InService'):
            response = sagemaker_client.delete_endpoint(
                EndpointName=endpoint_details['service_name']['S']
            )
            update_service_details(dynamodb_client, SERVICE_TABLE_NAME, 'inference_endpoint')
            print("successfully deleted endpoint after 10 minutes")
        else:
            print("No endpoint exist for deletion")
    else:
        print('Condition for deletion not met')

