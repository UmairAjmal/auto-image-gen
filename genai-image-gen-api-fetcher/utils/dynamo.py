def check_request_status(client,REQUEST_TABLE_NAME,request_id):
    # Set the primary key values
    primary_key = {
        "uuid": {"S": request_id}
    }
    # Get the item
    response = client.get_item(
        TableName=REQUEST_TABLE_NAME,
        Key=primary_key
    )
    print({'Request ID': request_id, 'Request response': response})
    if "Item" in response:
        # Get the status value
        status = response["Item"]["prompt_status"]["S"]
        return status
    else:
        return "Not found"