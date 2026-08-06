from fastapi import APIRouter
from app.api.routes import activity, assistant, auth, chat, preferences, products, receipts, recommendations, reviews, wishlists

api_router = APIRouter()
api_router.include_router(activity.router)
api_router.include_router(assistant.router)
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(preferences.router)
api_router.include_router(products.router)
api_router.include_router(receipts.router)
api_router.include_router(recommendations.router)
api_router.include_router(reviews.router)
api_router.include_router(wishlists.router)
