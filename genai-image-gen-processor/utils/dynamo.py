import boto3
from datetime import datetime

from constants import *

def update_service_status(dynamodb_client,service_table_name,service_type, status = None, service_name = None):
    primary_key = {
        'service_type': {'S': service_type},
    }
    updated_at = datetime.now().isoformat()

    if service_type == 'inference_endpoint':
        # Set the update expression
        update_expression = 'SET service_name  = :service_name, updated_at = :updated_at'
        expression_attribute_values = {
            ':service_name': {'S': service_name},
            ':updated_at': {'S': updated_at}
        }

    if service_type == 'queue':
        # Set the update expression
        update_expression = 'SET service_status = :new_status, updated_at = :updated_at'
        expression_attribute_values = {
            ':new_status': {'S': status},
            ':updated_at': {"S": updated_at}
        }
    
    # Update the item
    response = dynamodb_client.update_item(
        TableName=service_table_name,
        Key=primary_key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

def update_request_record(dynamodb_client, request_table_name, request_id, status, url = None):
    primary_key = {
        'uuid': {'S': request_id},
    }

    # Set the update expression
    update_expression = 'SET prompt_status = :new_status'
    expression_attribute_values = {
        ':new_status': {'S': status}
    }

    if url is not None:
        update_expression += ', output_image_url = :url'
        expression_attribute_values[':url'] = {'S':url}
    
    # Update the item
    response = dynamodb_client.update_item(
        TableName=request_table_name,
        Key=primary_key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )
    
    # Print the response
    print(response)  

def get_inference_endpoint(service_table_name):
    dynamodb = boto3.resource('dynamodb')
    dynamo_table_client = dynamodb.Table(service_table_name)
    response = dynamo_table_client.get_item(
        Key={
            'service_type': inference_endpoint_service_name,
        }
    )

    # Check if item exists and return the record
    if 'Item' in response:
        item = response['Item']
        return item.get('service_name', None)
    else:
        return None, None
