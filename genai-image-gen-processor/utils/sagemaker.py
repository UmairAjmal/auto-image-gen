def create_inference_endpoint(sagemaker_client, ENDPOINT_CONFIG_NAME, endpoint_name):
    sagemaker_client.create_endpoint(
        EndpointName= endpoint_name,
        EndpointConfigName= ENDPOINT_CONFIG_NAME
    )
    return endpoint_name
    
def get_inference_endpoint_status(sagemaker_client,endpoint_name):
    response = sagemaker_client.list_endpoints(
        NameContains=endpoint_name,
    )

    endpoints = response['Endpoints']
    status = None
    if len(endpoints) > 0:
        status = endpoints[0]['EndpointStatus']

    return status
