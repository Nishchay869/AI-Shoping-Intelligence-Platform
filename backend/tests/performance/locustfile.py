"""Load test: run against a real running instance (local uvicorn or a deployed environment), never against
TestClient/mocks - performance testing only means something against the real ASGI server, real DB connection
pool, and real network stack.

Usage:
    locust -f tests/performance/locustfile.py --host http://localhost:8000

Or headless, for a quick CI-friendly smoke run:
    locust -f tests/performance/locustfile.py --host http://localhost:8000 \\
           --users 20 --spawn-rate 5 --run-time 30s --headless --only-summary

Tasks are weighted to approximate real traffic shape for this app: browsing/searching the catalog dominates,
writes (register/review) are rare, and the personalized-recommendations path (the heaviest single request -
it runs a real pgvector query at read time) gets deliberately exercised on every authenticated user.
"""
import random

from locust import HttpUser, between, task


class ShopperUser(HttpUser):
    """A signed-in shopper: browses/searches/tracks activity for the rest of the run.

    Auth is now Supabase's responsibility, not this backend's - there's no local register/login endpoint
    left to mint a token from here. The auth-required tasks below (track_a_click,
    personalized_recommendations) already guard on `self.headers` and simply no-op without a real Supabase
    access token; get one manually (sign up via the frontend, then read it from localStorage) and set
    `self.headers` in on_start if you need to load-test the authenticated paths specifically.
    """

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        self.headers: dict[str, str] = {}

    @task(10)
    def browse_products(self) -> None:
        self.client.get("/api/v1/products", params={"limit": 20}, name="/products [list]")

    @task(6)
    def search_products(self) -> None:
        query = random.choice(["headphones", "speaker", "watch", "laptop", "shoes"])
        self.client.get("/api/v1/products", params={"q": query}, name="/products [search]")

    @task(3)
    def view_one_product(self) -> None:
        listing = self.client.get("/api/v1/products", params={"limit": 1}, name="/products [for detail lookup]").json()
        if listing:
            self.client.get(f"/api/v1/products/{listing[0]['id']}", name="/products/{id}")

    @task(2)
    def track_a_click(self) -> None:
        if not self.headers:
            return
        listing = self.client.get("/api/v1/products", params={"limit": 1}, name="/products [for click tracking]").json()
        if listing:
            self.client.post("/api/v1/activity/click", json={"product_id": listing[0]["id"]}, headers=self.headers, name="/activity/click")

    @task(2)
    def personalized_recommendations(self) -> None:
        """The single heaviest read in the app: a real pgvector cosine search against the whole product
        embedding index, run fresh on every call (see services/personalization.py) - the one endpoint whose
        p95 latency matters most as the catalog grows."""
        if not self.headers:
            return
        self.client.get("/api/v1/recommendations/personalized", headers=self.headers, name="/recommendations/personalized")

    @task(1)
    def check_health(self) -> None:
        self.client.get("/health", name="/health")


class AnonymousBrowserUser(HttpUser):
    """A not-signed-in visitor: only hits endpoints that don't require auth - the far more common case for
    a real storefront's traffic than the signed-in path above."""

    wait_time = between(1.0, 3.0)

    @task(5)
    def browse_products(self) -> None:
        self.client.get("/api/v1/products", params={"limit": 20}, name="/products [list, anon]")

    @task(3)
    def search_products(self) -> None:
        query = random.choice(["headphones", "speaker", "watch"])
        self.client.get("/api/v1/products", params={"q": query}, name="/products [search, anon]")
