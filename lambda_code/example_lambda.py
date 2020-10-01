def lambda_handler(event, context):
    print(f"event: {event}")
    return {"result": "success"}
