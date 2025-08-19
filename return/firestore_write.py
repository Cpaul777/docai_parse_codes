import firebase_admin
from firebase_admin import firestore
from typing import Optional
import re

# Application Default credentials are automatically created.
app = firebase_admin.initialize_app()
db = firestore.client(app, "extracted-data-db")

def check_for_doc(collection, docname):
    """ Will check firestore if the file already exists
        if it does, it will add an incrementation (1), (2) etc.
    """
    collection_ref = db.collection(collection)
    counter = 0
    while collection_ref.document(docname).get().exists:
        name = f"{docname}({counter})"
        counter += 1
    
    return name

# Writes to firestore database
def write_to_firestore(data, prefix: str, collection: Optional[str]):
    match = re.search(r'[^/]+$', prefix)
    docname = match.group(0) if match else prefix

    docname = check_for_doc(collection, docname)

    if match:
        print(f"Document name extracted: {docname}")
    if collection:
        print("Writing to database")
        doc_ref = db.collection(collection).document(docname)
        doc_ref.set(data)
    else:
        print("Writing to user Collection")
        doc_ref = db.collection("user").document(docname)
        doc_ref.set(data)

if __name__ == '__main__':
    data = {"first": "Ada", "last": "Lovelace", "born": 1815, "Diedat": 1852}
    user = "users"
    prefix = "alovelace"
    write_to_firestore(data, prefix, user)