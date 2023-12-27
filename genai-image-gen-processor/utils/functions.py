import json

def get_prompt(event):
    print("Get prompt")    
    record = event.get('Records')[0]
    request_id, prompt = record['messageId'], json.loads(record['body']).get('message')
    return request_id, prompt