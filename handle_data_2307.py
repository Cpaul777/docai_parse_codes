from datetime import datetime
from google.cloud import storage
from dateutil import parser
from google.cloud import documentai
import json

# CAPTURE ENYE CHARACTER ñ LATER

# below is only used in __app__==__main__
gcs_bucket = "practice_sample_training"
input_prefix = "docai/14582948428165940265/0/DUMMY 3 - 2307 - ROBERT-0.json"

def handle_data(document):
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
    
    table_values = ["income_payment_subject",
                    "atc",
                    "first_month",
                    "second_month",
                    "third_month",
                    "total_quarter",
                    "tax_withheld_quarter",]
    table_rows = []
    
    """ 
    # FOR TESTING PURPOSES
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcs_bucket)
    blob = bucket.blob(input_prefix)
    
    document = documentai.Document.from_json(
                blob.download_as_bytes(),
                ignore_unknown_fields=True
            )
    """
    # Extract form fields (labeled data) to only get the Key Value Pairs from raw json
    extracted_data = {}

    # Get all fields in the json
    # Adjustable for performance when looping through entities
    for field in document.entities:
        # Taking table rows
        if field.type == "details_monthly_income_payment_taxes":
            row_dict = {field_name: "" for field_name in table_values}

            for property in field.properties:
                property_type = property.type
                value = property.mention_text
                if property_type in table_values:
                    row_dict[property_type] = value

            table_rows.append(row_dict)

        confidence = round(field.confidence, 2)
        key = field.type.strip()

        # Taking field values
        if hasattr(field, 'normalized_value') and field.normalized_value:
            if "_tin_no" in field.type or "_date" in field.type:
                value = field.mention_text.strip()
            else:
                value = field.normalized_value.text.strip()
        else:
            value = field.mention_text.strip()
        extracted_data[key] = value

        # Included confidence, only average confidence are taken at final output
        extracted_data[f"{key}_confidence"] = confidence

    print(json.dumps(table_rows, indent=2))
    
    # UNUSED | TESTING PURPOSES
    # test_data = blob.download_as_string()

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
        else:
            field_values[key] = ""

    print(json.dumps(field_values, indent=2))

    # Validate the date range
    try:
        if not validate_date_range(field_values["from_date"], field_values["to_date"]):
            raise ValueError("Validatiing date Failed")
        
    except ValueError as e:
        print("Caught an Error: ", e)
    
    # Get the confidence average (This is only for field values)
    for key in data.keys():
        if "_confidence" in key:
            confidence += float(data.get(key, 0))
            count += 1
    if count != 0:
        confidence /= count

    field_values["confidence_average"] = str(round(confidence, 2))
    try:
        return {**field_values, "table_rows": table_rows}
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
    elif len(num) > 9 and len(num) < 13:
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
    date_format = "%m-%d-%Y"  # MM-DD-YYYY
    date = "".join(filter(str.isdigit, date_str))  # Remove non-numeric characters

    if(len(date) < 6 or  len(date) > 8):
        return f"{date} [INVALID]"
    year = date[-4:]
    mmdd = date[:-4]
    if len(mmdd) == 4:
        month = mmdd[:2]
        day = mmdd[2:]
    elif len(mmdd) == 3:
        month = mmdd[:1]
        day = mmdd[1:]
    elif len(mmdd) == 2:
        month = mmdd[:1]
        day = mmdd[1:]
    else:
        raise ValueError(f"Cannot infer MM/DD from: '{date_str}'")

    # Fill and validate
    try:
        dt = datetime.strptime(f"{month.zfill(2)}-{day.zfill(2)}-{year}", date_format)
    except ValueError:
        try:
            m2 = mmdd[:2]
            d2 = mmdd[2:]
            dt = datetime.strptime(f"{m2.zfill(2)}-{d2.zfill(2)}-{year}", date_format)
            return dt.strftime(date_format)
        except ValueError:
            return f"{date_str} [INVALID]"
    return dt.strftime(date_format)

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
    #   UNUSED
    # for testing purposes
    handle_data(document=None)
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