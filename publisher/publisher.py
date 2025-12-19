import requests
import os
import uuid
import random
from datetime import datetime

TARGET = os.getenv("TARGET_URL")

for i in range(50):
    event_id = str(uuid.uuid4()) if random.random() > 0.3 else "DUPLICATE-ID"

    payload = {
        "topic": "logs",
        "event_id": event_id,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "publisher",
        "payload": {"seq": i}
    }

    r = requests.post(TARGET, json=payload)
    print(r.json())
