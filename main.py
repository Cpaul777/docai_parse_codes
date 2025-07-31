from functions_framework import cloud_event
from cloudevents.http import CloudEvent
from typing import Any
import json

import extractor_caller
import handle_data
import preprocess

def trigger(event: CloudEvent):
    
    if isinstance(event.data, bytes):
        try:
            data = json.loads(event.data.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decode event data: {e}")
    else:
        raise TypeError("Unsupported event data type")

    bucket = data.get("bucket")
    name = data.get("name")

    # Check what type of file it is
    if name.endswith(".pdf"):
        mime_type = "application/pdf"
    elif name.endswith(".png"):
        mime_type = "image/png"
    elif name.endswith(".jpg") or name.endswith(".jpeg"):
        mime_type = "image/jpeg"
    
    extractor_caller.main(
        mime_type=mime_type,
        input=name)

    
    return f"File uploaded: {name} in bucket {bucket}"
    