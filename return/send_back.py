import requests
import os

# For local testing purposes
# from dotenv import load_dotenv
# load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:3000/api/webhook")

def send_result_to_frontend(data):
    """
    Sends the result data to the frontend via a POST request.
    Args:
        data (dict): The result data to send.
    Returns:
        dict: Response from the frontend or error info.
    """
    try:
        headers = {"Content-Type": "application/json", "x-webhook-secret": WEBHOOK_SECRET}
        response = requests.post(WEBHOOK_URL, json=data, headers=headers, timeout=5)
        response.raise_for_status()
        return {"status": "success", "response": response.json()}
    except requests.RequestException as e:
        return {"status": "error", 
                "message": str(e),
                "details": getattr(e.response, "text", None)}

if __name__ == '__main__':
    from google.cloud import storage
    import json
    # Testing purposes
    storage_client = storage.Client()
    bucket = storage_client.bucket("processed_output_bucket")
    blob = bucket.blob("processed_path/16746721153392958237/0/DUMMY 2 - 2307 - ROBERT-0_finalized.json")

    data = json.loads(blob.download_as_string())
    print(send_result_to_frontend(data))

