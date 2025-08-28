import functions_framework
from cloudevents.http import CloudEvent
from detect_mime_type import detect_mime_type
import extractor_caller
import service_extractor 
import json

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
    
    # Get the userId
    metadata = data.get('metadata') or {}
    userId = metadata.get('userid')
    print("The userId: ", userId)

    # Get the Document Type, form2307, service-invoice, etc.
    # metadata from signedURL are all lower cased
    doc_type = metadata.get('docType'.lower())
    print("The document type: ", doc_type)
    
    # Set default doc-type (change this if youre debugging/testing for a specific document type)
    if doc_type == None or doc_type == "":
        doc_type = "form2307"
    
    # Store the document type (img, pdf)
    mime_type = detect_mime_type(name)
    if mime_type == None:
        raise ValueError("Invalid file type")
    
    try:
        # Call functio according to its doc_type
        if doc_type == "form2307":
            extractor_caller.main(
            mime_type=mime_type,
            input=name,
            userId=userId,
            doc_type=doc_type,
            )
        elif doc_type == "service_invoice":
            service_extractor.main(
                mime_type=mime_type,
                bucket=bucket,
                input=name,
                userId=userId,
                doc_type=doc_type,
            )

        # TODO: AFTER CREATING THE EXTRACTOR FOR EXPENSE RECEIPT CREATE THE ELIF

        else:
            # Default to form 2307 extractor
            extractor_caller.main(
            mime_type=mime_type,
            input=name,
            userId=userId,
            doc_type=doc_type,
            )
    except ValueError as e:
        raise ValueError(f"You have some error: {ValueError}") 

    print("Process Complete")