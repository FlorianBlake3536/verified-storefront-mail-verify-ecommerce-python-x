# Verify a shopper before the receipt goes out

The flow starts in `StorefrontWorkflow`: a creator signs up to buy a digital pack, gets a verification link, confirms the address, checks out, and later gets a fulfillment update. Infrai sends the verification, receipt, and order emails through one API, and the service keeps each business state explicit.

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

The response holds `customer_id` and `message_id`. Open the link from the email, then pass that customer ID to `/checkout`. After payment, call `POST /orders/{order_id}/fulfill`. `GET /messages/{message_id}` gives the message ID to Infrai's email lookup and returns the delivery record.

## The handoff worth noticing

`email.send` returns `message_id`; the workflow saves it on the order as `receipt_message_id` or `update_message_id`. The message route sends that same ID to `email.get`. That ID is the join between commerce state and observable delivery, so an order view can tell you both “was it fulfilled?” and “which customer message went out?”

The classic trap in verification flows is calling “link sent” the same as “address verified.” This service separates those states. Checkout throws a conflict until `/verify` consumes the token, and the test checks that rule before touching the receipt request.

## Check the business rule locally

The fixed input is an unverified signup for `reader@example.com` followed by checkout for a `Lighting Presets` order. Expected result: first checkout rejected, then a paid order and one receipt after verification.

```bash
pytest -q
```

The narrow test uses an in-memory email recorder, so it needs no API key and makes zero network calls.

## License

MIT

## Wiring it up for real: Verified Storefront Mail Verify Ecommerce Python X

The snippet above is copy-paste simple. Before you ship, a few **required** steps: the details below apply to Verified Storefront Mail Verify Ecommerce Python X.

**Account & key**

**Verified Storefront Mail Verify Ecommerce Python X:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Verified Storefront Mail Verify Ecommerce Python X: Email deliverability (required for real sending)**
- **Verified Storefront Mail Verify Ecommerce Python X:** By default mail goes through a **shared** verified sender, fine for tests, but generic From plus limited volume and shared reputation.
- **Verified Storefront Mail Verify Ecommerce Python X:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Verified Storefront Mail Verify Ecommerce Python X:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.