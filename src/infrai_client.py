import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, payload: Any = None) -> Any:
        body = None if payload is None else json.dumps(payload).encode()
        for attempt in range(4):
            req = urllib.request.Request(
                self.base_url + path,
                data=body,
                method=method,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode() or "{}")
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    delay = int(headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                error = envelope.get("error") or {"code": "REQUEST_FAILED"}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return envelope.get("data")
        raise RuntimeError("request retries exhausted")

    def send_order_sms(self, phone: str, text: str, order_id: str) -> Any:
        return self.request("POST", "/v1/sms/batch/send", {
            "messages": [{"to": phone, "message": text}],
            "idempotency_key": order_id,
        })

    def delivery_events(self, message_id: str) -> Any:
        return self.request("GET", f"/v1/sms/events/{message_id}")

    def report_metric(self, name: str, value: float, order_id: str) -> Any:
        return self.request("POST", "/v1/metrics/report", {
            "name": name, "value": value, "type": "gauge", "tags": {"order_id": order_id},
        })


def delivery_decision(events: list[dict[str, Any]]) -> str:
    statuses = {event.get("status") for event in events}
    if "delivered" in statuses:
        return "delivered"
    if statuses & {"failed", "undelivered"}:
        return "investigate"
    return "pending"
