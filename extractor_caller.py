from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import RetryError
from google.cloud import documentai
from google.cloud import storage
from image_extract import clean_img, upload_pdf_gcs
from typing import Optional
import re
import json
import handle_data_2307
from google.protobuf import field_mask_pb2

def batch_process_documents(
    userId: str,
    doc_type: str,
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
        gcs_uri=gcs_output_uri, field_mask=field_mask,  
        sharding_config=documentai.DocumentOutputConfig.GcsOutputConfig.ShardingConfig(
            pages_per_shard=1
        )
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

    print("Output files:")
    # One process per Input Document
    for process in list(metadata.individual_process_statuses):
        # The list for uploading the pdf pages 
        pdf_list = []

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
        
        storage_client = storage.Client(output_bucket)

        # Get List of Document Objects from the Output Bucket
        output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

        bucket = storage_client.bucket(output_bucket)

        # Document AI may output multiple JSON files per source file
        for blob in output_blobs:
            # Document AI should only output JSON files to GCS
            if blob.content_type != "application/json":
                print(
                    f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                )
                continue
            if blob.name.endswith("_finalized.json"):
                continue
            process_output(blob, bucket, userId, doc_type)
            pdf_list.append(clean_img(blob))
        print("Stitching pdf")
        upload_pdf_gcs(blob.name, userId, pdf_list)
            

# Process the output 
def process_output(blob, bucket, userId, doc_type):
    
    print("Whats the userId: ", userId)

    print(f"Fetching {blob.name}")
    document = documentai.Document.from_json(
        blob.download_as_bytes(),
        ignore_unknown_fields=True
    )

    # Extracted data is now handled by handle_data_2307.handle_data
    final_data = handle_data_2307.handle_data(document)

    # Save extracted key-value pairs back to GCS
    output_blob_name = blob.name.replace(".json", "_finalized.json")
    text_blob = bucket.blob(output_blob_name)
    text_blob.metadata = {
        "userid" : userId,
        "doc-type" : doc_type,
    }

    text_blob.upload_from_string(
        json.dumps(final_data, indent=2),
        content_type="application/json"
    )

    print(f"Extracted fields saved to: gs://{bucket}/{output_blob_name}")

# Detect the file type
def detect_mime_type(filename):
    # Check what type of file it is
    if filename.endswith(".pdf"):
        return "application/pdf"
    elif filename.endswith(".png"):
        return "image/png"
    elif filename.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    else:
        return None

def main(mime_type, input, userId, doc_type):
    
    # SOON TO ADD: CONDITION FOR WHICH PROCESSOR TO USE
    # EITHER INVOICE PARSER OR CUSTOM EXTRACTOR FOR 2307
    # OR MAYBE JUST SEPARATE PYTHON FILES
    
    # Project ID
    project_id = "medtax-ocr-prototype"               

     # This is the ID of custom_processor_2307 processor
    processor_id = "c1792eca909556ee"      
    
    # For a specific version of the parser
    # If not included in the argument, the default version will be used
    processor_version_id = "6d9f64e0bc83f261"         

    # Processor location. For example: "us" or "eu".
    location = "us"        
   
    # Path to the output
    gcs_output_uri = f"gs://processed_output_bucket/processed_path/{userId}"
    
    # Configure Input pathing.
    gcs_input_uri = f"gs://run-sources-medtax-ocr-prototype-us-central1/{input}"    
    
    # Set the input mime type
    input_mime_type = mime_type
   
    # Field mask specifies which data to get from json so it doesnt load everything
    field_mask = "entities,pages.image,pages.blocks"
    
    """
    # For testing purposes without going through the whole trigger-function
    # hardcoded getting the document and processing it 

    gcs_output_uri = f"gs://practice_sample_training/results/"                  
    gcs_input_uri = f"gs://practice_sample_training/BRO WAHAPEN TO YOU.jpg"
    input_mime_type = "image/jpeg"
    """
    # This is for whole folder process
    gcs_input_prefix = f"gs://run-sources-medtax-ocr-prototype-us-central1/{input}"
    
    print("Starting the process...")

    # Commented arguments can be uncommented if you want to:
    # Specify a processor version
    # Batch upload using prefix
    # Add a field mask (include what will be extracted on the json result of Document AI) 
    # e.g. "page.image", "entities.properties", "entities.type" etc. Good for optimization
    batch_process_documents(
        userId=userId,
        doc_type=doc_type,
        project_id=project_id,
        location=location,
        processor_id=processor_id,
        gcs_output_uri=gcs_output_uri,
        gcs_input_uri=gcs_input_uri,
        # processor_version_id=processor_version_id,
        input_mime_type=input_mime_type,
        # gcs_input_prefix=gcs_input_prefix,
        field_mask=field_mask,
    )

if __name__ == '__main__':
    main("application/pdf", "2307 - BEA  SAMPLE (5).pdf", userId="sample", doc_type="form2307")