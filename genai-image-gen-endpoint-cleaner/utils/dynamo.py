def get_service_details(dynamodb_client, service_table_name, service_type):
    primary_key = {
        "service_type": {"S": service_type}
    }
    
    # Get the item
    response = dynamodb_client.get_item(
        TableName=service_table_name,
        Key=primary_key
    )
    
    if "Item" in response:
        # Get the status value
        return response["Item"]
    else:
        return None

def update_service_details(dynamodb_client, service_table_name, service_type):
    primary_key = {
        'service_type': {'S': service_type},
    }

    # Set the update expression
    update_expression = 'REMOVE service_name, updated_at'
    
    # Update the item
    response = dynamodb_client.update_item(
        TableName=service_table_name,
        Key=primary_key,
        UpdateExpression=update_expression
    )