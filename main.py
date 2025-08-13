import functions_framework
from cloudevents.http import CloudEvent
from typing import Any
import json

import extractor_caller

@functions_framework.cloud_event
def trigger(event: CloudEvent):
    
    if isinstance(event.data, bytes):
        try:
            data = json.loads(event.data.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decode event data: {e}")
    elif isinstance(event.data, dict):
        print(type(event.data))
        data = event.data
    else:
        raise TypeError(f"Unsupported event data type: {type(event.data)}")

    bucket = data.get("bucket")
    name = data.get("name")
    print(f"Received from bucket: {bucket}, file: {name}")
    
    # Store the document type (img, pdf)
    mime_type = extractor_caller.detect_mime_type(name)
    if mime_type == None:
        raise ValueError("Invalid file type")
    
    try:
        """
        IF INVIOCE:
            CALL INVOICE EXTRACTOR
        ELIF EXPENSE:
            CALL EXPENSE EXTRACTOR
        """
        extractor_caller.main(
            mime_type=mime_type,
            input=name)
    except ValueError:
        print("Error in extractor_caller.main, invalid input file type or content.")
    print("Process Complete")