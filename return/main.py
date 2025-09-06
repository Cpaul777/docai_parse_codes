import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import storage
from calc_field import calculateTable, calculateForServiceInvoice
from getquarter import quarter
from isSecondPage import isRelevant
import firestore_write
import json
import re

@functions_framework.cloud_event
def sendTrigger(event: CloudEvent):

    # Extract event payload
    data = event.data
    bucket_name = data.get("bucket")
    name = data.get("name")

    # Skip if no file name provided
    if name is None:
        print("Theres no file")
        return
    # Skip if not a finalized JSON
    elif not (name.endswith("_finalized.json")):
        print(f"Skipped file: {name}")
        return

    print(name)

    # Initialize Storage clients to get the blob
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(name)

    # Retrieve metadata set during earlier processing
    metadata = data.get('metadata') or {}
    userId = metadata.get("userid")
    print("userId: ", userId)

    doc_type = metadata.get('docType')
    print("The document type: ", doc_type)

    # Load JSON document from GCS
    print(f"Fetching {blob.name}")
    bytes = blob.download_as_bytes()
    document = json.loads(bytes)

    # Clean up file name (remove folder prefix + suffix like -0_finalized.json)
    name = re.sub(r'^.*/', '', name)
    name = re.sub(r'-\d+_finalized\.json$', '', name)

    # Route document by type

    # For form2307 document
    if(doc_type == "form2307"):
        print(f"Processing {doc_type}")
        # Check if its an irrelevant second page, skip if irrelevant
        if(isRelevant(document)):
            # Get and Add quarter field
            document = quarter(document)

            # If table rows exist, calculate totals and add the necessary fields
            if document.get("table_rows"):
                document = calculateTable(document)
                
            # Save final document to Firestore
            firestore_write.write_to_firestore(document, name, doc_type)
        else:
            print("Irrelevant document, skipping...")

    # For service invoice document
    elif(doc_type == "service_invoice"):
            print(f"Processing {doc_type}")
            # Quarter Field
            document = quarter(document)
            # table and calculated fields 
            document = calculateForServiceInvoice(document)
            # Write to firestore
            firestore_write.write_to_firestore(document, name, doc_type)
        
    # For expense receipts
    # Not finished
    elif(doc_type == "expense_receipt"):
        print(f"Processing {doc_type}")
        document = quarter(document)
        document = calculateForServiceInvoice(document) #Not yet final
        firestore_write.write_to_firestore(document, name, doc_type) #Not yet final
    else:
        print("Irrelevant, didnt write")
        print("Process Done", name)
