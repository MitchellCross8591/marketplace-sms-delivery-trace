import json
import os

from infrai_client import InfraiClient
from order_handoff import OrderUpdate, handoff


if __name__ == "__main__":
    if not os.environ.get("INFRAI_API_KEY"):
        raise SystemExit("Set INFRAI_API_KEY first")
    result = handoff(OrderUpdate("ORDER-42", "+15551234567", "ceramic-mug-blue", "ready for pickup"), InfraiClient())
    print(json.dumps(result, indent=2))
