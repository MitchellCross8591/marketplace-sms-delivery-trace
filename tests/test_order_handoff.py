from infrai_client import delivery_decision


def test_delivery_decision_prefers_delivered_event():
    events = [{"status": "queued"}, {"status": "delivered"}]
    assert delivery_decision(events) == "delivered"


def test_delivery_decision_flags_failed_delivery():
    assert delivery_decision([{"status": "undelivered"}]) == "investigate"
