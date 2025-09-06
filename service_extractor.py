# Google API exceptions for handling operation errors
from google.api_core.exceptions import InternalServerError
from google.api_core.exceptions import RetryError

# Google Cloud libraries for Document AI and Storage
from google.cloud import documentai
from google.cloud import storage

# Import image processing helpers
from image_extract import clean_img, upload_pdf_gcs

# Type hints
from typing import Optional

# Regex, JSON utils
import re
import json

# Handler for extracted service invoice data
import service_invoice_data_handler

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
    """
    - Sends document(s) to the processor
    - Waits for processing results
    - Reads back the generated JSON files from GCS
    - Extracts fields and cleaned images
    - Stitches pages into a PDF and uploads back to GCS

    This function is mostly from the documentation sample code with some modifications
    link to the documentation: https://cloud.google.com/document-ai/docs/send-request#batch-process
    """
    
    print("Connecting with the client...")
    client = documentai.DocumentProcessorServiceClient()

    # CONFIGURE INPUT DOCUMENTS
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

    # CONFIGURE OUTPUT LOCATION
    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=gcs_output_uri, field_mask=field_mask,  
        sharding_config=documentai.DocumentOutputConfig.GcsOutputConfig.ShardingConfig(
            pages_per_shard=1
        )
    )

    # Wrap config into DocumentOutputConfig
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

    # BUILD REQUEST AND PROCESS
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
    
    # Process output metadata
    metadata = documentai.BatchProcessMetadata(operation.metadata)
    # Check if process succeeded
    if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")

    print("Output files:")
    
    # Loop through processed documents
    
    # One process per Input Document
    for process in list(metadata.individual_process_statuses):
         # Collect processed image pages into a list 
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
       
        # Initialize storage client
        storage_client = storage.Client(output_bucket)

        # Get List of Document Objects from the Output Bucket
        output_blobs = storage_client.list_blobs(output_bucket, prefix=output_prefix)

        # Access the bucket
        bucket = storage_client.bucket(output_bucket)

        # Document AI may output multiple JSON files per source file
        
        # Loop through all output JSON Files
        for blob in output_blobs:
            # Document AI should only output JSON files to GCS
            if blob.content_type != "application/json":
                print(
                    f"Skipping non-supported file: {blob.name} - Mimetype: {blob.content_type}"
                )
                continue
            # Skip already processed finalized JSONs
            if blob.name.endswith("_finalized.json"):
                continue
            # Process output JSON (extract fields + save finalized.json)
            process_output(blob, bucket, userId, doc_type)
            
            # Clean image from blob and add to page list
            pdf_list.append(clean_img(blob=blob))
    
        # After processing all blobs for one input doc, stitch into PDF
        print("Stitching pdf")
        upload_pdf_gcs(blob.name, doc_type, pdf_list)
            
# Process the output 
def process_output(blob, bucket, userId, doc_type):
    """
    Processes a single Document AI JSON shard:
    - Loads JSON into Document object
    - Extracts entities/fields with data handler
    - Writes extracted fields into a new *_finalized.json in GCS
    """

    print(f"Fetching {blob.name}")
    document = documentai.Document.from_json(
        blob.download_as_bytes(),
        ignore_unknown_fields=True
    )

    # Call handler for service_invoice data extraction
    final_data = service_invoice_data_handler.handle_data(document)

     # Save results as a new finalized JSON file
    output_blob_name = blob.name.replace(".json", "_finalized.json")
    text_blob = bucket.blob(output_blob_name)
    # Attach metadata for traceability
    text_blob.metadata = {
        "userid" : userId,
        "docType" : doc_type,
    }

    # Upload JSON string with extracted fields
    text_blob.upload_from_string(
        json.dumps(final_data, indent=2),
        content_type="application/json"
    )

    print(f"Extracted fields saved to: gs://{bucket.name}/{output_blob_name}")


def main(mime_type, bucket, input, userId, doc_type):
    """
    Entrypoint for running document extraction.
    - Configures project, processor, paths
    - Calls batch_process_documents
    """
    
    print(mime_type)
    print("The input location is " , input)
    print(bucket)

    # Project ID
    project_id = "medtax-ocr-prototype"               

     # Service Invoice Parser processor ID
    processor_id = "100eafc3a81f4960"      
    
    # For a specific version of the parser
    # If not included in the argument, the default version will be used
    processor_version_id = "6d9f64e0bc83f261"         

    # Processor location. For example: "us" or "eu". 
    location = "us"        
    
    # Path to the output
    gcs_output_uri = f"gs://processed_output_bucket/processed_path/{doc_type}"
    
    # Path to input document (single file)
    gcs_input_uri = f"gs://{bucket}/{input}"    

    # MIME type of input file
    input_mime_type = mime_type
    
    # Field mask specifies which data to get from json so it doesnt load everything
    # This Field mask only extract entities, images, blocks (reduces payload size)
    field_mask = "entities,pages.image,pages.blocks"
    
    # For testing purposes without going through the whole trigger-function
    # hardcoded getting the document and processing it 
    """
    gcs_output_uri = f"gs://practice_sample_training/{doc_type}_tests"                 
    gcs_input_uri = f"gs://{bucket}/{input}"
    input_mime_type = mime_type
    """
    print(gcs_output_uri)
    print(gcs_input_uri)
   
    # Alternative for processing an entire folder instead of single file
    gcs_input_prefix = f"gs://{bucket}/{input}"
    
    print("Starting the process...")

    # Commented arguments can be uncommented if you want to:
    # Specify a processor version
    # Batch upload using prefix
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

# LOCAL TESTING
if __name__ == '__main__':
    main("image/jpeg", "run-sources-medtax-ocr-prototype-us-central1","service_invoice/arayyy moo _25.jpg", userId="sample", doc_type="service_invoice")
