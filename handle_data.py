from datetime import datetime
from google.cloud.storage import Client

import json


field_values = {
    "form_no": "2307",
    "form_title": "Certificate of Creditable Income Taxes Withheld at Source",
    "from_date": "",
    "to_date": "",
    "payee_tin_no": "",		
    "payee_name": "",
    "payee_registered_address": "",
    "zip_code_4A": "",
    "payee_foreign_address": "",
    "payor_tin_no": "",
    "payor_name": "",
    "payor_registered_address": "",
    "zip_code_8A": "",
}

gcs_bucket = "gs://practice_sample_training/"
input_prefix = "docai/process_path/16919130606771052652/0/2307 - BEA  SAMPLE (2)-0_extracted.json"
def handle_data(bucket, input_prefix):
    storage_client = storage.Client()
    bucket = storage_client.bucket()
    blob =  bucket.blob(input_prefix)

    """
    Process the output from Document AI and normalize, validate key-value pairs.
    
    Args:
        output_bucket (str): The GCS bucket where the output is stored.
        output_prefix (str): The prefix for the output files.
    """
    print(f"Processing data from bucket: {output_bucket} with prefix: {output_prefix}")

    if not output_bucket or not output_prefix:
        print("No output bucket or prefix provided.")
        return

    data = blob.download_as_text()
    

    try:
        print(data)
    except Exception as e:
        print(f"Error processing output: {e}")

def main():

    handle_data(gcs_bucket, input_prefix)

main()