

from google.cloud import storage
from google.cloud import documentai
import img2pdf
import cv2, numpy as np
import base64
import re
import uuid

# The bucket location
BUCKET_NAME = "document_img_bucket"
storage_client = storage.Client()

def deskew_using_layout(img, pages):
    """
    Deskews an image using Document AI layout metadata.
    
    img: grayscale OpenCV image
    page: document.pages[i] from Document AI
    """
    angles = []
    for block in pages.blocks:
        bbox = sorted(block.layout.bounding_poly.normalized_vertices,
                      key=lambda v: (v.y, v.x))  # sort by top row first
        if len(bbox) >= 2:
            
            dx = bbox[1].x - bbox[0].x
            dy = bbox[1].y - bbox[0].y
            angle = np.degrees(np.arctan2(dy, dx))
            angles.append(angle)
    if not angles:
        print("not angles")
        return img

    avg_angle = np.median(angles)  
    (h, w) = img.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, -avg_angle, 1.0) #type: ignore
    print("returning fixed rotation")
    return cv2.warpAffine(img, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)

def clean_img(blob):
    """
        Args:
            blob : The document to be processed
    """

    document = documentai.Document.from_json(
        blob.download_as_bytes()
    )

    for i, page in enumerate(document.pages, start=1):
        img_info = page.image
        if img_info and img_info.content:

            if(isinstance(img_info.content, bytes)):
                img_bytes = img_info.content
                
            else:
                img_bytes = base64.b64decode(img_info.content)
            
            print("type:", type(img_info.content), "decoded bytes len:", len(img_bytes))

            mime_type = page.image.mime_type # Example: image/png
            ext = ".png" #png by default
            if("jpeg" in mime_type.lower() or "jpg" in mime_type.lower()):
                ext = ".jpg"
                print("Entered the if statement, the extension is: ", ext)
            
            print("The mime type is: ", mime_type)
            
            # Decoding the image
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

            # Deskewing the image
            print("Deskewing now")
            img = deskew_using_layout(img, page)

            # Preprocessing the image
            img = cv2.medianBlur(img, 1)
            img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY, 35, 10)
            print("DONE")

            # Encoding back to bytes
            _, final_img = cv2.imencode(ext, img)
            new_pdf = (final_img.tobytes())
            return new_pdf

# This function is for service_invoice only as of now
def preprocess(src_bucket, blob, mime_type, docType):
    print("the name of the file is: ", blob)

    # Get the pic
    pic = storage_client.bucket(src_bucket).blob(blob).download_as_bytes()

    ext = ".png" #png by default
    if("jpeg" in mime_type.lower() or "jpg" in mime_type.lower()):
        ext = ".jpg"
        print("Entered the if statement, the extension is: ", ext)

    print("The mime type is: ", mime_type)

    # Decode
    nparr = np.frombuffer(pic, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError(f"Failed to decode image: {blob}")
    
    # Preprocess the image
    img = cv2.medianBlur(img, 1)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 35, 10)
    print("DONE")

    _, final_img = cv2.imencode(ext, img)
    new_pdf = img2pdf.convert((final_img.tobytes()))

    # Fixing the filename
    filename = re.sub(r'^.*/', '', blob)

    # Replace the extension ignoring sensitive case
    filename = re.sub(r"\.jpe?g$", ".pdf", filename, flags=re.IGNORECASE)

    # Prepare new name
    output_blob = f"{docType}/preprocessed_images/{filename}"    

    # Upload the new pdf and return the location
    storage_client.bucket(BUCKET_NAME).blob(output_blob).upload_from_string(new_pdf, content_type="application/pdf")

    return BUCKET_NAME, output_blob
    
    
def upload_pdf_gcs(filename, docType, page_list):

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME) # This is the bucket where the images are stored
    output_blob = filename.replace(".json", ".pdf")

    print("The output blob from clean_img: ", output_blob)

    output_blob = re.sub(r'^.*/', '', output_blob)
    output_blob = re.sub(r'-\d(?=\.)', '', output_blob)
    print("New output_blob: ", output_blob)

    output_blob = f"{docType}/{output_blob}"
    print("Applied the docType: ", output_blob )

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


    # For testing purposes
    # GCS setup
    
    bucket = storage_client.bucket("practice_sample_training")
    blob = bucket.blob("results/15737412520703530062/0/124-0.json")
    

    # Load Document JSON
    document = documentai.Document.from_json(blob.download_as_bytes())
    result = clean_img(blob)
    upload_pdf_gcs(blob.name, "sample", [result])
    print("process done")
