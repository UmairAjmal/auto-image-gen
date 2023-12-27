def get_messages_count(sqs_client, queue_url):
    response = sqs_client.get_queue_attributes(
    QueueUrl=queue_url,
    AttributeNames=[
        'All'
        ]
    )
    return int(response['Attributes'].get('ApproximateNumberOfMessages',0)) + int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))

def set_sqs_delay(sqs_client, delay_time, QUEUE_URL):
    response = sqs_client.set_queue_attributes(
        QueueUrl=QUEUE_URL,
        Attributes={
            'DelaySeconds': str(delay_time)
        }
    )