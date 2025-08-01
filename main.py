import functions_framework
from cloudevents.http import CloudEvent
from typing import Any
import json

import extractor_caller
import handle_data
import preprocess

@functions_framework.cloud_event
def trigger(event: CloudEvent):
    
    if isinstance(event.data, bytes):
        try:
            data = json.loads(event.data.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decode event data: {e}")
    elif isinstance(event.data, dict):
        data = event.data
    else:
        raise TypeError(f"Unsupported event data type: {type(event.data)}")

    bucket = data.get("bucket")
    name = data.get("name")

    mime_type = extractor_caller.detect_mime_type(name)
    if mime_type == None:
        raise ValueError("Invalid file type")
    
    try:
        extractor_caller.main(
            mime_type=mime_type,
            input=name)
    except ValueError:
        print("Error in extractor_caller.main, check the input file type or content.")
    return f"Process Complete"