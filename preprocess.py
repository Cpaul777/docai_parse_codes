from google.cloud import storage
import cv2
import numpy as np

bucket_name = "practice_sample_training"
input_blob_name = "training_sample/page_76.png"
output_blob_name = "docai/page_76_file.png"

def preprocess_in_memory(bucket_name, input_blob_name, output_blob_name):
    print("Preprocessing image...")

    # GCS setup
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(input_blob_name)

    # Download image as bytes
    image_bytes = blob.download_as_bytes()

    # Convert bytes to NumPy array
    np_arr = np.frombuffer(image_bytes, np.uint8)

    # Decode image from memory
    img = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
    
    # Apply thresholding for better edge detection
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    """
    # THIS IS FOR ROTATING THE IMAGE (UNNECESSARY IF IT GOES THROUGH DOCUMENT AI OCR)

    # Detect edges and find the angle of skew
     coords = np.column_stack(np.where(thresh > 0))
     angle = cv2.minAreaRect(coords)[-1]

     if angle < -45:
         angle = -(90 + angle)
     else:
         angle = -angle

     print("Fixing the angle...")

     Rotate image to deskew
     (h, w) = img.shape
     center = (w // 2, h // 2)
     M = cv2.getRotationMatrix2D(center, angle, 1.0)
     deskewed = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    """
    # Denoise or smooth images here if needed
    cleaned = cv2.fastNlMeansDenoising(thresh, h=30)
    
    # Optional: Enhance contrast
    enhanced = cv2.equalizeHist(cleaned)

    # Encode processed image to PNG (still in memory)
    print("Encoding the image...")
    success, encoded_image = cv2.imencode('.png', enhanced)
    if not success:
        raise ValueError("Image encoding failed")

    # Upload processed image to GCS
    print("Uploading the image to the bucket...")
    output_blob_name = output_blob_name.replace(".png", "_processed.png")
    output_blob = bucket.blob(output_blob_name)
    output_blob.upload_from_string(encoded_image.tobytes(), content_type="image/png")

    print(f"Processed image uploaded to gs://{bucket_name}/{output_blob_name}")

    return output_blob_name

def main():
    # IGNORE FOR NOW DOCUMENT AI DOES PREPROCESSING FOR DESKEWING
    return preprocess_in_memory(bucket_name, input_blob_name, output_blob_name)

