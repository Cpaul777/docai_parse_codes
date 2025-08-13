import functions_framework
from cloudevents.http import CloudEvent
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

    result = {"bucket": bucket, "name": name}
    response = send_back.send_result_to_frontend(result)

    print("Process Done", response)