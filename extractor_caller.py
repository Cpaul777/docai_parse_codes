from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import RetryError
from google.cloud import documentai
from google.cloud import storage

from typing import Optional
import re
import json
import time
import os
import handle_data


def batch_process_documents(
    project_id: str,
    location: str,
    processor_id: str,
    gcs_output_uri: str,
    processor_version_id: Optional[str] = None,
    gcs_input_uri: Optional[str] = None,
    input_mime_type: Optional[str] = None,
    gcs_input_prefix: Optional[str] = None,
    field_mask: Optional[str] = None,
    timeout: int = 400,
) -> None:

    print("Connecting with the client...")
    client = documentai.DocumentProcessorServiceClient()

    if gcs_input_uri:
        # Specify specific GCS URIs to process individual documents
        gcs_document = documentai.GcsDocument(
            gcs_uri=gcs_input_uri, mime_type=input_mime_type
        )

        # Load GCS Input URI into a List of document files
        gcs_documents = documentai.GcsDocuments(documents=[gcs_document])
        input_config = documentai.BatchDocumentsInputConfig(gcs_documents=gcs_documents)

    else:
        # Specify a GCS URI Prefix to process an entire directory
        gcs_prefix = documentai.GcsPrefix(gcs_uri_prefix=gcs_input_prefix)
        input_config = documentai.BatchDocumentsInputConfig(gcs_prefix=gcs_prefix)

    # Cloud Storage URI for the Output Directory
    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=gcs_output_uri, field_mask=field_mask
    )

    # Where to write results
    output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    print("Connecting to the processor version...")
    if processor_version_id:
        # The full resource name of the processor version, e.g.:
        # projects/{project_id}/locations/{location}/processors/{processor_id}/processorVersions/{processor_version_id}
        name = client.processor_version_path(
            project_id, location, processor_id, processor_version_id
        )

    else:
        # Using default version of the processor
        name = client.processor_path(project_id, location, processor_id)

    print("Requesting...")
    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    # Start the batch process
    print("Processing...")
    operation = client.batch_process_documents(request)

    # Starting the operation
    try:
        print(f"Waiting for operation {operation.operation.name} to complete...")
        operation.result(timeout=timeout)

    # Catch exception when operation doesn't finish before timeout
    except (RetryError, InternalServerError) as e:
        print(e.message)
    
    # After the operation is complete,
    # get output document information from operation metadata
    metadata = documentai.BatchProcessMetadata(operation.metadata)

    if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")

    storage_client = storage.Client()

    print("Output files:")
    # One process per Input Document
    for process in list(metadata.individual_process_statuses):
        
        # output_gcs_destination format: gs://BUCKET/PREFIX/OPERATION_NUMBER/INPUT_FILE_NUMBER/
        # The Cloud Storage API requires the bucket name and URI prefix separately
        matches = re.match(r"gs://(.*?)/(.*)", process.output_gcs_destination)
        if not matches:
            print(
                "Could not parse output GCS destination:",
                process.output_gcs_destination,
            )
            continue

        # Store the bucket name and prefix
        output_bucket, output_prefix = matches.groups()

        # Get List of Document Objects from the Output Bucket
        output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

        # Document AI may output multiple JSON files per source file
        for blob in output_blobs:
            # Document AI should only output JSON files to GCS
            if blob.content_type != "application/json":
                print(
                    f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                )
                continue

            process_output(output_bucket, output_prefix)

def process_output(output_bucket, output_prefix):
    storage_client = storage.Client(output_bucket)
    docai = documentai.DocumentProcessorServiceClient()
    bucket = storage_client.bucket(output_bucket)

    # List all output JSON files
    blobs = list(storage_client.list_blobs(output_bucket, prefix=output_prefix))
    for blob in blobs:
        if not blob.name.endswith(".json"):
            continue  # Skip non-JSON files

        print(f"Fetching {blob.name}")
        document = documentai.Document.from_json(
            blob.download_as_bytes(),
            ignore_unknown_fields=True
        )

        # Extract form fields (labeled data) to only get the Key Value Pairs
        extracted_data = {}
        # Get all fields in the json
        for field in document.entities:
            confidence = round(field.confidence, 2)
            key = field.type.strip()
            if hasattr(field, 'normalized_value') and field.normalized_value:
                if "_tin_no" in field.type:
                    value = field.mention_text.strip()
                else:
                    value = field.normalized_value.text.strip()
            else: 
                value = field.mention_text.strip()

            extracted_data[key] = value
            # Included confidence, only average confidence are taken at final output
            extracted_data[f"{key}_confidence"] = confidence

        # for now only form 2307 are normalized, validated and handle missing fields
        if extracted_data["form_no"] == "2307":
            final_data = handle_data.handle_data(
                bucket=output_bucket,
                input_prefix=blob.name,
                extracted_data=extracted_data
            )
        else:
            final_data = extracted_data

        # Save extracted key-value pairs back to GCS
        output_blob_name = blob.name.replace(".json", "_finalized.json")
        text_blob = bucket.blob(output_blob_name)
        text_blob.upload_from_string(
            json.dumps(final_data, indent=2),
            content_type="application/json"
        )

        print(f"Extracted fields saved to: gs://{output_bucket}/{output_blob_name}")

# Just debugging purposes
def connect():
    print("You are connected to extractor_caller.py")

def detect_mime_type(filename):
    # Check what type of file it is
    if filename.endswith(".pdf"):
        return "application/pdf"
    elif filename.endswith(".png"):
        return "image/png"
    elif filename.endswith(".jpg", ".jpeg"):
        return "image/jpeg"
    else:
        return None

def main(mime_type, input):

    project_id = "medtax-ocr-prototype"               # Project ID

    # SOON TO ADD: CONDITION FOR WHICH PROCESSOR TO USE
    # EITHER INVOICE PARSER OR CUSTOM EXTRACTOR FOR 2307
    processor_id = "7e831835ff6703a"                  # This is the ID of Custom Extractor for Form 2307 
    processor_version_id = "420979daa7968661"         # For a specific version of the parser  
    location = "us"                                   # Processor location. For example: "us" or "eu".

    gcs_output_uri = f"gs://processed_output_bucket/processed_path/"                  # Path to the output
    gcs_input_uri = f"gs://run-sources-medtax-ocr-prototype-us-central1/{input}"    # Configure Input pathing.
    input_mime_type = mime_type

    # This is for whole folder process, Not necessary for now
    gcs_input_prefix = f"gs://run-sources-medtax-ocr-prototype-us-central1/{input}"
    
    print("Starting the process...")
    batch_process_documents(
        project_id=project_id,
        location=location,
        processor_id=processor_id,
        gcs_output_uri=gcs_output_uri,
        gcs_input_uri=gcs_input_uri,
        processor_version_id=processor_version_id,
        input_mime_type=input_mime_type,
        # gcs_input_prefix=gcs_input_prefix,
    )


if __name__ == '__main__':
    main("application/pdf", "2307 - BEA  SAMPLE (2).pdf")