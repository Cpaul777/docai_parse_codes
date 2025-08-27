import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import storage
from calc_field import calculate
from getquarter import quarter
from isSecondPage import isRelevant
import firestore_write
import json
import re

@functions_framework.cloud_event
def sendTrigger(event: CloudEvent):
    data = event.data
    bucket_name = data.get("bucket")
    name = data.get("name")

    if name is None:
        print("Theres no file")
        return
    elif not (name.endswith("_finalized.json")):
        print(f"Skipped file: {name}")
        return

    print(name)

    # Initialize Storage clients to get the blob
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(name)

    metadata = data.get('metadata') or {}
    userId = metadata.get("userid")
    print("userId: ", userId)

    doc_type = metadata.get('docType')
    print("The document type: ", doc_type)

    print(f"Fetching {blob.name}")
    bytes = blob.download_as_bytes()
    document = json.loads(bytes)

    name = re.sub(r'^.*/', '', name)
    name = re.sub(r'-\d+_finalized\.json$', '', name)

    relevant = isRelevant(document)
    if(relevant):
        document = quarter(document)
        
        if document.get("table_rows"):
            document = calculate(document)
        else:
            print("Theres no table_rows.")
        
        firestore_write.write_to_firestore(document, name, doc_type)

    else:
        print("Irrelevant, didnt write")
        print("Process Done", name)