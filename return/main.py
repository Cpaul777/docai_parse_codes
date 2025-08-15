import functions_framework
from google.cloud import storage
from cloudevents.http import CloudEvent
import dir
import firestore_write
import send_back


@functions_framework.cloud_event
def sendTrigger(event: CloudEvent):
    data = event.data
    bucket = data.get("bucket")
    name = data.get("name")

    if name is None:
        print("Theres no file")
        return
    elif not (name.endswith("_finalized.json")):
        print(f"Skipped file: {name}")
        return

    print(name)

    # Initialize Storage clients to get the blob
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)
    blob = bucket.blob(name)

    metadata = event.get('metadata') or {}
    userId = metadata.get("userid")
    print("userId: ", userId)

    print(f"Fetching {blob.name}")
    document = blob.download_as_string()

    # response = send_back.send_result_to_frontend(document)

    firestore_write.write_to_firestore(document, name.split("_finalized.json")[0], userId)

    print("Process Done", name)