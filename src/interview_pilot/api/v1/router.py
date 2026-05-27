from fastapi import APIRouter

from interview_pilot.api.v1.endpoints import auth, health, notes, questions, reviews, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
