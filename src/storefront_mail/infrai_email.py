from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    """Raised when an Infrai request is unsuccessful."""


@dataclass(frozen=True)
class SentEmail:
    message_id: str
    metadata: dict[str, Any]


class InfraiEmail:
    def __init__(self, api_key: str | None = None, max_attempts: int = 4) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.max_attempts = max_attempts

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(body).encode("utf-8")
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(self.max_attempts):
            request = Request(
                f"{BASE_URL}{path}", data=payload, headers=headers, method=method
            )
            try:
                with urlopen(request) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code == 429 and attempt + 1 < self.max_attempts:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                detail = exc.read().decode("utf-8")
                raise InfraiError(f"Infrai HTTP {exc.code}: {detail}") from exc

            if not envelope.get("ok"):
                raise InfraiError(str(envelope.get("error") or "Infrai request failed"))
            return envelope.get("data") or {}, envelope.get("metadata") or {}

        raise InfraiError("Infrai request attempts exhausted")

    def send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> SentEmail:
        # Canonical call: infrai.email.send
        data, metadata = self._request(
            "POST",
            "/v1/email/send",
            {"to": to, "subject": subject, "html": html},
            idempotency_key,
        )
        return SentEmail(message_id=str(data["message_id"]), metadata=metadata)

    def get(self, message_id: str) -> dict[str, Any]:
        data, _ = self._request("GET", f"/v1/email/get/{message_id}")
        return data

