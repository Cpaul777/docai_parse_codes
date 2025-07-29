from google.cloud import storage
import cv2
import numpy as np


def preprocess_like_docai(bucket_name, input_blob_name, output_blob_name):
    """
    Deskew, denoise, and enhance image as closely as possible to Document AI preprocessing.
    """
    print("🚀 Starting preprocessing...")

    # Init GCS client and load the image from bucket
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(input_blob_name)

    image_bytes = blob.download_as_bytes()
    np_arr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Failed to decode image from GCS blob")

    # 1. Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. Adaptive Threshold (more robust than OTSU for scanned docs)
    binarized = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    # 3. Find skew angle and rotate
    coords = np.column_stack(np.where(binarized > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    print(f"📐 Detected skew angle: {angle:.2f} degrees")

    (h, w) = binarized.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(
        binarized, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    # 4. Denoise
    denoised = cv2.fastNlMeansDenoising(deskewed, h=30)

    # 5. Enhance contrast
    enhanced = cv2.equalizeHist(denoised)

    # 6. Encode and Upload
    success, encoded = cv2.imencode(".png", enhanced)
    if not success:
        raise ValueError("Image encoding failed")

    final_blob = output_blob_name.replace(".png", "_processed.png")
    output_blob = bucket.blob(final_blob)
    output_blob.upload_from_string(encoded.tobytes(), content_type="image/png")

    print(f"✅ Uploaded processed image to: gs://{bucket_name}/{final_blob}")
    return f"gs://{bucket_name}/{final_blob}"


def main():
    return preprocess_like_docai(
        bucket_name="practice_sample_training",
        input_blob_name="training_sample/page_76.png",
        output_blob_name="docai/page_76_file.png"
    )
