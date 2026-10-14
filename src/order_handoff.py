from dataclasses import dataclass
from typing import Any

from infrai_client import InfraiClient, delivery_decision


@dataclass(frozen=True)
class OrderUpdate:
    order_id: str
    buyer_phone: str
    seller_asset: str
    status_text: str


def handoff(update: OrderUpdate, client: InfraiClient) -> dict[str, Any]:
    text = f"Order {update.order_id}: {update.status_text}. Asset: {update.seller_asset}"
    sent = client.send_order_sms(update.buyer_phone, text, update.order_id)
    message_id = sent["message_id"] if isinstance(sent, dict) else sent
    events = client.delivery_events(message_id)
    decision = delivery_decision(events if isinstance(events, list) else events.get("events", []))
    client.report_metric("marketplace_sms_delivery", 1 if decision == "delivered" else 0, update.order_id)
    return {"order_id": update.order_id, "message_id": message_id, "delivery": decision}
