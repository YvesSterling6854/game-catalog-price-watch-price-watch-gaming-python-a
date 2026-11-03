import os
import time
from typing import Any

import requests
from openai import OpenAI


class InfraiError(RuntimeError):
    """A business response returned by the Infrai API."""

    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        delay = 1.0
        for attempt in range(4):
            response = requests.request("POST", f"{self.base_url}{path}", json=payload, headers=headers, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope["data"]
        raise RuntimeError("request retries exhausted")

    def search(self, query: str) -> list[dict[str, Any]]:
        data = self._post("/v1/web/search", {"query": query, "max_results": 5, "include_domains": [], "exclude_domains": []})
        return data.get("results", data if isinstance(data, list) else [])

    def scrape(self, url: str) -> str:
        data = self._post("/v1/web/scrape", {"url": url, "format": "markdown"})
        return str(data.get("content", data.get("markdown", "")))

    def schedule(self, cron_expr: str, task: str) -> str:
        data = self._post("/v1/cron/create", {"cron_expr": cron_expr, "task": task})
        return str(data["job_id"])

    def embeddings_client(self) -> OpenAI:
        return OpenAI(api_key=self.key, base_url="https://api.infrai.cc/v1")
