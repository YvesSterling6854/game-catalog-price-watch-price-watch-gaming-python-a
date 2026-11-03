import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class PriceWatchRequest:
    game_title: str
    reference_amount: Decimal
    schedule: str


@dataclass(frozen=True)
class CatalogOffer:
    name: str
    amount: Decimal | None


@dataclass(frozen=True)
class ReviewDecision:
    offer: CatalogOffer
    review: bool
    reason: str


@dataclass(frozen=True)
class WatchReport:
    source: str
    decisions: tuple[ReviewDecision, ...]
    job_id: str


def decide_reviews(offers: Iterable[CatalogOffer], reference_amount: Decimal) -> tuple[ReviewDecision, ...]:
    decisions = []
    for offer in offers:
        if offer.amount is None:
            decisions.append(ReviewDecision(offer, True, "amount missing"))
        elif offer.amount < reference_amount:
            decisions.append(ReviewDecision(offer, True, "below reference"))
        else:
            decisions.append(ReviewDecision(offer, False, "within reference"))
    return tuple(decisions)


def offers_from_markdown(markdown: str) -> tuple[CatalogOffer, ...]:
    offers = []
    for line in markdown.splitlines():
        if not line.strip().startswith("#"):
            continue
        match = re.search(r"([^$\n]+?)(?:\s+\$([0-9]+(?:\.[0-9]+)?))?$", line.lstrip("# ").strip())
        if match:
            amount = Decimal(match.group(2)) if match.group(2) else None
            offers.append(CatalogOffer(match.group(1).strip(), amount))
    return tuple(offers)


def run_watch(request: PriceWatchRequest, client: InfraiClient) -> WatchReport:
    results = client.search(f"{request.game_title} game catalog competitor assets")
    if not results:
        raise ValueError("no catalog source found")
    source = str(results[0].get("url", results[0].get("link", "")))
    decisions = decide_reviews(offers_from_markdown(client.scrape(source)), request.reference_amount)
    task = __import__("os").environ.get("PRICE_WATCH_TASK_URL", "http://localhost:8000/check")
    job_id = client.schedule(request.schedule, task)
    return WatchReport(source, decisions, job_id)


if __name__ == "__main__":
    request = PriceWatchRequest(sys.argv[1], Decimal(sys.argv[2]), sys.argv[3])
    report = run_watch(request, InfraiClient())
    print(report)
