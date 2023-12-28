from utils.dynamo import update_request_record
import json
import base64
from PIL import Image
from io import BytesIO

from constants import *

def store_image_in_s3(s3_client, dynamodb_client, s3_bucket, request_table_name, request_id, response):
    try:
        result = json.loads(response['Body'].read())
        base64_data= result['artifacts'][0]['base64']
        image_data = base64.b64decode(base64_data)
        image = Image.open(BytesIO(image_data))
        s3_key = request_id + ".jpg"
        s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=image_data)
        print("S3 KEY ", s3_key)
        # url=presigned_url(S3_BUCKET,s3_key)
        return 200, s3_key
    except Exception as excp:
        status=failed_status
        update_request_record(dynamodb_client, request_table_name, request_id, status)
        print("Exception ", excp)
        return 500,  json.dumps({"error": str(excp)})
