import json

from constants import *
from utils.dynamo import update_request_record

def create_inference_endpoint(sagemaker_client, endpoint_config_name, endpoint_name):
    sagemaker_client.create_endpoint(
        EndpointName= endpoint_name,
        EndpointConfigName= endpoint_config_name
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

def generate_image(dynamodb_client, sagemaker_runtime_client, content_type, request_table_name, cfg_scale, height, width, steps, seed, sampler, weight, samples, request_id, prompt, endpoint_name):
    print("Generate Image")
    payload = {
        "cfg_scale": cfg_scale,
        "height": height,
        "width": width,
        "steps": steps,
        "seed": seed,
        "sampler": sampler,
        "text_prompts": [
            {
                "text": prompt,
                "weight": weight
            }
        ],
        "samples": samples  # Set samples to 1 for a single image
    }
    
    print("Prompt ", prompt)

    try:
        print("Invoking endpoint")
        status=inprogress_status
        update_request_record(dynamodb_client, request_table_name,request_id,status)
        response = sagemaker_runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType=content_type,
            Body=json.dumps(payload)
        )
        print(" RESPONSE OF generate image is ", response)
        return 200, response
    except Exception as excp:
        status=failed_status
        update_request_record(dynamodb_client, request_table_name, request_id, status)
        print("Exception ", excp)
        return 500, json.dumps({"error": str(excp)})
