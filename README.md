
#  docai_parse_codes

> Utility scripts for integrating with **Google Cloud Document AI API** and processing document data.  
> Built for `medtax-ocr-prototype` on GCP.
> Let us know if we miss something to provide
---

##  Features
- Extracts document data from PDFs/images using **Document AI**.
- Processes and finalizes structured JSON output.
- Supports local testing or running in **Google Cloud Shell**.
- Includes a webhook sender to push results to a front-end application.

---

##  How to Test Locally

> **Note:** If you are using **Google Cloud Shell**, you can skip this section.

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

Testing Extraction
In extractor_caller.py, uncomment and update:
```python
  gcs_output_uri = "gs://practice_sample_training/docai/"
  gcs_input_uri = "gs://run-sources-medtax-ocr-prototype-us-central1/4 form 2307 pictures.pdf"
  input_mime_type = "application/pdf"
```

gcs_input_uri: path to the document you want to process.

gcs_output_uri: path where processed files will be saved.

To see the results:
  Uncomment print lines in handle_data.py to see results in your terminal.
  Or check the output file in your GCS bucket — files ending with _finalized.json contain extracted values.

## How to Test POST with Webhook
Create a .env file and create a WEBHOOK_URL and WEBHOOK_SECRET like this:
```env
  WEBHOOK_SECRET = "WHATEVER THIS IS"
  WEBHOOK_URL = "http://localhost:3000/api/webhook"
```
Just make sure it is the same WEBHOOK_SECRET as the one used in front-end

Open send_back.py and update:

```python
  bucket = bucket = storage_client.bucket("processed_output_bucket")
  blob = bucket.blob("processed_path/16746721153392958237/0/DUMMY 2 - 2307 - ROBERT-0_finalized.json")
```
To the bucket and finalized file of your choice.
And then run the python file 

```python
  python3 send_back.py
```

## In Production
When hosting the site:

Update `WEBHOOK_URL` to the production link.

Replace `WEBHOOK_SECRET` with a secure, random string.



