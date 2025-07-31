from google.cloud import documentai_v1beta3 as documentai
import io

"""

 NOT YET FINISHED/DECIDED

def process_document(project_id, input_uri, mime_type="application/pdf"):
    # Initialize the Document AI client
    client = documentai.DocumentUnderstandingServiceClient()

    # Set up the GCS input configuration
    gcs_input_uri = f"gs://{input_uri}"
    gcs_source = documentai.types.GcsSource(uri=gcs_input_uri)
    input_config = documentai.types.InputConfig(
        gcs_source=gcs_source,
        mime_type=mime_type,
    )

    # Set up the GCS output configuration
    gcs_output_uri = "gs://your-output-bucket/output/"
    gcs_destination = documentai.types.GcsDestination(uri=gcs_output_uri)
    output_config = documentai.types.OutputConfig(gcs_destination=gcs_destination)

    # Set up the request for Document AI
    request = documentai.types.ProcessRequest(
        name=f"projects/{project_id}/locations/us/processors/{your_processor_id}",
        raw_document=documentai.types.RawDocument(content=input_config),
        output_config=output_config,
    )

    # Process the document
    result = client.process_document(request=request)
    return result
"""


def extract_text_from_document(response):
    # Extract text
    document = response.document
    text = document.text

    # Print or return the extracted text for analysis
    print(text)
    return text


def classify_document(text):
    # Simple keyword-based classification
    invoice_keywords = ['invoice', 'total amount', 'invoice number', 'due date']
    form_2307_keywords = ['withholding tax', 'taxpayer', 'form 2307']

    # Check if the text contains any of the keywords for invoice or form 2307
    if any(keyword.lower() in text.lower() for keyword in invoice_keywords):
        return "Invoice"
    elif any(keyword.lower() in text.lower() for keyword in form_2307_keywords):
        return "Form 2307"
    else:
        return "Unknown Document Type"