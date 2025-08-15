import firebase_admin
from firebase_admin import firestore
from typing import Optional
import re

# Application Default credentials are automatically created.
app = firebase_admin.initialize_app()
db = firestore.client(app, "extracted-data-db")

# Writes to firestore database
def write_to_firestore(data, prefix: str, collection: Optional[str]):
    match = re.search(r'[^/]+$', prefix)
    docname = match.group(0) if match else prefix

    if match:
        print(f"Document name extracted: {docname}")
    if collection is not None:
        print("Writing to database")
        doc_ref = db.collection(collection).document(docname)
        doc_ref.set(data)
    else:
        doc_ref = db.collection("user").document(docname)
        doc_ref.set(data)

if __name__ == '__main__':
    data = {"first": "Ada", "last": "Lovelace", "born": 1815, "Diedat": 1852}
    user = "users"
    prefix = "alovelace"
    write_to_firestore(data, prefix, user)