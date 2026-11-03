from decimal import Decimal

from src.price_watch import CatalogOffer, decide_reviews


def test_moderation_review_catches_low_and_unpriced_offers():
    offers = (
        CatalogOffer("Starter pack", Decimal("8.00")),
        CatalogOffer("Season bundle", Decimal("15.00")),
        CatalogOffer("Creator bundle", None),
    )

    decisions = decide_reviews(offers, Decimal("12.00"))

    assert [decision.review for decision in decisions] == [True, False, True]
    assert decisions[0].reason == "below reference"
    assert decisions[2].reason == "amount missing"
