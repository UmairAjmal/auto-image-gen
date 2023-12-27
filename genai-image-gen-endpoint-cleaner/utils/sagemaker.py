def get_inference_endpoint_status(sagemaker_client, endpoint_name):
    response = sagemaker_client.list_endpoints(
        NameContains=endpoint_name,
    )

    endpoints = response['Endpoints']
    print({"List of endpoints": endpoints})
    status = None
    if len(endpoints) > 0:
        status = endpoints[0]['EndpointStatus']

    return status