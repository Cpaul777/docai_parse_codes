# Uses firebase admin to bypass the security rules of the firebase
import firebase_admin
from firebase_admin import firestore
from typing import Optional
import re

# Application Default credentials are automatically created.
# Initialize Firebase App + Firestore Client
app = firebase_admin.initialize_app()
# "extracted-data-db" is the name of the database
db = firestore.client(app, "extracted-data-db")

# This function gives the document a unique name
def check_for_doc(collection, docname):
    """ Will check firestore if the file already exists
        if it does, it will add an incrementation (1), (2) etc.
    """
    collection_ref = db.collection(collection)
    counter = 1
    name = docname

    # Keep looking until the document has no similar name
    while True:
        if collection_ref.document(name).get().exists:
            name = f"{docname}({counter})"
            counter += 1
        else:
            break
    return name

# Writes to firestore database
def write_to_firestore(data, prefix: str, collection):
    # Extract the last part of the prefix which is the file name
    match = re.search(r'[^/]+$', prefix)
    docname = match.group(0) if match else prefix
    pdf_name = docname

    # Ensure the name is unique
    docname = check_for_doc(collection, docname)

    if match:
        print(f"Document name extracted: {docname}")
    if collection:
        print("Writing to database")
        
        # Write the document to a specified collection
        doc_ref = db.collection(collection).document(docname)
        doc_ref.set(data)
        
        # Attach a pdf name, this is used for locating the PDF for preview
        doc_ref.set({"pdf_name" : f"{pdf_name}.pdf"}, merge=True)
    else:
        # Default to "user" collection if none provided
        print("Writing to user Collection")
        doc_ref = db.collection("user").document(docname)
        doc_ref.set(data)
        doc_ref.set({"pdf_name" : f"{pdf_name}.pdf"}, merge=True)

# For testing
if __name__ == '__main__':
    data = {"first": "Ada", "last": "Lovelace", "born": 1815, "Diedat": 1852}
    user = "users"
    prefix = "alovelace"
    write_to_firestore(data, prefix, user)
