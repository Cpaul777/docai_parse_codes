import math

# Calculates the table of 2307
def calculateTable(data: dict) -> dict:
    # Get the table
    tables = data["table_rows"]
    # Only process if the table exist
    if tables:
        table_length = len(tables)
        print("The length of the table is: ", table_length)

        # Get the Total row and create new key value pairs with net_amount, gross_amount and 
        # withheld_amount based on the calculated data
        for i, table in enumerate(tables):
            
            # Only get the first row with the subject Total in it
            # reason being the second Total row at the very last row doesnt have value from the sample documents
            # change this to ensure every Total row is extracted and calculated
            if "Total" in table["income_payment_subject"] and i != table_length - 1 and table.get("total_quarter") and table.get("tax_withheld_quarter"):
                # Get the value, remove the comma and default to 0 if theres no value. 
                # Parse to float
                tq = float(table.get("total_quarter", 0).replace(",", "") or 0)
                twq = float(table.get("tax_withheld_quarter", 0).replace(",", "") or 0)

                # Calculate the net_amount
                net_amount = tq - twq

                # Add the fields and their values to the document
                data['net_amount'] = round(net_amount, 2)
                data['gross_amount'] = round(tq, 2)
                data['withheld_amount'] = round(twq, 2)
                break

            # There are cases where the total_quarter and tax_withheld_quarter values are in the 
            # same row as the Money Payments text row, this is trying to catch that 
            elif "Money Payments" in table["income_payment_subject"] and (table.get("total_quarter") and table.get("tax_withheld_quarter")):
                tq = float(table.get("total_quarter", 0).replace(",", "") or 0)
                twq = float(table.get("tax_withheld_quarter", 0).replace(",", "") or 0)

                net_amount = tq - twq
                data['net_amount'] = round(net_amount, 2)
                data['gross_amount'] = round(tq, 2)
                data['withheld_amount'] = round(twq, 2)
                break
            else:
                print("Missing total Values when parsing for net_amount, gross_amount etc.")
        return data
    else:
        return data

# This calculates the service invoice tables
def calculateForServiceInvoice(data:dict):
    # Get the table
    table1 = data["Item_Table"]
    table2 = data["Item_Table_2"]
    print("Processing Item_Tables")

    # Only process if the tables exist
    if(table2 and table1):
        
        # Table 1 Values, default to 0 if theres no value, parse to float and remove comma
        amountNetAndGross = float(table1[0].get("Amount", 0).replace(",","") or 0)

        # Table 2 values, default to 0 if theres no value, parse to float and remove comma
        withheld_tax = float(table2[0].get("Less_Witholding_Tax", 0).replace(",", "") or 0)
        net_amount = float(table2[0].get("Total_Amount_Due", 0).replace(",","") or 0)

        # Calculate the tax rate, change this to 10, since the tax-rate is fixed to 10%
        tax_rate = (withheld_tax / amountNetAndGross) * 100

        # Add the fields and values to the documents
        data['gross_amount'] = round(amountNetAndGross, 2)
        data['withheld_amount'] = round(withheld_tax, 2)
        data['tax_rate'] = round(tax_rate, 2)
        data['net_receipt'] = round(amountNetAndGross, 2)
        data['net_amount'] = round(net_amount, 2)

        # Return the final data/document
        return data
    else:
        return data

# Used for testing
if __name__ == '__main__':
    from pprint import pprint
    data = { 
        "form_no": "2307",
        "form_title": "Certificate of Creditable Tax\nWithheld at Source",
        "from_date": "01-01-2025",
        "to_date": "01-30-2025",
        "payee_tin_no": "541-331-234-000",
        "payee_name": "JAO S. MA\u03a1\u039f\u03a5",
        "payee_registered_address": "",
        "zip_code_4A": "",
        "payee_foreign_address": "BACOOR, CAVITE",
        "payor_tin_no": "123-333-221-001",
        "payor_name": "HARMONY HOSPITAL",
        "payor_registered_address": "CANDELARIA QUEZON",
        "zip_code_8A": "4323",
        "confidence_average": "0.95",
        "table_rows": [
            {
            "income_payment_subject": "Rentals",
            "atc": "WC100",
            "first_month": "",
            "second_month": "",
            "third_month": "125,000.00",
            "total_quarter": "125,000.00",
            "tax_withheld_quarter": "6,250.00"
            },
            {
            "income_payment_subject": "Total",
            "atc": "",
            "first_month": "",
            "second_month": "",
            "third_month": "125,000.00",
            "total_quarter": "125,000.00",
            "tax_withheld_quarter": "1,250.00"
            },
            {
            "income_payment_subject": "Money Payments Subject to Withholding of",
            "atc": "",
            "first_month": "",
            "second_month": "",
            "third_month": "",
            "total_quarter": "",
            "tax_withheld_quarter": ""
            },
            {
            "income_payment_subject": "Business Tax (Government & Private)",
            "atc": "",
            "first_month": "",
            "second_month": "",
            "third_month": "",
            "total_quarter": "",
            "tax_withheld_quarter": ""
            },
            {
            "income_payment_subject": "Total",
            "atc": "",
            "first_month": "",
            "second_month": "",
            "third_month": "",
            "total_quarter": "",
            "tax_withheld_quarter": ""
            }
        ]
    }

    service_invoice_data = {
        "Invoice_No": "0266",
        "Date": "01/05/25 [INVALID]",
        "Business_Address": "141 Mindanao Ave proj 8",
        "Registered_Name": "Dr. Montano Ramos Gen Hospital",
        "Sold_To_Tin": "307-555-668-0001",
        "confidence_average": "1.0",
        "Item_Table": [
            {
            "Amount": "40000",
            "Item_Description_Nature_Of_Service": "Pr0fessi0na1 Fres 0aid t0 mesticat Practiti0neers"
            }
        ],
        "Item_Table_2": [
            {
            "Less_Witholding_Tax": "5000",
            "Total_Amount_Due": "45000"
            }
        ]
    }

    pprint(calculateTable(data))
    # pprint(calculateForServiceInvoice(service_invoice_data))
