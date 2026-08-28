from storefront_mail.infrai_email import SentEmail
from storefront_mail.order_workflow import CheckoutRequest, SignupRequest, StorefrontWorkflow


class RecordingEmail:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send(self, **message: str) -> SentEmail:
        self.sent.append(message)
        return SentEmail(f"message-{len(self.sent)}", {})

    def get(self, message_id: str) -> dict[str, object]:
        return {"message_id": message_id, "status": "delivered"}


def test_checkout_waits_for_verification_then_sends_receipt() -> None:
    email = RecordingEmail()
    workflow = StorefrontWorkflow(email, "https://shop.example")
    customer, verification = workflow.signup(
        SignupRequest(email="reader@example.com", display_name="Mina")
    )
    checkout = CheckoutRequest(
        customer_id=customer.customer_id,
        item_title="Lighting Presets",
        amount_cents=2400,
    )

    try:
        workflow.checkout(checkout)
        raise AssertionError("checkout should require email verification")
    except PermissionError:
        pass

    workflow.verify(customer.verification_token)
    order = workflow.checkout(checkout)

    assert verification.message_id == "message-1"
    assert order.receipt_message_id == "message-2"
    assert email.sent[1]["idempotency_key"] == f"receipt:{order.order_id}"
    assert "Lighting Presets" in email.sent[1]["html"]


def test_repeated_signup_uses_a_new_key_for_the_new_verification_payload() -> None:
    email = RecordingEmail()
    workflow = StorefrontWorkflow(email, "https://shop.example")

    first_customer, _ = workflow.signup(
        SignupRequest(email="reader@example.com", display_name="Mina")
    )
    repeated_customer, _ = workflow.signup(
        SignupRequest(email="reader@example.com", display_name="Changed Name")
    )

    assert repeated_customer.verification_token != first_customer.verification_token
    assert email.sent[1]["html"] != email.sent[0]["html"]
    assert email.sent[1]["idempotency_key"] != email.sent[0]["idempotency_key"]
