from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from enum import StrEnum
from html import escape
from typing import Protocol

from .infrai_email import SentEmail


class EmailPort(Protocol):
    def send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> SentEmail: ...

    def get(self, message_id: str) -> dict[str, object]: ...


@dataclass(frozen=True)
class SignupRequest:
    email: str
    display_name: str

    def __post_init__(self) -> None:
        local, separator, domain = self.email.partition("@")
        if not separator or not local or not domain or "@" in domain or any(
            character.isspace() for character in self.email
        ):
            raise ValueError("email must be a valid address")
        if not 1 <= len(self.display_name) <= 80:
            raise ValueError("display_name must contain between 1 and 80 characters")


@dataclass(frozen=True)
class CheckoutRequest:
    customer_id: str
    item_title: str
    amount_cents: int

    def __post_init__(self) -> None:
        if not 1 <= len(self.item_title) <= 160:
            raise ValueError("item_title must contain between 1 and 160 characters")
        if self.amount_cents <= 0:
            raise ValueError("amount_cents must be greater than zero")


@dataclass(frozen=True)
class VerificationRequest:
    token: str


class OrderState(StrEnum):
    PAID = "paid"
    FULFILLED = "fulfilled"


@dataclass
class Customer:
    customer_id: str
    email: str
    display_name: str
    verification_token: str
    verified: bool = False


@dataclass
class Order:
    order_id: str
    customer_id: str
    item_title: str
    amount_cents: int
    state: OrderState
    receipt_message_id: str | None = None
    update_message_id: str | None = None


class StorefrontWorkflow:
    def __init__(self, email: EmailPort, public_base_url: str) -> None:
        self.email = email
        self.public_base_url = public_base_url.rstrip("/")
        self.customers: dict[str, Customer] = {}
        self.orders: dict[str, Order] = {}

    def signup(self, request: SignupRequest) -> tuple[Customer, SentEmail]:
        customer_id = self._stable_id("customer", str(request.email))
        token = secrets.token_urlsafe(24)
        customer = Customer(
            customer_id, str(request.email), request.display_name, token
        )
        self.customers[customer_id] = customer
        link = f"{self.public_base_url}/verify?token={token}"
        message = self.email.send(
            to=customer.email,
            subject="Verify your email for Frame Shop",
            html=(
                f"<p>Hi {escape(customer.display_name)},</p>"
                f'<p><a href="{escape(link)}">Verify your email</a> to continue to checkout.</p>'
            ),
            idempotency_key=f"signup-verification:{customer_id}:{self._stable_id('token', token)}",
        )
        return customer, message

    def verify(self, token: str) -> Customer:
        customer = next(
            (item for item in self.customers.values() if item.verification_token == token),
            None,
        )
        if customer is None:
            raise ValueError("verification token is invalid")
        customer.verified = True
        return customer

    def checkout(self, request: CheckoutRequest) -> Order:
        customer = self.customers.get(request.customer_id)
        if customer is None:
            raise ValueError("customer does not exist")
        if not customer.verified:
            raise PermissionError("verify the customer email before checkout")

        order_id = self._stable_id(
            "order", f"{request.customer_id}:{request.item_title}:{request.amount_cents}"
        )
        order = Order(
            order_id,
            customer.customer_id,
            request.item_title,
            request.amount_cents,
            OrderState.PAID,
        )
        receipt = self.email.send(
            to=customer.email,
            subject=f"Receipt for order {order_id}",
            html=(
                f"<p>Payment received for {escape(order.item_title)}.</p>"
                f"<p>Total: ${order.amount_cents / 100:.2f}</p>"
            ),
            idempotency_key=f"receipt:{order_id}",
        )
        order.receipt_message_id = receipt.message_id
        self.orders[order_id] = order
        return order

    def fulfill(self, order_id: str) -> Order:
        order = self.orders[order_id]
        customer = self.customers[order.customer_id]
        order.state = OrderState.FULFILLED
        update = self.email.send(
            to=customer.email,
            subject=f"Order {order_id} is ready",
            html=f"<p>Your copy of {escape(order.item_title)} is ready.</p>",
            idempotency_key=f"fulfilled:{order_id}",
        )
        order.update_message_id = update.message_id
        return order

    def delivery(self, message_id: str) -> dict[str, object]:
        return self.email.get(message_id)

    @staticmethod
    def _stable_id(namespace: str, value: str) -> str:
        digest = hashlib.sha256(f"{namespace}:{value}".encode()).hexdigest()[:12]
        return f"{namespace}_{digest}"
