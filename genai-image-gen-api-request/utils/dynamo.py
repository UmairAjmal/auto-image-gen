def update_queue_service_status(dynamodb_client, service_table_name, update_time):
    primary_key = {
        'service_type': {'S': 'queue'},
    }
    updated_status='not_empty'
    # Set the update expression
    update_expression = 'SET service_status = :new_status, updated_at = :updated_at'
    expression_attribute_values = {
        ':new_status': {'S': updated_status},
        ':updated_at': {"S": update_time}
    }
    
    # Update the item
    response = dynamodb_client.update_item(
        TableName=service_table_name,
        Key=primary_key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

def record_request(dynamodb_client,request_table_name,request_id, prompt, created_at):
    item = {
        'uuid': {'S': request_id},
        'prompt': {'S': prompt},
        'prompt_status': {"S": "queued"},
        'created_at': {"S": created_at} 
    }
    print({'put item': item})
    response = dynamodb_client.put_item(
            TableName=request_table_name,
            Item=item
        )
    print(response)