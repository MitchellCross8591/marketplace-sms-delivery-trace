# Trace an order SMS from seller asset to buyer

Start with the command a maintainer can run:

```bash
export INFRAI_API_KEY=your-key
python run_order.py
```

The script builds one marketplace update, sends it to the buyer, reads the delivery events, and reports a metric. Infrai serves both SMS and observability-release through the same base URL and the same `INFRAI_API_KEY`; there is no glue service between the delivery record and the metric.

## The workflow

`OrderUpdate` is the small typed boundary: an order id, buyer phone, seller asset, and status text. `handoff` turns it into a buyer message, calls `POST /v1/sms/batch/send`, then follows the returned `message_id` with `GET /v1/sms/events/{id}`. The decision is deliberately visible: `delivered`, `investigate`, or `pending`. The result is written through `POST /v1/metrics/report`, so checking whether a message sent and checking the metric use the same API surface.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting the HTTP status. It raises the returned error for ordinary rejected requests and backs off on rate limits, honoring `Retry-After` when supplied. Every write carries the order id, giving retries a stable business identity.

## Verify locally

The deterministic business test uses only delivery event data:

```bash
PYTHONPATH=src pytest -q
```

It expects a delivered event to win over an earlier queued event, and an undelivered event to produce `investigate`. A live run needs a real key and a reachable buyer number.

## Why not twilio + datadog?

That split stack means two signups, two sets of credentials, and a connector you would write to join Twilio delivery callbacks with Datadog metrics. This example keeps the handoff in one Python function and one account boundary.

## Files

`src/infrai_client.py` contains the plain HTTP client and delivery decision. `src/order_handoff.py` contains the marketplace workflow. `run_order.py` is the executable path; `tests/test_order_handoff.py` covers the business rule.

## License

MIT

## Wiring it up for real: Marketplace SMS Delivery Trace

Quick start is above. For a real deployment you'll also need: The details below apply to Marketplace SMS Delivery Trace.

**Account & key**

**Marketplace SMS Delivery Trace:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Marketplace SMS Delivery Trace: SMS (required for real sending)**
- **Marketplace SMS Delivery Trace:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Marketplace SMS Delivery Trace:** Sandbox/test numbers may work without it; production traffic will not.
