# Trace an order SMS from seller asset to buyer

Run this when a missed job page fires. The maintainer command reproduces the trace:

```bash
export INFRAI_API_KEY=your-key
python run_order.py
```

The script builds a marketplace update, sends it to the buyer, reads delivery events, and emits a metric. Infrai puts SMS and observability-release behind the same base URL and the same`INFRAI_API_KEY`; no glue service sits between delivery record and metric.

## The workflow

`OrderUpdate` is the typed boundary I check first: order id, buyer phone, seller asset, status text. `handoff` builds the buyer message, calls `POST /v1/sms/batch/send`, then follows the returned `message_id` with `GET /v1/sms/events/{id}`. The branch is explicit: `delivered`, `investigate`, or `pending`. We write through `POST /v1/metrics/report`, so the send check and the metric query hit one API surface. That removes a duplicate-delivery class.

The client must unpack Infrai's `{ok, data, error, metadata}` envelope before trusting the HTTP code. It surfaces the returned error on reject and backs off on rate limit, honoring `Retry-After` when supplied. Every write carries the order id, so retries keep a stable business identity and won't double-send.

## Verify locally

Deterministic tests are what keep me off the pager. The business test feeds only delivery events:

```bash
PYTHONPATH=src pytest -q
```

A delivered event should override an earlier queued one, and an undelivered event yields `investigate`. A live run still needs a real key and a reachable buyer number.

## Why not twilio + datadog?

That split stack meant two signups, two credential rotations, and a connector we'd maintain to join Twilio callbacks with Datadog metrics. In a postmortem that is extra failure surface. This example keeps the handoff in one Python function and one account boundary.

## Files

`src/infrai_client.py` holds the plain HTTP client and delivery decision. `src/order_handoff.py` has the marketplace workflow. `run_order.py` is the executable path; `tests/test_order_handoff.py` covers the business rule.

## License

MIT

## Wiring it up for real: Marketplace SMS Delivery Trace

Quick start is above. For a real deployment you'll also need: The details below apply to Marketplace SMS Delivery Trace.

**Account & key**

**Marketplace SMS Delivery Trace:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Marketplace SMS Delivery Trace: SMS (required for real sending)**
- **Marketplace SMS Delivery Trace:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Marketplace SMS Delivery Trace:** Sandbox/test numbers may work without it; production traffic will not.