from datetime import datetime
from dateutil import parser
import re
import json
# CAPTURE ENYE CHARACTER ñ LATER

# below is only used in __app__==__main__
gcs_bucket = "practice_sample_training"
input_prefix = "docai/14582948428165940265/0/DUMMY 3 - 2307 - ROBERT-0.json"

def handle_data(document):
    field_values = {
        "Invoice_No": "",
        "Date": "",
        "Business_Address": "",
        "Registered_Name": "",
        "Sold_To_Tin": "",
    }

    table_one_values = ["Amount",
                        "Item_Description_Nature_Of_Service",
                    ]
    
    table_two_values = ["Less_Witholding_Tax",
                        "Total_Amount_Due",
                    ]
    
    Item_Table = []
    Item_Table_2 = []
    
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
    for field in document.entities:
        # Taking table rows
        if field.type == "Item_Table":

            row_dict = {field_name: "" for field_name in table_one_values}
            
            for property in field.properties:
                property_type = property.type
                value = property.mention_text

                # Making Exception for only normalizing currency fields
                if property_type != "Item_Description_Nature_Of_Service":
                    value = norm_currency(value)
                
                if property_type in table_one_values:
                    row_dict[property_type] = value
                

            Item_Table.append(row_dict)

        elif field.type == "Item_Table_2":
            row_dict2 = {field_name: "" for field_name in table_two_values}

            for property in field.properties:
                property_type = property.type
                value = property.mention_text
                value = norm_currency(value)
                if property_type in table_two_values:
                        row_dict2[property_type] = value
            
            Item_Table_2.append(row_dict2)
        
        confidence = round(field.confidence, 2)
        key = field.type.strip()

        # Taking field values
        # normalized_value in the raw json are google AI suggested texts
        # Not safe for tin numbers and date
        if hasattr(field, 'normalized_value') and field.normalized_value:
            if "Invoice_No" in field.type or "Date" in field.type or "Sold_To_Tin" in field.type:
                value = field.mention_text.strip()
            else:
                value = field.normalized_value.text.strip()
        else:
            value = field.mention_text.strip()
        extracted_data[key] = value

        # Included confidence, only average confidence are taken of the final output
        extracted_data[f"{key}_confidence"] = confidence

    # Printed in the logs, for debugging purposes
    # print(json.dumps(Item_Table, indent=2))
    # print(json.dumps(Item_Table_2, indent=2))


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
                if "Date" in key:
                    # Normalize date fields
                    field_values[key] = norm_date(value)

                elif "Sold_To_Tin" in key:
                    # Normalize TIN fields
                    field_values[key] = norm_tin(value)

                elif "Invoice_No" in key:
                    # Normalize ZIP code fields
                    field_values[key] = norm_invoice_no(value)
                else: 
                    field_values[key] = value
            except ValueError as e:
                print(f"Error normalizing field '{key}': {e}")
                field_values[key] = ""
        else:
            field_values[key] = ""

    # For debugging purposes, printed at logs
    # print(json.dumps(field_values, indent=2))
    
    # Get the confidence average (Currently only for field values not tables)
    for key in data.keys():
        if "_confidence" in key:
            confidence += float(data.get(key, 0))
            count += 1
    if count != 0:
        confidence /= count

    field_values["confidence_average"] = str(round(confidence, 2))
    try:
        # Adding table_row key to the field_values and its value is the table rows
        return {**field_values, "Item_Table": Item_Table, "Item_Table_2": Item_Table_2}
    except Exception as e:
        print(f"Error processing output: {e}")

def norm_currency(currency):
    """
    Normalize currency received
    
    Args:
        The amount/number
    
    Returns:
        str: The normalized currency in string in format.
    """
    mapping = {"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "p":"0"}
    for k, v in mapping.items():
        currency = currency.replace(k, v)
    
    cleaned = re.sub(r"[^0-9.,-]", "", currency) #Removes non number values
    return currency

def norm_tin(num):
    """
    Normalize TIN (Tax Identification Number) strings to a standard format.
    
    What counts as valid: 
        9 digits, and 12 digits

    Args:
        num (str): The TIN string to normalize.
    
    Returns:
        str: The normalized TIN string in a 9-13 digit format.
    """
    mapping = {"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "p":"0"}
    for k, v in mapping.items():
        num = num.replace(k, v)
    
    num = ''.join(filter(str.isdigit, num))  # Remove non-numeric characters
    if len(num) == 9:
        num = f"{num[:3]}-{num[3:6]}-{num[6:]}"  # Format XXX-XXX-XXX
    elif len(num) > 9 and len(num) < 15:
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
        str: The normalized date string in 'MM-DD-YYYY' format.
    """

    date_format = "%m-%d-%Y"  # MM-DD-YYYY
    date = "".join(filter(str.isdigit, date_str))  # Remove non-numeric characters
    print("Normalizing Date filtered the digits ",date)
    # Handles 3-1-2025, 03-1-2025, 03-01-2025, 312025  
    if(len(date) < 6 or  len(date) > 8):
        print("Early return: ", date)
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
    print("Month: ",month, " Day: ", day, " Year: ", year)
    
    # Handles years that only has the last 2 digits
    if (len(year) == 2 and (f"20{year}" == str(datetime.now().year))):
        print("The length of date is 2")
        year = f"20{year}"

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

def norm_invoice_no(invoice_no):
    """
    Normalize invoice number by filtering and mapping what isnt a digit

    Args:
        invoice_no (str): The invoice number to normalize

    Returns:
        invoice_no (str): Normalized value of invoice number.
    """
    mapping = {"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "p":"0"}
    for k, v in mapping.items():
        invoice_no = invoice_no.replace(k, v)
    invoice_no = "".join(filter(str.isdigit, invoice_no))
    return invoice_no
def main():
    #   UNUSED
    # for testing purposes
    handle_data(document=None)
    return 0

if __name__ == '__main__':
    main()