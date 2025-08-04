from datetime import datetime
from google.cloud import storage
from dateutil import parser

# Expected KVPs for Form 2307
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
    "confidence_average" : "0.0",
}

# UNUSED
gcs_bucket = "practice_sample_training"
input_prefix = "docai/process_path/16919130606771052652/0/2307 - BEA  SAMPLE (2)-0_extracted.json"

def handle_data(extracted_data: dict):

    # FOR TESTING PURPOSES
    # storage_client = storage.Client()
    # bucket = storage_client.bucket(gcs_bucket)
    # blob = bucket.blob(input_prefix)
    
    
    """
    Process the output from Document AI and normalize, validate key-value pairs.
    
    Args:
        output_bucket (str): The GCS bucket where the output is stored.
        output_prefix (str): The prefix for the output files.
    """
    
    # UNUSED | TESTING PURPOSES
    # test_data = blob.download_as_string()

    print("Validating and normalizing data")
    data = extracted_data
    count = 0
    confidence = 0
    
    for key in field_values.keys():
        if key in data:
            value = data.get(key)
            if value is None:
                continue
            try:
                if "_date" in key:
                    # Normalize date fields
                    field_values[key] = norm_date(value)

                elif "tin_no" in key:
                    # Normalize TIN fields
                    field_values[key] = norm_tin(value)

                elif "zip_code" in key:
                    # Normalize ZIP code fields
                    field_values[key] = norm_zip_code(value)
                else: 
                    field_values[key] = value
            except ValueError as e:
                print(f"Error normalizing field '{key}': {e}")
                field_values[key] = ""
    
    # Validate the date range
    try:
        if not validate_date_range(field_values["from_date"], field_values["to_date"]):
            raise ValueError("Invalid date range: 'from_date' is more recent than 'to_date'.")
    except ValueError as e:
        print("Caught an Error: ", e)
    
    # Get the confidence average
    for key in data.keys():
        if "_confidence" in key:
            confidence += float(data.get(key, 0))
            count += 1
    if count != 0:
        confidence /= count
    
    field_values["confidence_average"] = str(confidence)
    
    try:
        return field_values
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
    else:
        return (zip_code + " [INVALID]")

def norm_tin(num):
    """
    Normalize TIN (Tax Identification Number) strings to a standard format.
    
    Args:
        num (str): The TIN string to normalize.
    
    Returns:
        str: The normalized TIN string in a 9-13 digit format.
    """
    num = ''.join(filter(str.isdigit, num))  # Remove non-numeric characters
    if len(num) == 9:
        num = f"{num[:3]}-{num[3:6]}-{num[6:]}"  # Format XXX-XXX-XXX
    elif len(num) > 9 and len(num) <= 13:
        num = f"{num[:3]}-{num[3:6]}-{num[6:9]}-{num[9:]}" # Format XXX-XXX-XXX-XXXX
    else:
        num = f"{num[:3]}-{num[3:6]}-{num[6:9]}-{num[9:]} [INVALID]"

    return num

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
        return f"{date_str} [INVALID]"

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
    #               UNUSED
    # for testing purposes
    # handle_data(gcs_bucket, input_prefix, field_values)
    return 0

#                   UNUSED MIGHT USE LATER FOR TESTING PURPOSES
# def upload(bucket_name, file_source, data):
#     """
#     This function uploads the handled data after validation and normalization to the specified GCS bucket.

#     Args:
#         bucket (str): The GCS bucket where the output will be uploaded.
#         file_source (str): The path to the output file to be uploaded.
#         data (dict): The data to be uploaded.
#     """

#     storage_client = storage.Client()
#     bucket = storage_client.bucket(bucket_name)
#     blob = bucket.blob(file_source)

#     try:
#         # Convert data to JSON and write to file
#         blob.upload_from_filename(file_source)
#         print(f"File {file_source} uploaded to {bucket.name}.")
#     except Exception as e:
#         print(f"Error uploading file: {e}")


if __name__ == '__main__':
    main()