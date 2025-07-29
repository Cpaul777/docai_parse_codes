from google.cloud import storage
import cv2
import numpy as np


def preprocess_like_docai(bucket_name, input_blob_name, output_blob_name):
    """
    Deskew, denoise, and enhance image as closely as possible to Document AI preprocessing.
    Using Image Moments for Deskewing.
    """
    print("Starting preprocessing...")

    # Init GCS client and load the image from the bucket
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(input_blob_name)

    image_bytes = blob.download_as_bytes()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Use color image (not grayscale for deskew)

    if image is None:
        raise ValueError("Failed to decode image from GCS blob")

    # 1. Convert to grayscale (for deskewing and other processing)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. Adaptive Threshold to binarize the image
    binarized = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    # 3. Deskew using Image Moments
    # Find contours in the binary image
    contours, _ = cv2.findContours(binarized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Get the largest contour based on area
    largest_contour = max(contours, key=cv2.contourArea)

    # Get the rotated bounding box of the largest contour
    rect = cv2.minAreaRect(largest_contour)
    angle = rect[2]

    # Adjust the angle if necessary (fix range of angle)
    if angle < -45:
        angle = 90 + angle

    # Get the center of the image
    (h, w) = binarized.shape
    center = (w // 2, h // 2)

    # Calculate the rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Apply the rotation matrix to deskew the image
    deskewed = cv2.warpAffine(
        binarized, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    # 4. Denoise the image using Non-Local Means Denoising
    denoised = cv2.fastNlMeansDenoising(deskewed, h=30)

    # # 5. Enhance the contrast using histogram equalization
    # enhanced = cv2.equalizeHist(denoised)

    # 6. Encode the image to PNG format
    success, encoded = cv2.imencode(".png", denoised)
    if not success:
        raise ValueError("Image encoding failed")

    print("Preprocessing complete, uploading...")

    # Modify the output filename to ensure it has "_processed"
    final_blob = output_blob_name.replace(".png", "_processed.png")
    output_blob = bucket.blob(final_blob)

    # Upload the processed image back to the bucket
    output_blob.upload_from_string(encoded.tobytes(), content_type="image/png")

    print(f"✅ Uploaded processed image to: gs://{bucket_name}/{final_blob}")
    return f"gs://{bucket_name}/{final_blob}"


def main():
    return preprocess_like_docai(
        bucket_name="practice_sample_training",
        input_blob_name="training_sample/page_76.png",
        output_blob_name="docai/page_76_file(3).png"
    )

main()
