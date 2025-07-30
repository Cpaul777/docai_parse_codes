from functions_framework import cloud_event
from cloudevents.http import CloudEvent
from typing import Any

import extractor_caller
import handle_data
import preprocess

def trigger(event: CloudEvent, context: Any):
    data = event.data

    bucket = data.get("bucket")
    name = data.get("name")

    print(f"File uploaded: {name} in bucket {bucket}")
    print(f"Informations: {data}")

