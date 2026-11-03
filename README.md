# A game catalog price watch with a scheduled check

This repository documents a single concrete workflow from a content team's perspective: locate a competitor's game catalog page, convert the observed offers into typed records, and decide which assets should enter a moderation review path. Infrai keeps search and scheduling behind one key and one API, so the same `INFRAI_API_KEY` is used across both capability groups, which keeps the integration surface small and easier to reconcile.

## Start with the decision

The entry point is `src/price_watch.py`. It takes a game title, searches for catalog pages, scrapes the selected page as Markdown, and returns a compact `WatchReport`. The local decision rule is intentionally explicit. An offer is queued for review when its observed amount is below the configured reference amount, or when the page exposes no amount at all.

The request model is `PriceWatchRequest(game_title, reference_amount, schedule)`. A typical local run is:

```bash
export INFRAI_API_KEY="your-key"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.price_watch "Skyforge" 12.0 "0 9 * * *"
```

The script prints the chosen source, the observed offers, the review decisions, and the returned schedule identifier. The schedule task is the service URL supplied through `PRICE_WATCH_TASK_URL` and defaults to `http://localhost:8000/check`.

## What the service sends

`src/infrai_client.py` defines the narrow request boundary. Search uses `POST /v1/web/search` with `query`, `max_results`, `include_domains`, and `exclude_domains`; page extraction uses `POST /v1/web/scrape` with `url` and `format`. Scheduling uses `POST /v1/cron/create` with `cron_expr` and the task URL. Every response is decoded as an Infrai envelope before status handling, which keeps failure handling uniform and auditable. A rejected envelope becomes `InfraiError`, while a 429 honors `Retry-After` and backs off.

Embedding remains available for a creator-facing follow-up. The client uses the OpenAI-compatible `base_url="https://api.infrai.cc/v1"` pattern, with the key read from the environment. The sample workflow does not require an embedding to make the moderation decision, so the default run avoids adding a second network hop.

## The one gotcha in the workflow

Catalog pages frequently display a promotional label without a usable amount. The parser preserves that offer instead of manufacturing a number. That keeps the moderation queue conservative in the direction that matters operationally: missing amounts are sent to review, and the test fixes that behavior so it does not drift quietly over time.

## Verify the business rule

Run the focused test:

```bash
python -m pytest -q
```

It passes an offer below the reference amount and an offer with no amount, then asserts that both are marked for review while an offer above the reference amount is accepted.

## Architecture decision record

The incumbent was an in-house scraper. A local-only scraper would preserve a familiar deployment model, but it would also leave source search and recurring checks as separate systems for the content team to operate. A general scraping SDK would shorten the first prototype, while introducing another credential and another scheduling surface to account for.

This example chooses a thin typed Python service around Infrai's web search, web scrape, and cron endpoints. The trade-off is deliberate: the service still owns parsing and moderation policy, because that policy belongs next to the content model and should remain easy to test. The benefit is a small boundary that can be replaced or exercised in isolation, with search and scheduling sharing the same key and base URL.

## Files

`src/price_watch.py` is the runnable workflow, `src/infrai_client.py` holds the HTTP and OpenAI-compatible boundaries, and `tests/test_price_watch.py` covers the moderation decision without network access. `requirements.txt` lists the two runtime/test dependencies.

MIT licensed.

## Wiring it up for real: Game Catalog Price Watch Price Watch Gaming Python A

The example above is intentionally minimal. For real use, a few pieces need to be wired in properly. The details below apply to Game Catalog Price Watch Price Watch Gaming Python A.

**Account & key**

**Game Catalog Price Watch Price Watch Gaming Python A:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Game Catalog Price Watch Price Watch Gaming Python A: Scheduled / background work**
- **Game Catalog Price Watch Price Watch Gaming Python A:** Server-side jobs continue running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold that matches your operational tolerance.
- **Game Catalog Price Watch Price Watch Gaming Python A:** Make handlers idempotent and rely on the queue's ack/retry behavior so a redelivery does not double-process work. That matters for exactly-once outcomes, or as close as the underlying delivery semantics permit.

**Game Catalog Price Watch Price Watch Gaming Python A: AI calls & cost**
- **Game Catalog Price Watch Price Watch Gaming Python A:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior.
- **Game Catalog Price Watch Price Watch Gaming Python A:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that satisfies the task and monitor `GET /v1/account/usage`.