import functions_framework
from cloudevents.http import CloudEvent
from detect_mime_type import detect_mime_type
import extractor_caller
import service_extractor 
import json

# Cloud Function entrypoint that gets triggered by a CloudEvent
@functions_framework.cloud_event
def trigger(event: CloudEvent):
    
    # --- EVENT DATA EXTRACTION ---
    # Event data can arrive as raw bytes or as dict, handle both
    if isinstance(event.data, bytes):
        try:
            # Decode event payload from bytes → JSON dict
            data = json.loads(event.data.decode("utf-8"))
        except Exception as e:
            # Fail early if payload is malformed
            raise ValueError(f"Failed to decode event data: {e}")
    elif isinstance(event.data, dict):
        # For debugging: confirm dict type
        print(type(event.data))
        data = event.data
    else:
        # Catch-all for unsupported event formats
        raise TypeError(f"Unsupported event data type: {type(event.data)}")

    # Extract bucket and file name from event payload
    bucket = data.get("bucket")
    name = data.get("name")
    print(f"Received from bucket: {bucket}, file: {name}")
    
    # Get the userId (Although this is no longer used but might be useful in the future if logging in is required) 
    metadata = data.get('metadata') or {}
    userId = metadata.get('userid')
    print("The userId: ", userId)

    # Get the Document Type, form2307, service-invoice, etc.
    doc_type = metadata.get('docType'.lower())
    print("The document type: ", doc_type)
    
    # Set default doc-type ( you can change the default to whichever you like)
    # If you upload directly to the bucket where the trigger is, the file uploaded wont carry
    # the document type metadata, this mostly happens when testing 
    if doc_type == None or doc_type == "":
        doc_type = "form2307"
    
    # Store the file type (img, pdf)
    mime_type = detect_mime_type(name)
    if mime_type == None:
        raise ValueError("Invalid file type")
    
    try:
        # Call function according to its doc_type

        # use extractor_caller.main if its 2307
        if doc_type == "form2307":
            extractor_caller.main(
            mime_type=mime_type,
            input=name,
            userId=userId,
            doc_type=doc_type,
            )
        # Use service_extractor.main if its service invoice
        elif doc_type == "service_invoice":
            service_extractor.main(
                mime_type=mime_type,
                bucket=bucket,
                input=name,
                userId=userId,
                doc_type=doc_type,
            )

        # TODO: AFTER CREATING THE EXTRACTOR FOR EXPENSE RECEIPT CREATE THE ELIF
        
        # Lastly the exepense receipt 
        else:
            # Default to form 2307 extractor
            extractor_caller.main(
            mime_type=mime_type,
            input=name,
            userId=userId,
            doc_type=doc_type,
            )
            
    # if any of them failed, raise an error
    # These will be seen in the Cloud Function logs, same with the print statements
    except ValueError as e:
        raise ValueError(f"You have some error: {ValueError}") 

    print("Process Complete")
