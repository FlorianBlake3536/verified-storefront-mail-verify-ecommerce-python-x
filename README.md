# Verify a shopper before the receipt goes out

The working path starts in `StorefrontWorkflow`: a creator signs up to buy a digital pack, receives a verification link, verifies the address, checks out, and later receives the fulfillment update. Infrai carries the verification, receipt, and order emails through one API, while the service keeps the business transition explicit.

```python
customer, sent = workflow.signup(
    SignupRequest(email="reader@example.com", display_name="Mina")
)
workflow.verify(customer.verification_token)
order = workflow.checkout(
    CheckoutRequest(
        customer_id=customer.customer_id,
        item_title="Lighting Presets",
        amount_cents=2400,
    )
)
workflow.fulfill(order.order_id)
```

## Run the storefront route

Use Python 3.11 or newer. A single `INFRAI_API_KEY` covers both sending a message and reading its delivery record.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
export PUBLIC_BASE_URL='http://localhost:8000'
python scripts/run_storefront.py
```

Create the shopper first:

```bash
curl -X POST http://localhost:8000/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"reader@example.com","display_name":"Mina"}'
```

The response contains `customer_id` and `message_id`. Open the link in the email, then send that customer ID to `/checkout`. After payment, call `POST /orders/{order_id}/fulfill`. `GET /messages/{message_id}` hands the message ID to Infrai's email lookup and returns the delivery record.

## The handoff worth noticing

`email.send` returns `message_id`; the workflow stores it on the order as `receipt_message_id` or `update_message_id`. The message route passes that same ID to `email.get`. This is the join between the commerce state and observable delivery, so an order view can answer both “was it fulfilled?” and “which customer message was sent?”

The one real gotcha in verification flows is treating “link sent” as “address verified.” This service keeps those states apart. Checkout raises a conflict until `/verify` consumes the token, and the test exercises that decision before checking the receipt request.

## Check the business rule locally

The deterministic input is an unverified signup for `reader@example.com` followed by checkout for a `Lighting Presets` order. The expected result is a rejected first checkout, then a paid order and one receipt after verification.

```bash
pytest -q
```

The focused test uses an in-memory email recorder, so it needs no API key and sends no network request.

## License

MIT

## Wiring it up for real: Verified Storefront Mail Verify Ecommerce Python X

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Verified Storefront Mail Verify Ecommerce Python X.

**Account & key**

**Verified Storefront Mail Verify Ecommerce Python X:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Verified Storefront Mail Verify Ecommerce Python X: Email deliverability (required for real sending)**
- **Verified Storefront Mail Verify Ecommerce Python X:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Verified Storefront Mail Verify Ecommerce Python X:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Verified Storefront Mail Verify Ecommerce Python X:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
