"""One-off demo: feed a real scraped product price into the actual pricing/alert pipeline end-to-end.

Not a permanent feature (there's no real retailer-API price feed in this backend yet - see
services/pricing.py's docstring) - this exists to prove record_price_observation -> price_alerts ->
whatsapp actually fires together, using one real scraped data point instead of a live price feed.

Usage (from backend/, venv active):
    echo '{"title": "...", "price_minor": 3099900, "currency": "INR", "url": "https://...", "available": true}' \
        | python -m scripts.demo_scraped_price_alert <user_email>
"""
import json
import sys
from uuid import uuid4
from app.db.session import SessionLocal
from app.models import Product, ProductOffer, Retailer, User, Wishlist, WishlistItem
from app.services.pricing import record_price_observation


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: echo '<scraped-json>' | python -m scripts.demo_scraped_price_alert <user_email>")
        sys.exit(1)
    user_email = sys.argv[1]
    scraped = json.loads(sys.stdin.read())

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == user_email).one()

        retailer = db.query(Retailer).filter(Retailer.code == "demo_scraper").one_or_none()
        if not retailer:
            retailer = Retailer(name="Demo Scraper Source", code="demo_scraper", website_url="https://example.com")
            db.add(retailer)
            db.commit()
            db.refresh(retailer)

        offer = db.query(ProductOffer).filter(ProductOffer.retailer_id == retailer.id, ProductOffer.external_listing_id == scraped["url"]).one_or_none()
        if not offer:
            baseline_price_minor = scraped["price_minor"] + 200_000  # simulate a higher "previous" price so this first observation reads as a drop
            product = Product(
                id=uuid4(),
                title=scraped["title"],
                currency=scraped["currency"],
                current_price_minor=baseline_price_minor,
                retailer=retailer.name,
                image_url=scraped.get("image_url"),
            )
            db.add(product)
            db.commit()
            db.refresh(product)

            offer = ProductOffer(
                id=uuid4(),
                product_id=product.id,
                retailer_id=retailer.id,
                external_listing_id=scraped["url"],
                listing_url=scraped["url"],
                currency=scraped["currency"],
                current_price_minor=baseline_price_minor,
                is_available=True,
            )
            db.add(offer)
            db.commit()
            db.refresh(offer)
            print(f"Created product {product.title!r} with baseline price {baseline_price_minor / 100:.2f} {product.currency}")
        else:
            product = db.get(Product, offer.product_id)
            print(f"Reusing existing product {product.title!r}, current price {offer.current_price_minor / 100:.2f} {offer.currency}")

        wishlist = db.query(Wishlist).filter(Wishlist.user_id == user.id).one_or_none()
        if not wishlist:
            wishlist = Wishlist(id=uuid4(), user_id=user.id)
            db.add(wishlist)
            db.commit()
            db.refresh(wishlist)

        item = db.query(WishlistItem).filter(WishlistItem.wishlist_id == wishlist.id, WishlistItem.product_id == product.id).one_or_none()
        if not item:
            item = WishlistItem(id=uuid4(), wishlist_id=wishlist.id, product_id=product.id)
            db.add(item)
        item.target_price_minor = scraped["price_minor"]  # alert fires once the observed price is at/below this
        item.last_alerted_price_minor = None  # force a fresh alert even if this demo has been run before
        db.commit()

        print(f"Recording new observed price: {scraped['price_minor'] / 100:.2f} {scraped['currency']} (was {offer.current_price_minor / 100:.2f})")
        record_price_observation(db, offer, scraped["price_minor"], scraped.get("available", True))

        db.refresh(item)
        if item.last_alerted_price_minor == scraped["price_minor"]:
            print("Alert evaluated and marked sent (check WhatsApp / the whatsapp_messages table for delivery status).")
        else:
            print("No alert was triggered - check that the target price / wishlist conditions were actually met.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
