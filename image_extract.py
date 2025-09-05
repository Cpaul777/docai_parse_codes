

from google.cloud import storage
from google.cloud import documentai
import img2pdf
import cv2, numpy as np
import base64
import re
import json
import uuid


# The target bucket for final PDF uploads (change if deploying to another bucket)
BUCKET_NAME = "document_img_bucket"

# Reuse a storage client across functions
storage_client = storage.Client()

def deskew_using_layout(img, pages):
    """
    Deskews an image using Document AI layout metadata.
    
    img: grayscale OpenCV image
    page: document.pages[i] from Document AI
    """
    angles = []
     # Collect angles of each text block from its bounding polygon
    for block in pages.blocks:
        bbox = sorted(block.layout.bounding_poly.normalized_vertices,
                      key=lambda v: (v.y, v.x))  # Sort vertices row by row
        if len(bbox) >= 2:
            
            dx = bbox[1].x - bbox[0].x
            dy = bbox[1].y - bbox[0].y
            angle = np.degrees(np.arctan2(dy, dx))
            angles.append(angle)
   
    # If no angles found, skip deskewing
    if not angles:
        print("not angles")
        return img
        
    # Use median angle for stability against outliers
    avg_angle = np.median(angles)  
    (h, w) = img.shape
    center = (w // 2, h // 2)
    
    # Create rotation matrix (negative angle = clockwise)
    M = cv2.getRotationMatrix2D(center, -avg_angle, 1.0) #type: ignore
    print("returning fixed rotation")
    return cv2.warpAffine(img, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)

def clean_img(blob):
    """
    Cleans and deskews image(s) embedded in a Document AI JSON blob.

    Args:
        blob: Google Cloud Storage Blob containing Document AI JSON output.

    Returns:
        Encoded image bytes (PNG/JPEG) for the first valid page found.
    """
     # Load Document object from JSON blob
    document = documentai.Document.from_json(
        blob.download_as_bytes()
    )

    # Iterate through all pages in the document
    for i, page in enumerate(document.pages, start=1):
        img_info = page.image
        if img_info and img_info.content:

             # Decode base64 or raw bytes content
            if(isinstance(img_info.content, bytes)):
                img_bytes = img_info.content
            else:
                img_bytes = base64.b64decode(img_info.content)
            
            # Choose extension based on mime type
            mime_type = page.image.mime_type # Example: image/png
            ext = ".png" #png by default
            if("jpeg" in mime_type.lower() or "jpg" in mime_type.lower()):
                ext = ".jpg"
                print("Entered the if statement, the extension is: ", ext)
            
            # Converts bytes to numpy array and then to grayscale image
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

            # Deskewing the image using layout info
            print("Deskewing now")
            img = deskew_using_layout(img, page)

            # Apply Preprocessing filters
            img = cv2.medianBlur(img, 1)
            img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY, 35, 10)
            print("DONE PREPROCESSING")

            # Encode cleaned image back into bytes and return it 
            _, final_img = cv2.imencode(ext, img)
            new_pdf = (final_img.tobytes())
            return new_pdf
    
def upload_pdf_gcs(filename, docType, page_list):

    """
    Stitches processed image pages into a PDF and uploads to GCS.

    Args:
        filename: Source filename (usually JSON blob name).
        docType: Document type (used as prefix in GCS).
        page_list: List of image bytes to stitch into PDF.
    """
    
    storage_client = storage.Client()
    
    # Bucket where final PDFs will be stored
    bucket = storage_client.bucket(BUCKET_NAME) 
    # Convert JSON filename to PDF filename
    output_blob = filename.replace(".json", ".pdf")

    print("The output blob from clean_img: ", output_blob)

    # Strip path and trailing page numbers (e.g., -0, -1)
    output_blob = re.sub(r'^.*/', '', output_blob)
    output_blob = re.sub(r'-\d(?=\.)', '', output_blob)
    print("New output_blob: ", output_blob)

    # Add doctype as the prefix for organization
    output_blob = f"{docType}/{output_blob}"
    print("Applied the docType: ", output_blob )

    # Stitch all images into a single PDF
    new_pdf = img2pdf.convert(page_list)

    # Upload to GCS
    image_blob = bucket.blob(output_blob)
    image_blob.upload_from_string(new_pdf, content_type="application/pdf")
    print(f"sucessfully uploaded image in: {bucket.name}/{output_blob}")

    # Generate access token 
    token = str(uuid.uuid4())

    # Add url metadata 
    image_blob.metadata = {
        "firebaseStorageDownloadTokens": token
    }
    image_blob.patch()
    print("Done adding metadata")

if __name__ == '__main__':

    # For local testing purposes
    # GCS setup
    
    bucket = storage_client.bucket("practice_sample_training")
    blob = bucket.blob("arayyy moo _24.jpg")
    print("The initial bucket: ", bucket)
    print("The initial blob: ", blob)
    
    result = preprocess(src_bucket=bucket.name, blob=blob.name, mime_type="image/jpg")
    # # Load Document JSON
    # document = documentai.Document.from_json(blob.download_as_bytes())
    # result = clean_img(blob)
    
    upload_pdf_gcs(blob.name, "sample", result)
    print("process done")
