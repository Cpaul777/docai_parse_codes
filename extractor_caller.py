from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import RetryError
from google.cloud import documentai
from google.cloud import storage

from typing import Optional
import re
import json
import time
import os
import preprocess


# Project ID
project_id = "medtax-ocr-prototype"

# Processor ID as hexadecimal characters.
# Not to be confused with the Processor Display Name.

processor_id = "7e831835ff6703a" #This is the invoice parser id (default) 


# Optional for specific version. Example: pretrained-ocr-v1.0-2020-09-23
processor_version_id = "420979daa7968661" #For specific version of parser  

# Processor location. For example: "us" or "eu".
location = "us"

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
        # The full resource name of the processor, e.g.:
        # projects/{project_id}/locations/{location}/processors/{processor_id}
        name = client.processor_path(project_id, location, processor_id)

    print("Requesting...")
    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    # BatchProcess returns a Long Running Operation (LRO)
    print("Processing...")
    operation = client.batch_process_documents(request)

    # Continually polls the operation until it is complete.
    # This could take some time for larger files
    # Format: projects/{project_id}/locations/{location}/operations/{operation_id}
    try:
        print(f"Waiting for operation {operation.operation.name} to complete...")
        operation.result(timeout=timeout)
    # Catch exception when operation doesn't finish before timeout
    except (RetryError, InternalServerError) as e:
        print(e.message)

    # It seems that asynchronous is also possible, something about waiting and not waiting. Might be a key info later
    
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

        # Extract form fields (labeled data)
        # Adjustable for values with low confidence to just get the mention text or normalizedText
        # 

        extracted_data = {}
        for field in document.entities:
            confidence = round(field.confidence, 2)
            key = field.type.strip()
            if hasattr(field, 'normalized_value') and field.normalized_value:
                value = field.normalized_value.text.strip()
            else: 
                value = field.mention_text.strip()

            extracted_data[key] = value
            extracted_data[f"{key}_confidence"] = confidence

        # Save extracted key-value pairs back to GCS
        output_blob_name = blob.name.replace(".json", "_extracted.json")
        text_blob = bucket.blob(output_blob_name)
        text_blob.upload_from_string(
            json.dumps(extracted_data, indent=2),
            content_type="application/json"
        )
        print(f"Extracted fields saved to: gs://{output_bucket}/{output_blob_name}")

def main():

    # #Preprocess part
    # input = preprocess.main()

    print("Starting the process...")

    # Path to the output
    gcs_output_uri = "gs://practice_sample_training/docai/process_path/"

    # Configure Input pathing.
    gcs_input_uri = "gs://practice_sample_training/training_sample/form_2307_intern/2307 - BEA  SAMPLE (2).pdf"

    input_mime_type ="application/pdf"

    #This is for whole folder process 
    gcs_input_prefix = "gs://practice_sample_training/form_2307_intern/"

    batch_process_documents(
        project_id=project_id,
        location=location,
        processor_id=processor_id,
        gcs_output_uri=gcs_output_uri,
        gcs_input_uri=gcs_input_uri,
        processor_version_id=processor_version_id,
        input_mime_type=input_mime_type,
        gcs_input_prefix=gcs_input_prefix,
    )

main()