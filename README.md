# docai_parse_codes
These codes are for a project that uses Document AI API etc. from GCP 



HOW TO TEST LOCALLY

  to test extracting using document AI with a specific processor and finalizing the output, you can uncomment the:
  
        gcs_output_uri = f"gs://practice_sample_training/docai/"                  
        gcs_input_uri = f"gs://run-sources-medtax-ocr-prototype-us-central1/4 form 2307 pictures.pdf"
        input_mime_type = "application/pdf"
  
  part from the def main() function of extractor_caller.py file, just specificy the document you want to use in the gcs_input_uri and 
  location where the output will go in gcs_output_uri. 
  (Sample Documents are located in practice_sample_training bucket)

  after doing so, you can uncomment the print lines that are for testing/debugging purposes in the handle_data.py
  so the result gets printed in the terminal or just check the output file in the bucket and file path you specified,
  files taht ends with "_finalized.json" are the extracted final values
