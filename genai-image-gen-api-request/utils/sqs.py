import json

def get_messages_count(sqs_client,queue_url):
    response = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['All']
    )
    return int(response['Attributes'].get('ApproximateNumberOfMessages',0)) + int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))

def calculate_remaining_time(messages_in_queue,default_execution_time):
    return (messages_in_queue * default_execution_time) + default_execution_time
    
def save_message_in_sqs(sqs_client,message, request_id,QUEUE_URL):
    response = sqs_client.send_message(
        QueueUrl = QUEUE_URL,
        MessageBody=json.dumps({'message': message}),
        MessageGroupId='gen-request',
        MessageDeduplicationId=request_id
    )
    return response['MessageId']