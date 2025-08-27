from datetime import datetime
from dateutil import parser

def quarter(data: dict) -> dict:
    if data.get("to_date"):
        dateToCompare = parser.parse(str(data.get("to_date")))
        print(dateToCompare)

        month = int(dateToCompare.month)
        print("The month is", month)

        if(month >= 1 and month <= 3):
            data['quarter'] = "1st Quarter"
        elif(month >= 4 and month <= 6):
            data['quarter'] = "2nd Quarter"
        elif(month >= 7 and month <= 9):
            data['quarter'] = "3rd Quarter"
        elif(month >= 10 and month <= 12):
            data['quarter'] = "4th Quarter"
        else:
            data['quarter'] = ""
        
        return data
    else:
        print("No date available to parse")
        return data


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

    pprint(quarter(data))

