import json

from utils.dynamo import update_request_record

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

def generate_image(dynamodb_client, sagemaker_runtime_client, CONTENT_TYPE, REQUEST_TABLE_NAME, CFG_SCALE, HEIGHT, WIDTH, STEPS, SEED, SAMPLER, WEIGHT, SAMPLES, request_id, prompt, endpoint_name):
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
