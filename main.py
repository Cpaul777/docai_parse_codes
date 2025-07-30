from functions_framework import cloud_event
from cloudevents.http import CloudEvent
from typing import Any

import extractor_caller
import handle_data
import preprocess

@cloud_event
def hello_gcs(event):
    print("Hello GCS!")
    print(f"Event Data: {event.data}")
    print("DONEDONEDONEDONEDONEDONEDONEDONE")
    print(f"Event ID: {event['id']}")

def trigger(event: CloudEvent, context: Any):
    data = event.data

    bucket = data.get("bucket")
    name = data.get("name")

    print(f"File uploaded: {name} in bucket {bucket}")
    print(f"Informations: {data}")

