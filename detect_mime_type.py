
# Detect the file type
def detect_mime_type(filename):
    # Check what type of file it is
    if filename.endswith(".pdf"):
        return "application/pdf"
    elif filename.endswith(".png"):
        return "image/png"
    elif filename.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    else:
        return None