from utils.dynamo import update_request_record
import json
import base64
from PIL import Image
from io import BytesIO

def store_image_in_s3(s3_client, dynamodb_client, S3_BUCKET, REQUEST_TABLE_NAME, request_id, response):
    try:
        result = json.loads(response['Body'].read())
        base64_data= result['artifacts'][0]['base64']
        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))
        s3_key = request_id + ".jpg"
        s3_client.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=image_data)
        print("S3 KEY ", s3_key)
        # url=presigned_url(S3_BUCKET,s3_key)
        return 200, s3_key
    except Exception as excp:
        status="failed"
        update_request_record(dynamodb_client, REQUEST_TABLE_NAME, request_id, status)
        print("Exception ", excp)
        return 500,  json.dumps({"error": str(excp)})
