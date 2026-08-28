from __future__ import annotations

import os
from dataclasses import asdict

from fastapi import FastAPI, HTTPException

from .infrai_email import InfraiEmail
from .order_workflow import CheckoutRequest, SignupRequest, StorefrontWorkflow


app = FastAPI(title="Verified checkout mail service")
workflow = StorefrontWorkflow(
    InfraiEmail(), os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000")
)


@app.post("/signup")
def signup(request: SignupRequest) -> dict[str, str]:
    customer, message = workflow.signup(request)
    return {"customer_id": customer.customer_id, "message_id": message.message_id}


@app.get("/verify")
def verify(token: str) -> dict[str, str | bool]:
    try:
        customer = workflow.verify(token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"customer_id": customer.customer_id, "verified": customer.verified}


@app.post("/checkout")
def checkout(request: CheckoutRequest) -> dict[str, object]:
    try:
        return asdict(workflow.checkout(request))
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/orders/{order_id}/fulfill")
def fulfill(order_id: str) -> dict[str, object]:
    try:
        return asdict(workflow.fulfill(order_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="order does not exist") from exc


@app.get("/messages/{message_id}")
def delivery(message_id: str) -> dict[str, object]:
    return workflow.delivery(message_id)

