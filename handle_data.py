from datetime import datetime
from google.cloud import storage
from dateutil import parser
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

gcs_bucket = "practice_sample_training"
input_prefix = "docai/process_path/16919130606771052652/0/2307 - BEA  SAMPLE (2)-0_extracted.json"

def handle_data(bucket, input_prefix):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)
    blob =  bucket.blob(input_prefix)

    """
    Process the output from Document AI and normalize, validate key-value pairs.
    
    Args:
        output_bucket (str): The GCS bucket where the output is stored.
        output_prefix (str): The prefix for the output files.
    """
    print(f"Processing data from bucket: {bucket} with prefix: {input_prefix}")

    if not bucket or not input_prefix:
        print("No output bucket or prefix provided.")
        return
    
    data = blob.download_as_text()
    
    json_data = json.loads(data)

    for key in field_values.keys():
        if key in json_data:
            value = json_data[key]
            
            if "_date" in key:
                # Normalize date fields
                field_values[key] = norm_date(value)
            if "tin_no" in key:
                # Normalize TIN fields
                field_values[key] = norm_tin(value)
            if "zip_code" in key:
                # Normalize ZIP code fields
                field_values[key] = norm_zip_code(value)
            else: 
                field_values[key] = value
    
    if not validate_date_range(field_values["from_date"], field_values["to_date"]):
        print("Invalid date")
        return

    try:
        print(json.dumps(field_values, indent=4))
    except Exception as e:
        print(f"Error processing output: {e}")

def norm_zip_code(zip_code):
    """
    Normalize ZIP code strings to a standard 4-digit format.
    
    Args:
        zip_code (str): The ZIP code string to normalize.
    
    Returns:
        str: The normalized ZIP code string in 'XXXX' format.
    """
    zip_code = ''.join(filter(str.isdigit, zip_code))  # Remove non-numeric characters
    if len(zip_code) == 4:
        return zip_code
    elif len(zip_code) == 5:
        return zip_code[:4]  # Return first 4 digits
    else:
        raise ValueError(f"Error normalizing ZIP code: Invalid length ({len(zip_code)}) digits")

def norm_tin(num):
    """
    Normalize TIN (Tax Identification Number) strings to a standard format.
    
    Args:
        num (str): The TIN string to normalize.
    
    Returns:
        str: The normalized TIN string in a 9-12 digit format.
    """
    num = ''.join(filter(str.isdigit, num))  # Remove non-numeric characters
    if len(num) == 12:
        num = f"{num[:3]}-{num[3:6]}-{num[6:9]}-{num[9:]}" # Format as XXX-XX-XXXX-XXX
    elif len(num) == 9:
        num = f"{num[:3]}-{num[3:6]}-{num[6:]}"  # Format as XXX-XX-XXXX
    else:
        raise ValueError(f"Error normalizing TIN: Invalid length ({len(num)}) digits")

def norm_date(date_str):
    """
    Normalize date strings to a standard format.
    
    Args:
        date_str (str): The date string to normalize.
    
    Returns:
        str: The normalized date string in 'YYYY-MM-DD' format.
    """

    date_format = "%Y-%m-%d" #Changeable
    
    if not date_str:
        return ""

    try:
        parsed_date = parser.parse(date_str, fuzzy=True)
        return parsed_date.strftime(date_format)
    
    except Exception:
        print(f"Invalid date format: {date_str}")
        return ""

def validate_date_range(from_date_str, to_date_str):
    """
    Validates that 'from_date' is not more recent than 'to_date'.

    Args:
        from_date_str (str): Date string for the 'From' field (e.g., '2025-01-01')
        to_date_str (str): Date string for the 'To' field (e.g., '2025-03-31')

    Returns:
        bool: True if valid, False if invalid.
    """
    try:
        from_date = parser.parse(from_date_str)
        to_date = parser.parse(to_date_str)
        return from_date <= to_date
    except Exception as e:
        print(f"[Date Validation Error] {e}")
        return False


def main():
    handle_data(gcs_bucket, input_prefix)

main()