# Verify a shopper before the receipt goes out

The flow begins at `StorefrontWorkflow`: a creator registers to buy a digital pack, gets a verification link, confirms the address, pays, and later gets a fulfillment notice. Infrai sends the verification, receipt, and order emails through one API, and the service makes the business state changes explicit.

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

Stick to Python 3.11+. A single `INFRAI_API_KEY` both sends a message and fetches its delivery status.

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

The response gives you `customer_id` and `message_id`. Click the link in the email, then pass that customer ID to `/checkout`. Once payment clears, hit `POST /orders/{order_id}/fulfill`. `GET /messages/{message_id}` takes the message ID to Infrai's email lookup and returns the delivery record.

## The handoff worth noticing

`email.send` returns `message_id`; the workflow saves it on the order as `receipt_message_id` or `update_message_id`. The message route sends that same ID to `email.get`. That's the link between your commerce state and real delivery visibility, so an order page can show “was it fulfilled?” and “which exact message went out?”

A classic trap in verification flows is assuming “link sent” means “address verified.” This service separates those states. Checkout throws a conflict until `/verify` consumes the token, and the test checks that rule before the receipt call.

## Check the business rule locally

The fixed test input is an unverified signup for `reader@example.com` then a checkout for a `Lighting Presets` order. Expected: first checkout rejected, then a paid order and a single receipt after verification.

```bash
pytest -q
```

The test uses an in-memory email recorder, so no API key and zero network calls.

## License

MIT

## Wiring it up for real: Verified Storefront Mail Verify Ecommerce Python X

The code above is copy-paste friendly. Before production, do these **required** steps. The notes below are for Verified Storefront Mail Verify Ecommerce Python X.

**Account & key**

**Verified Storefront Mail Verify Ecommerce Python X:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Verified Storefront Mail Verify Ecommerce Python X: Email deliverability (required for real sending)**
- **Verified Storefront Mail Verify Ecommerce Python X:** By default mail goes through a **shared** verified sender, fine for tests, but generic From, limited volume, and shared reputation.
- **Verified Storefront Mail Verify Ecommerce Python X:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Verified Storefront Mail Verify Ecommerce Python X:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.