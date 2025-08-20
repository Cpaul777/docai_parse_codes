
def calculate(data: dict) -> dict:
    tables = data["table_rows"]

    table_length = len(tables)
    print("The length of the table is: ", table_length)

    # Get the Total row and create new key value pairs with net_amount, gross_amount and withheld_amount
    # Based on the calculated data
    for i, table in enumerate(tables):
        if "Total" in table["income_payment_subject"] and i != table_length - 1:
            tq = float(table.get("total_quarter", 0).replace(",", "") or 0)
            twq = float(table.get("tax_withheld_quarter", 0).replace(",", "") or 0)

            net_amount = tq - twq
            data['net_amount'] = f"{net_amount:,.2f}"
            data['gross_amount'] = f"{tq:,.2f}"
            data['withheld_amount'] = f"{twq:,.2f}"
            break

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

    pprint(calculate(data))