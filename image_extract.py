

from google.cloud import storage
from google.cloud import documentai
import img2pdf
import cv2, numpy as np
import base64
import re

# The bucket location
bucket_name = "document_img_bucket"

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
            if("jpeg" in mime_type or "jpg" in mime_type):
                ext = ".jpg"
            
            print("The mime type is: ", mime_type)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            print("Deskewing now")
            img = deskew_using_layout(img, page)

            img = cv2.medianBlur(img, 1)
            img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY, 35, 10)
            print("DONE")

            _, final_img = cv2.imencode(ext, img)
            new_pdf = (final_img.tobytes())
            return new_pdf
            

def upload_pdf_gcs(filename, userId, page_list):

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name) # This is the bucket where the images are stored
    output_blob = filename.replace(".json", ".pdf")

    print("The output blob from clean_img: ", output_blob)

    output_blob = re.sub(r'^.*/', '', output_blob)
    output_blob = re.sub(r'-\d(?=\.)', '', output_blob)
    print("New output_blob: ", output_blob)

    output_blob = f"{userId}/{output_blob}"
    print("Applied the userId: ", output_blob )

    new_pdf = img2pdf.convert(page_list)

    # Upload to GCS
    image_blob = bucket.blob(output_blob)
    image_blob.upload_from_string(new_pdf, content_type="application/pdf")
    print("sucessfully uploaded image in: ", output_blob)
        
if __name__ == '__main__':
    # For testing purposes
    # GCS setup
    storage_client = storage.Client()
    bucket = storage_client.bucket("practice_sample_training")
    blob = bucket.blob("results/15737412520703530062/0/124-0.json")
    
    # Load Document JSON
    document = documentai.Document.from_json(blob.download_as_bytes())
    result = clean_img(blob)
    if result is None:
        raise ValueError("No image to convert")
    with open("savedpdf.pdf", "wb") as f:
        f.write(img2pdf.convert(result))  #type: ignore



""""""