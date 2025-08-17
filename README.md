
#  docai_parse_codes

> Utility scripts for integrating with **Google Cloud Document AI API** and processing document data.  
> Built for `medtax-ocr-prototype` on GCP.
> 
> Let us know if we miss something to provide
---

##  Features
- Extracts document data from PDFs/images using **Document AI**.
- Processes and finalizes structured JSON output.
- Supports local testing or running in **Google Cloud Shell**.
- Includes a firestore writing process to store data.

---

##  How to Test Locally

> **Note:** If you are using **Google Cloud Shell**, you can skip the setup section.

### Setup Google Cloud
- Install **Google Cloud SDK**:  
  [Download GoogleCloudSDKInstaller.exe](https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe)
- In your project folder, run:
```bash
gcloud init
gcloud auth application-default login
```

This opens a browser — sign in with the Google account that has project access.
  Set the project:
```bash
gcloud config set project medtax-ocr-prototype
```
If a browser didn't open, copy the link and paste it on your browser

Install Dependencies:
```bash
pip install -r requirements.txt
```

## Testing Extraction
In `extractor_caller.py`, uncomment and update:
```python
gcs_output_uri = "gs://practice_sample_training/docai/"
gcs_input_uri = "gs://run-sources-medtax-ocr-prototype-us-central1/4 form 2307 pictures.pdf"
input_mime_type = "application/pdf"
```

**gcs_input_uri:** path to the document you want to process.

**gcs_output_uri:** path where processed files will be saved.

To see the results:
  Uncomment print lines in `handle_data.py` to see results in your terminal.
  Or check the output file in your GCS bucket — files ending with **_finalized.json** contain extracted values.





## Documentation links
- [Setup Document AI](https://cloud.google.com/document-ai/docs/setup)
- [Send Process Request Sample Code Used](https://cloud.google.com/document-ai/docs/send-request#batch-process)
- 
