# docai_parse_codes
These codes are for a project that uses Document AI API etc. from GCP 

HOW TO TEST LOCALLY

  You don't need to do this if you're using Cloud Shell.
  
  SETUP Google Cloud
  Install Google Cloud SDK:
  
  https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe

  In your project folder run the commands on your shell/terminal:
  
        `gcloud init`
  
  Authenticate with your google account

      `gcloud auth application-default login`
      
  This will open a browser window, sign in with the google account that
  has access to the project.

  Setup the project

  `gcloud config set project medtax-ocr-prototype`

  Install Dependencies
    Run this command inside the root of your project:

    `pip install -r requirements.txt `


Testing the functions 
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

# return

HOW TO TEST POST WITH WEBHOOK 

  Open the send_back.py and modify the blob variable and bucket variable under if __name__ == '__main__': to whatever finalized process 
  file you want to send to the front-end.

  Make sure your front-end next.js is running the server with the port localhost:3000 and you are on the page 
  http://localhost:3000/form2307

  Then you can run the file: send_back.py

IN PRODUCTION
  Once the website has been launched/hosted on the internet, if webhook will be the method for sending to front-end, 
  WEBHOOK_URL should be changed to the proper link and WEBHOOK_SECRET should be replaced with randomized string


# Notes

Requires GCP credentials with Document AI and Cloud Storage access


