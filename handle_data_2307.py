from datetime import datetime
from dateutil import parser
import json

# Example bucket & input path (only used in __main__ test runs)
gcs_bucket = "practice_sample_training"
input_prefix = "docai/14582948428165940265/0/DUMMY 3 - 2307 - ROBERT-0.json"

def handle_data(document):
    """
    Main handler for extracting and normalizing field values
    from a Document AI `document` object for BIR Form 2307.

    Steps:
    - Define initial expected fields (field_values dict).
    - Loop through document.entities to extract values and confidence scores.
    - Build table rows from monthly income/tax fields.
    - Normalize values (TIN, ZIP, Dates).
    - Validate date ranges.
    - Compute average confidence.
    - Return a merged dictionary with field values and table_rows.
    """
    
    # Initialize expected fields with defaults
    field_values = {
        "form_no": "2307",
        "form_title": "Certificate of Creditable Income Taxes Withheld at Source",
        "from_date": "",
        "to_date": "",
        "payee_tin_no": 0,
        "payee_name": "",
        "payee_registered_address": "",
        "zip_code_4A": "",
        "payee_foreign_address": "",
        "payor_tin_no": 0,
        "payor_name": "",
        "payor_registered_address": "",
        "zip_code_8A": "",
        "confidence_average" : 0,
    }
    
    # Expected fields inside the monthly income/tax details table
    table_values = ["income_payment_subject",
                    "atc",
                    "first_month",
                    "second_month",
                    "third_month",
                    "total_quarter",
                    "tax_withheld_quarter",]
    table_rows = []
    
    # Stores raw key-value extractions
    extracted_data = {}

    # Extract form fields and tables
    for field in document.entities:

        # If entity is part of the income/taxes table
        if field.type == "details_monthly_income_payment_taxes":
            # Initialize empty row with all table columns
            row_dict = {field_name: "" for field_name in table_values}

            # Fill row values from properties
            for property in field.properties:
                property_type = property.type
                value = property.mention_text
                if property_type in table_values:
                    row_dict[property_type] = value

            # Append row to table_rows list
            table_rows.append(row_dict)

        # Capture confidence score for this entity
        confidence = round(field.confidence, 2)
        key = field.type.strip()

        # Extract field value
        # Prefer normalized_value if available, except for sensitive fields (TIN, dates)
        if hasattr(field, 'normalized_value') and field.normalized_value:
            if "_tin_no" in field.type or "_date" in field.type:
                value = field.mention_text.strip()
            else:
                value = field.normalized_value.text.strip()
        else:
            value = field.mention_text.strip()
        extracted_data[key] = value

        # Store per-field confidence score
        extracted_data[f"{key}_confidence"] = confidence

    # Printed in the logs, for debugging purposes
    # print(json.dumps(table_rows, indent=2))

    # Normalize and validate fields
    data = extracted_data
    count = 0
    confidence = 0
    
    # Normalizing and validating the extracted data
    # Left as blank if missing 
    # Invalid values are concatenated with [INVALID]
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
            # If missing, leave blank
            field_values[key] = ""

    # For debugging purposes, printed at logs
    # print(json.dumps(field_values, indent=2))

    # Validate the date range
    if field_values["from_date"] and field_values["to_date"]:
        try:
            if not validate_date_range(field_values["from_date"], field_values["to_date"]):
                raise ValueError("Validatiing date Failed")
        except ValueError as e:
            print("Caught an Error: ", e)
    
    # Get the confidence average (Currently only for field values not tables)
    for key in data.keys():
        if "_confidence" in key:
            confidence += float(data.get(key, 0))
            count += 1
    if count != 0:
        confidence /= count
    
    field_values["confidence_average"] = round(confidence, 2)
    
    try:
        # Adding table_row key to the field_values and its value is the table rows
        extracted_data.clear()
        return {**field_values, "table_rows": table_rows}
    except Exception as e:
        print(f"Error processing output: {e}")

def norm_zip_code(zip_code):
    """
     Normalize ZIP code strings to a standard 4-digit format.
    - Replace common OCR misreads (O→0, I→1, S→5, etc.)
    - Keep only digits
    - If not 4 digits, append [INVALID]
    
    Args:
        zip_code (str): The ZIP code string to normalize.
    
    Returns:
        str: The normalized ZIP code string in 'XXXX' format.
    """
    mapping = {"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "p":"0"}
    for k, v in mapping.items():
        zip_code = zip_code.replace(k, v)
        
    zip_code = ''.join(filter(str.isdigit, zip_code))  # Remove non-numeric characters
    if len(zip_code) == 4:
        return zip_code
    else:
        return (zip_code + " [INVALID]")

def norm_tin(num):
    """
    Normalize TIN (Tax Identification Number).
    - Replace OCR misreads.
    - Keep only digits.
    - Currently returns as integer.
    Args:
        num (str): The TIN string to normalize.
    
    Returns:
        int: The normalized TIN.
    """
    
    mapping = {"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "p":"0"}
    for k, v in mapping.items():
        num = num.replace(k, v)

    num = ''.join(filter(str.isdigit, num))  # Remove non-numeric characters
    return int(num)

def norm_date(date_str):
    
    """
    Normalize date strings to 'MM-DD-YYYY' format.
    - Replaces common OCR misreads.
    - Extracts year (last 4 digits) and infers month/day from remaining part.
    - Attempts multiple parsing strategies if first fails.
    - Returns [INVALID] if cannot parse.
    Args:
        date_str (str): The date string to normalize.
    
    Returns:
        str: The normalized date string in 'MM-DD-YYYY' format.
    """
    mapping = {"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "p":"0"}
    for k, v in mapping.items():
        date_str = date_str.replace(k, v)
    
    date_format = "%m-%d-%Y"  # MM-DD-YYYY
    date = "".join(filter(str.isdigit, date_str))  # Remove non-numeric characters

    # Handles 3-1-2025, 03-1-2025, 03-01-2025, 312025  
    if(len(date) < 6 or  len(date) > 8):
        return f"{date} [INVALID]"
    
    year = date[-4:]
    mmdd = date[:-4]
    
    # Infer month/day from remaining digits
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

    # Validate Date
    try:
        dt = datetime.strptime(f"{month.zfill(2)}-{day.zfill(2)}-{year}", date_format)
    except ValueError:
        # Try alternate parsing if above fails
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
    Validate that from_date is earlier than or equal to to_date.
    Uses dateutil.parser for flexible parsing.
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
    """
    Test harness (currently unusable).
    Calls handle_data with None for quick testing.
    """
    handle_data(document=None)
    return 0

if __name__ == '__main__':
    main()
